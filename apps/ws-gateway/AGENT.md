# Agent Instructions - WS Gateway

> **Inherits from:** [/AGENT.md](/AGENT.md)
> **This file contains service-specific overrides and additions.**

---

## Service Overview

WS Gateway is the API Gateway for all WizardSofts microservices. It handles:
- Request routing to downstream services
- OAuth2/OIDC authentication via Keycloak
- Rate limiting and throttling
- Request/response logging
- Circuit breaker patterns

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Java 21 |
| Framework | Spring Boot 3.x, Spring Cloud Gateway |
| Auth | Spring Security OAuth2, Keycloak |
| Build | Maven |
| Testing | JUnit 5, Mockito, TestContainers |

---

## Service-Specific Rules

### Testing (Override from AGENT.md)

- **Minimum coverage:** 85% (higher than global 80%)
- **Required:** Controller integration tests for ALL endpoints
- **Required:** Security tests for all protected routes

```java
// Example: Always test both authenticated and unauthenticated scenarios
@Test
void shouldReturn401WhenNotAuthenticated() { ... }

@Test
@WithMockUser(roles = "USER")
void shouldReturn200WhenAuthenticated() { ... }
```

### Code Style (Override)

- **Constructor Injection ONLY** - No `@Autowired` on fields
- **DTOs as Records** - All DTOs must be Java records
- **Immutable by Default** - Use `final` on all possible fields

```java
// ✓ Correct
@Service
public class MyService {
    private final MyRepository repository;

    public MyService(MyRepository repository) {
        this.repository = repository;
    }
}

// ✗ Wrong
@Service
public class MyService {
    @Autowired
    private MyRepository repository;
}
```

### Security Rules (Addition)

- All endpoints require authentication except `/actuator/health`
- Rate limiting: 100 req/min for authenticated, 20 req/min for anonymous
- All request/response bodies must be logged (sanitized)
- No sensitive data in error responses

---

## Local Development

### Prerequisites

```bash
# Required services
docker-compose up -d keycloak postgres redis
```

### Run Service

```bash
# From apps/ws-gateway/
./mvnw spring-boot:run -Dspring-boot.run.profiles=local
```

### Run Tests

```bash
# Unit tests only
./mvnw test

# Integration tests (requires Docker)
./mvnw verify -Pintegration-tests

# With coverage report
./mvnw verify jacoco:report
# View: target/site/jacoco/index.html
```

### Debug Mode

```bash
./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=n,address=*:5005"
```

---

## Common Tasks

### Add New Endpoint

1. Create request/response DTOs in `dto/`
   ```java
   public record CreateOrderRequest(
       @NotNull String symbol,
       @Positive int quantity
   ) {}
   ```

2. Add controller method
   ```java
   @PostMapping("/orders")
   public ResponseEntity<OrderResponse> createOrder(
       @Valid @RequestBody CreateOrderRequest request,
       @AuthenticationPrincipal Jwt jwt
   ) { ... }
   ```

3. Add service method with business logic

4. Write tests
   - Unit test for service logic
   - Integration test for controller
   - Security test for auth requirements

5. Update OpenAPI spec in `src/main/resources/openapi/`

### Add New Route to Downstream Service

1. Update `application.yml`:
   ```yaml
   spring:
     cloud:
       gateway:
         routes:
           - id: new-service
             uri: lb://new-service
             predicates:
               - Path=/api/new/**
             filters:
               - StripPrefix=1
   ```

2. Add circuit breaker config if needed

3. Add rate limiting config if needed

4. Test with integration test

### Database Migration

```bash
# Create new migration
# File: src/main/resources/db/migration/V{version}__{description}.sql

# Test locally
./mvnw flyway:migrate -Dflyway.url=jdbc:postgresql://localhost:5432/gateway

# Migrations auto-run on deploy
```

---

## Health Check Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/actuator/health` | Kubernetes liveness probe |
| `/actuator/health/readiness` | Kubernetes readiness probe |
| `/actuator/info` | Service info (version, git commit) |
| `/actuator/prometheus` | Metrics for Prometheus |

---

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `KEYCLOAK_URL` | Keycloak server URL | `http://10.0.0.84:8180` |
| `EUREKA_URL` | Service registry URL | `http://10.0.0.84:8761/eureka` |
| `REDIS_HOST` | Redis for rate limiting | `10.0.0.84` |
| `DB_URL` | PostgreSQL connection | `jdbc:postgresql://...` |

### Profiles

| Profile | Use Case |
|---------|----------|
| `local` | Local development |
| `docker` | Running in Docker |
| `prod` | Production settings |

---

## Troubleshooting

### Service not registering with Eureka

```bash
# Check Eureka is running
curl http://10.0.0.84:8761/eureka/apps

# Check service logs
./mvnw spring-boot:run | grep -i eureka
```

### OAuth2 token validation failing

```bash
# Verify Keycloak is accessible
curl http://10.0.0.84:8180/realms/wizardsofts/.well-known/openid-configuration

# Check JWKS endpoint
curl http://10.0.0.84:8180/realms/wizardsofts/protocol/openid-connect/certs
```

### Rate limiting not working

```bash
# Verify Redis connection
redis-cli -h 10.0.0.84 ping

# Check rate limit keys
redis-cli -h 10.0.0.84 keys "rate-limit:*"
```

---

*Inherits all other rules from [/AGENT.md](/AGENT.md)*
