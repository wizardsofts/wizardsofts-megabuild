package com.wizardsofts.gibd.gateway_service.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Filter that extracts tenant context from JWT and adds it to request headers.
 * This enables tenant isolation in downstream microservices.
 *
 * Headers added:
 * - X-Tenant-ID: The tenant identifier from JWT claim
 * - X-User-ID: The user subject from JWT
 * - X-Correlation-ID: Unique ID for request tracing
 * - X-User-Roles: Comma-separated list of user roles
 */
@Slf4j
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 10)
public class TenantContextFilter extends OncePerRequestFilter {

    private static final String HEADER_TENANT_ID = "X-Tenant-ID";
    private static final String HEADER_USER_ID = "X-User-ID";
    private static final String HEADER_CORRELATION_ID = "X-Correlation-ID";
    private static final String HEADER_USER_ROLES = "X-User-Roles";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        // Generate or extract correlation ID
        String correlationId = request.getHeader(HEADER_CORRELATION_ID);
        if (correlationId == null || correlationId.isEmpty()) {
            correlationId = UUID.randomUUID().toString();
        }

        // Add correlation ID to response for client tracking
        response.setHeader(HEADER_CORRELATION_ID, correlationId);

        // Check if request is authenticated
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication instanceof JwtAuthenticationToken jwtAuth) {
            Jwt jwt = jwtAuth.getToken();

            String tenantId = extractTenantId(jwt);
            String userId = jwt.getSubject();
            String roles = extractRoles(jwt);

            log.debug("Processing request for tenant={}, user={}, correlationId={}",
                tenantId, userId, correlationId);

            // Wrap request to add headers for downstream services
            final String finalCorrelationId = correlationId;
            HttpServletRequest wrappedRequest = new TenantHeadersRequestWrapper(
                request, tenantId, userId, finalCorrelationId, roles
            );

            filterChain.doFilter(wrappedRequest, response);
        } else {
            // Unauthenticated request - still add correlation ID
            HttpServletRequest wrappedRequest = new TenantHeadersRequestWrapper(
                request, null, null, correlationId, null
            );
            filterChain.doFilter(wrappedRequest, response);
        }
    }

    /**
     * Extracts tenant_id from JWT claim.
     * First checks direct claim, then falls back to group-based tenant.
     */
    private String extractTenantId(Jwt jwt) {
        // Try direct tenant_id claim
        String tenantId = jwt.getClaimAsString("tenant_id");
        if (tenantId != null && !tenantId.isEmpty()) {
            return tenantId;
        }

        // Fallback: extract from groups claim (e.g., /tenants/company-a)
        List<String> groups = jwt.getClaimAsStringList("groups");
        if (groups != null) {
            for (String group : groups) {
                if (group.startsWith("/tenants/")) {
                    return group.substring("/tenants/".length());
                }
            }
        }

        log.warn("No tenant_id found in JWT for user {}", jwt.getSubject());
        return "unknown";
    }

    /**
     * Extracts roles from realm_access claim.
     */
    @SuppressWarnings("unchecked")
    private String extractRoles(Jwt jwt) {
        Map<String, Object> realmAccess = jwt.getClaim("realm_access");
        if (realmAccess != null && realmAccess.containsKey("roles")) {
            List<String> roles = (List<String>) realmAccess.get("roles");
            return String.join(",", roles);
        }
        return "";
    }

    /**
     * Request wrapper that adds tenant context headers.
     */
    private static class TenantHeadersRequestWrapper extends HttpServletRequestWrapper {

        private final Map<String, String> additionalHeaders = new HashMap<>();

        public TenantHeadersRequestWrapper(HttpServletRequest request,
                                           String tenantId,
                                           String userId,
                                           String correlationId,
                                           String roles) {
            super(request);

            if (tenantId != null) {
                additionalHeaders.put(HEADER_TENANT_ID, tenantId);
            }
            if (userId != null) {
                additionalHeaders.put(HEADER_USER_ID, userId);
            }
            if (correlationId != null) {
                additionalHeaders.put(HEADER_CORRELATION_ID, correlationId);
            }
            if (roles != null && !roles.isEmpty()) {
                additionalHeaders.put(HEADER_USER_ROLES, roles);
            }
        }

        @Override
        public String getHeader(String name) {
            String additionalValue = additionalHeaders.get(name);
            if (additionalValue != null) {
                return additionalValue;
            }
            return super.getHeader(name);
        }

        @Override
        public Enumeration<String> getHeaderNames() {
            List<String> names = Collections.list(super.getHeaderNames());
            names.addAll(additionalHeaders.keySet());
            return Collections.enumeration(names);
        }

        @Override
        public Enumeration<String> getHeaders(String name) {
            String additionalValue = additionalHeaders.get(name);
            if (additionalValue != null) {
                return Collections.enumeration(List.of(additionalValue));
            }
            return super.getHeaders(name);
        }
    }
}
