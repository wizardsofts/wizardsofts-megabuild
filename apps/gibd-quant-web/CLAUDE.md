# gibd-quant-web Development Guidelines

**Last Updated**: December 30, 2025
**Project**: Guardian Investment Bangladesh - Quant Analysis Platform
**Domain**: https://www.guardianinvestmentbd.com

---

## 🚀 Deployment & Security Rules

**CRITICAL**: This project follows strict deployment and security standards.

### Deployment - CI/CD ONLY

❌ **NEVER**:
- Use SSH to deploy services
- Run docker-compose commands on production
- Bypass CI/CD pipeline for "quick fixes"
- Deploy without running tests

✅ **ALWAYS**:
- Use GitLab CI/CD pipeline for all deployments
- Push code changes to GitLab repository
- Trigger deployments from GitLab UI
- Verify health checks pass
- **Verify HTTPS/SSL certificates after every deployment** (see below)

### Post-Deployment HTTPS Verification

**CRITICAL**: After every deployment, MUST verify HTTPS is working correctly:

```bash
# 1. Check domain certificate
openssl s_client -connect www.guardianinvestmentbd.com:443 -servername www.guardianinvestmentbd.com 2>/dev/null | openssl x509 -noout -dates

# 2. Verify secure connection (should show HTTP/2 200)
curl -I https://www.guardianinvestmentbd.com 2>&1 | head -5

# 3. Test all major routes
curl -sI https://www.guardianinvestmentbd.com/ | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/charts | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/signals | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/multi-criteria | grep HTTP

# 4. Check certificate issuer (should be Let's Encrypt)
openssl s_client -connect www.guardianinvestmentbd.com:443 -servername www.guardianinvestmentbd.com 2>/dev/null | openssl x509 -noout -issuer
```

**If "not secure" warning appears**:
1. Check Traefik Let's Encrypt configuration in `infrastructure/traefik/`
2. Verify DNS: `nslookup www.guardianinvestmentbd.com` should resolve to correct IP
3. Check Traefik logs: `docker logs traefik 2>&1 | grep -i "acme\|certificate\|guardianinvestmentbd"`
4. Verify ports 80/443 accessible for ACME challenge
5. Check Traefik dashboard: http://<server-ip>:8080
6. Force certificate renewal: Delete `infrastructure/traefik/acme.json` and restart Traefik

**See [AGENT_GUIDELINES.md](../../AGENT_GUIDELINES.md#httpsssl-verification-steps) for detailed troubleshooting**

### Port Binding - Via Traefik ONLY

This web application runs on internal port 3000 but MUST NOT be directly accessible:

```yaml
# docker-compose.yml
services:
  frontend:
    ports:
      - "3000:3000"  # Internal port mapping
    networks:
      - microservices-overlay  # ✅ Traefik network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gibd-quant-web.rule=Host(`www.guardianinvestmentbd.com`)"
      - "traefik.http.routers.gibd-quant-web.entrypoints=websecure"
      - "traefik.http.routers.gibd-quant-web.tls.certresolver=letsencrypt"
```

### Reference Documents

**MUST READ**:
- [CONSTITUTION.md](../../CONSTITUTION.md) - Project standards
- [AGENT_GUIDELINES.md](../../AGENT_GUIDELINES.md) - AI agent rules

---

## 🛠️ Technology Stack

- Next.js
- React
- TypeScript
- Tailwind CSS
- Chart.js / D3.js (Data visualization)
- Docker (Production)

## 📁 Project Structure

```
app/
  page.tsx              # Homepage/Dashboard
  charts/               # Stock charts
  signals/              # Trading signals
  multi-criteria/       # Multi-criteria analysis
  chat/                 # AI chat interface
  company/              # Company profiles
components/             # React components
public/                 # Static assets
```

## 🧪 Development Commands

```bash
# Navigate to project
cd apps/gibd-quant-web

# Install dependencies
npm install

# Run locally
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

## 📋 Testing Requirements

- Unit tests: Required for critical components
- Integration tests: Required for API integrations
- Tests MUST pass before deployment

**E2E Testing Mandate (CRITICAL)**:
- ✅ **All agents MUST run and pass relevant end-to-end/integration tests** before proceeding to next phase
- ✅ **For features involving backend integration**: Test complete workflow from UI → API → response
- ⚠️ **If tests fail or cannot run**: Development MUST pause, report to user
- 📝 **Document**: Test results, skipped tests (with reasons), any infrastructure issues
- 🚩 **Raise flags**: Business requirement conflicts, API integration issues, deployment blockers

**Example E2E Test Flow**:
```bash
# Run integration tests
npm test

# Test with actual backend services (if available)
npm run test:e2e

# Verify:
# - Component rendering
# - API calls succeed
# - Data displays correctly
# - Error handling works
```

## 🌐 Backend Services Integration

This frontend connects to:
- gibd-quant-signal (Port 5001) - Signal generation
- gibd-quant-nlq (Port 5002) - Natural language queries
- gibd-quant-calibration (Port 5003) - Model calibration
- gibd-quant-agent (Port 5004) - AI agent services

## Recent Changes

- December 30, 2025: Deployed to production via CI/CD
- December 30, 2025: Added HTTPS verification guidelines
- December 30, 2025: Fixed coming-soon directory permissions

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
