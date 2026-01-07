# WS Gateway Service

Multi-tenant API Gateway with OAuth2/Keycloak authentication, API key support, and rate limiting.

## Features

- **OAuth2 Authentication** - JWT validation via Keycloak
- **API Key Authentication** - Alternative auth for service-to-service
- **Multi-tenancy** - Tenant isolation with slug-based routing
- **Rate Limiting** - Tier-based request limits
- **Tenant Onboarding** - Self-service registration with Keycloak provisioning
- **Security Audit** - Comprehensive event logging

## Quick Start

```bash
# Required environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=gibd_gateway
export DB_USER=gibd
export DB_PASSWORD=your_password
export KEYCLOAK_ISSUER_URI=http://localhost:8180/realms/wizardsofts

# Run with profiles
./mvnw spring-boot:run -Dspring-boot.run.profiles=development,oauth2,database
```

## Configuration Profiles

| Profile | Purpose |
|---------|---------|
| `oauth2` | Keycloak JWT validation |
| `database` | PostgreSQL + Flyway |
| `development` | Debug logging, relaxed limits |
| `production` | Hardened security, restricted actuator |

## API Endpoints

### Tenant Onboarding
```
POST   /api/v1/tenants              # Register new tenant
GET    /api/v1/tenants/{id}         # Get tenant (admin)
PUT    /api/v1/tenants/{id}/suspend # Suspend tenant (admin)
PUT    /api/v1/tenants/{id}/reactivate # Reactivate (admin)
DELETE /api/v1/tenants/{id}         # Delete tenant (admin)
```

### API Keys
```
POST   /api/v1/tenants/{tenantId}/api-keys           # Create key
GET    /api/v1/tenants/{tenantId}/api-keys           # List keys
DELETE /api/v1/tenants/{tenantId}/api-keys/{keyId}   # Revoke key
POST   /api/v1/tenants/{tenantId}/api-keys/{keyId}/rotate # Rotate key
```

## Authentication

### JWT (OAuth2)
```
Authorization: Bearer <jwt_token>
```

### API Key
```
X-API-Key: ws_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Rate Limits

| Tier | Requests/min |
|------|-------------|
| FREE | 100 |
| STARTER | 1,000 |
| PROFESSIONAL | 10,000 |
| ENTERPRISE | 100,000 |

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Database Migrations

- `V1` - Tenants table
- `V2` - Audit events table
- `V3` - API keys + scopes tables

## Project Structure

```
src/main/java/.../gateway_service/
├── config/          # Security, OpenAPI, Async configs
├── controller/      # REST endpoints
├── dto/             # Request/Response objects
├── exception/       # Global error handling
├── filter/          # Gateway filters (auth, rate limit)
├── listener/        # Security event listeners
├── model/           # JPA entities
├── repository/      # Data access
├── security/        # Access checkers
├── service/         # Business logic
└── audit/           # Audit logging
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | localhost |
| `DB_PORT` | PostgreSQL port | 5432 |
| `DB_NAME` | Database name | gibd_gateway |
| `DB_USER` | Database user | gibd |
| `DB_PASSWORD` | Database password | - |
| `KEYCLOAK_ISSUER_URI` | Keycloak realm URL | - |
| `KEYCLOAK_ADMIN_BASE_URL` | Keycloak admin URL | - |
| `KEYCLOAK_ADMIN_CLIENT_ID` | Admin client ID | - |
| `KEYCLOAK_ADMIN_CLIENT_SECRET` | Admin client secret | - |

## Building

```bash
./mvnw clean package -DskipTests
```

## Testing

```bash
./mvnw test
```
