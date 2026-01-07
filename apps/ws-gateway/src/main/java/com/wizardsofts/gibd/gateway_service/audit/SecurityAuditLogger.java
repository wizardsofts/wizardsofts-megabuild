package com.wizardsofts.gibd.gateway_service.audit;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * Service for logging security audit events.
 *
 * Logs events in structured JSON format for easy parsing by log aggregators.
 * Uses SLF4J MDC for correlation ID propagation.
 *
 * Log destinations:
 * - SECURITY_AUDIT logger (separate log file in production)
 * - Optional external event publisher
 */
@Slf4j
@Service
public class SecurityAuditLogger {

    private static final org.slf4j.Logger AUDIT_LOG =
        org.slf4j.LoggerFactory.getLogger("SECURITY_AUDIT");

    private final ObjectMapper objectMapper;
    private final AuditEventPublisher eventPublisher;

    @Value("${security.audit.publish-events:false}")
    private boolean publishEvents;

    public SecurityAuditLogger(AuditEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
    }

    /**
     * Logs a security audit event.
     *
     * Sets MDC context for correlation and logs in JSON format.
     * Optionally publishes to external systems.
     */
    public void log(SecurityAuditEvent event) {
        // Set MDC for correlation
        try {
            MDC.put("eventId", event.getEventId());
            MDC.put("eventType", event.getEventType().name());
            MDC.put("userId", event.getUserId());
            MDC.put("tenantId", event.getTenantId());

            if (event.getCorrelationId() != null) {
                MDC.put("correlationId", event.getCorrelationId());
            }

            // Log as JSON
            String jsonEvent = toJson(event);
            AUDIT_LOG.info(jsonEvent);

            // Publish if enabled
            if (publishEvents) {
                eventPublisher.publish(event);
            }

            // Also log at appropriate level based on event type
            logByEventType(event, jsonEvent);

        } finally {
            // Clear MDC
            MDC.remove("eventId");
            MDC.remove("eventType");
            MDC.remove("userId");
            MDC.remove("tenantId");
            MDC.remove("correlationId");
        }
    }

    /**
     * Logs authentication success.
     */
    public void logAuthSuccess(String userId, String email, String clientId, String sourceIp, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.authSuccess(userId, email, clientId, sourceIp);
        event.setCorrelationId(correlationId);
        log(event);
    }

    /**
     * Logs authentication failure.
     */
    public void logAuthFailure(String clientId, String sourceIp, String reason, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.authFailure(clientId, sourceIp, reason);
        event.setCorrelationId(correlationId);
        log(event);
    }

    /**
     * Logs access denied.
     */
    public void logAccessDenied(String userId, String resource, String method, String reason, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.accessDenied(userId, resource, reason);
        event.setResource(resource);
        event.setMethod(method);
        event.setCorrelationId(correlationId);
        log(event);
    }

    /**
     * Logs token validation.
     */
    public void logTokenValidation(String userId, String clientId, boolean success, String reason, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.builder()
            .eventType(success ?
                SecurityAuditEvent.EventType.TOKEN_VALIDATION :
                SecurityAuditEvent.EventType.TOKEN_VALIDATION_FAILURE)
            .result(success ?
                SecurityAuditEvent.EventResult.SUCCESS :
                SecurityAuditEvent.EventResult.FAILURE)
            .userId(userId)
            .clientId(clientId)
            .failureReason(success ? null : reason)
            .correlationId(correlationId)
            .build();
        log(event);
    }

    /**
     * Logs tenant registration.
     */
    public void logTenantRegistration(String tenantId, String tenantSlug, String ownerEmail, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.builder()
            .eventType(SecurityAuditEvent.EventType.TENANT_REGISTRATION)
            .result(SecurityAuditEvent.EventResult.SUCCESS)
            .tenantId(tenantId)
            .tenantSlug(tenantSlug)
            .userEmail(ownerEmail)
            .correlationId(correlationId)
            .build();
        log(event);
    }

    /**
     * Logs tenant access attempt.
     */
    public void logTenantAccess(String userId, String tenantId, String tenantSlug, boolean success, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.tenantAccess(userId, tenantId, tenantSlug, success);
        event.setCorrelationId(correlationId);
        log(event);
    }

    /**
     * Logs admin action.
     */
    public void logAdminAction(String adminUserId, String action, Map<String, Object> details, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.builder()
            .eventType(SecurityAuditEvent.EventType.ADMIN_ACTION)
            .result(SecurityAuditEvent.EventResult.SUCCESS)
            .userId(adminUserId)
            .metadata(details)
            .correlationId(correlationId)
            .build();
        log(event);
    }

    /**
     * Logs rate limit exceeded.
     */
    public void logRateLimitExceeded(String userId, String sourceIp, String resource, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.builder()
            .eventType(SecurityAuditEvent.EventType.RATE_LIMIT_EXCEEDED)
            .result(SecurityAuditEvent.EventResult.DENIED)
            .userId(userId)
            .sourceIp(sourceIp)
            .resource(resource)
            .correlationId(correlationId)
            .build();
        log(event);
    }

    /**
     * Logs suspicious activity.
     */
    public void logSuspiciousActivity(String userId, String sourceIp, String description, Map<String, Object> details, String correlationId) {
        SecurityAuditEvent event = SecurityAuditEvent.builder()
            .eventType(SecurityAuditEvent.EventType.SUSPICIOUS_ACTIVITY)
            .result(SecurityAuditEvent.EventResult.FAILURE)
            .userId(userId)
            .sourceIp(sourceIp)
            .failureReason(description)
            .metadata(details)
            .correlationId(correlationId)
            .build();
        log(event);
    }

    private String toJson(SecurityAuditEvent event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize audit event", e);
            return "{\"error\":\"serialization_failed\",\"eventId\":\"" + event.getEventId() + "\"}";
        }
    }

    private void logByEventType(SecurityAuditEvent event, String jsonEvent) {
        switch (event.getEventType()) {
            case AUTHENTICATION_FAILURE:
            case TOKEN_VALIDATION_FAILURE:
            case ACCESS_DENIED:
                log.warn("Security event: {} - {}", event.getEventType(), event.getFailureReason());
                break;

            case RATE_LIMIT_EXCEEDED:
            case SUSPICIOUS_ACTIVITY:
            case BRUTE_FORCE_DETECTED:
                log.error("Security alert: {} from {} - {}",
                    event.getEventType(), event.getSourceIp(), event.getFailureReason());
                break;

            case TENANT_SUSPENSION:
            case TENANT_DELETION:
            case USER_ROLE_CHANGE:
            case PERMISSION_CHANGE:
                log.warn("Admin action: {} by {} on {}",
                    event.getEventType(), event.getUserId(), event.getTenantId());
                break;

            default:
                log.debug("Security event: {}", event.getEventType());
        }
    }
}
