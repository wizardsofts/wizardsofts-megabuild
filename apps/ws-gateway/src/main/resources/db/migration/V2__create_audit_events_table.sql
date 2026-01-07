-- Flyway Migration V2: Create security audit events table
-- Description: Persistent storage for security audit trail

CREATE TABLE IF NOT EXISTS security_audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    result VARCHAR(20) NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    tenant_id VARCHAR(50),
    tenant_slug VARCHAR(50),
    client_id VARCHAR(100),
    source_ip VARCHAR(45),
    user_agent TEXT,
    resource VARCHAR(500),
    method VARCHAR(10),
    correlation_id VARCHAR(50),
    failure_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_event_result CHECK (result IN ('SUCCESS', 'FAILURE', 'DENIED', 'PENDING'))
);

-- Indexes for audit queries
CREATE INDEX idx_audit_event_type ON security_audit_events(event_type);
CREATE INDEX idx_audit_user_id ON security_audit_events(user_id);
CREATE INDEX idx_audit_tenant_id ON security_audit_events(tenant_id);
CREATE INDEX idx_audit_correlation_id ON security_audit_events(correlation_id);
CREATE INDEX idx_audit_created_at ON security_audit_events(created_at);
CREATE INDEX idx_audit_source_ip ON security_audit_events(source_ip);

-- Composite index for common queries
CREATE INDEX idx_audit_user_tenant_time ON security_audit_events(user_id, tenant_id, created_at DESC);

-- Partial index for failures (commonly queried)
CREATE INDEX idx_audit_failures ON security_audit_events(event_type, created_at DESC)
    WHERE result IN ('FAILURE', 'DENIED');

-- Comments
COMMENT ON TABLE security_audit_events IS 'Security audit trail for compliance and monitoring';
COMMENT ON COLUMN security_audit_events.metadata IS 'Additional context stored as JSON';
