package com.wizardsofts.gibd.gateway_service.controller;

import com.wizardsofts.gibd.gateway_service.dto.TenantRegistrationRequest;
import com.wizardsofts.gibd.gateway_service.dto.TenantRegistrationResponse;
import com.wizardsofts.gibd.gateway_service.service.TenantOnboardingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * REST Controller for tenant self-service onboarding.
 *
 * Public endpoints:
 * - POST /api/v1/tenants - Register new tenant
 *
 * Authenticated endpoints:
 * - GET /api/v1/tenants/{id} - Get tenant by ID
 * - GET /api/v1/tenants/slug/{slug} - Get tenant by slug
 * - GET /api/v1/tenants/my-tenants - Get current user's tenants
 *
 * Admin endpoints:
 * - PUT /api/v1/tenants/{id}/suspend - Suspend tenant
 * - PUT /api/v1/tenants/{id}/reactivate - Reactivate tenant
 * - DELETE /api/v1/tenants/{id} - Delete tenant
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/tenants")
@RequiredArgsConstructor
@Tag(name = "Tenant Onboarding", description = "Self-service tenant registration and management")
public class TenantOnboardingController {

    private final TenantOnboardingService tenantOnboardingService;

    /**
     * Registers a new tenant.
     * This endpoint is public to allow self-service registration.
     */
    @PostMapping
    @Operation(
        summary = "Register a new tenant",
        description = "Creates a new tenant and triggers Keycloak provisioning"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Tenant created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid request or slug already taken"),
        @ApiResponse(responseCode = "429", description = "Too many tenant registrations")
    })
    public ResponseEntity<TenantRegistrationResponse> registerTenant(
            @Valid @RequestBody TenantRegistrationRequest request) {

        log.info("Received tenant registration request for slug: {}", request.getSlug());

        TenantRegistrationResponse response = tenantOnboardingService.registerTenant(request);

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Gets tenant by ID.
     */
    @GetMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'TENANT_ADMIN') or @tenantAccessChecker.canAccess(#jwt, #id)")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Get tenant by ID")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Tenant found"),
        @ApiResponse(responseCode = "403", description = "Access denied"),
        @ApiResponse(responseCode = "404", description = "Tenant not found")
    })
    public ResponseEntity<TenantRegistrationResponse> getTenant(
            @PathVariable UUID id,
            @AuthenticationPrincipal Jwt jwt) {

        return tenantOnboardingService.getTenant(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Gets tenant by slug.
     */
    @GetMapping("/slug/{slug}")
    @PreAuthorize("hasAnyRole('ADMIN', 'TENANT_ADMIN') or @tenantAccessChecker.canAccessBySlug(#jwt, #slug)")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Get tenant by slug")
    public ResponseEntity<TenantRegistrationResponse> getTenantBySlug(
            @PathVariable String slug,
            @AuthenticationPrincipal Jwt jwt) {

        return tenantOnboardingService.getTenantBySlug(slug)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Gets all tenants owned by the current user.
     */
    @GetMapping("/my-tenants")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Get current user's tenants")
    public ResponseEntity<List<TenantRegistrationResponse>> getMyTenants(
            @AuthenticationPrincipal Jwt jwt) {

        String email = jwt.getClaimAsString("email");
        if (email == null) {
            return ResponseEntity.badRequest().build();
        }

        List<TenantRegistrationResponse> tenants = tenantOnboardingService.getTenantsByOwner(email);
        return ResponseEntity.ok(tenants);
    }

    /**
     * Suspends a tenant (Admin only).
     */
    @PutMapping("/{id}/suspend")
    @PreAuthorize("hasRole('ADMIN')")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Suspend a tenant", description = "Admin only - suspends tenant access")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "Tenant suspended"),
        @ApiResponse(responseCode = "403", description = "Admin access required"),
        @ApiResponse(responseCode = "404", description = "Tenant not found")
    })
    public ResponseEntity<TenantRegistrationResponse> suspendTenant(
            @PathVariable UUID id,
            @RequestBody @Parameter(description = "Suspension reason") Map<String, String> body) {

        String reason = body.getOrDefault("reason", "Administrative action");

        log.warn("Admin suspending tenant {} with reason: {}", id, reason);

        TenantRegistrationResponse response = tenantOnboardingService.suspendTenant(id, reason);
        return ResponseEntity.ok(response);
    }

    /**
     * Reactivates a suspended tenant (Admin only).
     */
    @PutMapping("/{id}/reactivate")
    @PreAuthorize("hasRole('ADMIN')")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Reactivate a suspended tenant", description = "Admin only")
    public ResponseEntity<TenantRegistrationResponse> reactivateTenant(@PathVariable UUID id) {

        log.info("Admin reactivating tenant {}", id);

        TenantRegistrationResponse response = tenantOnboardingService.reactivateTenant(id);
        return ResponseEntity.ok(response);
    }

    /**
     * Deletes a tenant (Admin only).
     */
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    @SecurityRequirement(name = "bearer-jwt")
    @Operation(summary = "Delete a tenant", description = "Admin only - soft deletes tenant")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "Tenant deleted"),
        @ApiResponse(responseCode = "403", description = "Admin access required"),
        @ApiResponse(responseCode = "404", description = "Tenant not found")
    })
    public ResponseEntity<Void> deleteTenant(@PathVariable UUID id) {

        log.warn("Admin deleting tenant {}", id);

        tenantOnboardingService.deleteTenant(id);
        return ResponseEntity.noContent().build();
    }

    /**
     * Exception handler for validation errors.
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleValidationError(IllegalArgumentException e) {
        log.warn("Validation error: {}", e.getMessage());
        return ResponseEntity.badRequest().body(Map.of(
            "error", "Validation Error",
            "message", e.getMessage()
        ));
    }

    /**
     * Exception handler for state errors.
     */
    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<Map<String, String>> handleStateError(IllegalStateException e) {
        log.warn("State error: {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of(
            "error", "State Error",
            "message", e.getMessage()
        ));
    }
}
