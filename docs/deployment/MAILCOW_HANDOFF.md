# Mailcow Server Handoff & Documentation
**Date:** December 27, 2025
**Server:** 10.0.0.84 (GMK NucBox)

## 1. Access & Credentials

### Administrator Portal
- **URL:** [https://mail.wizardsofts.com](https://mail.wizardsofts.com) (Primary)
- **Alternate URL:** [https://mail.dailydeenguide.com](https://mail.dailydeenguide.com)
- **Username:** `wizardsofts`
- **Password:** `W1z4rdS0fts!2025`

> **Note:** The `admin` user has been renamed to `wizardsofts`.

### Webmail (SOGo)
- **URL:** [https://mail.wizardsofts.com/SOGo](https://mail.wizardsofts.com/SOGo)
- **Login:** Uses individual email account credentials (e.g., `user@wizardsofts.com`).
- **Master User:** Not configured (default).

---

## 2. Infrastructure Overview

Mailcow is deployed as a Dockerized stack on Server 84, sitting behind a Traefik reverse proxy.

### Network Flow
1.  **Traefik (Edge Router)**:
    *   Listens on ports 80 and 443.
    *   **HTTP (Port 80)**: Intercepts `/.well-known/acme-challenge/` requests and routes them to Mailcow's HTTP container for SSL validation. Redirects everything else to HTTPS.
    *   **HTTPS (Port 443)**: Uses **TCP Passthrough** (SNI) to route `mail.wizardsofts.com` and `mail.dailydeenguide.com` traffic directly to Mailcow's Nginx container. Traefik *does not* terminate TLS for Mailcow; Mailcow handles its own certificates.

### File Locations
- **Install Directory (Server 84):** `/home/wizardsofts/mailcow-dockerized`
- **Configuration File (Server 84):** `/home/wizardsofts/mailcow-dockerized/mailcow.conf`
- **Traefik Config (This Repo):** `traefik/dynamic_conf.yml` (Routes defined here)

---

## 3. SSL/TLS Certificates

Mailcow uses its own ACME (Let's Encrypt) container to manage certificates.

- **Domains Covered:**
    - `mail.wizardsofts.com` (Main Hostname)
    - `mail.dailydeenguide.com` (SAN - Subject Alternative Name)
- **Auto-Renewal:** Enabled. The `acme-mailcow` container runs daily checks.
- **Forcing Renewal:**
    If you add a new domain to `mailcow.conf` (under `ADDITIONAL_SAN`), run:
    ```bash
    cd /home/wizardsofts/mailcow-dockerized
    docker compose restart acme-mailcow
    docker logs -f mailcowdockerized-acme-mailcow-1
    ```

---

## 4. Common Management Tasks

### Restarting Services
```bash
cd /home/wizardsofts/mailcow-dockerized
docker compose restart
```

### Resetting Admin Password
If you lose access to the `wizardsofts` admin account:
1.  **Use the Helper Script:**
    ```bash
    cd /home/wizardsofts/mailcow-dockerized/helper-scripts
    sudo ./mailcow-reset-admin.sh
    ```
    *This will reset the user to `admin` with a random password.*

2.  **Manual Database Reset (Emergency Only):**
    ```bash
    # Generate SSHA256 Hash
    docker exec -it $(docker ps -qf name=dovecot-mailcow) doveadm pw -s SSHA256 -p "NEW_PASSWORD"

    # Update MySQL
    docker exec -it $(docker ps -qf name=mysql-mailcow) mysql -u mailcow -p$(grep DBPASS mailcow.conf | cut -d= -f2) mailcow
    > UPDATE admin SET password='{SSHA256}...' WHERE username='wizardsofts';
    ```

### Viewing Logs
```bash
# ACME / SSL Logs
docker logs mailcowdockerized-acme-mailcow-1

# Postfix (MTA) Logs
docker logs mailcowdockerized-postfix-mailcow-1

# Nginx (Web Server) Logs
docker logs mailcowdockerized-nginx-mailcow-1
```

---

## 5. Configuration Changes Summary (Dec 27, 2025)

1.  **Admin User Renamed:** Changed default `admin` user to `wizardsofts`.
2.  **Password Reset:** Updated admin password to standard project credential.
3.  **Multi-Domain SSL:** Added `mail.dailydeenguide.com` to `ADDITIONAL_SAN` in `mailcow.conf` so the certificate is valid for both domains.
4.  **Traefik Routing:** Verified `dynamic_conf.yml` correctly handles ACME challenges via HTTP and encrypted traffic via TCP Passthrough.
