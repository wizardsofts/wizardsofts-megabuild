package com.wizardsofts.gibd.gateway_service.service;

import com.wizardsofts.gibd.gateway_service.dto.TenantRegistrationRequest;
import com.wizardsofts.gibd.gateway_service.dto.TenantRegistrationResponse;
import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.repository.TenantRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Service for tenant self-registration and lifecycle management.
 *
 * Workflow:
 * 1. Validate registration request
 * 2. Create tenant in PENDING status
 * 3. Trigger async Keycloak provisioning
 * 4. Update status to ACTIVE on success
 *
 * Enforces:
 * - Maximum tenants per owner
 * - Unique slugs
 * - Tier-based feature limits
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TenantOnboardingService {

    private final TenantRepository tenantRepository;
    private final KeycloakTenantProvisioningService keycloakService;

    @Value("${tenant.max-per-owner:5}")
    private int maxTenantsPerOwner;

    /**
     * Registers a new tenant.
     *
     * @param request Registration details
     * @return Response with tenant details and next steps
     * @throws IllegalArgumentException if validation fails
     * @throws IllegalStateException if owner has too many tenants
     */
    @Transactional
    public TenantRegistrationResponse registerTenant(TenantRegistrationRequest request) {
        log.info("Processing tenant registration for slug: {}", request.getSlug());

        // Validate slug uniqueness
        if (tenantRepository.existsBySlugIgnoreCase(request.getSlug())) {
            throw new IllegalArgumentException("Slug '" + request.getSlug() + "' is already taken");
        }

        // Check owner tenant limit
        long ownerTenantCount = tenantRepository.countActiveByOwnerEmail(request.getOwnerEmail());
        if (ownerTenantCount >= maxTenantsPerOwner) {
            throw new IllegalStateException(
                "Maximum tenant limit (" + maxTenantsPerOwner + ") reached for this email"
            );
        }

        // Parse subscription tier
        Tenant.SubscriptionTier tier = Tenant.SubscriptionTier.FREE;
        if (request.getSubscriptionTier() != null) {
            tier = Tenant.SubscriptionTier.valueOf(request.getSubscriptionTier());
        }

        // Create tenant entity
        Tenant tenant = Tenant.builder()
            .slug(request.getSlug().toLowerCase())
            .name(request.getOrganizationName())
            .ownerEmail(request.getOwnerEmail().toLowerCase())
            .tier(tier)
            .status(Tenant.TenantStatus.PENDING)
            .metadata(request.getMetadata())
            .build();

        tenant = tenantRepository.save(tenant);
        log.info("Created tenant {} with ID {}", tenant.getSlug(), tenant.getId());

        // Trigger async provisioning
        provisionTenantAsync(tenant.getId());

        return TenantRegistrationResponse.fromEntity(tenant);
    }

    /**
     * Asynchronously provisions tenant in Keycloak.
     * Updates tenant status based on result.
     */
    @Async
    @Transactional
    public void provisionTenantAsync(UUID tenantId) {
        log.info("Starting async provisioning for tenant: {}", tenantId);

        Optional<Tenant> tenantOpt = tenantRepository.findById(tenantId);
        if (tenantOpt.isEmpty()) {
            log.error("Tenant {} not found for provisioning", tenantId);
            return;
        }

        Tenant tenant = tenantOpt.get();

        try {
            // Update to provisioning status
            tenant.setStatus(Tenant.TenantStatus.PROVISIONING);
            tenantRepository.save(tenant);

            // Provision in Keycloak
            String groupId = keycloakService.provisionTenant(tenant);

            // Update tenant with Keycloak group ID and activate
            tenant.setKeycloakGroupId(groupId);
            tenant.activate();
            tenantRepository.save(tenant);

            log.info("Successfully provisioned tenant {} with Keycloak group {}", tenant.getSlug(), groupId);

        } catch (Exception e) {
            log.error("Failed to provision tenant {}: {}", tenant.getSlug(), e.getMessage());
            // Keep in PENDING status for retry
            tenant.setStatus(Tenant.TenantStatus.PENDING);
            tenantRepository.save(tenant);
        }
    }

    /**
     * Gets tenant by ID.
     */
    @Transactional(readOnly = true)
    public Optional<TenantRegistrationResponse> getTenant(UUID tenantId) {
        return tenantRepository.findById(tenantId)
            .map(TenantRegistrationResponse::fromEntity);
    }

    /**
     * Gets tenant by slug.
     */
    @Transactional(readOnly = true)
    public Optional<TenantRegistrationResponse> getTenantBySlug(String slug) {
        return tenantRepository.findBySlugIgnoreCase(slug)
            .map(TenantRegistrationResponse::fromEntity);
    }

    /**
     * Gets all tenants for an owner.
     */
    @Transactional(readOnly = true)
    public List<TenantRegistrationResponse> getTenantsByOwner(String ownerEmail) {
        return tenantRepository.findByOwnerEmailIgnoreCase(ownerEmail).stream()
            .map(TenantRegistrationResponse::fromEntity)
            .toList();
    }

    /**
     * Suspends a tenant.
     */
    @Transactional
    public TenantRegistrationResponse suspendTenant(UUID tenantId, String reason) {
        Tenant tenant = tenantRepository.findById(tenantId)
            .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + tenantId));

        log.warn("Suspending tenant {} for reason: {}", tenant.getSlug(), reason);
        tenant.suspend();
        tenant = tenantRepository.save(tenant);

        return TenantRegistrationResponse.fromEntity(tenant);
    }

    /**
     * Reactivates a suspended tenant.
     */
    @Transactional
    public TenantRegistrationResponse reactivateTenant(UUID tenantId) {
        Tenant tenant = tenantRepository.findById(tenantId)
            .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + tenantId));

        if (tenant.getStatus() != Tenant.TenantStatus.SUSPENDED) {
            throw new IllegalStateException("Tenant is not suspended");
        }

        log.info("Reactivating tenant {}", tenant.getSlug());
        tenant.activate();
        tenant = tenantRepository.save(tenant);

        return TenantRegistrationResponse.fromEntity(tenant);
    }

    /**
     * Soft deletes a tenant.
     */
    @Transactional
    public void deleteTenant(UUID tenantId) {
        Tenant tenant = tenantRepository.findById(tenantId)
            .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + tenantId));

        log.warn("Deleting tenant {}", tenant.getSlug());

        // Deprovision from Keycloak
        if (tenant.getKeycloakGroupId() != null) {
            try {
                keycloakService.deprovisionTenant(tenant.getKeycloakGroupId());
            } catch (Exception e) {
                log.error("Failed to deprovision tenant from Keycloak: {}", e.getMessage());
            }
        }

        tenant.setStatus(Tenant.TenantStatus.DELETED);
        tenantRepository.save(tenant);
    }

    /**
     * Retries provisioning for pending tenants.
     */
    @Transactional
    public void retryPendingProvisioning() {
        List<Tenant> pendingTenants = tenantRepository.findByStatus(Tenant.TenantStatus.PENDING);

        log.info("Found {} pending tenants for retry", pendingTenants.size());

        for (Tenant tenant : pendingTenants) {
            provisionTenantAsync(tenant.getId());
        }
    }
}
