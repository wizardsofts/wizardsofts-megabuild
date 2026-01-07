package com.wizardsofts.gibd.gateway_service.filter;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import com.wizardsofts.gibd.gateway_service.metrics.AuthMetrics;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.context.ReactiveSecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.UUID;

/**
 * Gateway filter for security audit logging and metrics.
 *
 * Captures:
 * - Request correlation ID (generates if missing)
 * - Authentication context from JWT
 * - Request timing and status
 * - Security events (auth success/failure, access denied)
 *
 * Integrates with:
 * - SecurityAuditLogger for audit trail
 * - AuthMetrics for Prometheus metrics
 * - SLF4J MDC for log correlation
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SecurityAuditFilter implements GlobalFilter, Ordered {

    private static final String CORRELATION_ID_HEADER = "X-Correlation-ID";
    private static final String CORRELATION_ID_KEY = "correlationId";
    private static final String REQUEST_START_TIME = "requestStartTime";

    private final SecurityAuditLogger auditLogger;
    private final AuthMetrics authMetrics;

    @Override
    public int getOrder() {
        // Run early to set up correlation ID, but after security filters
        return -50;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Generate or extract correlation ID
        String correlationId = exchange.getRequest().getHeaders()
            .getFirst(CORRELATION_ID_HEADER);

        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        // Store for later use
        final String finalCorrelationId = correlationId;
        exchange.getAttributes().put(CORRELATION_ID_KEY, correlationId);
        exchange.getAttributes().put(REQUEST_START_TIME, System.currentTimeMillis());

        // Add correlation ID to response headers
        exchange.getResponse().getHeaders().add(CORRELATION_ID_HEADER, correlationId);

        // Get request info
        String method = exchange.getRequest().getMethod().name();
        String path = exchange.getRequest().getPath().value();
        String sourceIp = getClientIp(exchange);
        String userAgent = exchange.getRequest().getHeaders().getFirst("User-Agent");

        // Process with security context
        return ReactiveSecurityContextHolder.getContext()
            .map(ctx -> ctx.getAuthentication())
            .cast(JwtAuthenticationToken.class)
            .flatMap(auth -> {
                // Authenticated request
                Jwt jwt = auth.getToken();
                String userId = jwt.getSubject();
                String email = jwt.getClaimAsString("email");
                String clientId = jwt.getClaimAsString("azp");
                String tenantId = jwt.getClaimAsString("tenant_id");

                // Set MDC context
                MDC.put(CORRELATION_ID_KEY, finalCorrelationId);
                MDC.put("userId", userId);
                MDC.put("tenantId", tenantId != null ? tenantId : "none");

                return chain.filter(exchange)
                    .doOnSuccess(v -> {
                        HttpStatus status = exchange.getResponse().getStatusCode();
                        long duration = calculateDuration(exchange);

                        // Log successful authenticated request
                        if (status != null && status.is2xxSuccessful()) {
                            authMetrics.recordAuthSuccess(clientId);
                        } else if (status == HttpStatus.FORBIDDEN || status == HttpStatus.UNAUTHORIZED) {
                            authMetrics.recordAccessDenied(path);
                            auditLogger.logAccessDenied(userId, path, method, "HTTP " + status, finalCorrelationId);
                        }

                        log.info("Request completed: {} {} -> {} ({}ms) user={} tenant={}",
                            method, path, status, duration, userId, tenantId);
                    })
                    .doOnError(e -> {
                        authMetrics.recordAuthFailure("error");
                        log.error("Request failed: {} {} error={}", method, path, e.getMessage());
                    })
                    .doFinally(signal -> {
                        MDC.clear();
                    });
            })
            .switchIfEmpty(Mono.defer(() -> {
                // Unauthenticated request
                MDC.put(CORRELATION_ID_KEY, finalCorrelationId);

                return chain.filter(exchange)
                    .doOnSuccess(v -> {
                        HttpStatus status = exchange.getResponse().getStatusCode();
                        long duration = calculateDuration(exchange);

                        if (status == HttpStatus.UNAUTHORIZED) {
                            authMetrics.recordAuthFailure("unauthenticated");
                            auditLogger.logAuthFailure("unknown", sourceIp, "No authentication", finalCorrelationId);
                        }

                        log.info("Request completed: {} {} -> {} ({}ms) anonymous",
                            method, path, status, duration);
                    })
                    .doFinally(signal -> {
                        MDC.clear();
                    });
            }));
    }

    /**
     * Extracts client IP, considering X-Forwarded-For header.
     */
    private String getClientIp(ServerWebExchange exchange) {
        String forwardedFor = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            // Take first IP in chain (original client)
            return forwardedFor.split(",")[0].trim();
        }

        var remoteAddress = exchange.getRequest().getRemoteAddress();
        return remoteAddress != null ? remoteAddress.getAddress().getHostAddress() : "unknown";
    }

    /**
     * Calculates request duration from stored start time.
     */
    private long calculateDuration(ServerWebExchange exchange) {
        Long startTime = exchange.getAttribute(REQUEST_START_TIME);
        return startTime != null ? System.currentTimeMillis() - startTime : 0;
    }
}
