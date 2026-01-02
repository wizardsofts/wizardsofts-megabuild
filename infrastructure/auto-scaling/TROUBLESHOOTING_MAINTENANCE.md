# Troubleshooting Procedures and Maintenance Schedule
## Multi-Server Docker Auto-Scaling Platform

### Table of Contents
1. [Troubleshooting Guide](#troubleshooting-guide)
2. [Maintenance Schedule](#maintenance-schedule)
3. [System Monitoring](#system-monitoring)
4. [Performance Optimization](#performance-optimization)

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: Autoscaler won't start
**Symptoms:**
- `docker-compose logs autoscaler` shows startup errors
- API endpoint `http://10.0.0.80:8000/` is not responding

**Solutions:**
1. Check the configuration file syntax:
   ```bash
   yamllint /opt/autoscaler/config.yaml
   ```

2. Verify SSH connectivity to all servers:
   ```bash
   ssh wizardsofts@10.0.0.81 "hostname"
   ssh wizardsofts@10.0.0.84 "hostname"
   ssh -p 2025 deploy@10.0.0.82 "hostname"
   ```

3. Check if Docker socket is accessible (from the autoscaler container):
   ```bash
   docker exec autoscaler ls -l /var/run/docker.sock
   ```

4. Verify all required dependencies:
   ```bash
   cd /opt/autoscaler/app
   pip install -r requirements.txt
   ```

5. Restart the autoscaler:
   ```bash
   docker-compose restart autoscaler
   ```

#### Issue: Containers not scaling
**Symptoms:**
- Container count remains constant regardless of load
- No scaling events in `/events` endpoint
- CPU monitoring seems incorrect

**Solutions:**
1. Check if business hours are preventing scaling:
   ```bash
   curl http://10.0.0.80:8000/
   ```

2. Verify the scaling thresholds in the configuration:
   ```bash
   curl http://10.0.0.80:8000/services/ollama/stats
   ```

3. Check logs for scaling decisions:
   ```bash
   docker-compose logs autoscaler | grep -i scale
   ```

4. Verify the check interval and cooldown settings:
   - Check `check_interval` in config.yaml (default: 30s)
   - Check `cooldown_period` in config.yaml (default: 60s)

#### Issue: Load balancer not routing traffic
**Symptoms:**
- HAProxy stats page accessible but no backend servers
- Requests to service endpoints timeout
- HAProxy configuration appears empty

**Solutions:**
1. Check HAProxy configuration:
   ```bash
   docker exec haproxy cat /usr/local/etc/haproxy/haproxy.cfg
   ```

2. Verify that Ollama containers are running and accessible:
   ```bash
   for server in 10.0.0.80 10.0.0.81 10.0.0.82 10.0.0.84; do
       echo "Checking $server:"
       ssh -p $(if [ "$server" = "10.0.0.82" ]; then echo "2025"; else echo "22"; fi) $(if [ "$server" = "10.0.0.82" ]; then echo "deploy"; else echo "wizardsofts"; fi)@$server "docker ps | grep ollama"
   done
   ```

3. Verify HAProxy can reach the backend servers:
   ```bash
   docker exec haproxy netstat -tuln
   ```

4. Check HAProxy logs:
   ```bash
   docker-compose logs haproxy
   ```

#### Issue: High resource usage
**Symptoms:**
- Control server consuming excessive CPU/RAM
- Slow API responses
- General system sluggishness

**Solutions:**
1. Check which component is consuming resources:
   ```bash
   docker stats
   ```

2. If autoscaler is using too much CPU:
   - Increase `check_interval` in config.yaml
   - Reduce the frequency of health checks

3. If Prometheus is using too much RAM/disk:
   - Reduce `retention` period in config
   - Reduce scrape frequency in prometheus.yml

4. Monitor resource usage:
   ```bash
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

#### Issue: SSH connection failures
**Symptoms:**
- Docker manager fails to connect to remote servers
- Error messages about SSH connectivity
- Autoscaler reports server as unavailable

**Solutions:**
1. Verify SSH keys are properly set up:
   ```bash
   ssh -T wizardsofts@10.0.0.81
   ssh -T -p 2025 deploy@10.0.0.82
   ```

2. Check SSH configuration on target servers:
   ```bash
   # On target server
   sudo systemctl status ssh
   sudo cat /etc/ssh/sshd_config | grep "^Port\|^PasswordAuthentication\|^PubkeyAuthentication"
   ```

3. Verify correct key paths in config.yaml

4. Check network connectivity:
   ```bash
   ping 10.0.0.81
   ```

### Advanced Troubleshooting

#### Log Analysis
Useful log monitoring commands:
```bash
# Monitor autoscaler in real-time
docker-compose logs -f autoscaler

# Monitor all services
docker-compose logs -f --tail=100

# Check specific error patterns
docker-compose logs autoscaler | grep -E "(ERROR|CRITICAL|Exception)"
```

#### Container Health Checks
Check individual container status:
```bash
# Check if containers are running properly
docker ps

# Check container logs
docker logs <container_name>

# Check container stats
docker stats <container_name>
```

#### Configuration Validation
Validate configuration files:
```bash
# Validate YAML syntax
yamllint /opt/autoscaler/config.yaml

# Validate Docker Compose file
docker-compose config

# Check if config has been loaded properly
curl http://10.0.0.80:8000/servers
```

## Maintenance Schedule

### Daily Operations (Automated)
- **Config backup**: Performed every day at 2:00 AM automatically via cron
- **Log rotation**: Built into Docker/compose setup
- **Health monitoring**: System monitors itself continuously

### Weekly Tasks (5 minutes)
```bash
# 1. Check system status
curl http://10.0.0.80:8000/status

# 2. Review logs for errors
docker-compose logs --tail=50 autoscaler | grep -i error

# 3. Check disk space
df -h /opt/autoscaler /data

# 4. Verify service containers
curl http://10.0.0.80:8000/services
```

### Monthly Tasks (30 minutes)
```bash
# 1. Update Docker images
cd /opt/autoscaler
docker-compose pull
docker-compose up -d

# 2. Clean up old Docker objects
docker system prune -f

# 3. Review Grafana dashboards for anomalies
# Access via http://10.0.0.80:3000

# 4. Review backup integrity
ls -lh /opt/autoscaler/backup/

# 5. Check system resource trends
docker stats --no-stream

# 6. Update Python dependencies (if needed)
cd /opt/autoscaler/app
pip list --outdated
```

### Quarterly Tasks (1 hour)
```bash
# 1. Full system audit
# Review all configurations
# Update any deprecated settings

# 2. Test disaster recovery
# Verify backup restoration works
# Test failover scenarios

# 3. Performance review
# Check scaling thresholds are still appropriate
# Review resource usage patterns

# 4. Security review
# Update SSH keys if needed
# Review access controls
# Check for security updates
```

### Maintenance Scripts

#### Health Check Script
Run the automated health check:
```bash
/opt/autoscaler/scripts/health_check.sh
```

#### Backup Script
Manual backup (automated backup runs daily):
```bash
/opt/autoscaler/scripts/backup.sh
```

#### System Status
Quick system overview:
```bash
# Check all services
docker-compose ps

# Check autoscaler status
curl http://10.0.0.80:8000/status

# Check service statistics
curl http://10.0.0.80:8000/services/ollama/stats | jq
```

## System Monitoring

### Dashboard Access
- **HAProxy Stats**: http://10.0.0.80:8404
- **Grafana Dashboard**: http://10.0.0.80:3000 (admin/admin)
- **Prometheus**: http://10.0.0.80:9090
- **Autoscaler API**: http://10.0.0.80:8000

### Key Metrics to Monitor
1. **Container Count**: Should fluctuate based on demand
2. **CPU Usage**: Triggers scaling actions
3. **Health Check Failures**: Indicate backend issues
4. **API Response Times**: Should be < 2 seconds
5. **System Resource Usage**: < 150MB RAM for control plane

### Alerting Guidelines
**Critical (requires immediate attention):**
- Autoscaler API not responding
- No active Ollama containers when needed
- System using > 500MB RAM
- All servers unreachable via SSH

**Warning (monitor closely):**
- Scaling at maximum container limit
- High API response times (> 5 seconds)
- Individual server not responding

**Info (normal operations):**
- Scaling events during business hours
- Regular backup completion
- Minor fluctuations in container count

## Performance Optimization

### Configuration Tuning
1. **Check Interval**: If system resources are tight, increase `check_interval` (default: 30s)
2. **Cooldown Period**: Adjust `cooldown_period` to prevent rapid scaling (default: 60s)
3. **Resource Limits**: Set appropriate limits in Docker Compose if needed

### Resource Management
```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Set resource limits in docker-compose.yml if needed
# Add to service definitions:
#   deploy:
#     resources:
#       limits:
#         memory: 256M
#         cpus: '0.5'
```

### Log Management
- By default, logs are stored in `/opt/autoscaler/logs/`
- Use log rotation to manage disk space
- Monitor log sizes to prevent disk space issues