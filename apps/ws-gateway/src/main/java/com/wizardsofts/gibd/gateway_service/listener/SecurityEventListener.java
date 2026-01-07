package com.wizardsofts.gibd.gateway_service.listener;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.security.authentication.event.AbstractAuthenticationFailureEvent;
import org.springframework.security.authentication.event.AuthenticationSuccessEvent;
import org.springframework.security.authentication.event.LogoutSuccessEvent;
import org.springframework.security.authorization.event.AuthorizationDeniedEvent;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

/**
 * Listener for Spring Security events.
 *
 * Captures and logs:
 * - Authentication success/failure
 * - Authorization denied
 * - Logout events
 *
 * Integrates with SecurityAuditLogger for audit trail.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SecurityEventListener {

    private final SecurityAuditLogger auditLogger;

    /**
     * Handles successful authentication events.
     */
    @EventListener
    public void onAuthenticationSuccess(AuthenticationSuccessEvent event) {
        Authentication auth = event.getAuthentication();

        String userId = auth.getName();
        String email = null;
        String clientId = null;

        if (auth instanceof JwtAuthenticationToken jwtAuth) {
            Jwt jwt = jwtAuth.getToken();
            userId = jwt.getSubject();
            email = jwt.getClaimAsString("email");
            clientId = jwt.getClaimAsString("azp");
        }

        log.debug("Authentication success: user={}, email={}, client={}",
            userId, email, clientId);

        auditLogger.logAuthSuccess(userId, email, clientId, null, null);
    }

    /**
     * Handles authentication failure events.
     */
    @EventListener
    public void onAuthenticationFailure(AbstractAuthenticationFailureEvent event) {
        Authentication auth = event.getAuthentication();
        String reason = event.getException().getMessage();

        String principal = auth != null ? auth.getName() : "unknown";

        log.warn("Authentication failure: principal={}, reason={}",
            principal, reason);

        auditLogger.logAuthFailure(principal, null, reason, null);
    }

    /**
     * Handles authorization denied events.
     */
    @EventListener
    public void onAuthorizationDenied(AuthorizationDeniedEvent<?> event) {
        Authentication auth = event.getAuthentication().get();
        String userId = auth != null ? auth.getName() : "anonymous";

        // Get resource if available
        String resource = "unknown";
        Object source = event.getSource();
        if (source != null) {
            resource = source.toString();
        }

        log.warn("Authorization denied: user={}, resource={}",
            userId, resource);

        auditLogger.logAccessDenied(userId, resource, null, null, null);
    }

    /**
     * Handles logout events.
     */
    @EventListener
    public void onLogoutSuccess(LogoutSuccessEvent event) {
        Authentication auth = event.getAuthentication();
        String userId = auth != null ? auth.getName() : "unknown";

        log.info("Logout success: user={}", userId);
    }
}
