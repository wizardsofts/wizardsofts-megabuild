package com.wizardsofts.gibd.gateway_service.service;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.model.TenantApiKey;
import com.wizardsofts.gibd.gateway_service.repository.TenantApiKeyRepository;
import com.wizardsofts.gibd.gateway_service.repository.TenantRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;

/**
 * Service for managing tenant API keys.
 *
 * Handles:
 * - Key generation with secure random
 * - Key validation and authentication
 * - Key rotation and revocation
 * - Usage tracking
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ApiKeyService {

    private final TenantApiKeyRepository apiKeyRepository;
    private final TenantRepository tenantRepository;
    private final SecurityAuditLogger auditLogger;

    @Value("${api-key.max-per-tenant:10}")
    private int maxKeysPerTenant;

    @Value("${api-key.default-expiry-days:365}")
    private int defaultExpiryDays;

    private static final SecureRandom SECURE_RANDOM = new SecureRandom();
    private static final String KEY_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

    /**
     * Result of creating an API key.
     * The plaintext key is only available at creation time.
     */
    public record ApiKeyCreationResult(
        UUID keyId,
        String keyPrefix,
        String plaintextKey,  // Only returned once!
        String name,
        Set<String> scopes,
        Instant expiresAt
    ) {}

    /**
     * Creates a new API key for a tenant.
     *
     * @param tenantId The tenant ID
     * @param name Human-readable name for the key
     * @param scopes Permission scopes
     * @param keyType LIVE or TEST
     * @param expiryDays Days until expiration (null for default)
     * @param createdBy User creating the key
     * @return Creation result with the plaintext key (shown only once)
     */
    @Transactional
    public ApiKeyCreationResult createApiKey(
            UUID tenantId,
            String name,
            Set<String> scopes,
            TenantApiKey.KeyType keyType,
            Integer expiryDays,
            String createdBy) {

        // Verify tenant exists and is active
        Tenant tenant = tenantRepository.findById(tenantId)
            .orElseThrow(() -> new IllegalArgumentException("Tenant not found: " + tenantId));

        if (!tenant.isActive()) {
            throw new IllegalStateException("Cannot create API key for inactive tenant");
        }

        // Check key limit
        long activeKeys = apiKeyRepository.countActiveByTenantId(tenantId);
        if (activeKeys >= maxKeysPerTenant) {
            throw new IllegalStateException(
                "Maximum API keys (" + maxKeysPerTenant + ") reached for this tenant");
        }

        // Generate key
        String prefix = generateKeyPrefix(keyType);
        String plaintextKey = prefix + generateRandomKey(32);
        String keyHash = hashKey(plaintextKey);

        // Calculate expiry
        int expiry = expiryDays != null ? expiryDays : defaultExpiryDays;
        Instant expiresAt = Instant.now().plus(expiry, ChronoUnit.DAYS);

        // Create entity
        TenantApiKey apiKey = TenantApiKey.builder()
            .tenant(tenant)
            .keyHash(keyHash)
            .keyPrefix(prefix)
            .name(name)
            .scopes(scopes != null ? scopes : Set.of())
            .keyType(keyType)
            .expiresAt(expiresAt)
            .createdBy(createdBy)
            .build();

        apiKey = apiKeyRepository.save(apiKey);

        log.info("Created API key {} for tenant {}", prefix, tenant.getSlug());
        auditLogger.logSensitiveOperation("API_KEY_CREATED",
            Map.of("tenantId", tenantId.toString(), "keyPrefix", prefix, "keyType", keyType.name()),
            true);

        return new ApiKeyCreationResult(
            apiKey.getId(),
            prefix,
            plaintextKey,  // Only returned here!
            name,
            apiKey.getScopes(),
            expiresAt
        );
    }

    /**
     * Validates an API key and returns the associated tenant.
     *
     * @param plaintextKey The API key to validate
     * @param requiredScope Required scope (optional)
     * @param clientIp Client IP for usage tracking
     * @return The authenticated tenant, or empty if invalid
     */
    @Transactional
    public Optional<Tenant> validateApiKey(String plaintextKey, String requiredScope, String clientIp) {
        if (plaintextKey == null || plaintextKey.length() < 16) {
            return Optional.empty();
        }

        String keyHash = hashKey(plaintextKey);
        Optional<TenantApiKey> keyOpt = apiKeyRepository.findActiveByKeyHash(keyHash);

        if (keyOpt.isEmpty()) {
            log.debug("API key not found or inactive");
            return Optional.empty();
        }

        TenantApiKey apiKey = keyOpt.get();

        // Check if key is active
        if (!apiKey.isActive()) {
            log.debug("API key {} is expired or revoked", apiKey.getKeyPrefix());
            return Optional.empty();
        }

        // Check scope if required
        if (requiredScope != null && !apiKey.hasScope(requiredScope)) {
            log.debug("API key {} lacks required scope: {}", apiKey.getKeyPrefix(), requiredScope);
            auditLogger.logAuthorizationFailure(
                "api-key:" + apiKey.getKeyPrefix(),
                requiredScope);
            return Optional.empty();
        }

        // Record usage
        apiKey.recordUsage(clientIp);
        apiKeyRepository.save(apiKey);

        Tenant tenant = apiKey.getTenant();
        log.debug("API key {} validated for tenant {}", apiKey.getKeyPrefix(), tenant.getSlug());

        return Optional.of(tenant);
    }

    /**
     * Revokes an API key.
     */
    @Transactional
    public void revokeApiKey(UUID keyId, String revokedBy, String reason) {
        TenantApiKey apiKey = apiKeyRepository.findById(keyId)
            .orElseThrow(() -> new IllegalArgumentException("API key not found: " + keyId));

        if (apiKey.getRevokedAt() != null) {
            throw new IllegalStateException("API key is already revoked");
        }

        apiKey.revoke(revokedBy, reason);
        apiKeyRepository.save(apiKey);

        log.info("Revoked API key {} by {}: {}", apiKey.getKeyPrefix(), revokedBy, reason);
        auditLogger.logSensitiveOperation("API_KEY_REVOKED",
            Map.of("keyPrefix", apiKey.getKeyPrefix(), "reason", reason),
            true);
    }

    /**
     * Lists API keys for a tenant (without sensitive data).
     */
    @Transactional(readOnly = true)
    public List<ApiKeyInfo> listApiKeys(UUID tenantId, boolean includeRevoked) {
        List<TenantApiKey> keys = includeRevoked ?
            apiKeyRepository.findByTenantIdOrderByCreatedAtDesc(tenantId) :
            apiKeyRepository.findActiveByTenantId(tenantId);

        return keys.stream()
            .map(this::toApiKeyInfo)
            .toList();
    }

    /**
     * Rotates an API key (creates new, revokes old).
     */
    @Transactional
    public ApiKeyCreationResult rotateApiKey(UUID oldKeyId, String rotatedBy) {
        TenantApiKey oldKey = apiKeyRepository.findById(oldKeyId)
            .orElseThrow(() -> new IllegalArgumentException("API key not found: " + oldKeyId));

        if (!oldKey.isActive()) {
            throw new IllegalStateException("Cannot rotate inactive key");
        }

        // Create new key with same settings
        ApiKeyCreationResult newKey = createApiKey(
            oldKey.getTenant().getId(),
            oldKey.getName() + " (rotated)",
            oldKey.getScopes(),
            oldKey.getKeyType(),
            null,
            rotatedBy
        );

        // Revoke old key
        revokeApiKey(oldKeyId, rotatedBy, "Rotated to " + newKey.keyPrefix());

        log.info("Rotated API key {} to {}", oldKey.getKeyPrefix(), newKey.keyPrefix());

        return newKey;
    }

    /**
     * DTO for API key info (without sensitive data).
     */
    public record ApiKeyInfo(
        UUID id,
        String keyPrefix,
        String name,
        String description,
        Set<String> scopes,
        TenantApiKey.KeyType keyType,
        Instant createdAt,
        Instant expiresAt,
        Instant lastUsedAt,
        boolean isActive,
        Instant revokedAt
    ) {}

    private ApiKeyInfo toApiKeyInfo(TenantApiKey key) {
        return new ApiKeyInfo(
            key.getId(),
            key.getKeyPrefix(),
            key.getName(),
            key.getDescription(),
            key.getScopes(),
            key.getKeyType(),
            key.getCreatedAt(),
            key.getExpiresAt(),
            key.getLastUsedAt(),
            key.isActive(),
            key.getRevokedAt()
        );
    }

    private String generateKeyPrefix(TenantApiKey.KeyType keyType) {
        String prefix = keyType == TenantApiKey.KeyType.LIVE ? "ws_live_" : "ws_test_";

        // Add 8 random chars
        StringBuilder sb = new StringBuilder(prefix);
        for (int i = 0; i < 8; i++) {
            sb.append(KEY_CHARS.charAt(SECURE_RANDOM.nextInt(KEY_CHARS.length())));
        }

        String fullPrefix = sb.toString();

        // Ensure uniqueness
        while (apiKeyRepository.existsByKeyPrefix(fullPrefix)) {
            sb.setLength(prefix.length());
            for (int i = 0; i < 8; i++) {
                sb.append(KEY_CHARS.charAt(SECURE_RANDOM.nextInt(KEY_CHARS.length())));
            }
            fullPrefix = sb.toString();
        }

        return fullPrefix;
    }

    private String generateRandomKey(int length) {
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(KEY_CHARS.charAt(SECURE_RANDOM.nextInt(KEY_CHARS.length())));
        }
        return sb.toString();
    }

    private String hashKey(String plaintextKey) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(plaintextKey.getBytes(StandardCharsets.UTF_8));
            return bytesToHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }

    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
}
