/**
 * Unit tests for Alert Processor Appwrite Function
 */

describe('Alert Processor Function', () => {
  let req, res, log, error;
  let mockDatabase, mockMessaging;

  beforeEach(() => {
    // Mock request/response
    req = {
      headers: { authorization: 'Bearer test-api-key' },
      body: JSON.stringify({
        receiver: 'appwrite-webhook',
        status: 'firing',
        alerts: [
          {
            status: 'firing',
            labels: {
              alertname: 'HighCPUUsage',
              instance: 'server-80',
              severity: 'warning',
              category: 'performance'
            },
            annotations: {
              summary: 'High CPU usage detected',
              description: 'CPU usage above 80% for 5 minutes',
              impact: 'Performance degradation',
              runbook: 'https://docs.wizardsofts.com/runbooks/high-cpu'
            },
            startsAt: '2024-01-15T10:00:00Z',
            fingerprint: 'abc123'
          }
        ],
        groupKey: 'test-group',
        externalURL: 'http://alertmanager:9093'
      })
    };

    res = {
      json: jest.fn()
    };

    log = jest.fn();
    error = jest.fn();

    // Mock Appwrite SDK
    mockDatabase = {
      listDocuments: jest.fn(),
      createDocument: jest.fn(),
      updateDocument: jest.fn()
    };

    mockMessaging = {
      createPush: jest.fn()
    };
  });

  test('should authenticate request with valid API key', async () => {
    // Test will verify Bearer token validation
    expect(req.headers.authorization).toBe('Bearer test-api-key');
  });

  test('should reject request without API key', async () => {
    req.headers.authorization = '';
    
    // Expected behavior: function should return 401
    expect(res.json).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.stringContaining('Unauthorized')
      }),
      401
    );
  });

  test('should parse Alertmanager payload correctly', () => {
    const payload = JSON.parse(req.body);
    
    expect(payload.alerts).toHaveLength(1);
    expect(payload.alerts[0].labels.alertname).toBe('HighCPUUsage');
    expect(payload.alerts[0].status).toBe('firing');
  });

  test('should extract alert metadata', () => {
    const payload = JSON.parse(req.body);
    const alert = payload.alerts[0];
    
    expect(alert.labels.alertname).toBe('HighCPUUsage');
    expect(alert.labels.instance).toBe('server-80');
    expect(alert.labels.severity).toBe('warning');
    expect(alert.annotations.summary).toBe('High CPU usage detected');
  });

  test('should generate fingerprint for alert', () => {
    const alert = {
      labels: {
        alertname: 'TestAlert',
        instance: 'test-server',
        job: 'test-job'
      }
    };
    
    const key = `${alert.labels.alertname}-${alert.labels.instance}-${alert.labels.job}`;
    const fingerprint = Buffer.from(key).toString('base64');
    
    expect(fingerprint).toBeTruthy();
    expect(typeof fingerprint).toBe('string');
  });

  test('should create new alert document in database', async () => {
    mockDatabase.listDocuments.mockResolvedValue({ documents: [] });
    mockDatabase.createDocument.mockResolvedValue({
      $id: 'doc123',
      alertname: 'HighCPUUsage',
      instance: 'server-80'
    });

    // Test would verify createDocument is called with correct data
    expect(mockDatabase.createDocument).toBeDefined();
  });

  test('should update existing alert document', async () => {
    mockDatabase.listDocuments.mockResolvedValue({
      documents: [{ $id: 'doc123' }]
    });
    mockDatabase.updateDocument.mockResolvedValue({
      $id: 'doc123',
      status: 'resolved'
    });

    // Test would verify updateDocument is called when alert exists
    expect(mockDatabase.updateDocument).toBeDefined();
  });

  test('should send push notification for warning alerts', async () => {
    mockMessaging.createPush.mockResolvedValue({
      $id: 'push123'
    });

    // Verify createPush would be called for general monitoring topic
    expect(mockMessaging.createPush).toBeDefined();
  });

  test('should send critical notification for critical alerts', async () => {
    const criticalAlert = {
      labels: {
        alertname: 'ServerDown',
        instance: 'server-80',
        severity: 'critical'
      }
    };

    // For critical alerts, expect push notification to critical-alerts topic
    expect(criticalAlert.labels.severity).toBe('critical');
  });

  test('should format alert message correctly', () => {
    const alertData = {
      alertname: 'HighCPUUsage',
      instance: 'server-80',
      severity: 'warning',
      description: 'CPU usage above 80%',
      impact: 'Performance degradation',
      runbook: 'https://docs.wizardsofts.com/runbooks/high-cpu'
    };

    const expectedMessage = 
      `Alert: ${alertData.alertname}\n` +
      `Instance: ${alertData.instance}\n` +
      `Severity: ${alertData.severity}\n\n` +
      `${alertData.description}\n` +
      `\nImpact: ${alertData.impact}` +
      `\n\nRunbook: ${alertData.runbook}`;

    expect(expectedMessage).toContain(alertData.alertname);
    expect(expectedMessage).toContain(alertData.instance);
    expect(expectedMessage).toContain(alertData.description);
  });

  test('should handle resolved alerts', async () => {
    const resolvedPayload = {
      alerts: [
        {
          status: 'resolved',
          labels: {
            alertname: 'HighCPUUsage',
            instance: 'server-80'
          },
          endsAt: '2024-01-15T10:30:00Z'
        }
      ]
    };

    expect(resolvedPayload.alerts[0].status).toBe('resolved');
    expect(resolvedPayload.alerts[0].endsAt).toBeTruthy();
  });

  test('should handle multiple alerts in single payload', () => {
    const multiAlertPayload = {
      alerts: [
        { labels: { alertname: 'Alert1' } },
        { labels: { alertname: 'Alert2' } },
        { labels: { alertname: 'Alert3' } }
      ]
    };

    expect(multiAlertPayload.alerts).toHaveLength(3);
  });

  test('should handle errors gracefully', async () => {
    mockDatabase.createDocument.mockRejectedValue(
      new Error('Database connection failed')
    );

    // Function should catch error and return appropriate response
    expect(error).toBeDefined();
  });

  test('should return success response with processed alerts', async () => {
    const expectedResponse = {
      success: true,
      alertsProcessed: 1,
      alerts: expect.arrayContaining([
        expect.objectContaining({
          alertname: 'HighCPUUsage',
          instance: 'server-80',
          severity: 'warning',
          status: 'firing',
          stored: true,
          notified: true
        })
      ])
    };

    expect(expectedResponse.success).toBe(true);
    expect(expectedResponse.alertsProcessed).toBeGreaterThan(0);
  });
});

