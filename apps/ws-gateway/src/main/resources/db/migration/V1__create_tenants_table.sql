-- Flyway Migration V1: Create tenants table
-- Description: Initial schema for multi-tenant support

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    slug VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    owner_email VARCHAR(255) NOT NULL,
    keycloak_group_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    tier VARCHAR(20) NOT NULL DEFAULT 'FREE',
    metadata TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    suspended_at TIMESTAMP,

    CONSTRAINT uk_tenant_slug UNIQUE (slug),
    CONSTRAINT chk_tenant_status CHECK (status IN ('PENDING', 'PROVISIONING', 'ACTIVE', 'SUSPENDED', 'DELETED')),
    CONSTRAINT chk_tenant_tier CHECK (tier IN ('FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE'))
);

-- Indexes for common queries
CREATE INDEX idx_tenant_slug ON tenants(slug);
CREATE INDEX idx_tenant_owner_email ON tenants(owner_email);
CREATE INDEX idx_tenant_keycloak_group ON tenants(keycloak_group_id);
CREATE INDEX idx_tenant_status ON tenants(status);

-- Comments
COMMENT ON TABLE tenants IS 'Multi-tenant organizations with Keycloak integration';
COMMENT ON COLUMN tenants.slug IS 'URL-friendly unique identifier for the tenant';
COMMENT ON COLUMN tenants.keycloak_group_id IS 'Keycloak group ID for role-based access';
COMMENT ON COLUMN tenants.tier IS 'Subscription tier determining feature limits';
