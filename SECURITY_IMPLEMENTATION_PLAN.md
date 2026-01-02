# WizardSofts Megabuild - Comprehensive Security Implementation Plan

**Document Version:** 1.0
**Created:** December 31, 2025
**Status:** PENDING USER VALIDATION

---

## Executive Summary

Following a cryptocurrency mining malware incident and comprehensive security audit, this document outlines a complete security hardening plan for the WizardSofts Megabuild infrastructure. The attack exploited **CVE-2025-66478** (Next.js RCE vulnerability) and spread to all 68 containers via Docker socket access.

### Attack Timeline
1. Attacker exploited Next.js 15.5.4 RCE vulnerability
2. Malware (`/tmp/cc.txt`) deployed to compromised containers
3. Spread to ALL containers via Docker socket
4. Attempted to disable security controls, clear logs, modify SSH keys

### Key Statistics
- **68 containers** were running, **ALL infected**
- **2 critical** application vulnerabilities found (hardcoded credentials, missing auth)
- **3 high-severity** issues found (SQL injection risk, insecure deserialization, input validation)
- **6 medium-severity** infrastructure issues found

---

## Part 1: Current System Inventory

### 1.1 Infrastructure Components

| Component | Version | Purpose | Risk Level |
|-----------|---------|---------|------------|
| Traefik | v2.10 | Reverse Proxy | HIGH (Docker socket access) |
| PostgreSQL | 15-alpine, 16 | Databases | MEDIUM |
| Redis | 7-alpine | Cache/Session | MEDIUM |
| Appwrite | 1.8.1 | BaaS Platform | HIGH (executor has RW socket) |
| GitLab CE | 18.4.1 | CI/CD | MEDIUM |
| Keycloak | 24.0.0 | Identity Management | LOW |
| Prometheus | latest | Monitoring | LOW |
| Grafana | latest | Dashboards | MEDIUM (exposed port) |
| MariaDB | 10.11 | Appwrite Database | MEDIUM |
| Mailcow | Various | Email Server | MEDIUM |

### 1.2 Web Applications

| Application | Technology | Port | Status |
|-------------|------------|------|--------|
| wizardsofts.com | Next.js 16.1.1 | 3000 | PATCHED |
| dailydeenguide.com | Next.js 16.1.1 | 3000 | PATCHED |
| gibd-quant-web | Next.js | 3000 | NEEDS UPDATE |
| pf-padmafoods-web | Next.js | 3000 | NEEDS UPDATE |
| ws-gateway | Spring Boot | 8080 | NO AUTH |
| ws-company | Spring Boot | 8183 | NO AUTH |
| ws-trades | Spring Boot | 8182 | NO AUTH |
| ws-news | Spring Boot | 8184 | NO AUTH |
| gibd-quant-nlq | FastAPI | 5002 | CORS * |

### 1.3 Exposed Ports (Production Server 10.0.0.84)

**Public Ports:**
- 80 (HTTP) - Traefik
- 443 (HTTPS) - Traefik
- 2222 (SSH) - GitLab
- 25, 465, 587 (SMTP) - Mailcow
- 110, 143, 993, 995 (IMAP/POP) - Mailcow

**Internal but Accessible:**
- 3002 (Grafana) - Should be behind Traefik
- 8080 (Traefik Dashboard) - Has basic auth
- 8090 (GitLab HTTP) - Should be HTTPS only
- 9090 (Prometheus) - Should be localhost only
- 9093 (Alertmanager) - Should be localhost only
- 9100 (Node Exporter) - Should be localhost only

---

## Part 2: Identified Vulnerabilities

### 2.1 CRITICAL SEVERITY

#### C1: Appwrite Executor Docker Socket (READ-WRITE)
- **Location:** `docker-compose.appwrite.yml`
- **Risk:** Full Docker daemon control = Host compromise
- **Current:** `/var/run/docker.sock:/var/run/docker.sock` (RW)
- **Required Action:** Change to `:ro` or use socket proxy

#### C2: Hardcoded Database Credentials
- **Location:** `apps/ws-company/src/main/resources/application-hp.properties`
- **Content:** `spring.datasource.password=29Dec2#24`
- **Risk:** Anyone with repo access can access production DB
- **Required Action:** Remove from code, use environment variables

#### C3: Missing Authentication on APIs
- **Locations:** All Spring Boot controllers, Python FastAPI services
- **Risk:** Public write access to financial data
- **Required Action:** Implement Spring Security + API keys

### 2.2 HIGH SEVERITY

#### H1: Insecure Pickle Deserialization
- **Location:** `apps/gibd-vector-context/vector_store/faiss_store.py`
- **Risk:** RCE via crafted pickle file
- **Required Action:** Replace with JSON or MessagePack