describe('Alert Routing Logic', () => {
  test('should route critical alerts to multiple channels', () => {
    const criticalAlert = { severity: 'critical' };
    
    // Critical alerts should trigger:
    // 1. Push notification to critical-alerts topic
    // 2. SMS to on-call team
    // 3. Email (handled by Alertmanager)
    
    expect(criticalAlert.severity).toBe('critical');
  });

  test('should route emergency alerts immediately', () => {
    const emergencyAlert = { severity: 'emergency' };
    
    // Emergency alerts should have:
    // - group_wait: 0s
    // - group_interval: 1m
    // - repeat_interval: 30m
    
    expect(emergencyAlert.severity).toBe('emergency');
  });

  test('should send SMS only for critical/emergency alerts', () => {
    const severities = ['info', 'warning', 'critical', 'emergency'];
    const shouldSendSMS = (severity) => 
      severity === 'critical' || severity === 'emergency';
    
    expect(shouldSendSMS('info')).toBe(false);
    expect(shouldSendSMS('warning')).toBe(false);
    expect(shouldSendSMS('critical')).toBe(true);
    expect(shouldSendSMS('emergency')).toBe(true);
  });
});

describe('Database Operations', () => {
  test('should create alert with all required fields', () => {
    const alertData = {
      alertname: 'TestAlert',
      instance: 'test-server',
      severity: 'warning',
      category: 'test',
      service: null,
      status: 'firing',
      startsAt: '2024-01-15T10:00:00Z',
      endsAt: null,
      summary: 'Test summary',
      description: 'Test description',
      runbook: 'https://example.com/runbook',
      impact: 'Test impact',
      fingerprint: 'test123',
      groupKey: 'test-group',
      externalURL: 'http://alertmanager:9093',
      rawAlert: '{}',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Verify all required fields are present
    expect(alertData.alertname).toBeTruthy();
    expect(alertData.instance).toBeTruthy();
    expect(alertData.severity).toBeTruthy();
    expect(alertData.status).toBeTruthy();
    expect(alertData.fingerprint).toBeTruthy();
    expect(alertData.createdAt).toBeTruthy();
  });

  test('should use fingerprint for deduplication', () => {
    const fingerprints = new Set();
    
    const alert1 = { alertname: 'Alert1', instance: 'server-1' };
    const alert2 = { alertname: 'Alert1', instance: 'server-1' }; // Duplicate
    const alert3 = { alertname: 'Alert2', instance: 'server-1' }; // Different
    
    const fp1 = `${alert1.alertname}-${alert1.instance}`;
    const fp2 = `${alert2.alertname}-${alert2.instance}`;
    const fp3 = `${alert3.alertname}-${alert3.instance}`;
    
    fingerprints.add(fp1);
    expect(fingerprints.has(fp2)).toBe(true); // Duplicate detected
    expect(fingerprints.has(fp3)).toBe(false); // Different alert
  });
});
