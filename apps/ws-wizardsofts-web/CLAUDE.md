# ws-wizardsofts-web Development Guidelines

**Last Updated**: December 30, 2025
**Project**: Wizardsofts Corporate Website
**Domain**: https://www.wizardsofts.com

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
# 1. Check main domain certificate
openssl s_client -connect www.wizardsofts.com:443 -servername www.wizardsofts.com 2>/dev/null | openssl x509 -noout -dates

# 2. Verify secure connection (should show HTTP/2 200)
curl -I https://www.wizardsofts.com 2>&1 | head -5

# 3. Test all major routes
curl -sI https://www.wizardsofts.com/ | grep HTTP
curl -sI https://www.wizardsofts.com/bondwala | grep HTTP
curl -sI https://www.wizardsofts.com/about | grep HTTP
curl -sI https://www.wizardsofts.com/services | grep HTTP
curl -sI https://www.wizardsofts.com/contact | grep HTTP

# 4. Check certificate issuer (should be Let's Encrypt)
openssl s_client -connect www.wizardsofts.com:443 -servername www.wizardsofts.com 2>/dev/null | openssl x509 -noout -issuer
```

**If "not secure" warning appears**:
1. Check Traefik Let's Encrypt configuration in `infrastructure/traefik/`
2. Verify DNS: `nslookup www.wizardsofts.com` should resolve to correct IP
3. Check Traefik logs: `docker logs traefik 2>&1 | grep -i "acme\|certificate\|www.wizardsofts.com"`
4. Verify ports 80/443 accessible: `telnet <server-ip> 443`
5. Check Traefik dashboard: http://<server-ip>:8080
6. Force certificate renewal: Delete `infrastructure/traefik/acme.json` and restart Traefik

**Common Issues**:
- **Self-signed certificate**: Let's Encrypt ACME challenge failed
- **Certificate expired**: Automatic renewal failed
- **Wrong domain**: SNI configuration mismatch in Traefik
- **Mixed content**: Some assets loading over HTTP

### Port Binding - Via Traefik ONLY

This web application runs on port 3000 but MUST NOT be directly accessible:

```yaml
# docker-compose.yml
services:
  frontend:
    ports:
      - "3000:3000"  # ✅ CORRECT - No host binding, only on Docker network
    networks:
      - microservices-overlay  # ✅ CORRECT - Traefik network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.wizardsofts-web.rule=Host(`www.wizardsofts.com`)"
      - "traefik.http.routers.wizardsofts-web.entrypoints=websecure"
      - "traefik.http.routers.wizardsofts-web.tls.certresolver=letsencrypt"
```

### Reference Documents

**MUST READ**:
- [CONSTITUTION.md](../../CONSTITUTION.md) - Project standards
- [AGENT_GUIDELINES.md](../../AGENT_GUIDELINES.md) - AI agent rules
- [Deployment Checklist](../../AGENT_GUIDELINES.md#deployment-checklist)

---

## 🛠️ Technology Stack

- Next.js 15.5.4
- React 19
- TypeScript
- Tailwind CSS
- Docker (Production)

## 📁 Project Structure

```
app/
  page.tsx              # Homepage
  about/                # About page
  bondwala/             # BondWala landing page
  contact/              # Contact page
  services/             # Services pages
components/             # React components
public/                 # Static assets
tests/
  unit/                 # Unit tests
```

## 🧪 Development Commands

```bash
# Navigate to project
cd apps/ws-wizardsofts-web

# Install dependencies
npm install --legacy-peer-deps

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
- Integration tests: Required for API routes
- Tests MUST pass before deployment
- Visual regression tests: For major UI changes

## 🌐 Deployed Routes

All routes accessible via HTTPS only:

- `/` - Homepage
- `/about` - About us
- `/services` - Services listing
- `/services/[slug]` - Individual service pages
- `/bondwala` - BondWala landing page (Coming Soon)
- `/contact` - Contact form
- `/privacy` - Privacy policy
- `/terms` - Terms of service

## Recent Changes

- December 30, 2025: BondWala landing page deployed
- December 30, 2025: Added HTTPS verification guidelines

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
