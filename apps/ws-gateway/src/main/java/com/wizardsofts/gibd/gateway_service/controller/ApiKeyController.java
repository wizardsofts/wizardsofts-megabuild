package com.wizardsofts.gibd.gateway_service.controller;

import com.wizardsofts.gibd.gateway_service.model.TenantApiKey;
import com.wizardsofts.gibd.gateway_service.service.ApiKeyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
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
import java.util.Set;
import java.util.UUID;

/**
 * REST Controller for tenant API key management.
 *
 * Endpoints:
 * - POST /api/v1/tenants/{tenantId}/api-keys - Create new API key
 * - GET /api/v1/tenants/{tenantId}/api-keys - List API keys
 * - DELETE /api/v1/tenants/{tenantId}/api-keys/{keyId} - Revoke key
 * - POST /api/v1/tenants/{tenantId}/api-keys/{keyId}/rotate - Rotate key
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/tenants/{tenantId}/api-keys")
@RequiredArgsConstructor
@Tag(name = "API Keys", description = "Tenant API key management")
@SecurityRequirement(name = "bearer-jwt")
public class ApiKeyController {

    private final ApiKeyService apiKeyService;

    @Data
    public static class CreateApiKeyRequest {
        @NotBlank(message = "Name is required")
        @Size(min = 3, max = 100, message = "Name must be 3-100 characters")
        private String name;

        private String description;

        private Set<String> scopes;

        private TenantApiKey.KeyType keyType = TenantApiKey.KeyType.LIVE;

        private Integer expiryDays;
    }

    @Data
    public static class RevokeApiKeyRequest {
        @NotBlank(message = "Reason is required")
        private String reason;
    }

    /**
     * Creates a new API key for the tenant.
     *
     * The plaintext key is only returned in this response.
     * Store it securely - it cannot be retrieved again.
     */
    @PostMapping
    @PreAuthorize("@tenantAccessChecker.hasTenantRole(#jwt, #tenantId, 'tenant-admin')")
    @Operation(
        summary = "Create API key",
        description = "Creates a new API key. The plaintext key is only shown once."
    )
    public ResponseEntity<ApiKeyService.ApiKeyCreationResult> createApiKey(
            @PathVariable UUID tenantId,
            @Valid @RequestBody CreateApiKeyRequest request,
            @AuthenticationPrincipal Jwt jwt) {

        String createdBy = jwt.getSubject();

        ApiKeyService.ApiKeyCreationResult result = apiKeyService.createApiKey(
            tenantId,
            request.getName(),
            request.getScopes(),
            request.getKeyType(),
            request.getExpiryDays(),
            createdBy
        );

        log.info("API key created for tenant {} by {}", tenantId, createdBy);

        return ResponseEntity.status(HttpStatus.CREATED).body(result);
    }

    /**
     * Lists all API keys for the tenant.
     * Does not include the key values (only prefixes).
     */
    @GetMapping
    @PreAuthorize("@tenantAccessChecker.canAccess(#jwt, #tenantId)")
    @Operation(summary = "List API keys", description = "Lists all API keys for the tenant")
    public ResponseEntity<List<ApiKeyService.ApiKeyInfo>> listApiKeys(
            @PathVariable UUID tenantId,
            @RequestParam(defaultValue = "false") boolean includeRevoked,
            @AuthenticationPrincipal Jwt jwt) {

        List<ApiKeyService.ApiKeyInfo> keys = apiKeyService.listApiKeys(tenantId, includeRevoked);

        return ResponseEntity.ok(keys);
    }

    /**
     * Revokes an API key.
     */
    @DeleteMapping("/{keyId}")
    @PreAuthorize("@tenantAccessChecker.hasTenantRole(#jwt, #tenantId, 'tenant-admin')")
    @Operation(summary = "Revoke API key", description = "Permanently revokes an API key")
    public ResponseEntity<Map<String, String>> revokeApiKey(
            @PathVariable UUID tenantId,
            @PathVariable UUID keyId,
            @Valid @RequestBody RevokeApiKeyRequest request,
            @AuthenticationPrincipal Jwt jwt) {

        String revokedBy = jwt.getSubject();

        apiKeyService.revokeApiKey(keyId, revokedBy, request.getReason());

        log.info("API key {} revoked for tenant {} by {}", keyId, tenantId, revokedBy);

        return ResponseEntity.ok(Map.of(
            "message", "API key revoked successfully",
            "keyId", keyId.toString()
        ));
    }

    /**
     * Rotates an API key (creates new, revokes old).
     *
     * Returns the new key - store it securely.
     */
    @PostMapping("/{keyId}/rotate")
    @PreAuthorize("@tenantAccessChecker.hasTenantRole(#jwt, #tenantId, 'tenant-admin')")
    @Operation(
        summary = "Rotate API key",
        description = "Creates a new key and revokes the old one"
    )
    public ResponseEntity<ApiKeyService.ApiKeyCreationResult> rotateApiKey(
            @PathVariable UUID tenantId,
            @PathVariable UUID keyId,
            @AuthenticationPrincipal Jwt jwt) {

        String rotatedBy = jwt.getSubject();

        ApiKeyService.ApiKeyCreationResult result = apiKeyService.rotateApiKey(keyId, rotatedBy);

        log.info("API key {} rotated for tenant {} by {}", keyId, tenantId, rotatedBy);

        return ResponseEntity.ok(result);
    }

    /**
     * Exception handler for API key errors.
     */
    @ExceptionHandler({IllegalArgumentException.class, IllegalStateException.class})
    public ResponseEntity<Map<String, String>> handleError(Exception e) {
        log.warn("API key error: {}", e.getMessage());
        return ResponseEntity.badRequest().body(Map.of(
            "error", "API Key Error",
            "message", e.getMessage()
        ));
    }
}
