# Server-Setup Project Constitution

## Security Hardening Principles

All contributors and automation (including Copilot) must adhere to the following security hardening checklist for Docker and service deployment:

1. **Restrict Exposed Ports**
   - Only expose ports that are strictly necessary for external access.
   - Internal services (e.g., Redis, Postgres) should not be mapped to host ports unless required.

2. **Limit Sensitive Volume Mounts**
   - Avoid mounting sensitive directories (e.g., `~/.ssh`, `/var/run/docker.sock`) unless absolutely necessary.
   - Ensure no sensitive host data is exposed to containers.

3. **Use Environment Files for Secrets**
   - Move all credentials and secrets to `.env` files.
   - Restrict permissions on `.env` files.

4. **Use Official, Trusted Images**
   - Always pull images from official sources.
   - Rebuild containers from clean, trusted images after an incident.

5. **Patch and Update Regularly**
   - Keep all images and dependencies up to date.
   - Apply security patches promptly.

6. **Network Segmentation**
   - Use Docker networks to isolate services.
   - Only connect containers to networks they need.

7. **Least Privilege Principle**
   - Run containers as non-root users where possible.
   - Limit container capabilities and privileges.

8. **Healthchecks and Monitoring**
   - Implement healthchecks for all critical services.
   - Monitor logs and container health.
   - **CRITICAL**: Health check ports MUST match the service's configured listening port.
     - Example: If `external_url` is `http://host:8090`, health check must use `localhost:8090`
     - Default health checks often assume port 80; always verify when using non-standard ports.

9. **Firewall and Access Controls**
   - Restrict host firewall (UFW/iptables) to allow only trusted IPs.
   - Deny all other incoming connections by default.

10. **Audit and Review**
    - Regularly audit Docker Compose files, images, and running containers.
    - Remove unused containers, images, and volumes.

## Authentication and Authorization

11. **Keycloak as Central Identity Provider**
    - **Keycloak MUST be used** as the central authentication provider for ALL administrative interfaces.
    - Single Sign-On (SSO) is REQUIRED for all admin services.
    - Supported authentication methods:
      - Native OIDC/OAuth2 integration (preferred)
      - Traefik Forward Auth via OAuth2 Proxy (for services without native OIDC)
    - User: `mashfiqur.rahman` must have administrative access to all services.
    - Multi-Factor Authentication (MFA) should be enabled for administrative accounts.
    - Session timeouts and security policies are managed centrally in Keycloak.

## Enforcement

- All PRs and automated changes must be reviewed for compliance with this checklist.
- Copilot and other AI agents must reference this constitution and the checklist in `.github/copilot-instructions.md` for all code and config changes.
- **NEW SERVICES**: Any new administrative interface MUST integrate with Keycloak for authentication before deployment.
