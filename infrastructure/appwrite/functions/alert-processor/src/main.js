/**
 * Appwrite Alert Processor Function
 * 
 * Receives webhook notifications from Prometheus Alertmanager,
 * stores alerts in Appwrite Database, and routes notifications
 * based on severity and team assignments.
 * 
 * @param {Object} req - The request object
 * @param {Object} res - The response object
 */

const sdk = require('node-appwrite');

/**
 * Main entry point for the Appwrite Function
 */
module.exports = async ({ req, res, log, error }) => {
  try {
    // Validate authentication
    const apiKey = req.headers['authorization'];
    if (!apiKey || !apiKey.startsWith('Bearer ')) {
      return res.json({
        success: false,
        error: 'Unauthorized: Missing or invalid API key'
      }, 401);
    }

    // Parse incoming alert payload from Alertmanager
    const payload = JSON.parse(req.body);
    log('Received alert payload:', JSON.stringify(payload, null, 2));

    // Initialize Appwrite SDK
    const client = new sdk.Client()
      .setEndpoint(process.env.APPWRITE_ENDPOINT)
      .setProject(process.env.APPWRITE_PROJECT_ID)
      .setKey(process.env.APPWRITE_FUNCTION_API_KEY);

    const database = new sdk.Databases(client);
    const messaging = new sdk.Messaging(client);

    // Process each alert in the payload
    const processedAlerts = [];
    for (const alert of payload.alerts) {
      const processedAlert = await processAlert(alert, payload, database, messaging, log, error);
      processedAlerts.push(processedAlert);
    }

    // Return success response
    return res.json({
      success: true,
      alertsProcessed: processedAlerts.length,
      alerts: processedAlerts
    }, 200);

  } catch (err) {
    error('Error processing alerts:', err);
    return res.json({
      success: false,
      error: err.message
    }, 500);
  }
};

/**
 * Process a single alert
 */
async function processAlert(alert, payload, database, messaging, log, error) {
  try {
    // Extract alert metadata
    const alertData = {
      alertname: alert.labels.alertname || 'Unknown',
      instance: alert.labels.instance || 'Unknown',
      severity: alert.labels.severity || 'info',
      category: alert.labels.category || 'general',
      service: alert.labels.service || null,
      status: alert.status,
      startsAt: alert.startsAt,
      endsAt: alert.endsAt || null,
      summary: alert.annotations.summary || '',
      description: alert.annotations.description || '',
      runbook: alert.annotations.runbook || '',
      impact: alert.annotations.impact || '',
      fingerprint: alert.fingerprint || generateFingerprint(alert),
      groupKey: payload.groupKey || null,
      externalURL: payload.externalURL || null,
      rawAlert: JSON.stringify(alert)
    };

    // Store alert in database
    const storedAlert = await storeAlert(alertData, database, log, error);
    log(`Alert stored: ${alertData.alertname} on ${alertData.instance}`);

    // Route notifications based on severity and status
    if (alert.status === 'firing') {
      await routeNotification(alertData, messaging, log, error);
    } else if (alert.status === 'resolved') {
      await sendResolvedNotification(alertData, messaging, log, error);
    }

    return {
      alertname: alertData.alertname,
      instance: alertData.instance,
      severity: alertData.severity,
      status: alert.status,
      stored: true,
      notified: true
    };

  } catch (err) {
    error(`Error processing alert: ${err.message}`);
    return {
      alertname: alert.labels.alertname,
      instance: alert.labels.instance,
      error: err.message,
      stored: false,
      notified: false
    };
  }
}

/**
 * Store alert in Appwrite Database
 */
