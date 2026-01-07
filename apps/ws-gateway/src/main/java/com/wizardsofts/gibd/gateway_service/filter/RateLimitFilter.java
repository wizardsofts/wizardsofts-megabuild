package com.wizardsofts.gibd.gateway_service.filter;

import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.service.RateLimitService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

/**
 * Gateway filter for rate limiting.
 *
 * Applies rate limits based on:
 * - Tenant subscription tier
 * - User identity
 * - Client IP address
 *
 * Adds rate limit headers to responses:
 * - X-RateLimit-Limit: Maximum requests per window
 * - X-RateLimit-Remaining: Requests remaining
 * - X-RateLimit-Reset: Unix timestamp of window reset
 * - Retry-After: Seconds until retry (when limited)
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RateLimitFilter implements GlobalFilter, Ordered {

    private static final String TENANT_ID_HEADER = "X-Tenant-ID";
    private static final String USER_ID_HEADER = "X-User-ID";
    private static final String TENANT_TIER_HEADER = "X-Tenant-Tier";

    private final RateLimitService rateLimitService;

    @Override
    public int getOrder() {
        // Run after authentication filters
        return -80;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        // Skip rate limiting for health checks
        String path = request.getPath().value();
        if (path.startsWith("/actuator/") || path.equals("/health")) {
            return chain.filter(exchange);
        }

        // Extract context
        String tenantId = request.getHeaders().getFirst(TENANT_ID_HEADER);
        String userId = request.getHeaders().getFirst(USER_ID_HEADER);
        String tierHeader = request.getHeaders().getFirst(TENANT_TIER_HEADER);
        String clientIp = getClientIp(exchange);

        // Parse tier
        Tenant.SubscriptionTier tier = null;
        if (tierHeader != null) {
            try {
                tier = Tenant.SubscriptionTier.valueOf(tierHeader);
            } catch (IllegalArgumentException e) {
                log.debug("Invalid tier header: {}", tierHeader);
            }
        }

        // Check rate limit
        RateLimitService.RateLimitResult result = rateLimitService.checkRateLimit(
            tenantId, userId, tier, clientIp
        );

        // Add rate limit headers to response
        ServerHttpResponse response = exchange.getResponse();
        response.getHeaders().add("X-RateLimit-Limit", String.valueOf(result.limit()));
        response.getHeaders().add("X-RateLimit-Remaining", String.valueOf(result.remaining()));
        response.getHeaders().add("X-RateLimit-Reset", String.valueOf(result.resetAt()));

        if (!result.allowed()) {
            // Rate limited
            response.setStatusCode(HttpStatus.TOO_MANY_REQUESTS);
            response.getHeaders().add("Retry-After", result.retryAfter());

            log.warn("Rate limited request from {} (tenant: {}, user: {})",
                clientIp, tenantId, userId);

            return response.setComplete();
        }

        return chain.filter(exchange);
    }

    private String getClientIp(ServerWebExchange exchange) {
        String forwardedFor = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            return forwardedFor.split(",")[0].trim();
        }

        var remoteAddress = exchange.getRequest().getRemoteAddress();
        return remoteAddress != null ? remoteAddress.getAddress().getHostAddress() : "unknown";
    }
}