#### H2: Missing Input Validation
- **Locations:** All controllers and API endpoints
- **Risk:** SQL injection, XSS, DoS
- **Required Action:** Add validation annotations/schemas

#### H3: Wildcard CORS Configuration
- **Location:** `apps/gibd-quant-nlq/src/api/main.py`
- **Content:** `allow_origins=["*"]` with `allow_credentials=True`
- **Risk:** CSRF attacks
- **Required Action:** Specify exact allowed origins

### 2.3 MEDIUM SEVERITY

#### M1: Traefik Docker Socket Access
- **Risk:** Container escape potential
- **Required Action:** Implement Docker socket proxy

#### M2: Exposed Monitoring Ports
- **Ports:** 3002, 9090, 9093, 9100
- **Risk:** Information disclosure
- **Required Action:** Move behind Traefik or bind to localhost

#### M3: No Rate Limiting on APIs
- **Risk:** DoS attacks, expensive LLM API charges
- **Required Action:** Implement rate limiting middleware

#### M4: Missing Security Headers
- **Risk:** Clickjacking, XSS
- **Required Action:** Add CSP, X-Frame-Options, etc.

#### M5: Grafana Keycloak Secret Hardcoded
- **Location:** Docker Compose files
- **Required Action:** Move to CI/CD variables

#### M6: No Automated Dependency Updates
- **Risk:** Known vulnerabilities in dependencies
- **Required Action:** Set up Dependabot/Renovate

---

## Part 3: System Requirements for Implementation

### 3.1 Infrastructure Requirements

| Requirement | Description | Validation Method |
|-------------|-------------|-------------------|
| Docker Socket Proxy | Tecnativa/docker-socket-proxy container | `docker ps | grep socket-proxy` |
| Secret Management | HashiCorp Vault or GitLab CI/CD variables | Verify no secrets in code |
| Network Segmentation | Internal-only networks for backend | `docker network inspect` |
| TLS Everywhere | All internal communication encrypted | Certificate verification |
| Backup System | Automated daily backups | Backup verification test |

### 3.2 Application Requirements

| Requirement | Description | Validation Method |
|-------------|-------------|-------------------|
| Authentication | All write endpoints require auth | API test without token |
| Input Validation | All inputs validated | Fuzz testing |
| Rate Limiting | Max 100 req/min per IP | Load testing |
| CORS Whitelist | Only allowed origins | Cross-origin test |
| Security Headers | CSP, X-Frame-Options, etc. | Security header scan |

### 3.3 CI/CD Requirements

| Requirement | Description | Validation Method |
|-------------|-------------|-------------------|
| Secret Detection | Pre-commit and pipeline scanning | Trufflehog/GitLeaks |
| Dependency Scanning | npm audit, pip-audit, OWASP DC | Pipeline artifacts |
| Container Scanning | Trivy image scanning | Pipeline artifacts |
| SAST | Semgrep static analysis | Pipeline artifacts |
| Automated Updates | Dependabot/Renovate PRs | Weekly PR check |

### 3.4 Monitoring Requirements

| Requirement | Description | Validation Method |
|-------------|-------------|-------------------|
| Security Logging | Auth failures, API errors | Loki/Grafana alerts |
| Container Monitoring | Resource usage, health | Prometheus metrics |
| Intrusion Detection | Unusual patterns | Alertmanager rules |
| Audit Logging | All admin actions | Log review |

---

## Part 4: Implementation Plan

### Phase 1: Emergency Fixes (Immediate - Week 1)

#### P1.1 Docker Socket Hardening
**Status:** [ ] Not Started

```yaml
# Add to docker-compose.infrastructure.yml
services:
  socket-proxy:
    image: tecnativa/docker-socket-proxy:latest
    container_name: socket-proxy
    restart: unless-stopped
    environment:
      CONTAINERS: 1
      SERVICES: 0
      TASKS: 0
      NETWORKS: 0
      NODES: 0
      SWARM: 0
      SECRETS: 0
      CONFIGS: 0
      PLUGINS: 0
      SYSTEM: 0
      VOLUMES: 0
      INFO: 0
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - socket-proxy

networks:
  socket-proxy:
    internal: true
```

**Traefik Update:**
```yaml
traefik:
  environment:
    - DOCKER_HOST=tcp://socket-proxy:2375
  # Remove: - /var/run/docker.sock:/var/run/docker.sock:ro
  networks:
    - socket-proxy
    - traefik-public
```

#### P1.2 Remove Hardcoded Credentials
**Status:** [ ] Not Started

Files to update:
- [ ] `apps/ws-company/src/main/resources/application-hp.properties`
- [ ] `apps/ws-trades/src/main/resources/application-hp.properties`
- [ ] Any other `application-*.properties` files