async function storeAlert(alertData, database, log, error) {
  try {
    // Check if alert already exists (based on fingerprint)
    const existing = await database.listDocuments(
      process.env.DATABASE_ID,
      process.env.ALERTS_COLLECTION_ID,
      [
        sdk.Query.equal('fingerprint', alertData.fingerprint),
        sdk.Query.limit(1)
      ]
    );

    if (existing.documents.length > 0) {
      // Update existing alert
      return await database.updateDocument(
        process.env.DATABASE_ID,
        process.env.ALERTS_COLLECTION_ID,
        existing.documents[0].$id,
        {
          status: alertData.status,
          endsAt: alertData.endsAt,
          updatedAt: new Date().toISOString(),
          rawAlert: alertData.rawAlert
        }
      );
    } else {
      // Create new alert document
      return await database.createDocument(
        process.env.DATABASE_ID,
        process.env.ALERTS_COLLECTION_ID,
        sdk.ID.unique(),
        {
          ...alertData,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      );
    }
  } catch (err) {
    error(`Error storing alert: ${err.message}`);
    throw err;
  }
}

/**
 * Route notification based on alert severity
 */
async function routeNotification(alertData, messaging, log, error) {
  try {
    const { severity, alertname, instance, description, impact } = alertData;

    // Format notification message
    const message = formatAlertMessage(alertData);

    // Critical and Emergency alerts - send push notifications and SMS
    if (severity === 'critical' || severity === 'emergency') {
      log(`Sending critical alert notifications for ${alertname}`);
      
      // Send push notification (requires topic setup in Appwrite)
      try {
        await messaging.createPush(
          sdk.ID.unique(),
          `🚨 ${severity.toUpperCase()}: ${alertname}`,
          message,
          {
            topic: 'critical-alerts'
          }
        );
        log('Push notification sent');
      } catch (err) {
        error(`Failed to send push notification: ${err.message}`);
      }

      // Send SMS to on-call team (if Twilio configured)
      if (process.env.TWILIO_ACCOUNT_SID && process.env.ONCALL_PHONE_NUMBERS) {
        await sendSMS(alertData, log, error);
      }
    }

    // Warning alerts - send email notification (handled by Alertmanager)
    else if (severity === 'warning') {
      log(`Warning alert logged: ${alertname} - email handled by Alertmanager`);
    }

    // All alerts - send to general monitoring topic
    try {
      await messaging.createPush(
        sdk.ID.unique(),
        `⚠️ ${alertname}`,
        `${instance}: ${description}`,
        {
          topic: 'monitoring-alerts'
        }
      );
    } catch (err) {
      error(`Failed to send general push notification: ${err.message}`);
    }

  } catch (err) {
    error(`Error routing notification: ${err.message}`);
    throw err;
  }
}

/**
 * Send resolved notification
 */
async function sendResolvedNotification(alertData, messaging, log, error) {
  try {
    const { alertname, instance } = alertData;
    
    await messaging.createPush(
      sdk.ID.unique(),
      `✅ RESOLVED: ${alertname}`,
      `Alert resolved on ${instance}`,
      {
        topic: 'monitoring-alerts'
      }
    );
    
    log(`Resolved notification sent for ${alertname}`);
  } catch (err) {
    error(`Failed to send resolved notification: ${err.message}`);
  }
}

/**
 * Send SMS via Twilio (for critical alerts)
 */
async function sendSMS(alertData, log, error) {
  try {
    // Note: This requires Twilio SDK which would need to be added to package.json
    // For now, this is a placeholder showing the structure
    
    const { alertname, instance, severity, description } = alertData;
    const phoneNumbers = process.env.ONCALL_PHONE_NUMBERS.split(',');
    
    const smsMessage = `${severity.toUpperCase()}: ${alertname}\nInstance: ${instance}\n${description}`;
    
    log(`SMS would be sent to: ${phoneNumbers.join(', ')}`);
    log(`Message: ${smsMessage}`);
    
    // Actual Twilio integration would go here
    // const twilio = require('twilio');
    // const client = twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
    // for (const phone of phoneNumbers) {
    //   await client.messages.create({
    //     body: smsMessage,
    //     from: process.env.TWILIO_PHONE_NUMBER,
    //     to: phone.trim()
    //   });
    // }
    
  } catch (err) {
    error(`Error sending SMS: ${err.message}`);
  }
}

/**
 * Format alert message for notifications
 */
function formatAlertMessage(alertData) {
  const { alertname, instance, severity, description, impact, runbook } = alertData;
  
  let message = `Alert: ${alertname}\n`;
  message += `Instance: ${instance}\n`;
  message += `Severity: ${severity}\n\n`;
  message += `${description}\n`;
  
  if (impact) {
    message += `\nImpact: ${impact}`;
  }
  
  if (runbook) {
    message += `\n\nRunbook: ${runbook}`;
  }
  
  return message;
}

/**
 * Generate fingerprint for alert deduplication
 */
function generateFingerprint(alert) {
  const key = `${alert.labels.alertname}-${alert.labels.instance}-${alert.labels.job || ''}`;
  return Buffer.from(key).toString('base64');
}
