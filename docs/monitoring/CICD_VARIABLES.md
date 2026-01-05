# CI/CD Variables Required for Monitoring Deployment

## Overview
The monitoring deployment job requires several CI/CD variables to be configured in GitLab for proper operation. These variables are injected into the `.env` file during deployment.

## Setup Instructions

1. Navigate to your GitLab project
2. Go to **Settings → CI/CD → Variables**
3. Add the following variables (mark as **Protected** and **Masked**):

## Required Variables

### 1. SMTP_PASSWORD
- **Purpose**: Gmail app password for Alertmanager email notifications
- **Type**: Protected, Masked
- **How to get**:
  1. Go to Google Account → Security → 2-Step Verification
  2. At the bottom, select "App passwords"
  3. Select "Mail" and your device
  4. Copy the generated 16-character password
- **Example**: `abcd efgh ijkl mnop` (no spaces in actual value)

### 2. APPWRITE_MONITORING_API_KEY
- **Purpose**: API key for Appwrite alert processor webhook authentication
- **Type**: Protected, Masked
- **How to get**:
  1. Go to Appwrite Console → Project Settings → API Keys
  2. Create new API key with name "Monitoring Alerts"
  3. Grant permissions: `functions.read`, `functions.write`
  4. Copy the generated API key
- **Example**: `standard_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### 3. GRAFANA_ADMIN_PASSWORD
- **Purpose**: Admin password for Grafana dashboard access
- **Type**: Protected, Masked
- **Recommendation**: Use a strong password (min 16 chars, mix of upper/lower/numbers/symbols)
- **Example**: `MySecureGrafana2025!`

### 4. SLACK_WEBHOOK_URL (Optional)
- **Purpose**: Slack webhook URL for alert notifications
- **Type**: Protected, Masked
- **How to get**:
  1. Go to Slack App settings → Incoming Webhooks
  2. Create new webhook for your channel
  3. Copy the webhook URL
- **Example**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX`
- **Note**: If not provided, Slack notifications will be disabled

## Additional CI/CD Variables (Already Configured)

These should already exist in your GitLab CI/CD variables:

- **SSH_PRIVATE_KEY**: SSH key for deployment to Server 84
- **DEPLOY_HOST**: Target deployment host (default: 10.0.0.84)

## Verification

After adding these variables, you can verify they're set correctly:

1. Push a change to `infrastructure/auto-scaling/monitoring/**`
2. Check the `validate-monitoring-config` job runs successfully
3. Manually trigger the `deploy-monitoring` job
4. SSH into Server 84 and check:
   ```bash
   cat /home/mashfiqur/wizardsofts-megabuild/infrastructure/auto-scaling/.env
   ```
   You should see all variables populated (passwords will be masked)

## Security Best Practices

1. **Always mark sensitive variables as Protected and Masked**
2. **Never commit these values to git**
3. **Rotate passwords periodically**
4. **Use app-specific passwords for email (not your main Gmail password)**
5. **Limit API key permissions to minimum required**

## Troubleshooting

### Variable not appearing in .env file
- Check variable name spelling matches exactly
- Verify variable is marked as "Protected" (only available on protected branches)
- Check job logs for any error messages during .env creation

### Email notifications not working
- Verify SMTP_PASSWORD is a valid Gmail app password (not your account password)
- Check SMTP_USER is set to a valid Gmail address in the deployment script
- Test Gmail settings allow less secure app access if needed

### Appwrite webhook not receiving alerts
- Verify APPWRITE_MONITORING_API_KEY has correct permissions
- Check Appwrite function is deployed and active
- Test webhook URL is accessible from Server 84

## Related Documentation

- [Monitoring Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Alert Configuration](./ALERTS_CONFIGURATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
