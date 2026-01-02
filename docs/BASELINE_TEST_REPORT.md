# Baseline Test Report - Before Megabuild Deployment

**Date**: December 27, 2025
**Server**: 10.0.0.84

---

## Current Running Services

### Web Applications

| Service | Container | Status | Ports | Access URL |
|---------|-----------|--------|-------|------------|
| **Wizardsofts.com** | wwwwizardsoftscom-web-1 | Running (3 days) | 3000:3000 | http://10.0.0.84:3000 ✅ |
| **Daily Deen Guide** | daily-deen-guide-frontend | Running (3 days) | Internal | Via Traefik only |

### Infrastructure

| Service | Container | Status | Ports |
|---------|-----------|--------|-------|
| **Traefik** | traefik | Running (16 hours) | 80, 443, 8080 |
| **Grafana** | grafana | Running (4 hours) | 3002:3000 |
| **Prometheus** | prometheus | Running (2 hours) | 9090:9090 |
| **HAProxy** | haproxy | Running (15 hours) | 8404, 11434 |
| **Keycloak** | keycloak | Running (16 hours) | Internal 8080 |

### Email (Mailcow)

All mailcow containers running (16 hours):
- nginx-mailcow: 10080:10080, 10443:10443
- postfix-mailcow: 25, 465, 587
- dovecot-mailcow: 110, 143, 993, 995, 4190

---

## Current Traefik Configuration

### Location
`/home/wizardsofts/traefik/dynamic_conf.yml`

### Routes Configured

#### HTTP Routers

1. **Dashboard**
   - Rule: `Host(traefik.localhost) || Host(10.0.0.84)`
   - Entry Point: websecure
   - TLS: Yes
   - Middleware: dashboard-auth

2. **Mailcow ACME Challenge**
   - Rule: `PathPrefix(/.well-known/acme-challenge/)`
   - Entry Point: web
   - Priority: 1000

#### TCP Routers

1. **Mailcow UI**
   - Rule: `HostSNI(mail.wizardsofts.com) || HostSNI(mail.dailydeenguide.com)`
   - Entry Point: websecure
   - TLS Passthrough: Yes

---

## Docker Labels (Wizardsofts.com)

```yaml
traefik.enable: true

# HTTP Route
traefik.http.routers.wizardsofts.entrypoints: web
traefik.http.routers.wizardsofts.rule: Host(`www.wizardsofts.com`) || Host(`wizardsofts.com`)
traefik.http.routers.wizardsofts.service: wizardsofts

# HTTPS Route
traefik.http.routers.wizardsofts-secure.entrypoints: websecure
traefik.http.routers.wizardsofts-secure.rule: Host(`www.wizardsofts.com`) || Host(`wizardsofts.com`)
traefik.http.routers.wizardsofts-secure.service: wizardsofts
traefik.http.routers.wizardsofts-secure.tls: true
traefik.http.routers.wizardsofts-secure.tls.certresolver: myresolver

# IP-based Route
traefik.http.routers.wizardsofts-local.entrypoints: web
traefik.http.routers.wizardsofts-local.rule: Host(`10.0.0.84`)
traefik.http.routers.wizardsofts-local.service: wizardsofts

# Service
traefik.http.services.wizardsofts.loadbalancer.server.port: 3000
```

---

## Playwright Test Results

### Test 1: Direct Port Access

**URL**: http://10.0.0.84:3000
**Status**: ✅ SUCCESS
**Page Title**: WizardSofts - Innovative Software Solutions
**Response Time**: < 1s

**Screenshot**: Page loaded successfully with:
- Navigation menu (Home, About, Services, Contact)
- Hero section: "ERP, POS & FinTech Solutions"
- Company stats (Founded 2016, 20+ Projects, 6 Services, 9 Years)
- Service cards (Custom ERP, POS Systems, FinTech Platforms)

### Test 2: Traefik Dashboard

