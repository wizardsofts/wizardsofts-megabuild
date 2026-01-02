# Deployment Checklist
## Multi-Server Docker Auto-Scaling Platform

### Pre-Deployment Verification

#### Infrastructure Requirements
- [ ] All 4 servers are accessible via SSH with key authentication:
  - [ ] 10.0.0.80 (Control Server, user: wizardsofts, port: 22)
  - [ ] 10.0.0.81 (Worker, user: wizardsofts, port: 22)
  - [ ] 10.0.0.82 (Worker, user: deploy, port: 2025)
  - [ ] 10.0.0.84 (Worker, user: wizardsofts, port: 22)
- [ ] Docker is installed and running on all servers
- [ ] GitLab instance is accessible for CI/CD
- [ ] Sufficient disk space on all servers
- [ ] Network connectivity between all servers verified

#### Files and Configurations
- [ ] `/opt/autoscaler/config.yaml` contains correct server details and service configurations
- [ ] SSH keys properly configured for cross-server access
- [ ] All application files are in place:
  - [ ] `/opt/autoscaler/app/main.py`
  - [ ] `/opt/autoscaler/app/autoscaler.py`
  - [ ] `/opt/autoscaler/app/docker_manager.py`
  - [ ] `/opt/autoscaler/app/haproxy_manager.py`
  - [ ] `/opt/autoscaler/app/scheduler.py`
  - [ ] `/opt/autoscaler/app/requirements.txt`
- [ ] Docker images available or can be pulled
- [ ] HAProxy configuration file is in place: `/opt/autoscaler/haproxy/haproxy.cfg`
- [ ] Docker Compose file exists: `/opt/autoscaler/docker-compose.yml`

### Deployment Steps

#### Step 1: Deploy Control Plane
- [ ] Run the control plane deployment script: `./deploy_control_plane.sh`
- [ ] Verify all services are running: `docker-compose ps`
- [ ] Confirm API is accessible: `curl http://localhost:8000/`
- [ ] Verify HAProxy stats: `curl http://localhost:8404/`
- [ ] Confirm Prometheus health: `curl http://localhost:9090/-/healthy`
- [ ] Confirm Grafana health: `curl http://localhost:3000/api/health`

#### Step 2: Deploy Ollama Service
- [ ] Run the Ollama deployment script: `./deploy_ollama.sh`
- [ ] Verify Ollama containers are running on all servers:
  - [ ] `ssh wizardsofts@10.0.0.80 "docker ps | grep ollama"`
  - [ ] `ssh wizardsofts@10.0.0.81 "docker ps | grep ollama"`
  - [ ] `ssh -p 2025 deploy@10.0.0.82 "docker ps | grep ollama"`
  - [ ] `ssh wizardsofts@10.0.0.84 "docker ps | grep ollama"`
- [ ] Verify load balancer routes to Ollama: `curl http://10.0.0.80:11434/api/tags`

#### Step 3: Deploy cAdvisor for Monitoring
- [ ] Run cAdvisor deployment script: `./deploy_cadvisor.sh`
- [ ] Verify cAdvisor is accessible on all servers:
  - [ ] `curl http://10.0.0.80:8080/metrics`
  - [ ] `curl http://10.0.0.81:8080/metrics`
  - [ ] `curl http://10.0.0.82:8080/metrics`
  - [ ] `curl http://10.0.0.84:8080/metrics`
- [ ] Verify Prometheus is scraping cAdvisor metrics

#### Step 4: Configure Auto-Start Service
- [ ] Run the systemd service setup: `./setup_systemd_service.sh`
- [ ] Verify the service is enabled: `systemctl is-enabled autoscaler.service`
- [ ] Check the service status: `systemctl status autoscaler.service`

#### Step 5: Test Auto-Scaling Functionality
- [ ] Run the autoscaling test: `./test_autoscaling.sh`
- [ ] Verify scaling thresholds are appropriate for your workload
- [ ] Confirm business hours configuration is correct
- [ ] Test manual scaling via API: `curl -X POST http://10.0.0.80:8000/services/ollama/scale/up`

#### Step 6: Test CI/CD Pipeline
- [ ] Review the GitLab CI/CD configuration: `.gitlab-ci.yml`
- [ ] Set up GitLab CI/CD variables:
  - [ ] `SSH_PRIVATE_KEY`
  - [ ] `CI_REGISTRY`
  - [ ] `CI_REGISTRY_USER`
  - [ ] `CI_REGISTRY_PASSWORD`
- [ ] Run CI/CD test script: `./test_ci_cd.sh`

### Post-Deployment Verification

