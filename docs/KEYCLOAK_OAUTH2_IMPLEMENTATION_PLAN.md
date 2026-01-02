# Keycloak OAuth2 Implementation Plan

**Date:** December 31, 2025
**Status:** Planning Phase (Updated with Security Best Practices)
**Author:** Architecture Team
**Version:** 2.0

---

## Security Best Practices Applied

This implementation follows security best practices from authoritative sources:

### Sources Referenced
- [OWASP OAuth2 Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- [Keycloak Securing Applications Guide](https://www.keycloak.org/docs/25.0.6/securing_apps/index.html)
- [RFC 9700 - OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/rfc9700)
- [Spring Security OAuth2 Resource Server](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)

### Key Security Principles Applied

| Principle | Implementation |
|-----------|----------------|
| **OAuth 2.1 Compliance** | PKCE mandatory, Implicit/Password grants disabled |
| **DPoP (Proof-of-Possession)** | Enabled for sensitive operations (Keycloak 25+) |
| **Strict Redirect URIs** | Exact string matching, no wildcards |
| **Audience Validation** | JWT `aud` claim validated at resource servers |
| **Sender-Constrained Tokens** | Refresh tokens one-time use with rotation |
| **State Parameter** | CSRF protection in all authorization requests |
| **Backend-For-Frontend** | Tokens stored server-side, not in browser localStorage |
| **Short-Lived Access Tokens** | 5 minutes, with automatic refresh |
| **Token Binding** | mTLS for confidential clients in production |

### Deprecated Flows (NOT USED)
Per [RFC 9700](https://datatracker.ietf.org/doc/html/rfc9700) and OAuth 2.1:
- ❌ **Implicit Flow** - MUST NOT be used
- ❌ **Resource Owner Password Credentials** - MUST NOT be used
- ❌ **Hybrid Flow** - Access tokens may leak via browser history

---

## Executive Summary

This document outlines the implementation plan for enterprise-grade OAuth2/OIDC authentication using Keycloak across the WizardSofts Megabuild platform.

### Requirements Summary

| Requirement | Decision |
|-------------|----------|
| **Tenants** | <100, Single realm with groups |
| **Tenant Branding** | Nice to have (Phase 2) |
| **Onboarding** | Self-service via invitation |
| **User Types** | Internal employees + External customers |
| **Social Login** | Nice to have (Google, GitHub) |
| **MFA** | Nice to have (TOTP) |
| **Authorization** | Simple RBAC (admin/user/viewer) |
| **Service-to-Service** | Client credentials (service identity) |
| **User Context Propagation** | Token exchange (future) |
| **Compliance** | Best practices, no specific framework |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              KEYCLOAK                                        │
│                         id.wizardsofts.com                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Realm: wizardsofts                                                  │   │
│  │  ├── Clients: gibd-quant-web, ws-gateway, mobile-app (future)       │   │
│  │  ├── Groups: /tenants/company-a, /tenants/company-b, /internal      │   │
│  │  ├── Realm Roles: super-admin, tenant-admin, user, viewer           │   │
│  │  └── Client Roles: per-app specific roles                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐            ┌────────────────┐           ┌─────────────────┐
│ gibd-quant-web│            │   ws-gateway   │           │ Service-to-     │
│ (OIDC Client) │            │  (Resource     │           │ Service Clients │
│               │            │   Server +     │           │ (Client Creds)  │
│ Auth Code +   │            │   Auth Filter) │           │                 │
│ PKCE Flow     │            │                │           │ ws-trades-svc   │
└───────┬───────┘            └────────┬───────┘           │ ws-company-svc  │
        │                             │                   │ ws-news-svc     │
        │                             │                   └─────────────────┘
        │                             │
        │                             ▼
        │              ┌──────────────────────────────────────────────────┐
        │              │           Microservices (Resource Servers)        │
        │              │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
        └──────────────│  │ws-trades │ │ws-company│ │ ws-news  │          │
                       │  │JWT Valid │ │JWT Valid │ │JWT Valid │          │
                       │  └──────────┘ └──────────┘ └──────────┘          │
                       └──────────────────────────────────────────────────┘
```

---

## Phase 1: Keycloak Realm Configuration

**Duration:** Foundation
**Dependencies:** None

### 1.1 Create Production Realm

```yaml
Realm Configuration:
  Name: wizardsofts
  Display Name: WizardSofts Platform
  Enabled: true
  Registration Allowed: false  # Controlled via invitation
  Email as Username: true
  Login with Email: true
  Duplicate Emails Allowed: false
  Reset Password Allowed: true
  Remember Me: true
  Verify Email: true

Token Settings:
  Access Token Lifespan: 5 minutes  # Short-lived per OWASP recommendation
  Refresh Token Lifespan: 30 days
  Refresh Token Max Reuse: 0        # One-time use (rotation enabled)
  SSO Session Idle: 30 minutes
  SSO Session Max: 10 hours

Security Settings (OAuth 2.1 Compliance):
  Proof Key for Code Exchange: Required  # PKCE mandatory for all clients
  Require Pushed Authorization Requests: false  # Enable later for high-security
  Client Authentication for Token Requests: confidential-clients-only

Brute Force Protection:
  Enabled: true
  Max Login Failures: 5
  Wait Increment: 60 seconds
  Quick Login Check: 1000 ms
  Lock Duration: 600 seconds  # 10 minutes

Password Policy:
  Length: 12
  Uppercase: 1
  Lowercase: 1
  Digits: 1
  Special Characters: 1
  Not Username: true
  Password History: 5
```

### 1.2 Define Realm Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `super-admin` | Platform administrators | Full system access, manage tenants |
| `tenant-admin` | Tenant administrators | Manage users within tenant, configure tenant settings |
| `user` | Standard user | Access to assigned applications |
| `viewer` | Read-only user | View-only access |

### 1.3 Create Client Applications

#### 1.3.1 Frontend Client (gibd-quant-web)

```yaml
Client ID: gibd-quant-web
Client Protocol: openid-connect
Access Type: public
Standard Flow Enabled: true
Direct Access Grants: false  # MUST be false per RFC 9700
Implicit Flow Enabled: false  # MUST be false - deprecated in OAuth 2.1

# SECURITY: Strict Redirect URIs - NO WILDCARDS in production
Valid Redirect URIs:
  - https://quant.wizardsofts.com/api/auth/callback/keycloak
  - http://localhost:3000/api/auth/callback/keycloak  # Development only
Web Origins:
  - https://quant.wizardsofts.com
  - http://localhost:3000

# OAuth 2.1 Security Requirements
PKCE Code Challenge Method: S256  # Required, SHA-256 (plain is weak)
Proof Key for Code Exchange Required: true

# Audience Configuration (for JWT validation)
Full Scope Allowed: false
Default Client Scopes:
  - openid
  - profile
  - email
Optional Client Scopes:
  - offline_access  # For refresh tokens

# Token Settings (client-level overrides)
Access Token Lifespan: 300  # 5 minutes
```

#### 1.3.2 Gateway Resource Server (ws-gateway)

```yaml
Client ID: ws-gateway
Client Protocol: openid-connect
Access Type: confidential
Service Accounts Enabled: true
Authorization Enabled: false  # Simple RBAC for now
Standard Flow Enabled: false
Direct Access Grants: false
```

#### 1.3.3 Service-to-Service Clients

```yaml
# One for each microservice
Client ID: ws-trades-service
Client Protocol: openid-connect
Access Type: confidential
Service Accounts Enabled: true
Standard Flow Enabled: false

Client ID: ws-company-service
# ... same pattern

Client ID: ws-news-service
# ... same pattern
```

### 1.4 Configure Multi-Tenancy (Groups)

```
Group Structure:
├── /tenants
│   ├── /tenants/company-a
│   │   ├── attributes: { tenant_id: "company-a", plan: "enterprise" }
│   │   └── roles: [user]
│   ├── /tenants/company-b
│   │   ├── attributes: { tenant_id: "company-b", plan: "standard" }
│   │   └── roles: [user]
│   └── /tenants/company-c
│       └── ...
└── /internal
    ├── attributes: { tenant_id: "wizardsofts", plan: "internal" }
    └── roles: [super-admin]
```

### 1.5 Custom Token Mappers

Add custom claims to JWT tokens:

| Mapper | Claim Name | Source |
|--------|-----------|--------|
| Tenant ID | `tenant_id` | User attribute or Group attribute |
| Tenant Plan | `tenant_plan` | Group attribute |
| Full Name | `name` | User property |
| User Roles | `roles` | Realm roles |

### 1.6 Deliverables

- [ ] Realm export JSON (`keycloak/realms/wizardsofts-realm.json`)
- [ ] Client configurations
- [ ] Role definitions
- [ ] Group structure
- [ ] Token mapper configurations
- [ ] Documentation for admin portal access

---

## Phase 2: API Gateway Authentication

**Duration:** Core Auth
**Dependencies:** Phase 1

### 2.1 Spring Cloud Gateway Security

#### 2.1.1 Add Dependencies

```xml
<!-- pom.xml additions for ws-gateway -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

#### 2.1.2 Security Configuration

```java
// SecurityConfig.java
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain springSecurityFilterChain(ServerHttpSecurity http) {
        return http
            .csrf(csrf -> csrf.disable())
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .authorizeExchange(exchanges -> exchanges
                // Public endpoints
                .pathMatchers("/actuator/health/**").permitAll()
                .pathMatchers("/api/public/**").permitAll()
                // Protected endpoints
                .pathMatchers("/api/admin/**").hasRole("super-admin")
                .pathMatchers("/api/**").authenticated()
                .anyExchange().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthConverter()))
            )
            .build();
    }

    @Bean
    public ReactiveJwtAuthenticationConverterAdapter jwtAuthConverter() {
        JwtGrantedAuthoritiesConverter converter = new JwtGrantedAuthoritiesConverter();
        converter.setAuthorityPrefix("ROLE_");
        converter.setAuthoritiesClaimName("roles");

        JwtAuthenticationConverter jwtConverter = new JwtAuthenticationConverter();
        jwtConverter.setJwtGrantedAuthoritiesConverter(converter);

        return new ReactiveJwtAuthenticationConverterAdapter(jwtConverter);
    }
}
```

#### 2.1.3 Application Properties

```yaml
# application.yml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://id.wizardsofts.com/realms/wizardsofts
          jwk-set-uri: https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/certs
          # SECURITY: Audience validation - tokens must be intended for this service
          audiences:
            - ws-gateway
            - account
```

#### 2.1.4 Custom JWT Validator with Audience Check

```java
// JwtAudienceValidator.java
@Component
public class JwtAudienceValidator implements OAuth2TokenValidator<Jwt> {

    private final Set<String> allowedAudiences;

    public JwtAudienceValidator(@Value("${jwt.allowed-audiences}") List<String> audiences) {
        this.allowedAudiences = new HashSet<>(audiences);
    }

    @Override
    public OAuth2TokenValidatorResult validate(Jwt jwt) {
        List<String> tokenAudiences = jwt.getAudience();

        if (tokenAudiences == null || tokenAudiences.isEmpty()) {
            return OAuth2TokenValidatorResult.failure(
                new OAuth2Error("invalid_token", "Missing audience claim", null));
        }

        boolean hasValidAudience = tokenAudiences.stream()
            .anyMatch(allowedAudiences::contains);

        if (!hasValidAudience) {
            return OAuth2TokenValidatorResult.failure(
                new OAuth2Error("invalid_token",
                    "Token not intended for this audience", null));
        }

        return OAuth2TokenValidatorResult.success();
    }
}

// SecurityConfig.java - Add custom validator
@Bean
public JwtDecoder jwtDecoder(JwtAudienceValidator audienceValidator) {
    NimbusJwtDecoder decoder = NimbusJwtDecoder
        .withJwkSetUri(jwkSetUri)
        .build();

    OAuth2TokenValidator<Jwt> validators = new DelegatingOAuth2TokenValidator<>(
        JwtValidators.createDefaultWithIssuer(issuerUri),
        audienceValidator,
        new JwtTimestampValidator()
    );

    decoder.setJwtValidator(validators);
    return decoder;
}
```

### 2.2 Tenant Context Extraction

```java
// TenantContextFilter.java
@Component
public class TenantContextFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        return ReactiveSecurityContextHolder.getContext()
            .map(ctx -> ctx.getAuthentication())
            .cast(JwtAuthenticationToken.class)
            .flatMap(auth -> {
                String tenantId = auth.getToken().getClaimAsString("tenant_id");
                exchange.getAttributes().put("tenantId", tenantId);

                // Add to headers for downstream services
                ServerHttpRequest request = exchange.getRequest().mutate()
                    .header("X-Tenant-ID", tenantId)
                    .header("X-User-ID", auth.getToken().getSubject())
                    .build();

                return chain.filter(exchange.mutate().request(request).build());
            })
            .switchIfEmpty(chain.filter(exchange));
    }
}
```

### 2.3 Deliverables

- [ ] `ws-gateway/pom.xml` - Security dependencies
- [ ] `ws-gateway/src/.../config/SecurityConfig.java`
- [ ] `ws-gateway/src/.../filter/TenantContextFilter.java`
- [ ] `ws-gateway/src/.../filter/CorrelationIdFilter.java`
- [ ] `ws-gateway/src/main/resources/application-oauth2.yml`
- [ ] Integration tests for authentication

---

## Phase 3: Microservices as Resource Servers

**Duration:** Service Auth
**Dependencies:** Phase 2

### 3.1 Common Security Module

Create a shared security library for all microservices:

```
libs/
└── ws-security-common/
    ├── pom.xml
    └── src/main/java/com/wizardsofts/security/
        ├── config/ResourceServerConfig.java
        ├── filter/TenantFilter.java
        ├── context/TenantContext.java
        ├── annotation/RequireRole.java
        └── util/JwtUtils.java
```

### 3.2 Service Updates

For each microservice (ws-trades, ws-company, ws-news):

#### 3.2.1 Dependencies

```xml
<dependency>
    <groupId>com.wizardsofts</groupId>
    <artifactId>ws-security-common</artifactId>
    <version>${project.version}</version>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
</dependency>
```

#### 3.2.2 Configuration

```yaml
# application-oauth2.yml (each service)
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://id.wizardsofts.com/realms/wizardsofts
```

### 3.3 Tenant Data Isolation

```java
// TenantAwareRepository.java
public interface TenantAwareRepository<T, ID> extends JpaRepository<T, ID> {

    @Query("SELECT e FROM #{#entityName} e WHERE e.tenantId = :tenantId")
    List<T> findAllByTenantId(@Param("tenantId") String tenantId);

    @Query("SELECT e FROM #{#entityName} e WHERE e.id = :id AND e.tenantId = :tenantId")
    Optional<T> findByIdAndTenantId(@Param("id") ID id, @Param("tenantId") String tenantId);
}
```

### 3.4 Deliverables

- [ ] `libs/ws-security-common/` - Shared security module
- [ ] `ws-trades/` - OAuth2 resource server config
- [ ] `ws-company/` - OAuth2 resource server config
- [ ] `ws-news/` - OAuth2 resource server config
- [ ] Tenant-aware entity base class
- [ ] Data isolation tests

---

## Phase 4: Frontend OIDC Integration

**Duration:** User Auth
**Dependencies:** Phase 1

### 4.1 Install Dependencies

```bash
cd apps/gibd-quant-web
npm install @auth0/nextjs-auth0  # Or next-auth with Keycloak provider
```

### 4.2 Auth Configuration

```typescript
// lib/auth/keycloak.ts
export const keycloakConfig = {
  issuer: process.env.KEYCLOAK_ISSUER,
  clientId: process.env.KEYCLOAK_CLIENT_ID,
  clientSecret: process.env.KEYCLOAK_CLIENT_SECRET, // For server-side
  scopes: ['openid', 'profile', 'email', 'roles'],
};
```

### 4.3 Auth Provider Setup

```typescript
// app/providers.tsx
'use client';

import { SessionProvider } from 'next-auth/react';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      {children}
    </SessionProvider>
  );
}
```

### 4.4 Protected Routes

```typescript
// middleware.ts
import { withAuth } from 'next-auth/middleware';

export default withAuth({
  pages: {
    signIn: '/auth/signin',
  },
});

export const config = {
  matcher: ['/dashboard/:path*', '/portfolio/:path*', '/api/protected/:path*'],
};
```

### 4.5 API Client with Token

```typescript
// lib/api/client.ts
import { getSession } from 'next-auth/react';

export async function apiClient(endpoint: string, options: RequestInit = {}) {
  const session = await getSession();

  const headers = {
    'Content-Type': 'application/json',
    ...(session?.accessToken && {
      Authorization: `Bearer ${session.accessToken}`,
    }),
    ...options.headers,
  };

  return fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers,
  });
}
```

### 4.6 Deliverables

- [ ] `apps/gibd-quant-web/lib/auth/` - Auth configuration
- [ ] `apps/gibd-quant-web/app/api/auth/` - NextAuth routes
- [ ] `apps/gibd-quant-web/middleware.ts` - Route protection
- [ ] `apps/gibd-quant-web/components/auth/` - Login/Logout components
- [ ] Environment variables for Keycloak
- [ ] User session context

---

## Phase 5: Service-to-Service Authentication

**Duration:** Internal Auth
**Dependencies:** Phase 1, Phase 3

### 5.1 Client Credentials Configuration

```java
// OAuth2ClientConfig.java
@Configuration
public class OAuth2ClientConfig {

    @Bean
    public OAuth2AuthorizedClientManager authorizedClientManager(
            ClientRegistrationRepository clientRepo,
            OAuth2AuthorizedClientRepository authorizedClientRepo) {

        OAuth2AuthorizedClientProvider provider =
            OAuth2AuthorizedClientProviderBuilder.builder()
                .clientCredentials()
                .build();

        DefaultOAuth2AuthorizedClientManager manager =
            new DefaultOAuth2AuthorizedClientManager(clientRepo, authorizedClientRepo);
        manager.setAuthorizedClientProvider(provider);

        return manager;
    }

    @Bean
    public WebClient webClient(OAuth2AuthorizedClientManager authorizedClientManager) {
        ServletOAuth2AuthorizedClientExchangeFilterFunction oauth2 =
            new ServletOAuth2AuthorizedClientExchangeFilterFunction(authorizedClientManager);
        oauth2.setDefaultClientRegistrationId("keycloak");

        return WebClient.builder()
            .apply(oauth2.oauth2Configuration())
            .build();
    }
}
```

### 5.2 Service Communication

```java
// NewsServiceClient.java
@Service
public class NewsServiceClient {

    private final WebClient webClient;

    public NewsServiceClient(WebClient webClient) {
        this.webClient = webClient;
    }

    public Mono<List<News>> getNewsByTenant(String tenantId) {
        return webClient.get()
            .uri("http://ws-news/api/news")
            .header("X-Tenant-ID", tenantId)
            .retrieve()
            .bodyToFlux(News.class)
            .collectList();
    }
}
```

### 5.3 Deliverables

- [ ] Client registration for each service
- [ ] OAuth2 client configuration beans
- [ ] WebClient with OAuth2 filter
- [ ] Service client classes
- [ ] Integration tests

---

## Phase 6: Self-Service Tenant Onboarding

**Duration:** Tenancy
**Dependencies:** Phase 1

### 6.1 Tenant Management API

```java
// TenantController.java
@RestController
@RequestMapping("/api/admin/tenants")
@PreAuthorize("hasRole('super-admin')")
public class TenantController {

    @PostMapping
    public ResponseEntity<Tenant> createTenant(@RequestBody CreateTenantRequest request) {
        // 1. Create Keycloak group
        // 2. Create initial admin user
        // 3. Send invitation email
        return ResponseEntity.ok(tenant);
    }

    @PostMapping("/{tenantId}/invite")
    public ResponseEntity<Void> inviteUser(
            @PathVariable String tenantId,
            @RequestBody InviteUserRequest request) {
        // 1. Create user in Keycloak with temporary password
        // 2. Add to tenant group
        // 3. Send invitation email with password reset link
        return ResponseEntity.accepted().build();
    }
}
```

### 6.2 Keycloak Admin Client

```java
// KeycloakAdminService.java
@Service
public class KeycloakAdminService {

    private final Keycloak keycloak;

    public String createTenantGroup(String tenantName, Map<String, List<String>> attributes) {
        GroupRepresentation group = new GroupRepresentation();
        group.setName(tenantName);
        group.setPath("/tenants/" + tenantName);
        group.setAttributes(attributes);

        Response response = keycloak.realm("wizardsofts")
            .groups()
            .add(group);

        return getCreatedId(response);
    }

    public void addUserToTenant(String userId, String tenantId) {
        GroupRepresentation group = findGroupByPath("/tenants/" + tenantId);
        keycloak.realm("wizardsofts")
            .users()
            .get(userId)
            .joinGroup(group.getId());
    }
}
```

### 6.3 Deliverables

- [ ] Tenant management REST API
- [ ] Keycloak admin client service
- [ ] Invitation email templates
- [ ] Self-service onboarding flow
- [ ] Admin UI for tenant management

---

## Phase 7: Audit & Observability

**Duration:** Tracking
**Dependencies:** Phase 2, Phase 3

### 7.1 Audit Logging

```java
// AuditService.java
@Service
public class AuditService {

    @Autowired
    private AuditLogRepository auditRepo;

    public void logAccess(
            String userId,
            String tenantId,
            String resource,
            String action,
            String outcome) {

        AuditLog log = AuditLog.builder()
            .userId(userId)
            .tenantId(tenantId)
            .resource(resource)
            .action(action)
            .outcome(outcome)
            .timestamp(Instant.now())
            .correlationId(MDC.get("correlationId"))
            .ipAddress(MDC.get("clientIp"))
            .userAgent(MDC.get("userAgent"))
            .build();

        auditRepo.save(log);
    }
}
```

### 7.2 Keycloak Event Listener

Enable event logging in Keycloak:

```json
{
  "eventsEnabled": true,
  "eventsListeners": ["jboss-logging", "metrics-listener"],
  "enabledEventTypes": [
    "LOGIN", "LOGOUT", "LOGIN_ERROR",
    "REGISTER", "UPDATE_PROFILE",
    "CLIENT_LOGIN", "TOKEN_EXCHANGE",
    "CODE_TO_TOKEN", "CODE_TO_TOKEN_ERROR",
    "REFRESH_TOKEN", "REFRESH_TOKEN_ERROR",
    "INTROSPECT_TOKEN", "INTROSPECT_TOKEN_ERROR",
    "FEDERATED_IDENTITY_LINK", "REMOVE_FEDERATED_IDENTITY"
  ],
  "adminEventsEnabled": true,
  "adminEventsDetailsEnabled": true
}
```

### 7.3 Keycloak Metrics SPI (Prometheus Integration)

Install and configure [Keycloak Metrics SPI](https://github.com/aerogear/keycloak-metrics-spi) for Prometheus monitoring:

```yaml
# docker-compose.keycloak.yml
keycloak:
  environment:
    KC_HEALTH_ENABLED: 'true'
    KC_METRICS_ENABLED: 'true'
  volumes:
    - ./keycloak/providers/keycloak-metrics-spi.jar:/opt/keycloak/providers/keycloak-metrics-spi.jar

# prometheus.yml - scrape config
scrape_configs:
  - job_name: 'keycloak'
    scheme: https
    static_configs:
      - targets: ['id.wizardsofts.com']
    metrics_path: /realms/wizardsofts/metrics
    tls_config:
      insecure_skip_verify: false
```

### 7.4 Security Alerting Rules

```yaml
# prometheus/security-alerts-keycloak.yml
groups:
  - name: keycloak_security_alerts
    rules:
      - alert: HighFailedLoginRate
        expr: rate(keycloak_login_error_total[5m]) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"
          description: "More than 0.5 failed logins per second for 2 minutes"

      - alert: BruteForceAttackDetected
        expr: rate(keycloak_login_error_total{error="user_temporarily_disabled"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Brute force attack - accounts locked"
          description: "Users being temporarily disabled due to failed login attempts"

      - alert: AbnormalTokenRefreshRate
        expr: rate(keycloak_refresh_token_total[5m]) > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Abnormally high token refresh rate"
          description: "Possible token theft or misconfigured client"

      - alert: SuspiciousAdminActivity
        expr: rate(keycloak_admin_event_total{operation=~"CREATE|DELETE"}[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Unusual admin activity detected"
          description: "High rate of admin CREATE/DELETE operations"

      - alert: CrossTenantAccessAttempt
        expr: rate(auth_cross_tenant_access_attempts_total[5m]) > 0
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "Cross-tenant access attempt detected"
          description: "User attempted to access resources from another tenant"
```

### 7.5 Application-Level Auth Metrics

```java
// AuthMetrics.java
@Component
public class AuthMetrics {

    private final Counter loginAttempts = Counter.build()
        .name("auth_login_attempts_total")
        .help("Total login attempts")
        .labelNames("tenant_id", "outcome")
        .register();

    private final Counter tokenValidations = Counter.build()
        .name("auth_token_validations_total")
        .help("Total token validations")
        .labelNames("service", "outcome")
        .register();

    private final Counter crossTenantAccessAttempts = Counter.build()
        .name("auth_cross_tenant_access_attempts_total")
        .help("Cross-tenant access attempts (security alert)")
        .labelNames("user_id", "source_tenant", "target_tenant")
        .register();

    private final Histogram tokenValidationDuration = Histogram.build()
        .name("auth_token_validation_duration_seconds")
        .help("Time to validate JWT tokens")
        .labelNames("service")
        .register();

    public void recordCrossTenantAttempt(String userId, String sourceTenant, String targetTenant) {
        crossTenantAccessAttempts.labels(userId, sourceTenant, targetTenant).inc();
        log.warn("SECURITY: Cross-tenant access attempt - user={}, from={}, to={}",
            userId, sourceTenant, targetTenant);
    }
}
```

### 7.6 Grafana Dashboard

Import the official [Keycloak Grafana Dashboard](https://grafana.com/grafana/dashboards/10441-keycloak-metrics-dashboard/) and extend with custom panels:

```json
// grafana/dashboards/keycloak-security.json
{
  "title": "Keycloak Security Dashboard",
  "panels": [
    { "title": "Login Success vs Failure Rate", "type": "graph" },
    { "title": "Active Sessions by Tenant", "type": "stat" },
    { "title": "Token Refresh Rate", "type": "timeseries" },
    { "title": "Brute Force Lock Events", "type": "alertlist" },
    { "title": "Cross-Tenant Access Attempts", "type": "alertlist" },
    { "title": "Top 10 Failed Login Users", "type": "table" }
  ]
}
```

### 7.7 Deliverables

- [ ] Audit log entity and repository
- [ ] Audit service with correlation ID tracking
- [ ] Keycloak event configuration export
- [ ] Keycloak Metrics SPI installation
- [ ] Prometheus scrape config for Keycloak
- [ ] Security alerting rules (prometheus)
- [ ] Application-level auth metrics
- [ ] Grafana dashboard for auth metrics
- [ ] Log aggregation setup (ELK/Loki)

---

## Implementation Checklist

### Phase 1: Keycloak Realm Configuration
- [ ] Create `wizardsofts` realm
- [ ] Configure realm settings (tokens, sessions)
- [ ] Create realm roles (super-admin, tenant-admin, user, viewer)
- [ ] Create `gibd-quant-web` client (public, PKCE)
- [ ] Create `ws-gateway` client (confidential)
- [ ] Create service clients (ws-trades-service, etc.)
- [ ] Configure group structure (/tenants/*, /internal)
- [ ] Add custom token mappers (tenant_id, roles)
- [ ] Export realm configuration to JSON
- [ ] Test login flow manually

### Phase 2: API Gateway Authentication
- [ ] Add security dependencies to ws-gateway
- [ ] Create SecurityConfig.java
- [ ] Create TenantContextFilter.java
- [ ] Create CorrelationIdFilter.java
- [ ] Configure application-oauth2.yml
- [ ] Update docker-compose with OAUTH2 profile
- [ ] Test gateway authentication

### Phase 3: Microservices as Resource Servers
- [ ] Create ws-security-common library
- [ ] Add security to ws-trades
- [ ] Add security to ws-company
- [ ] Add security to ws-news
- [ ] Implement tenant data isolation
- [ ] Test JWT validation in services

### Phase 4: Frontend OIDC Integration
- [ ] Install next-auth dependencies
- [ ] Configure Keycloak provider
- [ ] Create auth API routes
- [ ] Implement middleware for protected routes
- [ ] Create login/logout components
- [ ] Update API client with token injection
- [ ] Test full login flow

### Phase 5: Service-to-Service Authentication
- [ ] Configure client credentials in services
- [ ] Create WebClient with OAuth2 filter
- [ ] Update service-to-service calls
- [ ] Test token propagation

### Phase 6: Self-Service Tenant Onboarding
- [ ] Create TenantController
- [ ] Create KeycloakAdminService
- [ ] Design invitation email templates
- [ ] Implement user invitation flow
- [ ] Test tenant creation

### Phase 7: Audit & Observability
- [ ] Create AuditLog entity
- [ ] Implement AuditService
- [ ] Enable Keycloak events
- [ ] Add Prometheus metrics
- [ ] Create Grafana dashboard
- [ ] Test audit logging

---

## Environment Variables

### Keycloak Server
```bash
KEYCLOAK_REALM=wizardsofts
KEYCLOAK_URL=https://id.wizardsofts.com
```

### Backend Services
```bash
KEYCLOAK_ISSUER_URI=https://id.wizardsofts.com/realms/wizardsofts
KEYCLOAK_JWK_SET_URI=https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/certs

# Service clients
WS_GATEWAY_CLIENT_ID=ws-gateway
WS_GATEWAY_CLIENT_SECRET=${WS_GATEWAY_CLIENT_SECRET}

WS_TRADES_CLIENT_ID=ws-trades-service
WS_TRADES_CLIENT_SECRET=${WS_TRADES_CLIENT_SECRET}
# ... etc
```

### Frontend
```bash
KEYCLOAK_ISSUER=https://id.wizardsofts.com/realms/wizardsofts
KEYCLOAK_CLIENT_ID=gibd-quant-web
NEXTAUTH_URL=https://quant.wizardsofts.com
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
```

---

## Security Considerations

### Token Security (OAuth 2.1 Compliant)
- Access tokens: 5-minute lifespan (short-lived per OWASP)
- Refresh tokens: 30-day lifespan with **one-time use rotation**
- PKCE (S256) required for ALL public clients - plain method disabled
- Tokens stored in **httpOnly, Secure, SameSite=Strict** cookies
- Access tokens NEVER stored in localStorage or sessionStorage
- Audience (`aud`) claim validated at each resource server
- Issuer (`iss`) claim validated against configured issuer URI

### Authentication Flow Security
- **Authorization Code + PKCE**: Only allowed flow for browser clients
- **Client Credentials**: Only for service-to-service (confidential clients)
- **Implicit Flow**: DISABLED (deprecated in OAuth 2.1)
- **Password Grant**: DISABLED (deprecated in OAuth 2.1)
- State parameter: Required for CSRF protection
- Nonce validation: Enabled for OIDC flows

### Network Security
- All Keycloak traffic over HTTPS (TLS 1.2+)
- HSTS enabled with 1-year max-age, includeSubDomains, preload
- Internal services validate JWT signatures via JWKS endpoint
- JWKS endpoint cached with periodic refresh (not per-request)
- Service-to-service uses confidential clients with client_secret_post
- Rate limiting on token and authorization endpoints
- IP-based blocking after repeated failures (Keycloak brute force protection)

### Data Security
- Tenant isolation via `tenant_id` claim in JWT
- All queries filtered by tenant context at repository layer
- Cross-tenant access attempts: immediately logged + alerted
- PII encrypted at rest (AES-256)
- Passwords: Argon2id hashing (Keycloak default)

### Session Security
- SSO session idle timeout: 30 minutes
- SSO session max lifespan: 10 hours
- Concurrent sessions: Limited per user (configurable)
- Session invalidation on password change
- Remember-me: Optional, with extended but limited duration

### Monitoring & Detection
- All login events logged with: IP, user-agent, tenant, outcome
- Failed login attempts tracked per user and per IP
- Brute force detection: 5 failures = 10-minute lockout
- Real-time alerts for: high failure rates, cross-tenant attempts, admin activity
- Correlation IDs propagated through all service calls

---

## Rollback Plan

If issues occur during implementation:

1. **Gateway fails auth**: Revert to pre-OAuth2 branch, disable security filter
2. **Services reject tokens**: Verify JWK cache, check issuer URI
3. **Frontend login broken**: Fall back to API key auth temporarily
4. **Performance issues**: Increase token lifespan, add caching

---

## Success Criteria

- [ ] All API endpoints require authentication
- [ ] Users can log in via Keycloak
- [ ] Tenant data is properly isolated
- [ ] Service-to-service calls authenticated
- [ ] Audit logs capture all auth events
- [ ] No increase in p99 latency >50ms
- [ ] All existing tests pass

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Approve implementation** to proceed
3. **Create feature branch**: `feature/keycloak-oauth2-integration`
4. **Start Phase 1**: Keycloak realm configuration
5. **Iterate through phases** with MR per phase

---

**Document Status:** Ready for Review
**Estimated Total Effort:** 7 phases
**Dependencies:** Keycloak server already running

