# pf-padmafoods-web Development Guidelines

**Last Updated**: December 30, 2025
**Project**: Padma Foods - Food Processing Company Website
**Domain**: https://www.mypadmafoods.com

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
openssl s_client -connect www.mypadmafoods.com:443 -servername www.mypadmafoods.com 2>/dev/null | openssl x509 -noout -dates

# 2. Verify secure connection (should show HTTP/2 200)
curl -I https://www.mypadmafoods.com 2>&1 | head -5

# 3. Test all major routes
curl -sI https://www.mypadmafoods.com/ | grep HTTP
curl -sI https://www.mypadmafoods.com/products | grep HTTP
curl -sI https://www.mypadmafoods.com/about | grep HTTP
curl -sI https://www.mypadmafoods.com/contact | grep HTTP

# 4. Check certificate issuer (should be Let's Encrypt)
openssl s_client -connect www.mypadmafoods.com:443 -servername www.mypadmafoods.com 2>/dev/null | openssl x509 -noout -issuer
```

**If "not secure" warning appears**:
1. Check Traefik Let's Encrypt configuration in `infrastructure/traefik/`
2. Verify DNS: `nslookup www.mypadmafoods.com` should resolve to correct IP
3. Check Traefik logs: `docker logs traefik 2>&1 | grep -i "acme\|certificate\|mypadmafoods"`
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
      - "traefik.http.routers.padmafoods-web.rule=Host(`www.mypadmafoods.com`)"
      - "traefik.http.routers.padmafoods-web.entrypoints=websecure"
      - "traefik.http.routers.padmafoods-web.tls.certresolver=letsencrypt"
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
- Docker (Production)

## 📁 Project Structure

```
app/
  page.tsx              # Homepage
  products/             # Products catalog
  about/                # About page
  contact/              # Contact page
components/             # React components
public/                 # Static assets
```

## 🧪 Development Commands

```bash
# Navigate to project
cd apps/pf-padmafoods-web

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
- Tests MUST pass before deployment

## Recent Changes

- December 30, 2025: Deployed to production via CI/CD
- December 30, 2025: Added HTTPS verification guidelines

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
