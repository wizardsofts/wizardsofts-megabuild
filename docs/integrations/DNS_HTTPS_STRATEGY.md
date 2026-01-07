# DNS and HTTPS Strategy for Wizardsofts Infrastructure

**Date**: December 30, 2025
**Status**: Decision Required
**Priority**: High

---

## Current Situation

### Servers
- **Production**: 106.70.161.3 (not actively used)
- **Development**: 10.0.0.84 (currently serving all applications)

### DNS Configuration
All production domains currently resolve to 106.70.161.3:
```bash
www.wizardsofts.com         → 106.70.161.3
www.mypadmafoods.com        → 106.70.161.3
www.guardianinvestmentbd.com → 106.70.161.3
```

### The Problem
**HTTPS certificates cannot be obtained** on dev server (10.0.0.84) because:
1. Let's Encrypt connects to 106.70.161.3 (based on DNS)
2. ACME validation fails (wrong server)
3. Rate limits triggered (5 failures per hour per hostname)

### Current Workaround (Implemented)
✅ Traefik configured with Let's Encrypt **staging server** on 10.0.0.84:
- No rate limits for testing
- Certificates work but browsers show "not secure" (expected for staging certs)
- Configuration: `caServer: https://acme-staging-v02.api.letsencrypt.org/directory`

---

## Options for Resolution

### **Option A: Staging Subdomains (Recommended)**

Create separate DNS records for development:

```
Production (106.70.161.3):
- www.wizardsofts.com
- www.mypadmafoods.com
- www.guardianinvestmentbd.com

Development (10.0.0.84):
- dev.wizardsofts.com
- dev.mypadmafoods.com
- dev.guardianinvestmentbd.com
```

**Implementation**:
1. Add DNS A records for dev subdomains → 10.0.0.84
2. Update Traefik labels in docker-compose files to use dev domains
3. Switch back to production ACME server
4. Obtain valid Let's Encrypt certificates

**Pros**:
✅ Clean separation of environments
✅ Valid HTTPS certificates on both servers
✅ No browser warnings
✅ Professional setup
✅ Easy to distinguish which environment you're accessing

**Cons**:
❌ Requires DNS changes
❌ Need to update docker-compose labels
❌ Users must use different URLs for dev vs prod

**Cost**: Free (just DNS record addition)
**Time**: 1-2 hours (DNS propagation + configuration)

---

### **Option B: Point Production DNS to Dev Server**

Update DNS to point production domains to 10.0.0.84:

```
All domains → 10.0.0.84:
- www.wizardsofts.com
- www.mypadmafoods.com
- www.guardianinvestmentbd.com
```

**Implementation**:
1. Update A records to point to 10.0.0.84
2. Wait for DNS propagation (TTL dependent)
3. Switch Traefik to production ACME server
4. Obtain valid certificates

**Pros**:
✅ Simple - just DNS changes
✅ Valid HTTPS certificates
✅ No code changes needed

**Cons**:
❌ **BREAKS PRODUCTION** if 106.70.161.3 is serving traffic
❌ No separate development environment
❌ Can't test without affecting users
❌ DNS propagation delay (up to 48 hours)

**Recommended**: **Only if 106.70.161.3 is not in use**
**Cost**: Free
**Time**: DNS propagation (minutes to hours)

---

### **Option C: Keep Staging Certificates (Current State)**

Continue using Let's Encrypt staging server on 10.0.0.84:

**Implementation**:
- Already done! Currently active.

**Pros**:
✅ Already implemented
✅ No DNS changes needed
✅ No rate limits
✅ Good for testing

**Cons**:
❌ Browsers show "not secure" warning
❌ Users must accept security exception
❌ Not professional for demos/clients
❌ Certificate warnings on every visit

**Recommended**: **Only for pure development/testing**
**Cost**: Free
**Time**: 0 (already done)

---

### **Option D: Self-Signed Certificates**

Generate self-signed certificates for local development:

**Implementation**:
1. Generate self-signed certs with openssl
2. Configure Traefik to use file provider with certs
3. Disable ACME entirely

**Pros**:
✅ No external dependencies
✅ Works offline
✅ Full control over certificates

**Cons**:
❌ Browser "not secure" warnings
❌ Must manually generate and renew certs
❌ Not suitable for demos/clients
❌ More configuration complexity

**Recommended**: **Not recommended** (Option C is better)
**Cost**: Free
**Time**: 2-3 hours setup

---

## Recommendation

### **For Production-Ready Development: Option A (Staging Subdomains)**

This is the **best long-term solution** that provides:
- Valid HTTPS certificates
- Clean environment separation
- Professional setup
- Easy testing without affecting production

### **Quick Actions Required**

#### 1. DNS Configuration (with your DNS provider)

Add these A records:
```
dev.wizardsofts.com           A  10.0.0.84
dev.mypadmafoods.com          A  10.0.0.84
dev.guardianinvestmentbd.com  A  10.0.0.84
```