Replace with:
```properties
spring.datasource.password=${DB_PASSWORD}
```

#### P1.3 Update All Next.js Applications
**Status:** [ ] Not Started

Applications to update:
- [ ] gibd-quant-web → Next.js 16.1.1
- [ ] pf-padmafoods-web → Next.js 16.1.1
- [ ] Verify ws-wizardsofts-web (already updated)
- [ ] Verify ws-daily-deen-web (already updated)

Command:
```bash
npm install next@latest --legacy-peer-deps
```

#### P1.4 Secret Rotation
**Status:** [ ] Not Started

Secrets to rotate:
- [ ] Database passwords
- [ ] Redis passwords
- [ ] OpenAI API keys
- [ ] Keycloak secrets
- [ ] Appwrite encryption keys
- [ ] GitLab tokens

### Phase 2: Authentication & Authorization (Week 2)

#### P2.1 Spring Security Implementation
**Status:** [ ] Not Started

Add to each Spring Boot service:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

Security configuration:
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .httpBasic(Customizer.withDefaults());
        return http.build();
    }
}
```

#### P2.2 FastAPI Authentication
**Status:** [ ] Not Started

Add API key authentication:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/api/v1/nlq/query")
async def execute_query(
    request: QueryRequest,
    api_key: str = Security(verify_api_key)
):
    ...
```

#### P2.3 Fix CORS Configuration
**Status:** [ ] Not Started

Update:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.guardianinvestmentbd.com",
        "https://guardianinvestmentbd.com",
        "https://www.wizardsofts.com",
        "https://wizardsofts.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

### Phase 3: Input Validation & Hardening (Week 3)

#### P3.1 Java Input Validation
**Status:** [ ] Not Started

Add validation annotations:
```java
@Data
public class PriceByTradingCodeRequest {
    @NotBlank(message = "Scrip is required")
    @Size(max = 20, message = "Scrip must be <= 20 characters")
    @Pattern(regexp = "^[A-Z0-9]+$", message = "Invalid scrip format")
    private String scrip;

    @NotNull(message = "Start date is required")
    private LocalDate startDate;

    @NotNull(message = "End date is required")
    private LocalDate endDate;
}
```

#### P3.2 Python Input Validation
**Status:** [ ] Not Started

Add Pydantic validators:
```python
from pydantic import BaseModel, Field, validator

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    tickers: list[str] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=1000)

    @validator('tickers')
    def validate_tickers(cls, v):
        for ticker in v:
            if not re.match(r'^[A-Z0-9]{1,10}$', ticker):
                raise ValueError(f'Invalid ticker: {ticker}')
        return v
```

#### P3.3 Rate Limiting
**Status:** [ ] Not Started

Spring Boot:
```java
@Configuration
public class RateLimitConfig {
    @Bean
    public Bucket bucket() {
        Bandwidth limit = Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1)));
        return Bucket.builder().addLimit(limit).build();
    }
}
```

FastAPI:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/nlq/query")
@limiter.limit("60/minute")
async def execute_query(request: Request, query: QueryRequest):
    ...
```

#### P3.4 Replace Pickle with JSON
**Status:** [ ] Not Started

Update `faiss_store.py`:
```python
import json

def _load_index_and_meta(self):
    if os.path.exists(self.meta_file):
        with open(self.meta_file, 'r') as f:
            metadata = json.load(f)  # Safe deserialization
```

### Phase 4: Infrastructure Hardening (Week 4)

#### P4.1 Network Segmentation
**Status:** [ ] Not Started

Create internal networks:
```yaml
networks:
  backend:
    internal: true
  monitoring:
    internal: true
  public:
    internal: false
```

Assign services:
- Public: traefik
- Backend: databases, redis, microservices
- Monitoring: prometheus, grafana, loki

#### P4.2 Container Hardening
**Status:** [ ] Not Started

Add to all services:
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
read_only: true
tmpfs:
  - /tmp
  - /var/run
```

#### P4.3 Security Headers in Traefik
**Status:** [ ] Not Started

Add middleware:
```yaml
http:
  middlewares:
    security-headers:
      headers:
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        contentSecurityPolicy: "default-src 'self'"
        referrerPolicy: "strict-origin-when-cross-origin"
```

#### P4.4 Move Monitoring Behind Traefik
**Status:** [ ] Not Started

- [ ] Update Grafana to use Traefik routing
- [ ] Bind Prometheus to 127.0.0.1
- [ ] Bind Alertmanager to 127.0.0.1
- [ ] Bind Node Exporter to 127.0.0.1

### Phase 5: CI/CD Security Pipeline (Week 5)

