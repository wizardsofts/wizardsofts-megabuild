package com.wizardsofts.gibd.gateway_service.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;

/**
 * API Key entity for tenant service-to-service authentication.
 *
 * Each tenant can have multiple API keys with:
 * - Scoped permissions
 * - Expiration dates
 * - Usage tracking
 * - Revocation support
 *
 * Security: Only the key hash is stored, never the plaintext key.
 */
@Entity
@Table(name = "tenant_api_keys", indexes = {
    @Index(name = "idx_api_key_tenant", columnList = "tenant_id"),
    @Index(name = "idx_api_key_prefix", columnList = "keyPrefix", unique = true),
    @Index(name = "idx_api_key_hash", columnList = "keyHash")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TenantApiKey {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tenant_id", nullable = false)
    private Tenant tenant;

    /**
     * SHA-256 hash of the API key.
     * The plaintext key is only shown once at creation time.
     */
    @Column(name = "key_hash", nullable = false, length = 64)
    private String keyHash;

    /**
     * First 8 characters of the key for identification.
     * Format: ws_live_XXXXXXXX or ws_test_XXXXXXXX
     */
    @Column(name = "key_prefix", nullable = false, length = 16, unique = true)
    private String keyPrefix;

    /**
     * Human-readable name for the key.
     */
    @Column(nullable = false, length = 100)
    private String name;

    /**
     * Optional description.
     */
    @Column(columnDefinition = "TEXT")
    private String description;

    /**
     * Scopes/permissions granted to this key.
     */
    @ElementCollection
    @CollectionTable(name = "api_key_scopes", joinColumns = @JoinColumn(name = "api_key_id"))
    @Column(name = "scope")
    @Builder.Default
    private Set<String> scopes = Set.of();

    /**
     * Key type: live (production) or test (sandbox).
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private KeyType keyType = KeyType.LIVE;

    /**
     * Expiration timestamp (null = never expires).
     */
    @Column
    private Instant expiresAt;

    /**
     * Last time the key was used.
     */
    @Column
    private Instant lastUsedAt;

    /**
     * IP address of last use.
     */
    @Column(length = 45)
    private String lastUsedIp;

    /**
     * User who created the key.
     */
    @Column(nullable = false)
    private String createdBy;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    /**
     * Revocation timestamp (null = active).
     */
    @Column
    private Instant revokedAt;

    /**
     * User who revoked the key.
     */
    @Column
    private String revokedBy;

    /**
     * Reason for revocation.
     */
    @Column
    private String revocationReason;

    public enum KeyType {
        LIVE,  // Production key
        TEST   // Sandbox/test key
    }

    /**
     * Checks if the key is active (not expired, not revoked).
     */
    public boolean isActive() {
        if (revokedAt != null) {
            return false;
        }
        if (expiresAt != null && Instant.now().isAfter(expiresAt)) {
            return false;
        }
        return true;
    }

    /**
     * Checks if the key has a specific scope.
     */
    public boolean hasScope(String scope) {
        return scopes.contains(scope) || scopes.contains("*");
    }

    /**
     * Records usage of the key.
     */
    public void recordUsage(String ipAddress) {
        this.lastUsedAt = Instant.now();
        this.lastUsedIp = ipAddress;
    }

    /**
     * Revokes the key.
     */
    public void revoke(String revokedBy, String reason) {
        this.revokedAt = Instant.now();
        this.revokedBy = revokedBy;
        this.revocationReason = reason;
    }
}
