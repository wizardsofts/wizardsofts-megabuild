# Alert Processor - Appwrite Function

This Appwrite Function receives webhook notifications from Prometheus Alertmanager, processes alerts, stores them in the database, and routes notifications based on severity and team assignments.

## Features

- **Alert Storage**: Stores all alerts in Appwrite Database with deduplication
- **Smart Routing**: Routes notifications based on severity levels:
  - `critical`/`emergency`: Push notifications + SMS to on-call team
  - `warning`: Email notifications (handled by Alertmanager)
  - All alerts: Logged to general monitoring topic
- **Resolved Notifications**: Sends confirmation when alerts are resolved
- **Idempotent**: Handles duplicate alerts gracefully using fingerprinting

## Deployment

### 1. Create Database Schema

Create a new database in Appwrite Console with the following structure:

**Database ID**: `monitoring`

**Collection**: `alerts`  
**Collection ID**: `alerts`

**Attributes**:
```json
{
  "alertname": { "type": "string", "size": 255, "required": true },
  "instance": { "type": "string", "size": 255, "required": true },
  "severity": { "type": "enum", "elements": ["info", "warning", "critical", "emergency"], "required": true },
  "category": { "type": "string", "size": 100, "required": true },
  "service": { "type": "string", "size": 255, "required": false },
  "status": { "type": "enum", "elements": ["firing", "resolved"], "required": true },
  "startsAt": { "type": "datetime", "required": true },
  "endsAt": { "type": "datetime", "required": false },
  "summary": { "type": "string", "size": 500, "required": false },
  "description": { "type": "string", "size": 2000, "required": false },
  "runbook": { "type": "string", "size": 500, "required": false },
  "impact": { "type": "string", "size": 1000, "required": false },
  "fingerprint": { "type": "string", "size": 255, "required": true },
  "groupKey": { "type": "string", "size": 255, "required": false },
  "externalURL": { "type": "url", "required": false },
  "rawAlert": { "type": "string", "size": 65535, "required": true },
  "createdAt": { "type": "datetime", "required": true },
  "updatedAt": { "type": "datetime", "required": true }
}
```

**Indexes**:
- `fingerprint` (unique, key index)
- `status` (key index)
- `severity` (key index)
- `instance` (key index)
- `startsAt` (key index, descending)

### 2. Create Messaging Topics

In Appwrite Messaging, create the following topics:
- `critical-alerts` - For critical/emergency alerts
- `monitoring-alerts` - For all alerts

Subscribe users/devices to these topics as needed.

### 3. Deploy Function

#### Via Appwrite CLI:

```bash
cd infrastructure/appwrite/functions/alert-processor

# Install dependencies
npm install

# Login to Appwrite
appwrite login

# Deploy function
appwrite deploy function \
  --function-id alert-processor \
  --name "Alert Processor" \
  --runtime node-18.0 \
  --entrypoint src/main.js \
  --execute any
```

#### Via Appwrite Console:

1. Go to Functions → Create Function
2. **Function ID**: `alert-processor`
3. **Name**: Alert Processor
4. **Runtime**: Node.js 18
5. **Entrypoint**: `src/main.js`
6. **Execute Access**: Any (webhook will use API key auth)
7. Upload the function code as a tar.gz

### 4. Configure Environment Variables

In the Appwrite Function settings, add these environment variables:

```bash
# Appwrite Configuration
APPWRITE_ENDPOINT=https://appwrite.wizardsofts.com/v1
APPWRITE_PROJECT_ID=wizardsofts-prod
APPWRITE_FUNCTION_API_KEY=<your-api-key-here>

# Database Configuration
DATABASE_ID=monitoring
ALERTS_COLLECTION_ID=alerts

# SMS Configuration (Optional - for critical alerts)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=<your-twilio-account-sid>
TWILIO_AUTH_TOKEN=<your-twilio-auth-token>
TWILIO_PHONE_NUMBER=<your-twilio-phone-number>
ONCALL_PHONE_NUMBERS=+1234567890,+0987654321
```

### 5. Get Function Webhook URL

After deployment, the function will be available at:
```
https://appwrite.wizardsofts.com/v1/functions/alert-processor/executions
```

This URL is already configured in the Alertmanager configuration.

### 6. Create API Key for Alertmanager

1. Go to Appwrite Console → API Keys
2. Create a new API Key with:
   - **Name**: Alertmanager Webhook
   - **Scopes**: 
     - `functions.read`
     - `functions.execute`
   - **Expiration**: None or set appropriate duration

3. Copy the API key and add it to your `.env` file:
```bash
APPWRITE_API_KEY=<your-api-key>
```

## Testing

### Test with curl:

```bash
curl -X POST https://appwrite.wizardsofts.com/v1/functions/alert-processor/executions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver": "appwrite-webhook",
    "status": "firing",
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "TestAlert",
          "instance": "test-server",
          "severity": "warning",
          "category": "test"
        },
        "annotations": {
          "summary": "This is a test alert",
          "description": "Testing the alert processor function",
          "impact": "No impact - test only"
        },
        "startsAt": "2024-01-15T10:00:00Z",
        "fingerprint": "test123"
      }
    ],
    "groupKey": "test-group",
    "externalURL": "http://alertmanager:9093"
  }'
```

### Expected Response:

```json
{
  "success": true,
  "alertsProcessed": 1,
  "alerts": [
    {
      "alertname": "TestAlert",
      "instance": "test-server",
      "severity": "warning",
      "status": "firing",
      "stored": true,
      "notified": true
    }
  ]
}
```

## Notification Flow

```
Prometheus → Alertmanager → Appwrite Function → [Store in DB, Send Notifications]
                                                  ├─ Push Notification (critical/emergency)
                                                  ├─ SMS (critical/emergency)
                                                  └─ General monitoring topic
```

## Alert Severity Handling

| Severity | Storage | Push Notification | SMS | Email |
|----------|---------|-------------------|-----|-------|
| info     | ✅      | ✅ (general)      | ❌  | ❌    |
| warning  | ✅      | ✅ (general)      | ❌  | ✅ (via Alertmanager) |
| critical | ✅      | ✅ (critical)     | ✅  | ✅ (via Alertmanager) |
| emergency| ✅      | ✅ (critical)     | ✅  | ✅ (via Alertmanager) |

## Monitoring the Function

View function logs in Appwrite Console:
1. Go to Functions → alert-processor
2. Click on "Executions" tab
3. View logs for each execution

## Troubleshooting

### Function not receiving webhooks:
- Verify API key is correct in Alertmanager config
- Check function is deployed and active
- Verify webhook URL is accessible from Alertmanager

### Alerts not being stored:
- Check database and collection IDs are correct
- Verify API key has database write permissions
- Review function execution logs

### Notifications not sending:
- Verify messaging topics exist
- Check users/devices are subscribed to topics
- Review Twilio credentials (for SMS)

## Future Enhancements

- [ ] Add alert acknowledgment workflow
- [ ] Implement alert escalation policies
- [ ] Add integration with PagerDuty/Opsgenie
- [ ] Create dashboard for alert analytics
- [ ] Add alert correlation and grouping
- [ ] Implement custom notification templates
