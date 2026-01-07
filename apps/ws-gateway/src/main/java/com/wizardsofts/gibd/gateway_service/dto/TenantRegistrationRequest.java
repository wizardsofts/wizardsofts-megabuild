package com.wizardsofts.gibd.gateway_service.dto;

import jakarta.validation.constraints.*;
import lombok.*;

/**
 * Request DTO for tenant registration.
 *
 * Validates:
 * - Organization name (2-100 chars)
 * - Slug (URL-friendly identifier, 3-50 chars, lowercase alphanumeric with hyphens)
 * - Owner email (valid email format)
 * - Subscription tier (optional, defaults to FREE)
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TenantRegistrationRequest {

    @NotBlank(message = "Organization name is required")
    @Size(min = 2, max = 100, message = "Organization name must be 2-100 characters")
    private String organizationName;

    @NotBlank(message = "Slug is required")
    @Size(min = 3, max = 50, message = "Slug must be 3-50 characters")
    @Pattern(regexp = "^[a-z0-9][a-z0-9-]*[a-z0-9]$",
             message = "Slug must be lowercase alphanumeric with hyphens, cannot start/end with hyphen")
    private String slug;

    @NotBlank(message = "Owner email is required")
    @Email(message = "Invalid email format")
    private String ownerEmail;

    @Pattern(regexp = "^(FREE|STARTER|PROFESSIONAL|ENTERPRISE)$",
             message = "Invalid subscription tier")
    private String subscriptionTier;

    /**
     * Optional metadata as JSON string for extensibility.
     */
    private String metadata;
}