#### Service Functionality
- [ ] All 4 servers are visible in the API: `curl http://10.0.0.80:8000/servers`
- [ ] Services are listed correctly: `curl http://10.0.0.80:8000/services`
- [ ] Service statistics are accessible: `curl http://10.0.0.80:8000/services/ollama/stats`
- [ ] Manual scaling works: `curl -X POST http://10.0.0.80:8000/services/ollama/scale/up`
- [ ] Load balancer distributes requests across all Ollama instances

#### Monitoring and Alerts
- [ ] Grafana dashboard is accessible and shows metrics
- [ ] Prometheus shows all targets as healthy
- [ ] All servers appear in cAdvisor monitoring
- [ ] Historical metrics are being collected

#### System Resources
- [ ] Control plane uses < 150MB RAM: `docker stats --no-stream`
- [ ] System responds within expected timeframes
- [ ] No memory leaks detected after 30 minutes of operation
- [ ] Disk space usage is reasonable on all servers

#### Security Verification
- [ ] Only SSH key authentication is used (no passwords)
- [ ] Docker socket access is properly restricted
- [ ] Network ports are properly configured and secured
- [ ] API endpoints are not exposed to public internet (if applicable)

### Operational Validation

#### Business Hours Logic
- [ ] Scaling only occurs during configured business hours
- [ ] Manual scaling works outside business hours
- [ ] System respects timezone configuration

#### Failover Testing
- [ ] Verify system continues to operate if one worker server fails
- [ ] Test container crash recovery
- [ ] Verify autoscaler restart recovery
- [ ] Test configuration reload functionality

#### Performance Testing
- [ ] System handles expected peak load
- [ ] Scaling decisions happen within expected timeframes
- [ ] API response times are acceptable (< 2 seconds)
- [ ] No resource exhaustion under load

### Configuration Finalization

#### Customizations
- [ ] Update scaling thresholds in `config.yaml` if needed for your specific workload
- [ ] Adjust business hours in `config.yaml` to match your schedule
- [ ] Set appropriate min/max replicas for your services
- [ ] Configure cooldown periods to prevent rapid scaling

#### Documentation Review
- [ ] Verify Quick Reference Guide (`QUICKREF.md`) has correct server IPs
- [ ] Confirm troubleshooting procedures match your setup
- [ ] Review maintenance schedule and tasks
- [ ] Ensure backup procedures are tested and working

### Go-Live Checklist

#### Final Preparations
- [ ] All tests pass successfully
- [ ] System meets performance requirements
- [ ] Monitoring dashboards are set up and accessible
- [ ] Maintenance scripts are tested and working
- [ ] Backup cron job is configured and tested
- [ ] System auto-start is configured and verified

#### Documentation Update
- [ ] Update server IP addresses in all documentation if different from defaults
- [ ] Verify Grafana credentials are documented
- [ ] Confirm all configuration parameters are documented
- [ ] Ensure troubleshooting procedures are accurate for your setup

#### Handoff Preparation
- [ ] Create a summary document of the deployment
- [ ] Document any customizations made during deployment
- [ ] Provide access information for monitoring systems
- [ ] Supply emergency contact information for support

### Success Criteria Verification

#### Setup Success
- [ ] Complete setup in < 4 hours
- [ ] All 4 servers reporting healthy
- [ ] Dashboard accessible at http://10.0.0.80:3000
- [ ] Ollama responds through load balancer at http://10.0.0.80:11434

#### Operational Success
- [ ] Zero manual scaling interventions per week (autonomous operation)
- [ ] Deployments complete in < 15 minutes via CI/CD
- [ ] System overhead < 150MB RAM on control server
- [ ] < 2 hours maintenance per month

#### Reliability Success
- [ ] > 99% uptime (business hours)
- [ ] Auto-recovery from single server failure
- [ ] No data loss from crashes
- [ ] Quick recovery from system failures

### Emergency Procedures Reference

#### Immediate Actions
- **System Down**: `docker-compose restart` in `/opt/autoscaler`
- **No Scaling**: Check logs: `docker-compose logs autoscaler`
- **Load Balancer Down**: Verify HAProxy: `docker-compose logs haproxy`
- **API Unresponsive**: Check autoscaler: `docker-compose logs autoscaler`

#### Critical Commands
```bash
# System status
docker-compose ps

# Main logs
docker-compose logs -f autoscaler

# Service control
docker-compose restart autoscaler

# Full restart
docker-compose down && docker-compose up -d

# Configuration reload
curl -X POST http://10.0.0.80:8000/config/reload

# Manual scale
curl -X POST http://10.0.0.80:8000/services/ollama/scale/up
```

---

**Deployment Complete**: Once all checklists are verified, the system is ready for production use.