**URL**: http://10.0.0.84:8080
**Status**: ❌ FAILED
**Error**: ERR_CONNECTION_REFUSED

**Reason**: Dashboard requires HTTPS (websecure entry point) and basic auth

### Test 3: Traefik HTTP → HTTPS Redirect

**URL**: http://10.0.0.84
**Status**: ⚠️ PARTIAL
**Behavior**: Redirects to HTTPS
**Error**: ERR_CERT_AUTHORITY_INVALID (expected without valid SSL cert)

---

## Current Access Patterns

### How Services Are Currently Accessed

1. **www.wizardsofts.com**
   - Via Traefik: http://10.0.0.84 (redirects to HTTPS, but cert invalid)
   - Direct: http://10.0.0.84:3000 ✅ WORKS

2. **Daily Deen Guide**
   - Via Traefik: (needs investigation - no public port)
   - Direct: No port exposed

3. **Grafana**
   - Direct: http://10.0.0.84:3002 (port 3002 mapped to container port 3000)

4. **Traefik Dashboard**
   - Via HTTPS: https://10.0.0.84 (would require valid cert + auth)
   - Via HTTP: Not accessible (websecure only)

---

## Expected Changes After Megabuild Deployment

### New Configuration

1. **File-based Traefik config**
   - traefik/traefik.yml (static)
   - traefik/dynamic_conf.yml (dynamic)

2. **New Routes**
   - www.wizardsofts.com (HTTPS)
   - dailydeenguide.com (HTTPS) - Fixed domain
   - www.guardianinvestmentbd.com (HTTPS) - Fixed domain

3. **IP-based Routes**
   - http://10.0.0.84/wizardsofts
   - http://10.0.0.84/dailydeen
   - http://10.0.0.84/quant

4. **Removed Port Exposures**
   - Web apps: No direct port access (ports: [])
   - All traffic via Traefik

---

## Breaking Change Risk Assessment

### HIGH RISK ⚠️

1. **Port 3000 removal**
   - Current: http://10.0.0.84:3000 works
   - After: Will NOT work (port removed)
   - Mitigation: http://10.0.0.84/wizardsofts

2. **Service names change**
   - Current: `wwwwizardsoftscom-web-1`
   - After: `ws-wizardsofts-web`
   - Impact: Docker labels need updating

### MEDIUM RISK ⚠️

1. **Daily Deen domain change**
   - Current: dailydeenguide.wizardsofts.com
   - After: dailydeenguide.com
   - Impact: DNS needs updating

2. **Grafana port conflict**
   - Current: Port 3002 (Grafana)
   - Megabuild: Port 3002 (Daily Deen Guide)
   - Resolution needed: Move Grafana or Daily Deen to different port

### LOW RISK ✅

1. **Traefik dashboard**
   - Current: Port 8080
   - After: Port 8080 (same)
   - No change

---

## Recommended Deployment Strategy

### Phase 1: Prepare (No Downtime)

1. Create /opt/wizardsofts-megabuild directory
2. Copy all files to server
3. Create .env file with all credentials
4. Validate docker-compose files

### Phase 2: Deploy (Controlled Downtime)

1. Stop existing wizardsofts.com container
2. Start megabuild services
3. Test IP-based access
4. Configure DNS
5. Test domain-based access

### Phase 3: Validate

1. Test all URLs with Playwright
2. Compare with baseline
3. Monitor logs for errors
4. Rollback plan ready

---

## Rollback Plan

### If Deployment Fails

```bash
# Stop megabuild
cd /opt/wizardsofts-megabuild
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Restart existing services
cd /home/wizardsofts
docker compose up -d wwwwizardsoftscom-web-1
```

---

## Next Steps

1. ✅ Baseline documented
2. ⏸️ Create deployment package
3. ⏸️ Test locally first
4. ⏸️ Deploy to server
5. ⏸️ Run Playwright validation tests
6. ⏸️ Compare results with baseline
7. ⏸️ Update DNS records
