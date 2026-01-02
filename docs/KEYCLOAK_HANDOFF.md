# Keycloak OAuth2 Implementation Handoff

**Project:** WizardSofts Megabuild
**Date:** December 31, 2025
**Status:** Implementation Complete - Ready for Configuration

---

## Quick Start

### 1. Keycloak Setup

Create clients in Keycloak admin console (`https://id.wizardsofts.com`):

```
1. Login as admin
2. Navigate to Clients
3. Create clients as listed below
4. Configure client scopes
5. Set up role mappers
```

#### Client: gibd-quant-web (Frontend)
```
Client ID: gibd-quant-web
Client Type: Public
Standard Flow: Enabled
PKCE: Required (S256)
Redirect URIs:
  - https://app.wizardsofts.com/*
  - http://localhost:3001/*
Web Origins:
  - https://app.wizardsofts.com
  - http://localhost:3001
```

#### Client: ws-gateway-service (Gateway S2S)
```
Client ID: ws-gateway-service
Client Type: Confidential
Service Account: Enabled
Client Credentials: Enabled
Scope: openid
Client Secret: Generate and save
```

#### Client: ws-trades-service, ws-company-service, ws-news-service
Same configuration as ws-gateway-service with respective client IDs.

### 2. Environment Configuration

Copy to `.env` files:

**ws-gateway:**
```env
KEYCLOAK_ISSUER_URI=https://id.wizardsofts.com/realms/wizardsofts
WS_GATEWAY_CLIENT_SECRET=<from-keycloak>
SPRING_PROFILES_ACTIVE=oauth2,tenant,observability
```

**ws-trades, ws-company, ws-news:**
```env
KEYCLOAK_ISSUER_URI=https://id.wizardsofts.com/realms/wizardsofts
WS_{SERVICE}_CLIENT_SECRET=<from-keycloak>
```

**gibd-quant-web:**
```env
NEXTAUTH_URL=https://app.wizardsofts.com
NEXTAUTH_SECRET=$(openssl rand -base64 32)
KEYCLOAK_CLIENT_ID=gibd-quant-web
KEYCLOAK_ISSUER=https://id.wizardsofts.com/realms/wizardsofts
```

### 3. Database Migration

Run migration for tenants table:

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    owner_email VARCHAR(255) NOT NULL,
    keycloak_group_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    tier VARCHAR(20) NOT NULL DEFAULT 'FREE',
    metadata TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    suspended_at TIMESTAMP
);

CREATE INDEX idx_tenant_slug ON tenants(slug);
CREATE INDEX idx_tenant_keycloak_group ON tenants(keycloak_group_id);
```

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Browser   │────▶│  Keycloak   │────▶│   Frontend (OIDC)   │
└─────────────┘     └─────────────┘     └──────────┬──────────┘
                                                    │
                    ┌───────────────────────────────▼───────────────────────────┐
                    │                     ws-gateway                             │
                    │  ┌─────────────────────────────────────────────────────┐  │
                    │  │ JWT Validation │ Role Extraction │ Tenant Context   │  │
                    │  └─────────────────────────────────────────────────────┘  │
                    └───────────┬───────────────────┬───────────────┬───────────┘
                                │                   │               │
                    ┌───────────▼───┐   ┌───────────▼───┐   ┌───────▼───────┐
                    │   ws-trades   │   │  ws-company   │   │    ws-news    │
                    │ (Resource Srv)│   │ (Resource Srv)│   │ (Resource Srv)│
                    └───────────────┘   └───────────────┘   └───────────────┘
```

---

## Files Modified/Created

### ws-gateway

| Path | Description |
|------|-------------|
| `config/SecurityConfig.java` | OAuth2 Resource Server |
| `config/JwtAudienceValidator.java` | Audience validation |
| `filter/TenantContextFilter.java` | JWT → Headers |
| `filter/SecurityAuditFilter.java` | Audit logging |
| `metrics/AuthMetrics.java` | Prometheus metrics |
| `service/OAuth2ClientService.java` | S2S auth |
| `service/TenantOnboardingService.java` | Tenant registration |
| `service/KeycloakTenantProvisioningService.java` | Keycloak groups |
| `controller/TenantOnboardingController.java` | Tenant API |
| `model/Tenant.java` | Tenant entity |
| `repository/TenantRepository.java` | Tenant DAO |
| `security/TenantAccessChecker.java` | Authorization |
| `audit/*.java` | Audit event system |
| `application-oauth2.yml` | OAuth2 config |
| `application-tenant.yml` | Tenant config |
| `application-observability.yml` | Observability |

### ws-trades, ws-company, ws-news

| Path | Description |
|------|-------------|
| `security/TenantContext.java` | Tenant context record |
| `security/TenantContextHolder.java` | ThreadLocal |
| `security/TenantContextFilter.java` | Header extraction |
| `security/GatewayHeaderAuthFilter.java` | Header auth |
| `config/SecurityConfig.java` | Dual auth support |
| `service/OAuth2ClientService.java` | S2S auth |
| `audit/SecurityAuditLogger.java` | Audit logging |

### gibd-quant-web

| Path | Description |
|------|-------------|
| `lib/auth.ts` | NextAuth config |
| `app/api/auth/[...nextauth]/route.ts` | API handler |
| `app/auth/signin/page.tsx` | Sign-in page |
| `app/auth/error/page.tsx` | Error page |
| `components/providers/auth-provider.tsx` | Provider |
| `hooks/use-auth.ts` | Auth hooks |
| `.env.example` | Environment template |

---

## Testing

### Quick Validation

1. **Health Check:**
   ```bash
   curl https://api.wizardsofts.com/actuator/health
   ```

2. **Get Token:**
   ```bash
   curl -X POST https://id.wizardsofts.com/realms/wizardsofts/protocol/openid-connect/token \
     -d "grant_type=client_credentials" \
     -d "client_id=ws-gateway-service" \
     -d "client_secret=YOUR_SECRET"
   ```

3. **Test Protected Endpoint:**
   ```bash
   curl https://api.wizardsofts.com/api/v1/test \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Frontend Login:**
   - Navigate to https://app.wizardsofts.com
   - Click "Sign In"
   - Authenticate with Keycloak
   - Verify redirect and session

### Monitoring

- Prometheus metrics: `/actuator/prometheus`
- Health: `/actuator/health`
- Audit logs: Look for `SECURITY_AUDIT` logger

---

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check token expiration
   - Verify audience claim includes service
   - Check Keycloak issuer URI

2. **403 Forbidden**
   - Check role claims in token
   - Verify @PreAuthorize annotations
   - Check tenant access

3. **Token Refresh Failures**
   - Check NEXTAUTH_SECRET consistency
   - Verify Keycloak session timeout
   - Check refresh token rotation

4. **S2S Auth Failures**
   - Verify client credentials
   - Check network access to Keycloak
   - Review OAuth2ClientService logs

---

## Contacts

For questions about this implementation:
- Review commit history for each phase
- Check inline documentation in source files
- Refer to `KEYCLOAK_OAUTH2_IMPLEMENTATION_REPORT.md` for details

---

*Handoff document generated by Claude Code*
