package com.wizardsofts.gibd.gateway_service.filter;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.service.ApiKeyService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Optional;

/**
 * Gateway filter for API key authentication.
 *
 * Supports authentication via:
 * - X-API-Key header
 * - Authorization: ApiKey <key> header
 *
 * When authenticated via API key:
 * - Sets X-Tenant-ID header from the key's tenant
 * - Sets X-Auth-Method: api-key header
 * - Bypasses JWT validation
 *
 * Priority: JWT authentication takes precedence over API key.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ApiKeyAuthenticationFilter implements GlobalFilter, Ordered {

    private static final String API_KEY_HEADER = "X-API-Key";
    private static final String AUTH_METHOD_HEADER = "X-Auth-Method";
    private static final String TENANT_ID_HEADER = "X-Tenant-ID";
    private static final String API_KEY_PREFIX = "ApiKey ";

    private final ApiKeyService apiKeyService;
    private final SecurityAuditLogger auditLogger;

    @Override
    public int getOrder() {
        // Run before TenantContextFilter but after security
        return -100;
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        // Skip if already authenticated via JWT (Authorization: Bearer header)
        String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            log.debug("JWT auth present, skipping API key auth");
            return chain.filter(exchange);
        }

        // Try to extract API key
        String apiKey = extractApiKey(request);
        if (apiKey == null) {
            return chain.filter(exchange);
        }

        // Get client IP for tracking
        String clientIp = getClientIp(exchange);

        // Validate API key
        Optional<Tenant> tenantOpt = apiKeyService.validateApiKey(apiKey, null, clientIp);

        if (tenantOpt.isEmpty()) {
            log.debug("Invalid API key from {}", clientIp);
            auditLogger.logAuthFailure("api-key", clientIp, "Invalid API key", null);
            return unauthorized(exchange);
        }

        Tenant tenant = tenantOpt.get();

        // Check if tenant is active
        if (!tenant.isActive()) {
            log.warn("API key for inactive tenant: {}", tenant.getSlug());
            auditLogger.logAuthFailure("api-key:" + tenant.getSlug(), clientIp, "Tenant inactive", null);
            return unauthorized(exchange);
        }

        log.debug("API key authenticated for tenant: {}", tenant.getSlug());

        // Add tenant context headers
        ServerHttpRequest mutatedRequest = request.mutate()
            .header(TENANT_ID_HEADER, tenant.getId().toString())
            .header(AUTH_METHOD_HEADER, "api-key")
            .header("X-Tenant-Slug", tenant.getSlug())
            .header("X-Tenant-Tier", tenant.getTier().name())
            .build();

        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }

    /**
     * Extracts API key from request headers.
     *
     * Supports:
     * - X-API-Key: <key>
     * - Authorization: ApiKey <key>
     */
    private String extractApiKey(ServerHttpRequest request) {
        // Try X-API-Key header
        String apiKey = request.getHeaders().getFirst(API_KEY_HEADER);
        if (apiKey != null && !apiKey.isBlank()) {
            return apiKey.trim();
        }

        // Try Authorization: ApiKey header
        String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (authHeader != null && authHeader.startsWith(API_KEY_PREFIX)) {
            return authHeader.substring(API_KEY_PREFIX.length()).trim();
        }

        return null;
    }

    private String getClientIp(ServerWebExchange exchange) {
        String forwardedFor = exchange.getRequest().getHeaders().getFirst("X-Forwarded-For");
        if (forwardedFor != null && !forwardedFor.isBlank()) {
            return forwardedFor.split(",")[0].trim();
        }

        var remoteAddress = exchange.getRequest().getRemoteAddress();
        return remoteAddress != null ? remoteAddress.getAddress().getHostAddress() : "unknown";
    }

    private Mono<Void> unauthorized(ServerWebExchange exchange) {
        exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
        exchange.getResponse().getHeaders().add("WWW-Authenticate", "ApiKey");
        return exchange.getResponse().setComplete();
    }
}
