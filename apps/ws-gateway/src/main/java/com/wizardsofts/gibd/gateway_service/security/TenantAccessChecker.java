package com.wizardsofts.gibd.gateway_service.security;

import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.repository.TenantRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.UUID;

/**
 * Authorization checker for tenant access control.
 *
 * Used in @PreAuthorize expressions to verify:
 * - User is owner of the tenant
 * - User belongs to the tenant's Keycloak group
 * - User has appropriate tenant role
 *
 * Example usage:
 *   @PreAuthorize("@tenantAccessChecker.canAccess(#jwt, #tenantId)")
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TenantAccessChecker {

    private final TenantRepository tenantRepository;

    /**
     * Checks if user can access tenant by ID.
     *
     * Access granted if:
     * - User is the tenant owner (by email)
     * - User's tenant_id claim matches
     * - User belongs to tenant's Keycloak group
     */
    public boolean canAccess(Jwt jwt, UUID tenantId) {
        if (jwt == null || tenantId == null) {
            return false;
        }

        String userEmail = jwt.getClaimAsString("email");
        String userTenantId = jwt.getClaimAsString("tenant_id");

        // Check if user's tenant_id claim matches
        if (userTenantId != null && userTenantId.equals(tenantId.toString())) {
            log.debug("Access granted: tenant_id claim matches");
            return true;
        }

        // Check if user is owner
        Optional<Tenant> tenant = tenantRepository.findById(tenantId);
        if (tenant.isPresent()) {
            if (userEmail != null && userEmail.equalsIgnoreCase(tenant.get().getOwnerEmail())) {
                log.debug("Access granted: user is tenant owner");
                return true;
            }

            // Check Keycloak group membership
            if (isMemberOfTenantGroup(jwt, tenant.get())) {
                log.debug("Access granted: user belongs to tenant group");
                return true;
            }
        }

        log.debug("Access denied for user {} to tenant {}", userEmail, tenantId);
        return false;
    }

    /**
     * Checks if user can access tenant by slug.
     */
    public boolean canAccessBySlug(Jwt jwt, String slug) {
        if (jwt == null || slug == null) {
            return false;
        }

        Optional<Tenant> tenant = tenantRepository.findBySlugIgnoreCase(slug);
        return tenant.map(t -> canAccess(jwt, t.getId())).orElse(false);
    }

    /**
     * Checks if user is owner of the tenant.
     */
    public boolean isOwner(Jwt jwt, UUID tenantId) {
        if (jwt == null || tenantId == null) {
            return false;
        }

        String userEmail = jwt.getClaimAsString("email");
        if (userEmail == null) {
            return false;
        }

        return tenantRepository.findById(tenantId)
            .map(t -> userEmail.equalsIgnoreCase(t.getOwnerEmail()))
            .orElse(false);
    }

    /**
     * Checks if user is a member of the tenant's Keycloak group.
     */
    private boolean isMemberOfTenantGroup(Jwt jwt, Tenant tenant) {
        if (tenant.getKeycloakGroupId() == null) {
            return false;
        }

        // Check groups claim for tenant group membership
        Object groupsClaim = jwt.getClaim("groups");
        if (groupsClaim instanceof Iterable<?>) {
            String tenantGroupPath = "/tenant:" + tenant.getSlug();

            for (Object group : (Iterable<?>) groupsClaim) {
                if (group != null && group.toString().startsWith(tenantGroupPath)) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * Checks if user has specific role within tenant.
     */
    public boolean hasTenantRole(Jwt jwt, UUID tenantId, String role) {
        if (jwt == null || tenantId == null || role == null) {
            return false;
        }

        Optional<Tenant> tenant = tenantRepository.findById(tenantId);
        if (tenant.isEmpty()) {
            return false;
        }

        // Check groups claim for tenant role
        Object groupsClaim = jwt.getClaim("groups");
        if (groupsClaim instanceof Iterable<?>) {
            String expectedGroup = "/tenant:" + tenant.get().getSlug() + "/" + role;

            for (Object group : (Iterable<?>) groupsClaim) {
                if (expectedGroup.equals(group)) {
                    return true;
                }
            }
        }

        return false;
    }
}
