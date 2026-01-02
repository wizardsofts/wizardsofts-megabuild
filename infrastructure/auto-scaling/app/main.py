from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import logging
import os
from datetime import datetime

# Import local modules
from autoscaler import AutoScaler
from docker_manager import DockerManager
from haproxy_manager import HAProxyManager
from scheduler import BusinessHoursScheduler
from config_model import load_and_validate_config, ConfigModel

# Import Prometheus metrics
from prometheus_client import make_asgi_app, Counter, Gauge, Histogram
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/autoscaler/logs/autoscaler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
# API request counter
api_requests_total = Counter(
    'api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)

# API request duration histogram
api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

# Scaling events counter
scaling_events_total = Counter(
    'scaling_events_total',
    'Total scaling events',
    ['service', 'action']  # action: scale_up, scale_down, health_remove
)

# Container count gauge
container_count = Gauge(
    'container_count',
    'Current container count per service',
    ['service']
)

app = FastAPI(title="Docker Auto-Scaler API", version="1.0.0")

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize components
autoscaler = AutoScaler()
docker_manager = DockerManager()
haproxy_manager = HAProxyManager()
scheduler = BusinessHoursScheduler()

# Pydantic models
class ServiceScaleRequest(BaseModel):
    replicas: Optional[int] = None

class ServiceConfig(BaseModel):
    name: str
    image: str
    port: int
    min_replicas: int
    max_replicas: int
    scale_up_threshold: int
    scale_down_threshold: int
    cooldown_period: int
    business_hours_only: bool
    health_check: Dict
    volumes: List[str]
    environment: List[str]

class ServerInfo(BaseModel):
    host: str
    name: str
    ssh_user: str
    ssh_port: int
    max_containers: int
    current_containers: int
    cpu_usage: float
    memory_usage: float

# Middleware to track metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    api_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response


# API Endpoints
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "running", "timestamp": datetime.utcnow()}

@app.get("/status")
async def get_status():
    """Overall system status"""
    return {
        "status": "running",
        "uptime": "N/A",  # Will be implemented
        "services": await autoscaler.get_service_stats(),
        "timestamp": datetime.utcnow()
    }

@app.get("/services")
async def get_services():
    """List all services with container counts"""
    return await autoscaler.get_service_stats()

@app.get("/services/{service_name}/stats")
async def get_service_stats(service_name: str):
    """Get detailed stats for a specific service"""
    try:
        stats = await autoscaler.get_service_detailed_stats(service_name)
        return stats
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found: {str(e)}")

@app.post("/services/{service_name}/scale/up")
async def manual_scale_up(service_name: str):
    """Manually scale up a service by 1 replica"""
    try:
        result = await autoscaler.manual_scale_up(service_name)
        return {"message": f"Scale up initiated for {service_name}", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scale up {service_name}: {str(e)}")

@app.post("/services/{service_name}/scale/down")
async def manual_scale_down(service_name: str):
    """Manually scale down a service by 1 replica"""
    try:
        result = await autoscaler.manual_scale_down(service_name)
        return {"message": f"Scale down initiated for {service_name}", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scale down {service_name}: {str(e)}")

@app.post("/services/{service_name}/restart")
async def restart_service(service_name: str):
    """Restart all containers for a service"""
    try:
        result = await autoscaler.restart_service(service_name)
        return {"message": f"Restart initiated for {service_name}", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to restart {service_name}: {str(e)}")

@app.get("/servers")
async def get_servers():
    """Get information about all servers"""
    try:
        servers_info = await docker_manager.get_all_servers_info()
        return servers_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server info: {str(e)}")

@app.get("/events")
async def get_events():
    """Get recent scaling events"""
    try:
        events = await autoscaler.get_recent_events(100)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")

@app.post("/config/reload")
async def reload_config():
    """Reload configuration without restarting"""
    try:
        autoscaler.reload_config()
        return {"message": "Configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    # This would return metrics in Prometheus format
    # Implementation depends on the metrics needed
    return {"message": "Metrics endpoint"}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Auto-Scaler API")
    
    # Initialize components
    await autoscaler.initialize()
    await docker_manager.initialize()
    await haproxy_manager.initialize()
    await scheduler.initialize()
    
    # Start the main autoscaling loop
    asyncio.create_task(autoscaler.start_scaling_loop())
    
    logger.info("Auto-Scaler API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Auto-Scaler API")
    await autoscaler.shutdown()
    logger.info("Auto-Scaler API shutdown complete")