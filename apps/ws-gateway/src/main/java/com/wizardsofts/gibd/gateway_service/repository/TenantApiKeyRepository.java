package com.wizardsofts.gibd.gateway_service.repository;

import com.wizardsofts.gibd.gateway_service.model.TenantApiKey;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for TenantApiKey entity operations.
 */
@Repository
public interface TenantApiKeyRepository extends JpaRepository<TenantApiKey, UUID> {

    /**
     * Finds an active API key by its hash.
     */
    @Query("SELECT k FROM TenantApiKey k WHERE k.keyHash = :keyHash AND k.revokedAt IS NULL")
    Optional<TenantApiKey> findActiveByKeyHash(String keyHash);

    /**
     * Finds an API key by its prefix (for identification).
     */
    Optional<TenantApiKey> findByKeyPrefix(String keyPrefix);

    /**
     * Finds all active keys for a tenant.
     */
    @Query("SELECT k FROM TenantApiKey k WHERE k.tenant.id = :tenantId AND k.revokedAt IS NULL ORDER BY k.createdAt DESC")
    List<TenantApiKey> findActiveByTenantId(UUID tenantId);

    /**
     * Finds all keys for a tenant (including revoked).
     */
    List<TenantApiKey> findByTenantIdOrderByCreatedAtDesc(UUID tenantId);

    /**
     * Counts active keys for a tenant.
     */
    @Query("SELECT COUNT(k) FROM TenantApiKey k WHERE k.tenant.id = :tenantId AND k.revokedAt IS NULL")
    long countActiveByTenantId(UUID tenantId);

    /**
     * Finds expired but not yet revoked keys.
     */
    @Query("SELECT k FROM TenantApiKey k WHERE k.expiresAt < :now AND k.revokedAt IS NULL")
    List<TenantApiKey> findExpiredKeys(Instant now);

    /**
     * Checks if a key prefix already exists.
     */
    boolean existsByKeyPrefix(String keyPrefix);
}
