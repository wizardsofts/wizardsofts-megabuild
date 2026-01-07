# Appwrite Deployment - Next Steps

**Current Status:** ✅ Appwrite fully deployed and operational on 10.0.0.84

---

## What You Have Right Now

15 Appwrite containers running and healthy:
- Main API server
- Self-hosted console UI
- Realtime WebSocket server
- 10 background workers (messaging, webhooks, etc.)
- MariaDB database (credentials: wizardsofts / W1z4rdS0fts2025Secure)
- Redis cache

---

## What You Need to Do

### Step 1: Configure DNS (Required for external access)

Add these A records to your DNS provider:

```
appwrite.wizardsofts.com    A    10.0.0.84
appwrite.bondwala.com       A    10.0.0.84
```

**How to verify DNS is working:**
```bash
nslookup appwrite.wizardsofts.com
# Should return: 10.0.0.84
```

### Step 2: Deploy Traefik (Required for HTTPS console access)

On server 10.0.0.84:

```bash
cd /opt/wizardsofts-megabuild

# This should start Traefik + Let's Encrypt + main services
docker compose -f docker-compose.yml --env-file .env up -d

# Verify Traefik is running
docker ps | grep traefik
```

### Step 3: Access Appwrite Console

Once DNS and Traefik are ready:

1. Go to: **https://appwrite.wizardsofts.com/console**
2. Sign up with: **admin@wizardsofts.com**
3. Create a password
4. Create the **BondWala** project

### Step 4: Configure Push Notification Providers

In Appwrite Console → BondWala Project:

1. **For iOS (APNs):**
   - Settings → Messaging → APNs Provider
   - Add your Apple Team ID
   - Upload signing key

2. **For Android (FCM):**
   - Settings → Messaging → FCM Provider
   - Add your Google Service Account credentials

3. **Create Messaging Topics:**
   - all-users (broadcast to everyone)
   - win-alerts (lottery wins)
   - draw-updates (new draws)

### Step 5: Generate API Keys

In Console → BondWala Project → Settings → API Keys:

**Create server key:**
- Name: bondwala-server
- Scopes: messaging.*, database.*
- Copy this for backend

**Create client key:**
- Name: bondwala-client  
- Scopes: messaging.topics.read, messaging.messages.create
- Copy this for mobile app

### Step 6: Integrate with BondWala Backend

Install Appwrite SDK:
```bash
npm install node-appwrite
```

Create messaging service:
```typescript
import { Client, Messaging } from 'node-appwrite';

const client = new Client()
  .setEndpoint('https://appwrite.bondwala.com/v1')
  .setProject('PROJECT_ID')
  .setKey('API_KEY');

const messaging = new Messaging(client);

// Send push notification
await messaging.sendPush('all-users', 'Hi users!', {
  title: 'New Draw Available'
});
```

### Step 7: Integrate with BondWala Mobile App

Install Appwrite SDK:
```bash
npm install react-native-appwrite
```

Update notification service:
```typescript
import { Client, Messaging } from 'react-native-appwrite';

const client = new Client()
  .setEndpoint('https://appwrite.bondwala.com/v1')
  .setProject('PROJECT_ID');

// Subscribe to topic
const messaging = new Messaging(client);
await messaging.subscribeToTopic('win-alerts');

// Listen for messages
messaging.onMessage((message) => {
  console.log('Got notification:', message);
});
```

### Step 8: Test Push Notifications

1. Register a test device in your mobile app
2. Subscribe it to a topic (e.g., win-alerts)
3. Send a test message from backend
4. Verify notification appears on device

---

## Quick Commands

Check deployment status:
```bash
# SSH to server
ssh wizardsofts@10.0.0.84

# Check Appwrite containers
docker ps | grep appwrite

# View logs
docker logs appwrite -f

# Test health
curl http://appwrite/v1/health
```

Setup backups:
```bash
chmod +x /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# 0 2 * * * /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh >> /var/log/appwrite-backup.log 2>&1
```

---

## Documentation

- [APPWRITE_DEPLOYMENT_VERIFICATION.md](APPWRITE_DEPLOYMENT_VERIFICATION.md) - Full verification report
- [APPWRITE_DEPLOYMENT_SUMMARY.md](APPWRITE_DEPLOYMENT_SUMMARY.md) - Overview & credentials
- [APPWRITE_QUICK_REFERENCE.md](APPWRITE_QUICK_REFERENCE.md) - Operations cheat sheet
- [docs/APPWRITE_DEPLOYMENT.md](docs/APPWRITE_DEPLOYMENT.md) - Complete guide
- [docs/APPWRITE_HARDENING.md](docs/APPWRITE_HARDENING.md) - Security details

---

## Support

- **Tech Lead:** tech@wizardsofts.com
- **System Admin:** admin@wizardsofts.com
- **Appwrite Docs:** https://appwrite.io/docs

---

## Current Status by Component

| Component | Status | Notes |
|-----------|--------|-------|
| Appwrite API | ✅ Running | Ready for requests |
| MariaDB | ✅ Running | Database operational |
| Redis | ✅ Running | Cache ready |
| Messaging Worker | ✅ Running | Push notifications ready |
| Traefik | ⏳ Pending | Deploy from docker-compose.yml |
| DNS | ⏳ Pending | Configure A records |
| Console | ✅ Running | Self-hosted at /console |
| APNs Provider | ⏳ Pending | Configure in console |
| FCM Provider | ⏳ Pending | Configure in console |
| Backend Integration | ⏳ Pending | SDK installation |
| Mobile Integration | ⏳ Pending | SDK installation |

---

**You're ready to proceed with DNS configuration!**
