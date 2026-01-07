package com.wizardsofts.gibd.gateway_service.audit;

import lombok.*;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

/**
 * Security audit event for tracking authentication and authorization activities.
 *
 * Events are logged for:
 * - Authentication attempts (success/failure)
 * - Token validation
 * - Authorization decisions
 * - Tenant access
 * - Admin actions
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class SecurityAuditEvent {

    /**
     * Unique event identifier.
     */
    @Builder.Default
    private String eventId = UUID.randomUUID().toString();

    /**
     * Event timestamp.
     */
    @Builder.Default
    private Instant timestamp = Instant.now();

    /**
     * Type of security event.
     */
    private EventType eventType;

    /**
     * Result of the event.
     */
    private EventResult result;

    /**
     * User identifier (subject claim from JWT or username).
     */
    private String userId;

    /**
     * User's email address.
     */
    private String userEmail;

    /**
     * Tenant ID if applicable.
     */
    private String tenantId;

    /**
     * Tenant slug if applicable.
     */
    private String tenantSlug;

    /**
     * Client ID (OAuth2 client).
     */
    private String clientId;

    /**
     * Source IP address.
     */
    private String sourceIp;

    /**
     * User agent string.
     */
    private String userAgent;

    /**
     * Request path/resource.
     */
    private String resource;

    /**
     * HTTP method.
     */
    private String method;

    /**
     * Correlation ID for request tracing.
     */
    private String correlationId;

    /**
     * Failure reason if result is FAILURE or DENIED.
     */
    private String failureReason;

    /**
     * Additional context data.
     */
    private Map<String, Object> metadata;

    /**
     * Types of security events.
     */
    public enum EventType {
        // Authentication events
        AUTHENTICATION_ATTEMPT,
        AUTHENTICATION_SUCCESS,
        AUTHENTICATION_FAILURE,
        TOKEN_REFRESH,
        TOKEN_VALIDATION,
        TOKEN_VALIDATION_FAILURE,
        LOGOUT,

        // Authorization events
        AUTHORIZATION_SUCCESS,
        AUTHORIZATION_FAILURE,
        ACCESS_DENIED,

        // Tenant events
        TENANT_REGISTRATION,
        TENANT_ACTIVATION,
        TENANT_SUSPENSION,
        TENANT_DELETION,
        TENANT_ACCESS,

        // Admin events
        ADMIN_ACTION,
        USER_ROLE_CHANGE,
        PERMISSION_CHANGE,

        // Security alerts
        RATE_LIMIT_EXCEEDED,
        SUSPICIOUS_ACTIVITY,
        BRUTE_FORCE_DETECTED
    }

    /**
     * Event results.
     */
    public enum EventResult {
        SUCCESS,
        FAILURE,
        DENIED,
        PENDING
    }

    /**
     * Creates an authentication success event.
     */
    public static SecurityAuditEvent authSuccess(String userId, String email, String clientId, String sourceIp) {
        return SecurityAuditEvent.builder()
            .eventType(EventType.AUTHENTICATION_SUCCESS)
            .result(EventResult.SUCCESS)
            .userId(userId)
            .userEmail(email)
            .clientId(clientId)
            .sourceIp(sourceIp)
            .build();
    }

    /**
     * Creates an authentication failure event.
     */
    public static SecurityAuditEvent authFailure(String clientId, String sourceIp, String reason) {
        return SecurityAuditEvent.builder()
            .eventType(EventType.AUTHENTICATION_FAILURE)
            .result(EventResult.FAILURE)
            .clientId(clientId)
            .sourceIp(sourceIp)
            .failureReason(reason)
            .build();
    }

    /**
     * Creates an access denied event.
     */
    public static SecurityAuditEvent accessDenied(String userId, String resource, String reason) {
        return SecurityAuditEvent.builder()
            .eventType(EventType.ACCESS_DENIED)
            .result(EventResult.DENIED)
            .userId(userId)
            .resource(resource)
            .failureReason(reason)
            .build();
    }

    /**
     * Creates a tenant access event.
     */
    public static SecurityAuditEvent tenantAccess(String userId, String tenantId, String tenantSlug, boolean success) {
        return SecurityAuditEvent.builder()
            .eventType(EventType.TENANT_ACCESS)
            .result(success ? EventResult.SUCCESS : EventResult.DENIED)
            .userId(userId)
            .tenantId(tenantId)
            .tenantSlug(tenantSlug)
            .build();
    }
}