#### 2. Update Docker Compose Labels

For each web app, change Traefik labels:

**ws-wizardsofts-web/docker-compose.yml**:
```yaml
labels:
  - "traefik.http.routers.wizardsofts-web.rule=Host(`dev.wizardsofts.com`)"
  # Instead of: Host(`www.wizardsofts.com`)
```

**pf-padmafoods-web/docker-compose.yml**:
```yaml
labels:
  - "traefik.http.routers.pf-padmafoods-web.rule=Host(`dev.mypadmafoods.com`)"
  # Instead of: Host(`www.mypadmafoods.com`)
```

**gibd-quant-web/docker-compose.yml**:
```yaml
labels:
  - "traefik.http.routers.gibd-quant-web.rule=Host(`dev.guardianinvestmentbd.com`)"
  # Instead of: Host(`www.guardianinvestmentbd.com`)
```

#### 3. Update Traefik to Production ACME

Once DNS is propagated, update `traefik.yml`:
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@wizardsofts.com
      storage: /letsencrypt/acme.json
      # Remove or comment out caServer line to use production
      # caServer: https://acme-staging-v02.api.letsencrypt.org/directory
      tlsChallenge: {}
```

#### 4. Restart Services
```bash
cd /home/wizardsofts/traefik
docker-compose down && docker-compose up -d

# Restart web apps
cd /home/wizardsofts/apps/ws-wizardsofts-web && docker-compose restart
cd /home/wizardsofts/apps/pf-padmafoods-web && docker-compose restart
cd /home/wizardsofts/apps/gibd-quant-web && docker-compose restart
```

---

## Alternative: If Production Server (106.70.161.3) is Not in Use

If 106.70.161.3 is **not serving any traffic**, then **Option B** is simpler:

1. **Update DNS** to point all domains to 10.0.0.84:
   ```
   www.wizardsofts.com         A  10.0.0.84
   www.mypadmafoods.com        A  10.0.0.84
   www.guardianinvestmentbd.com A  10.0.0.84
   ```

2. **Switch Traefik to production ACME** (remove caServer line)

3. **Restart Traefik** and wait for certificate acquisition

**Verification**: Check DNS resolution:
```bash
nslookup www.wizardsofts.com
# Should show: 10.0.0.84
```

---

## Current Status Summary

### ✅ Working Now
- All web applications accessible via HTTP
- Traefik healthy and routing correctly
- HTTP → HTTPS redirects working
- Let's Encrypt staging certificates being issued

### ❌ Not Working
- **HTTPS shows "not secure"** (staging certificates)
- Certificate warnings on every page
- Not suitable for demos or client presentations

### 🔧 Configuration Files Updated
- `/home/wizardsofts/traefik/traefik.yml` - Using staging ACME server
- `/home/wizardsofts/traefik/docker-compose.yml` - Has acme.json volume (traefik-ssl)
- Backups created with timestamps

---

## Next Steps

**Immediate (User Decision Required)**:
1. ⏹️ **Choose Option A or Option B**
2. ⏹️ **If Option A**: Provide DNS access or request DNS team to add records
3. ⏹️ **If Option B**: Confirm 106.70.161.3 is not in use

**After Decision**:
1. Update DNS records
2. Update docker-compose labels (if Option A)
3. Switch Traefik to production ACME
4. Verify HTTPS certificates
5. Document final configuration

---

## Testing Checklist (After Implementation)

```bash
# 1. DNS Resolution
nslookup dev.wizardsofts.com  # Should show 10.0.0.84

# 2. HTTP Access
curl -I http://dev.wizardsofts.com  # Should redirect to HTTPS (308)

# 3. HTTPS Certificate
openssl s_client -connect dev.wizardsofts.com:443 -servername dev.wizardsofts.com 2>/dev/null | openssl x509 -noout -dates -issuer

# 4. Browser Test
# Open https://dev.wizardsofts.com
# Should show lock icon, no warnings

# 5. Certificate Issuer
# Should show: "issuer=C = US, O = Let's Encrypt..."
```

---

## Files to Update (Option A)

1. `apps/ws-wizardsofts-web/docker-compose.yml` - Traefik labels
2. `apps/pf-padmafoods-web/docker-compose.yml` - Traefik labels
3. `apps/gibd-quant-web/docker-compose.yml` - Traefik labels
4. `infrastructure/traefik/traefik.yml` - Remove caServer line
5. `AGENT_GUIDELINES.md` - Update with dev subdomain strategy
6. All `CLAUDE.md` files - Update domain references

---

## Contact & Support

- DNS Provider: (Add your DNS provider details)
- Cloudflare / Route53 / Other
- DNS Management Access: (Who has access?)

---

**Decision Required By**: User (mashfiqurrahman)
**Technical Lead**: Claude Agent
**Last Updated**: December 30, 2025

