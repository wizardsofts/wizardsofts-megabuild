package com.wizardsofts.gibd.gateway_service.repository;

import com.wizardsofts.gibd.gateway_service.model.Tenant;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for Tenant entity operations.
 *
 * Provides CRUD operations and custom queries for:
 * - Slug lookups (case-insensitive)
 * - Owner email lookups
 * - Status-based filtering
 * - Keycloak group ID lookups
 */
@Repository
public interface TenantRepository extends JpaRepository<Tenant, UUID> {

    /**
     * Finds tenant by slug (case-insensitive).
     */
    Optional<Tenant> findBySlugIgnoreCase(String slug);

    /**
     * Checks if slug already exists.
     */
    boolean existsBySlugIgnoreCase(String slug);

    /**
     * Finds all tenants owned by email.
     */
    List<Tenant> findByOwnerEmailIgnoreCase(String ownerEmail);

    /**
     * Finds tenant by Keycloak group ID.
     */
    Optional<Tenant> findByKeycloakGroupId(String keycloakGroupId);

    /**
     * Finds all tenants with given status.
     */
    List<Tenant> findByStatus(Tenant.TenantStatus status);

    /**
     * Finds active tenants by subscription tier.
     */
    List<Tenant> findByStatusAndTier(Tenant.TenantStatus status, Tenant.SubscriptionTier tier);

    /**
     * Counts tenants by status.
     */
    long countByStatus(Tenant.TenantStatus status);

    /**
     * Finds tenants pending provisioning (ordered by creation time).
     */
    @Query("SELECT t FROM Tenant t WHERE t.status = 'PROVISIONING' ORDER BY t.createdAt ASC")
    List<Tenant> findPendingProvisioning();

    /**
     * Checks if owner already has maximum allowed tenants.
     */
    @Query("SELECT COUNT(t) FROM Tenant t WHERE t.ownerEmail = :email AND t.status != 'DELETED'")
    long countActiveByOwnerEmail(String email);
}
