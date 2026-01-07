package com.wizardsofts.gibd.gateway_service.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * OAuth2 Client Credentials Service for service-to-service authentication.
 *
 * Uses Keycloak client credentials grant to obtain access tokens for
 * calling other services. Implements token caching and refresh.
 *
 * Usage:
 *   String token = oauth2ClientService.getServiceToken();
 *   headers.set("Authorization", "Bearer " + token);
 */
@Slf4j
@Service
public class OAuth2ClientService {

    @Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
    private String issuerUri;

    @Value("${oauth2.client.id:ws-gateway}")
    private String clientId;

    @Value("${oauth2.client.secret:}")
    private String clientSecret;

    private final RestTemplate restTemplate = new RestTemplate();
    private final Map<String, CachedToken> tokenCache = new ConcurrentHashMap<>();

    /**
     * Cached token with expiration
     */
    private static class CachedToken {
        String accessToken;
        Instant expiresAt;

        CachedToken(String accessToken, long expiresIn) {
            this.accessToken = accessToken;
            // Refresh 60 seconds before expiration
            this.expiresAt = Instant.now().plusSeconds(expiresIn - 60);
        }

        boolean isExpired() {
            return Instant.now().isAfter(expiresAt);
        }
    }

    /**
     * Gets an access token using client credentials grant.
     * Returns cached token if still valid.
     *
     * @return Access token for service-to-service calls
     */
    public String getServiceToken() {
        CachedToken cached = tokenCache.get(clientId);

        if (cached != null && !cached.isExpired()) {
            log.debug("Using cached service token for client: {}", clientId);
            return cached.accessToken;
        }

        log.info("Obtaining new service token for client: {}", clientId);
        return refreshToken();
    }

    /**
     * Gets an access token for a specific target service.
     * Useful when different scopes are needed for different services.
     *
     * @param targetService The service to call
     * @param scope Additional scopes to request
     * @return Access token
     */
    public String getServiceToken(String targetService, String scope) {
        String cacheKey = clientId + ":" + targetService;
        CachedToken cached = tokenCache.get(cacheKey);

        if (cached != null && !cached.isExpired()) {
            return cached.accessToken;
        }

        return refreshToken(scope, cacheKey);
    }

    private String refreshToken() {
        return refreshToken("openid", clientId);
    }

    private String refreshToken(String scope, String cacheKey) {
        try {
            String tokenEndpoint = issuerUri + "/protocol/openid-connect/token";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

            MultiValueMap<String, String> body = new LinkedMultiValueMap<>();
            body.add("grant_type", "client_credentials");
            body.add("client_id", clientId);
            body.add("client_secret", clientSecret);
            body.add("scope", scope);

            HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(body, headers);

            ResponseEntity<Map> response = restTemplate.exchange(
                tokenEndpoint,
                HttpMethod.POST,
                request,
                Map.class
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> tokenResponse = response.getBody();
                String accessToken = (String) tokenResponse.get("access_token");
                long expiresIn = ((Number) tokenResponse.get("expires_in")).longValue();

                tokenCache.put(cacheKey, new CachedToken(accessToken, expiresIn));
                log.info("Successfully obtained service token, expires in {} seconds", expiresIn);

                return accessToken;
            }

            throw new RuntimeException("Failed to obtain service token");

        } catch (Exception e) {
            log.error("Error obtaining service token: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to obtain service token", e);
        }
    }

    /**
     * Clears the token cache. Useful for testing or forced refresh.
     */
    public void clearCache() {
        tokenCache.clear();
        log.info("Token cache cleared");
    }

    /**
     * Creates HTTP headers with the service token for outbound calls.
     *
     * @return HttpHeaders with Authorization bearer token
     */
    public HttpHeaders createAuthHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set(HttpHeaders.AUTHORIZATION, "Bearer " + getServiceToken());
        return headers;
    }
}
