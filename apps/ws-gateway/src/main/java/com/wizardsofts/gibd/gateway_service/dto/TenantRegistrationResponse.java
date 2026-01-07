package com.wizardsofts.gibd.gateway_service.dto;

import com.wizardsofts.gibd.gateway_service.model.Tenant;
import lombok.*;

import java.time.Instant;
import java.util.UUID;

/**
 * Response DTO for tenant registration.
 *
 * Returns tenant details including:
 * - Generated UUID
 * - Provisioning status
 * - Keycloak group ID (once provisioned)
 * - Next steps for the tenant owner
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TenantRegistrationResponse {

    private UUID tenantId;
    private String slug;
    private String organizationName;
    private String ownerEmail;
    private String status;
    private String subscriptionTier;
    private String keycloakGroupId;
    private Instant createdAt;
    private String message;
    private String nextSteps;

    /**
     * Factory method to create response from Tenant entity.
     */
    public static TenantRegistrationResponse fromEntity(Tenant tenant) {
        return TenantRegistrationResponse.builder()
            .tenantId(tenant.getId())
            .slug(tenant.getSlug())
            .organizationName(tenant.getName())
            .ownerEmail(tenant.getOwnerEmail())
            .status(tenant.getStatus().name())
            .subscriptionTier(tenant.getTier().name())
            .keycloakGroupId(tenant.getKeycloakGroupId())
            .createdAt(tenant.getCreatedAt())
            .message(getStatusMessage(tenant.getStatus()))
            .nextSteps(getNextSteps(tenant.getStatus()))
            .build();
    }

    private static String getStatusMessage(Tenant.TenantStatus status) {
        return switch (status) {
            case PENDING -> "Tenant registration received. Please verify your email.";
            case PROVISIONING -> "Tenant is being set up. This may take a few moments.";
            case ACTIVE -> "Tenant is active and ready to use.";
            case SUSPENDED -> "Tenant is suspended. Please contact support.";
            case DELETED -> "Tenant has been deleted.";
        };
    }

    private static String getNextSteps(Tenant.TenantStatus status) {
        return switch (status) {
            case PENDING -> "Check your email for verification link.";
            case PROVISIONING -> "Wait for setup to complete, then log in.";
            case ACTIVE -> "Log in to start using the platform.";
            case SUSPENDED -> "Contact support@wizardsofts.com to resolve.";
            case DELETED -> "Register a new tenant to continue.";
        };
    }
}
