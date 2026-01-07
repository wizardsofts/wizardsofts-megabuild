package com.wizardsofts.gibd.gateway_service.metrics;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * Authentication and authorization metrics for Prometheus monitoring.
 * These metrics enable security alerting for:
 * - Token validation failures
 * - Cross-tenant access attempts
 * - Authentication rate monitoring
 */
@Slf4j
@Component
public class AuthMetrics {

    private final MeterRegistry meterRegistry;

    // Counters
    private final Counter tokenValidationsSuccess;
    private final Counter tokenValidationsFailure;
    private final Counter crossTenantAccessAttempts;
    private final Counter authorizationDenied;

    // Timers
    private final Timer tokenValidationTimer;

    public AuthMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;

        // Token validation metrics
        this.tokenValidationsSuccess = Counter.builder("auth_token_validations_total")
            .tag("outcome", "success")
            .description("Total successful token validations")
            .register(meterRegistry);

        this.tokenValidationsFailure = Counter.builder("auth_token_validations_total")
            .tag("outcome", "failure")
            .description("Total failed token validations")
            .register(meterRegistry);

        // Security alert metrics
        this.crossTenantAccessAttempts = Counter.builder("auth_cross_tenant_access_attempts_total")
            .description("Cross-tenant access attempts (security alert)")
            .register(meterRegistry);

        this.authorizationDenied = Counter.builder("auth_authorization_denied_total")
            .description("Authorization denied events")
            .register(meterRegistry);

        // Performance metrics
        this.tokenValidationTimer = Timer.builder("auth_token_validation_duration_seconds")
            .description("Time to validate JWT tokens")
            .register(meterRegistry);
    }

    /**
     * Records a successful token validation.
     */
    public void recordTokenValidationSuccess() {
        tokenValidationsSuccess.increment();
    }

    /**
     * Records a failed token validation with reason.
     */
    public void recordTokenValidationFailure(String reason) {
        tokenValidationsFailure.increment();
        Counter.builder("auth_token_validation_failures_total")
            .tag("reason", reason)
            .register(meterRegistry)
            .increment();
    }

    /**
     * Records a cross-tenant access attempt.
     * This is a CRITICAL security event that should trigger alerts.
     */
    public void recordCrossTenantAccessAttempt(String userId, String sourceTenant, String targetTenant) {
        crossTenantAccessAttempts.increment();

        // Create detailed counter for investigation
        Counter.builder("auth_cross_tenant_access_details_total")
            .tag("source_tenant", sourceTenant)
            .tag("target_tenant", targetTenant)
            .register(meterRegistry)
            .increment();

        log.warn("SECURITY ALERT: Cross-tenant access attempt - user={}, from={}, to={}",
            userId, sourceTenant, targetTenant);
    }

    /**
     * Records an authorization denied event.
     */
    public void recordAuthorizationDenied(String userId, String resource, String action) {
        authorizationDenied.increment();

        Counter.builder("auth_authorization_denied_details_total")
            .tag("resource", resource)
            .tag("action", action)
            .register(meterRegistry)
            .increment();

        log.warn("Authorization denied: user={}, resource={}, action={}", userId, resource, action);
    }

    /**
     * Times a token validation operation.
     */
    public Timer.Sample startTokenValidation() {
        return Timer.start(meterRegistry);
    }

    /**
     * Stops timing a token validation.
     */
    public void stopTokenValidation(Timer.Sample sample) {
        sample.stop(tokenValidationTimer);
    }
}
