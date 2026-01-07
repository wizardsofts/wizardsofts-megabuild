package com.wizardsofts.gibd.gateway_service.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2TokenValidator;
import org.springframework.security.oauth2.core.OAuth2TokenValidatorResult;
import org.springframework.security.oauth2.jwt.Jwt;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Custom JWT validator that checks the audience (aud) claim.
 * Per OAuth 2.1 best practices, tokens should only be accepted
 * if they were intended for this specific resource server.
 *
 * Security: Prevents token confusion attacks where a token
 * intended for one service is used to access another.
 */
@Slf4j
public class JwtAudienceValidator implements OAuth2TokenValidator<Jwt> {

    private final Set<String> allowedAudiences;

    public JwtAudienceValidator(List<String> audiences) {
        this.allowedAudiences = new HashSet<>(audiences);
        log.info("JWT Audience Validator initialized with allowed audiences: {}", audiences);
    }

    @Override
    public OAuth2TokenValidatorResult validate(Jwt jwt) {
        List<String> tokenAudiences = jwt.getAudience();

        // Check if token has any audience claim
        if (tokenAudiences == null || tokenAudiences.isEmpty()) {
            log.warn("JWT validation failed: Missing audience claim for subject {}", jwt.getSubject());
            return OAuth2TokenValidatorResult.failure(
                new OAuth2Error(
                    "invalid_token",
                    "Missing audience claim in token",
                    null
                )
            );
        }

        // Check if any of the token's audiences match our allowed audiences
        boolean hasValidAudience = tokenAudiences.stream()
            .anyMatch(allowedAudiences::contains);

        if (!hasValidAudience) {
            log.warn("JWT validation failed: Token audience {} not in allowed list {} for subject {}",
                tokenAudiences, allowedAudiences, jwt.getSubject());
            return OAuth2TokenValidatorResult.failure(
                new OAuth2Error(
                    "invalid_token",
                    "Token not intended for this audience",
                    null
                )
            );
        }

        log.debug("JWT audience validation passed for subject {}", jwt.getSubject());
        return OAuth2TokenValidatorResult.success();
    }
}