#### P5.1 Enhanced Security Scanning
**Status:** [ ] Not Started

Update `.gitlab/ci/security.gitlab-ci.yml`:
```yaml
stages:
  - security

secret-detection:
  stage: security
  image: trufflesecurity/trufflehog:latest
  script:
    - trufflehog git --since-commit HEAD~1 .
  allow_failure: false  # Block on secrets

dependency-scan:
  stage: security
  image: owasp/dependency-check:latest
  script:
    - dependency-check.sh --project "WizardSofts" --scan . --format JSON
  artifacts:
    paths:
      - dependency-check-report.json
  allow_failure: false  # Block on critical vulns

container-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $CI_REGISTRY_IMAGE
  allow_failure: false

sast:
  stage: security
  image: returntocorp/semgrep
  script:
    - semgrep --config auto --error
  allow_failure: true  # Warning only for now
```

#### P5.2 Automated Dependency Updates
**Status:** [ ] Not Started

Create `.github/dependabot.yml` (or GitLab equivalent):
```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/apps/gibd-quant-web"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "maven"
    directory: "/apps/ws-gateway"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/apps/gibd-quant-nlq"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### Phase 6: Monitoring & Alerting (Week 6)

#### P6.1 Security Alerting Rules
**Status:** [ ] Not Started

Add Prometheus rules:
```yaml
groups:
  - name: security
    rules:
      - alert: HighAuthFailures
        expr: rate(auth_failures_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"

      - alert: ContainerPrivilegeEscalation
        expr: container_security_context_privileged == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Privileged container detected"

      - alert: UnusualOutboundTraffic
        expr: rate(container_network_transmit_bytes_total[5m]) > 10000000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Unusual outbound network traffic"
```

#### P6.2 Grafana Security Dashboard
**Status:** [ ] Not Started

Create dashboard with:
- Authentication failures over time
- API error rates
- Container resource usage
- Network traffic patterns
- Vulnerability scan results

---

## Part 5: Validation Checklist

### Pre-Implementation Validation (USER APPROVAL REQUIRED)

- [ ] **C1**: Agree to implement Docker socket proxy for Traefik and Appwrite?
- [ ] **C2**: Confirm database password rotation is acceptable (will require app restarts)?
- [ ] **C3**: Approve adding authentication to ALL API endpoints?
- [ ] **H1**: Approve replacing pickle with JSON (may break existing vector store)?
- [ ] **H2**: Approve adding strict input validation (may reject previously valid requests)?
- [ ] **H3**: Confirm the list of allowed CORS origins?
- [ ] **M1-M6**: Approve all medium-severity fixes?

### Downtime Requirements

| Phase | Expected Downtime | Rollback Plan |
|-------|-------------------|---------------|
| Phase 1 | 30-60 minutes | Git revert + docker-compose down/up |
| Phase 2 | 15-30 minutes per service | Remove Security dependency |
| Phase 3 | 0 (rolling updates) | N/A |
| Phase 4 | 30 minutes | Revert docker-compose files |
| Phase 5 | 0 (CI/CD only) | Revert .gitlab-ci.yml |
| Phase 6 | 0 (monitoring only) | N/A |

---

## Part 6: Ongoing Maintenance

### Weekly Tasks
- [ ] Review Dependabot/Renovate PRs
- [ ] Check security scan results in CI/CD
- [ ] Review authentication failure logs

### Monthly Tasks
- [ ] Rotate API keys
- [ ] Review and update firewall rules
- [ ] Test backup restoration

### Quarterly Tasks
- [ ] Penetration testing
- [ ] Security audit
- [ ] Update this document
- [ ] Disaster recovery drill

---

## Part 7: Resources

### Official Documentation
- [Docker Security](https://docs.docker.com/engine/security/)
- [OWASP Docker Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [Next.js Security Advisory](https://nextjs.org/blog/CVE-2025-66478)
- [Appwrite Production Security](https://appwrite.io/docs/advanced/self-hosting/production/security)
- [GitLab Dependency Scanning](https://docs.gitlab.com/user/application_security/dependency_scanning/)
- [Traefik Docker Socket Proxy](https://github.com/wollomatic/traefik-hardened)

### Tools
- [Trivy](https://github.com/aquasecurity/trivy) - Container scanning
- [Semgrep](https://semgrep.dev/) - SAST
- [TruffleHog](https://github.com/trufflesecurity/trufflehog) - Secret detection
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/) - Dependency scanning
- [Docker Socket Proxy](https://github.com/Tecnativa/docker-socket-proxy)

---

## Approval Section

**Prepared By:** Claude Code Security Audit
**Date:** December 31, 2025

**Approved By:** ___________________
**Date:** ___________________

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

*This document will be updated as implementation progresses.*
