-- Flyway Migration V3: Create tenant API keys table
-- Description: API key management for service-to-service authentication

CREATE TABLE IF NOT EXISTS tenant_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    key_type VARCHAR(10) NOT NULL DEFAULT 'LIVE',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_used_ip VARCHAR(45),
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by VARCHAR(255),
    revocation_reason TEXT,

    CONSTRAINT fk_api_key_tenant FOREIGN KEY (tenant_id)
        REFERENCES tenants(id) ON DELETE CASCADE,
    CONSTRAINT uk_api_key_prefix UNIQUE (key_prefix),
    CONSTRAINT chk_key_type CHECK (key_type IN ('LIVE', 'TEST'))
);

-- Join table for API key scopes (many-to-many)
CREATE TABLE IF NOT EXISTS api_key_scopes (
    api_key_id UUID NOT NULL,
    scope VARCHAR(100) NOT NULL,

    CONSTRAINT fk_scope_api_key FOREIGN KEY (api_key_id)
        REFERENCES tenant_api_keys(id) ON DELETE CASCADE,
    CONSTRAINT pk_api_key_scope PRIMARY KEY (api_key_id, scope)
);

-- Indexes for tenant_api_keys
CREATE INDEX idx_api_key_tenant ON tenant_api_keys(tenant_id);
CREATE INDEX idx_api_key_prefix ON tenant_api_keys(key_prefix);
CREATE INDEX idx_api_key_hash ON tenant_api_keys(key_hash);
CREATE INDEX idx_api_key_expires ON tenant_api_keys(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_api_key_type ON tenant_api_keys(key_type);

-- Partial index for active keys
CREATE INDEX idx_api_key_active ON tenant_api_keys(tenant_id, key_prefix)
    WHERE revoked_at IS NULL;

-- Index for scopes
CREATE INDEX idx_api_key_scopes ON api_key_scopes(api_key_id);

-- Comments
COMMENT ON TABLE tenant_api_keys IS 'API keys for tenant service-to-service authentication';
COMMENT ON COLUMN tenant_api_keys.key_hash IS 'SHA-256 hash of the API key';
COMMENT ON COLUMN tenant_api_keys.key_prefix IS 'First characters of key for identification (ws_live_ or ws_test_)';
COMMENT ON COLUMN tenant_api_keys.key_type IS 'LIVE for production keys, TEST for sandbox keys';
COMMENT ON COLUMN tenant_api_keys.last_used_ip IS 'IP address of the last request using this key';
COMMENT ON TABLE api_key_scopes IS 'Scopes/permissions granted to each API key';
