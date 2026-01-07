# Technical Brief: Server 84 Monitoring & Infrastructure

## 1. Current Infrastructure (What We Have)
We have successfully deployed a robust, multi-service infrastructure on Server 84 (`10.0.0.84`) capable of mail hosting, reverse proxying, and full-stack observability.

### Core Services
*   **Mailcow**: Full email stack deployed.
    *   **Domains**: `mail.wizardsofts.com`, `mail.dailydeenguide.com`.
    *   **Routing**: Integrated with Traefik via TCP (port 443) and HTTP (port 80) passthrough.
*   **Traefik**: Edge router handling SSL termination and routing for all services.
*   **HAProxy**: Load balancer for the autoscaling application.

### Observability Stack (Fully Deployed)
We have implemented the "Observability Tripod" (Logs & Metrics):
*   **Prometheus (Metrics)**: Scrapes numerical data for trending and alerting.
    *   *Targets*: HAProxy, Autoscaler, cAdvisor, Node Exporter.
*   **Loki + Promtail (Logs)**: Centralized log aggregation.
    *   *Source*: Promtail ships Docker container logs to Loki.
    *   *Volume*: Correctly mapped to Snap Docker paths.
*   **Grafana (Visualization)**: Dashboard UI running on port `3002`.
    *   *Datasources*: Connected to both Prometheus and Loki.
*   **Server Health Agents**:
    *   **Node Exporter (Port 9100)**: Monitors Host OS metrics (CPU, RAM, Disk I/O).
    *   **cAdvisor (Port 8085)**: Monitors Docker container resource usage.

### Security
*   **UFW Firewall**: Enabled.
    *   **Public**: Ports 22 (SSH), 80 (HTTP), 443 (HTTPS).
    *   **Private/Local**: Port 3002 (Grafana) restricted to local subnets (`10.x`, `172.x`, `192.x`).

---

## 2. Gap Analysis (What We Need to Add)
The infrastructure is functional, but specific configurations are needed to finalize production readiness.

### Critical Action Items
1.  **Mailcow DNS Resolution**:
    *   **Status**: Blocked.
    *   **Action**: Manually delete the conflicting `CNAME` record for `mail.wizardsofts.com` in AWS Route53. This allows the automated script to create the correct `A` record pointing to Server 84.
2.  **Mailcow Metrics Integration**:
    *   **Status**: Missing.
    *   **Action**: Configure Prometheus to scrape Mailcow's internal metrics (Postfix, Dovecot, Nginx) for email-specific monitoring (queue length, rejected mails).
3.  **Dashboards**:
    *   **Status**: Basic.
    *   **Action**: Import specific Grafana dashboards for:
        *   **Docker Containers** (visualizing cAdvisor data).
        *   **Node Exporter** (visualizing Host OS health).
        *   **Mailcow** (visualizing email stats).
4.  **Alerting Rules**:
    *   **Status**: None.
    *   **Action**: Define critical alerts in Prometheus (e.g., "High CPU," "Mail Queue Full," "Site Down") and configure notification channels (e.g., Slack, Email).
