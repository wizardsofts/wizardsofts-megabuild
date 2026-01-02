# Multi-Server Docker Auto-Scaling Platform

A complete autoscaling solution for managing Docker containers across multiple servers with business hours support and comprehensive monitoring.

## Features

- **Autoscaling**: Automatically scale containers based on CPU usage with configurable thresholds
- **Business Hours**: Configurable business hours with timezone support (scale only during specified times)
- **Load Balancing**: Dynamic HAProxy configuration with health checks
- **Health Monitoring**: Continuous health check and auto-removal of unhealthy containers
- **Monitoring**: Prometheus metrics collection and Grafana dashboard
- **CI/CD**: GitLab CI/CD pipeline with secure deployment
- **Configuration Validation**: Pydantic-based config validation with detailed error messages
- **Metrics**: Prometheus metrics for monitoring scaling events and performance
- **Security**: SSH key-based authentication, secure CI/CD pipeline

## Architecture

This system uses a hybrid load balancer approach where your existing nginx handles public-facing traffic while HAProxy manages internal autoscaling:

```
Internet → [nginx (public reverse proxy)] → [HAProxy (internal autoscaling LB)] → Service containers
```

```
┌─────────────────────────────────────────────────────────┐
│              Control Server (10.0.0.80)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   HAProxy    │  │  Autoscaler  │  │   Prometheus │  │
│  │     LB       │  │   FastAPI    │  │   + Grafana  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼─────────────────┬───────────┐
        │                   │                 │           │
┌───────▼────────┐  ┌───────▼────────┐  ┌────▼──────┐ ┌──▼────────┐
│   Server 1     │  │   Server 2     │  │ Server 3  │ │ Server 4  │
│   (Control)    │  │                │  │           │ │           │
│  Ollama x1     │  │  Ollama x2     │  │ Ollama x1 │ │ Ollama x1 │
│  App-A x1      │  │  App-A x1      │  │ App-B x1  │ │ App-C x1  │
└────────────────┘  └────────────────┘  └───────────┘ └───────────┘
```

**Recommended Production Setup**: Keep your existing `nginx` as the public-facing reverse proxy and use HAProxy internally for autoscaler-managed services only. This minimizes disruption while providing autoscaling capabilities for backend services.

## Configuration

### Timezone Support
Business hours can be configured with any timezone supported by the system:
```yaml
autoscaler:
  business_hours:
    start: "09:00"
    end: "17:00"
    timezone: "America/New_York"  # or "Asia/Dhaka", "Europe/London", etc.
```

### Container Placement Policy
The autoscaler uses a "least containers, then lowest CPU" placement strategy:
1. First, prefer servers with the fewest containers running for the service
2. Then, prefer servers with lower overall CPU utilization
3. Avoid overloading the control server unless necessary
This keeps distribution even while avoiding control-plane overload.

### Service Configuration
Each service can have individual scaling parameters:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    port: 11434
    min_replicas: 1
    max_replicas: 8
    scale_up_threshold: 75    # Scale up when avg CPU > 75%
    scale_down_threshold: 25  # Scale down when avg CPU < 25%
    cooldown_period: 60       # 60 seconds between scaling actions
    business_hours_only: true # Only scale during business hours
    health_check:
      path: /api/tags
      interval: 10
      timeout: 5
```

## Security Features

- **SSH Key Authentication**: All server communication uses SSH keys (no password authentication)
- **CI/CD Security**: GitLab variables are masked and protected
- **Input Validation**: All configuration is validated using Pydantic models
- **Metrics Protection**: Prometheus metrics are available at /metrics endpoint

## Monitoring

- **Autoscaler Metrics**: API request counters and duration histograms
- **Scaling Events**: Track all scaling actions with service and action labels
- **Container Count**: Gauge for current container counts per service
- **Health Checks**: Automatic removal of unhealthy containers

## Deployment

1. **Prerequisites**: 4 servers on local network with Docker and SSH access
2. **Setup**: Run `scripts/setup.sh` on control server
3. **Configuration**: Update `config.yaml` with server details
4. **Deploy**: Run `deploy_control_plane.sh` followed by `deploy_ollama.sh`
5. **Monitoring**: Access Grafana at http://10.0.0.80:3000

## CI/CD Pipeline

The GitLab CI/CD pipeline includes:
- Configuration validation
- Docker image building and pushing
- Secure deployment using masked variables
- Manual deployment trigger to prevent accidental deploys

**Current Status**: CI pipeline is set up for validation purposes only. Deployment stage is disabled until credentials and infrastructure are properly configured.

## Testing

Unit tests are available in the `tests/` directory:
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_config.py
```

## Maintenance

- **Daily**: Automatic config backups at 2:00 AM
- **Weekly**: Health checks and error log reviews
- **Monthly**: Docker image updates and resource usage review
- **Quarterly**: Full system audit and security review

## API Endpoints

- `GET /` - Health check
- `GET /status` - Overall system status
- `GET /services` - List all services
- `GET /services/{name}/stats` - Service statistics
- `POST /services/{name}/scale/up` - Manual scale up
- `POST /services/{name}/scale/down` - Manual scale down
- `POST /config/reload` - Reload configuration
- `GET /metrics` - Prometheus metrics
- `GET /events` - Recent scaling events

## Troubleshooting

If experiencing issues:
1. Check logs: `docker-compose logs -f autoscaler`
2. Validate config: Navigate to the app directory and run - `cd /opt/autoscaler/app && python -c "from config_model import load_and_validate_config; load_and_validate_config('/opt/autoscaler/config.yaml')"`
3. Check HAProxy: `curl http://10.0.0.80:8404/`
4. Verify business hours: `curl http://10.0.0.80:8000/`