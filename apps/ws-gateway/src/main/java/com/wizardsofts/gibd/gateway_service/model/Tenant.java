package com.wizardsofts.gibd.gateway_service.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.Instant;
import java.util.UUID;

/**
 * Tenant entity for multi-tenant support.
 *
 * Each tenant represents an organization with:
 * - Unique identifier (UUID)
 * - Keycloak group for role-based access
 * - Subscription tier for feature gating
 * - Status for lifecycle management
 */
@Entity
@Table(name = "tenants", indexes = {
    @Index(name = "idx_tenant_slug", columnList = "slug", unique = true),
    @Index(name = "idx_tenant_keycloak_group", columnList = "keycloakGroupId")
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Tenant {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, unique = true)
    private String slug;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private String ownerEmail;

    @Column
    private String keycloakGroupId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private TenantStatus status = TenantStatus.PENDING;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private SubscriptionTier tier = SubscriptionTier.FREE;

    @Column(columnDefinition = "TEXT")
    private String metadata;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @UpdateTimestamp
    @Column(nullable = false)
    private Instant updatedAt;

    @Column
    private Instant activatedAt;

    @Column
    private Instant suspendedAt;

    public enum TenantStatus {
        PENDING,      // Awaiting email verification
        PROVISIONING, // Keycloak setup in progress
        ACTIVE,       // Fully operational
        SUSPENDED,    // Temporarily disabled
        DELETED       // Soft deleted
    }

    public enum SubscriptionTier {
        FREE,       // Limited features
        STARTER,    // Basic paid tier
        PROFESSIONAL, // Full features
        ENTERPRISE  // Custom features + support
    }

    /**
     * Activates the tenant after successful provisioning.
     */
    public void activate() {
        this.status = TenantStatus.ACTIVE;
        this.activatedAt = Instant.now();
    }

    /**
     * Suspends the tenant (e.g., payment failure, ToS violation).
     */
    public void suspend() {
        this.status = TenantStatus.SUSPENDED;
        this.suspendedAt = Instant.now();
    }

    /**
     * Checks if tenant is in an active state.
     */
    public boolean isActive() {
        return status == TenantStatus.ACTIVE;
    }
}
