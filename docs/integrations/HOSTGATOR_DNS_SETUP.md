# HostGator DNS Configuration

**Date**: December 27, 2025
**Server**: 10.0.0.84
**Public IP**: 106.70.161.3

---

## DNS Records to Add in HostGator

### guardianinvestmentbd.com

Add these A records in HostGator DNS Zone Editor:

```dns
# A Records for guardianinvestmentbd.com
@                               A    106.70.161.3
www                             A    106.70.161.3
```

**Result**:
- guardianinvestmentbd.com → 106.70.161.3
- www.guardianinvestmentbd.com → 106.70.161.3

---

## How Router Forwards Traffic

```
Internet Request
    ↓
guardianinvestmentbd.com (DNS lookup)
    ↓
106.70.161.3 (Public IP - Your Router)
    ↓
Router Port Forward (80→10.0.0.84:80, 443→10.0.0.84:443)
    ↓
10.0.0.84 (Server)
    ↓
Traefik (Reverse Proxy)
    ↓
gibd-quant-web:3000 (Container)
```

---

## Traefik Configuration

Already configured on server (`~/traefik/dynamic_conf.yml`):

```yaml
quant-web-https:
  rule: Host(`www.guardianinvestmentbd.com`) || Host(`guardianinvestmentbd.com`)
  service: quant-web
  entryPoints:
    - websecure
  tls:
    certResolver: myresolver

services:
  quant-web:
    loadBalancer:
      servers:
        - url: "http://gibd-quant-web:3000"
```

**Features**:
- ✅ HTTP automatically redirects to HTTPS
- ✅ SSL certificate will auto-generate via Let's Encrypt
- ✅ Routing ready for when gibd-quant-web container is deployed

---

## Before Deployment Checklist

### 1. HostGator DNS Setup
- [ ] Log into HostGator cPanel
- [ ] Go to Zone Editor for guardianinvestmentbd.com
- [ ] Add A record: `@` → `106.70.161.3`
- [ ] Add A record: `www` → `106.70.161.3`
- [ ] Wait for DNS propagation (5-60 minutes)

### 2. Verify DNS Propagation

```bash
# Check DNS from your local machine
dig guardianinvestmentbd.com
dig www.guardianinvestmentbd.com

# Should return: 106.70.161.3
```

### 3. Deploy gibd-quant-web

The service isn't deployed yet. When ready:

```bash
# Option 1: Deploy from local (requires full monorepo sync)
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
rsync -avz --exclude 'node_modules' --exclude '.git' ./ wizardsofts@10.0.0.84:~/wizardsofts-megabuild/
ssh wizardsofts@10.0.0.84 "cd ~/wizardsofts-megabuild && docker compose --profile gibd-quant up -d gibd-quant-web"

# Option 2: Deploy on port 4002 first (safer)
# Test at http://10.0.0.84:4002 before removing port
```

### 4. Verify HTTPS Access

After DNS propagates and service is deployed:

```bash
# Test HTTP → HTTPS redirect
curl -I http://guardianinvestmentbd.com

# Test HTTPS
curl -I https://www.guardianinvestmentbd.com

# Should return HTTP/2 200
```

---

## Current Status

| Domain | DNS Status | Traefik Config | Service Status |
|--------|-----------|----------------|----------------|
| **www.wizardsofts.com** | ✅ Configured (106.70.161.3) | ✅ Configured | ✅ Running |
| **dailydeenguide.com** | ⏸️ Needs DNS update | ✅ Configured | ✅ Running (port 4001) |
| **guardianinvestmentbd.com** | ❌ Not configured | ✅ Configured | ❌ Not deployed |

---

## Testing After DNS Setup

### Test from Browser
1. Navigate to: http://guardianinvestmentbd.com
2. Should redirect to: https://www.guardianinvestmentbd.com
3. SSL certificate should be valid (Let's Encrypt)
4. Page should load from gibd-quant-web container

### Test from Command Line

```bash
# Test DNS resolution
nslookup guardianinvestmentbd.com

# Test HTTP → HTTPS redirect
curl -I http://guardianinvestmentbd.com

# Test HTTPS (skip cert verification during testing)
curl -Ik https://www.guardianinvestmentbd.com

# Expected: HTTP/2 200 when service is running
```

---

## Troubleshooting

### Issue: DNS not resolving to 106.70.161.3
**Solution**: Wait for DNS propagation (can take up to 48 hours, usually 5-60 minutes)

### Issue: 404 Not Found
**Cause**: gibd-quant-web container not running
**Solution**: Deploy the service (see "Deploy gibd-quant-web" above)

### Issue: SSL certificate error
**Cause**: Let's Encrypt can't verify domain ownership
**Solution**:
1. Ensure DNS points to correct IP
2. Ensure ports 80 and 443 are forwarded
3. Check Traefik logs: `docker logs traefik`

### Issue: 502 Bad Gateway
**Cause**: Container exists but not responding
**Solution**: Check container health: `docker ps | grep gibd-quant-web`

---

## DNS Records Summary

Add these in HostGator DNS Zone Editor:

| Type | Host | Points To | TTL |
|------|------|-----------|-----|
| A | @ | 106.70.161.3 | 14400 |
| A | www | 106.70.161.3 | 14400 |

**Domain**: guardianinvestmentbd.com
**Public IP**: 106.70.161.3 (router)
**Server IP**: 10.0.0.84 (internal)
**Service**: gibd-quant-web:3000
