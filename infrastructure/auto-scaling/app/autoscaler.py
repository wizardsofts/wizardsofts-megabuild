import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from docker_manager import DockerManager
from scheduler import BusinessHoursScheduler
from haproxy_manager import HAProxyManager
import sys
from pathlib import Path
# Add the app directory to Python path to allow imports
sys.path.append(str(Path(__file__).parent))

from config_model import load_and_validate_config, ConfigModel, ServiceConfigModel
from service_config import ServiceConfig
import json

logger = logging.getLogger(__name__)

@dataclass
class ScalingEvent:
    service_name: str
    action: str  # 'scale_up', 'scale_down', 'no_action'
    from_count: int
    to_count: int
    reason: str
    timestamp: datetime

class AutoScaler:
    def __init__(self):
        self.config: Optional[ConfigModel] = None
        self.services: Dict[str, ServiceConfig] = {}
        self.docker_manager = DockerManager()
        self.haproxy_manager = HAProxyManager()
        self.scheduler = BusinessHoursScheduler()
        self.scaling_cooldowns: Dict[str, float] = {}  # service_name: last_scale_time
        self.scaling_events: List[ScalingEvent] = []
        self.scaling_loop_task = None
        self.check_interval = 30  # seconds
        self.is_scaling_active = True
        
    async def initialize(self):
        """Initialize the autoscaler with configuration"""
        await self.load_config()
        await self.docker_manager.initialize()
        await self.haproxy_manager.initialize()
        await self.scheduler.initialize()
        logger.info("AutoScaler initialized successfully")
    
    async def load_config(self):
        """Load and validate configuration from config.yaml"""
        try:
            # Use the new config model for validation
            validated_config = load_and_validate_config('/opt/autoscaler/config.yaml')
            self.config = validated_config
            
            # Parse service configurations from validated model
            self.services = {}
            for service_name, service_model in validated_config.services.items():
                self.services[service_name] = ServiceConfig(
                    name=service_name,
                    image=service_model.image,
                    port=service_model.port,
                    min_replicas=service_model.min_replicas,
                    max_replicas=service_model.max_replicas,
                    scale_up_threshold=service_model.scale_up_threshold,
                    scale_down_threshold=service_model.scale_down_threshold,
                    cooldown_period=service_model.cooldown_period,
                    business_hours_only=service_model.business_hours_only,
                    health_check=service_model.health_check.dict(),
                    volumes=service_model.volumes,
                    environment=service_model.environment
                )
            
            # Set check interval from config
            self.check_interval = validated_config.autoscaler.check_interval
            
            logger.info(f"Loaded {len(self.services)} services from validated config")
        except Exception as e:
            logger.error(f"Failed to load and validate config: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration without restarting"""
        old_services = set(self.services.keys())
        self.load_config()
        new_services = set(self.services.keys())
        
        # Log changes
        added = new_services - old_services
        removed = old_services - new_services
        
        if added:
            logger.info(f"Added services: {added}")
        if removed:
            logger.info(f"Removed services: {removed}")
        
        logger.info("Configuration reloaded successfully")
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get basic stats for all services"""
        stats = {}
        
        for service_name, service_config in self.services.items():
            try:
                container_count = await self.docker_manager.get_service_container_count(service_name)
                stats[service_name] = {
                    'container_count': container_count,
                    'min_replicas': service_config.min_replicas,
                    'max_replicas': service_config.max_replicas,
                    'scale_up_threshold': service_config.scale_up_threshold,
                    'scale_down_threshold': service_config.scale_down_threshold
                }
            except Exception as e:
                logger.error(f"Error getting stats for {service_name}: {e}")
                stats[service_name] = {'error': str(e)}
        
        return stats
    
    async def get_service_detailed_stats(self, service_name: str) -> Dict[str, Any]:
        """Get detailed stats for a specific service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in configuration")
        
        service_config = self.services[service_name]
        
        try:
            containers = await self.docker_manager.get_service_containers(service_name)
            container_details = []
            
            total_cpu = 0
            container_count = 0
            
            for container in containers:
                # Get container details
                container_info = {
                    'id': container.short_id,
                    'status': container.status,
                    'names': container.name,
                    'ports': str(container.ports) if container.ports else 'N/A',
                    'created': container.attrs.get('Created', 'N/A')
                }
                
                # Get CPU usage if possible
                try:
                    stats = container.stats(stream=False)
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                    
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                        container_info['cpu_percent'] = round(cpu_percent, 2)
                        total_cpu += cpu_percent
                        container_count += 1
                except:
                    container_info['cpu_percent'] = 'N/A'
                
                container_details.append(container_info)
            
            avg_cpu = total_cpu / container_count if container_count > 0 else 0
            
            return {
                'service_name': service_name,
                'container_count': len(containers),
                'min_replicas': service_config.min_replicas,
                'max_replicas': service_config.max_replicas,
                'scale_up_threshold': service_config.scale_up_threshold,
                'scale_down_threshold': service_config.scale_down_threshold,
                'avg_cpu': round(avg_cpu, 2),
                'containers': container_details,
                'cooldown_remaining': self.get_cooldown_remaining(service_name),
                'is_business_hours': await self.scheduler.is_business_hours(),
                'scaling_enabled': not service_config.business_hours_only or await self.scheduler.is_business_hours()
            }
        except Exception as e:
            logger.error(f"Error getting detailed stats for {service_name}: {e}")
            raise
    
    def get_cooldown_remaining(self, service_name: str) -> float:
        """Get remaining cooldown time for a service"""
        if service_name not in self.scaling_cooldowns:
            return 0
        
        elapsed = time.time() - self.scaling_cooldowns[service_name]
        cooldown_period = self.services[service_name].cooldown_period
        
        remaining = max(0, cooldown_period - elapsed)
        return round(remaining, 2)
    
    async def can_scale(self, service_name: str) -> bool:
        """Check if scaling is allowed for a service (cooldown and business hours)"""
        # Check cooldown
        if service_name in self.scaling_cooldowns:
            elapsed = time.time() - self.scaling_cooldowns[service_name]
            if elapsed < self.services[service_name].cooldown_period:
                return False
        
        # Check business hours if required
        service_config = self.services[service_name]
        if service_config.business_hours_only:
            is_business_hours = await self.scheduler.is_business_hours()
            return is_business_hours
        
        return True
    
    async def manual_scale_up(self, service_name: str) -> Dict[str, Any]:
        """Manually scale up a service by 1 replica"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in configuration")
        
        service_config = self.services[service_name]
        
        # Check if we're at max replicas
        current_count = await self.docker_manager.get_service_container_count(service_name)
        if current_count >= service_config.max_replicas:
            return {
                'success': False,
                'message': f'Already at max replicas ({service_config.max_replicas})'
            }
        
        # Deploy a new container
        try:
            container = await self.docker_manager.deploy_container(service_config)
            self._record_scaling_event(service_name, 'scale_up', current_count, current_count + 1, 'manual scale up')
            
            # Update HAProxy configuration to include the new container
            try:
                updated_containers = await self.docker_manager.get_service_containers(service_name)
                await self.haproxy_manager.update_backend_servers(service_name, updated_containers)
                logger.info(f"HAProxy configuration updated for {service_name} after manual scale up")
            except Exception as haproxy_error:
                logger.error(f"Failed to update HAProxy after manual scale up: {haproxy_error}")
            
            return {
                'success': True,
                'message': f'Container deployed for {service_name}',
                'container_id': container.id
            }
        except Exception as e:
            logger.error(f"Failed to manually scale up {service_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to scale up: {str(e)}'
            }
    
    async def manual_scale_down(self, service_name: str) -> Dict[str, Any]:
        """Manually scale down a service by 1 replica"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in configuration")
        
        service_config = self.services[service_name]
        
        # Check if we're at min replicas
        current_count = await self.docker_manager.get_service_container_count(service_name)
        if current_count <= service_config.min_replicas:
            return {
                'success': False,
                'message': f'At min replicas ({service_config.min_replicas})'
            }
        
        # Stop a container
        try:
            stopped_container = await self.docker_manager.stop_service_container(service_name)
            if stopped_container:
                self._record_scaling_event(service_name, 'scale_down', current_count, current_count - 1, 'manual scale down')
                
                # Update HAProxy configuration to remove the container from backend
                try:
                    updated_containers = await self.docker_manager.get_service_containers(service_name)
                    await self.haproxy_manager.update_backend_servers(service_name, updated_containers)
                    logger.info(f"HAProxy configuration updated for {service_name} after manual scale down")
                except Exception as haproxy_error:
                    logger.error(f"Failed to update HAProxy after manual scale down: {haproxy_error}")
                
                return {
                    'success': True,
                    'message': f'Container stopped for {service_name}',
                    'container_id': stopped_container.id
                }
            else:
                return {
                    'success': False,
                    'message': 'No container found to stop'
                }
        except Exception as e:
            logger.error(f"Failed to manually scale down {service_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to scale down: {str(e)}'
            }
    
    async def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart all containers for a service"""
        if service_name not in self.services:
            raise ValueError(f"Service {service_name} not found in configuration")
        
        try:
            result = await self.docker_manager.restart_service_containers(service_name)
            return {
                'success': True,
                'message': f'Restarted {result} containers for {service_name}'
            }
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return {
                'success': False,
                'message': f'Failed to restart service: {str(e)}'
            }
    
    def _record_scaling_event(self, service_name: str, action: str, from_count: int, to_count: int, reason: str):
        """Record a scaling event"""
        event = ScalingEvent(
            service_name=service_name,
            action=action,
            from_count=from_count,
            to_count=to_count,
            reason=reason,
            timestamp=datetime.now()
        )
        self.scaling_events.append(event)
        
        # Keep only last 100 events
        if len(self.scaling_events) > 100:
            self.scaling_events = self.scaling_events[-100:]
        
        # Update Prometheus metrics
        from main import scaling_events_total, container_count
        scaling_events_total.labels(service=service_name, action=action).inc()
        container_count.labels(service=service_name).set(to_count)
        
        logger.info(f"Scaling event: {service_name} {action} from {from_count} to {to_count} - {reason}")
    
    async def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent scaling events"""
        events = []
        for event in self.scaling_events[-count:]:
            events.append({
                'service_name': event.service_name,
                'action': event.action,
                'from_count': event.from_count,
                'to_count': event.to_count,
                'reason': event.reason,
                'timestamp': event.timestamp.isoformat()
            })
        return events
    
    async def start_scaling_loop(self):
        """Main scaling loop - runs continuously"""
        logger.info("Starting scaling loop")
        
        while self.is_scaling_active:
            try:
                # Run scaling logic for each service
                for service_name in self.services:
                    await self._evaluate_scaling(service_name)
                
                # Wait for the next check
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")
                await asyncio.sleep(10)  # Wait a bit before retrying
    
    async def _evaluate_scaling(self, service_name: str):
        """Evaluate if scaling is needed for a service"""
        if not await self.can_scale(service_name):
            return  # Skip if in cooldown or outside business hours
        
        service_config = self.services[service_name]
        current_count = await self.docker_manager.get_service_container_count(service_name)
        
        # Calculate average CPU across all containers of this service
        avg_cpu = await self._get_service_avg_cpu(service_name)
        
        should_scale_up = avg_cpu >= service_config.scale_up_threshold
        should_scale_down = avg_cpu <= service_config.scale_down_threshold
        can_scale_up = current_count < service_config.max_replicas
        can_scale_down = current_count > service_config.min_replicas
        
        # Perform scaling actions
        if should_scale_up and can_scale_up:
            await self._scale_up(service_name)
        elif should_scale_down and can_scale_down and avg_cpu > 0:  # Only scale down if CPU is being measured properly
            await self._scale_down(service_name)
    
    async def _get_service_avg_cpu(self, service_name: str) -> float:
        """Get average CPU usage across all containers of a service"""
        containers = await self.docker_manager.get_service_containers(service_name)
        
        if not containers:
            return 0.0
        
        total_cpu = 0.0
        valid_samples = 0
        
        for container in containers:
            try:
                stats = container.stats(stream=False)
                # Calculate CPU percentage (simplified)
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
                    total_cpu += cpu_percent
                    valid_samples += 1
            except:
                # If we can't get stats for a container, skip it
                continue
        
        return total_cpu / valid_samples if valid_samples > 0 else 0.0

    async def _perform_health_checks(self):
        """Perform health checks on all service containers and remove unhealthy ones"""
        for service_name, service_config in self.services.items():
            containers = await self.docker_manager.get_service_containers(service_name)
            
            for container in containers:
                is_healthy = await self._check_container_health(container, service_config)
                
                if not is_healthy:
                    logger.warning(f"Container {container.get('id', 'unknown')} for service {service_name} is unhealthy, removing...")
                    try:
                        # Stop and remove the unhealthy container
                        stopped_container = await self.docker_manager.stop_service_container(service_name, specific_container=container)
                        if stopped_container:
                            logger.info(f"Removed unhealthy container {stopped_container.id} for service {service_name}")
                            
                            # Record the event
                            current_count = await self.docker_manager.get_service_container_count(service_name)
                            self._record_scaling_event(
                                service_name, 
                                'health_remove', 
                                current_count + 1,  # We removed one, so previous count was +1
                                current_count, 
                                'Container removed due to health check failure'
                            )
                            
                            # Update HAProxy configuration to remove the unhealthy container from backend
                            try:
                                updated_containers = await self.docker_manager.get_service_containers(service_name)
                                await self.haproxy_manager.update_backend_servers(service_name, updated_containers)
                                logger.info(f"HAProxy configuration updated for {service_name} after removing unhealthy container")
                            except Exception as haproxy_error:
                                logger.error(f"Failed to update HAProxy after removing unhealthy container: {haproxy_error}")
                    except Exception as e:
                        logger.error(f"Failed to remove unhealthy container {container.get('id', 'unknown')}: {e}")

    async def _check_container_health(self, container, service_config) -> bool:
        """Check if a container is healthy based on its health check config"""
        try:
            # Get the host and mapped port from container info
            host = container.get('host', 'localhost')
            container_port = service_config.health_check.get('port', service_config.port)
            
            # We need to determine the actual mapped port by parsing the port mapping
            if 'ports' in container and container['ports'] != 'N/A':
                import re
                port_match = re.search(r'0.0.0.0:(\d+)->', container['ports'])
                if port_match:
                    mapped_port = int(port_match.group(1))
                    
                    # Perform HTTP health check
                    import requests
                    health_url = f"http://{host}:{mapped_port}{service_config.health_check['path']}"
                    
                    response = requests.get(
                        health_url,
                        timeout=service_config.health_check.get('timeout', 5)
                    )
                    
                    # Consider container healthy if we get a successful response
                    return 200 <= response.status_code < 400
                else:
                    # If no mapped port found, try the original port (for direct access)
                    import requests
                    health_url = f"http://{host}:{container_port}{service_config.health_check['path']}"
                    
                    response = requests.get(
                        health_url,
                        timeout=service_config.health_check.get('timeout', 5)
                    )
                    
                    return 200 <= response.status_code < 400
            else:
                # If we can't determine the port, assume it's unhealthy
                return False
        except Exception as e:
            logger.debug(f"Health check failed for container {container.get('id', 'unknown')}: {e}")
            return False

    async def start_scaling_loop(self):
        """Main scaling loop - runs continuously"""
        logger.info("Starting scaling loop")
        
        # Start health check loop as a background task
        health_check_task = asyncio.create_task(self._health_check_loop())
        
        while self.is_scaling_active:
            try:
                # Run scaling logic for each service
                for service_name in self.services:
                    await self._evaluate_scaling(service_name)
                
                # Wait for the next check
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")
                await asyncio.sleep(10)  # Wait a bit before retrying
        
        # Cancel health check loop when scaling loop stops
        health_check_task.cancel()

    async def _health_check_loop(self):
        """Background loop for performing health checks"""
        while self.is_scaling_active:
            try:
                await self._perform_health_checks()
                # Health checks run more frequently than scaling checks
                await asyncio.sleep(10)  # Default to every 10 seconds as per PRD
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)
    
    async def _scale_up(self, service_name: str):
        """Scale up a service by deploying an additional container"""
        try:
            service_config = self.services[service_name]
            current_count = await self.docker_manager.get_service_container_count(service_name)
            new_count = current_count + 1
            
            logger.info(f"Scaling UP {service_name} from {current_count} to {new_count} containers")
            
            # Deploy new container
            container = await self.docker_manager.deploy_container(service_config)
            
            # Update cooldown
            self.scaling_cooldowns[service_name] = time.time()
            
            # Record event
            self._record_scaling_event(
                service_name, 
                'scale_up', 
                current_count, 
                new_count, 
                f'CPU avg ({await self._get_service_avg_cpu(service_name)}%) >= threshold ({service_config.scale_up_threshold}%)'
            )
            
            # Update HAProxy configuration to include the new container
            try:
                updated_containers = await self.docker_manager.get_service_containers(service_name)
                await self.haproxy_manager.update_backend_servers(service_name, updated_containers)
                logger.info(f"HAProxy configuration updated for {service_name} after scaling up")
            except Exception as haproxy_error:
                logger.error(f"Failed to update HAProxy after scaling up: {haproxy_error}")
            
            logger.info(f"Scaled UP {service_name} to {new_count} containers")
            
        except Exception as e:
            logger.error(f"Failed to scale up {service_name}: {e}")
    
    async def _scale_down(self, service_name: str):
        """Scale down a service by stopping a container"""
        try:
            service_config = self.services[service_name]
            current_count = await self.docker_manager.get_service_container_count(service_name)
            new_count = current_count - 1
            
            logger.info(f"Scaling DOWN {service_name} from {current_count} to {new_count} containers")
            
            # Stop a container
            stopped_container = await self.docker_manager.stop_service_container(service_name)
            
            if stopped_container:
                # Update cooldown
                self.scaling_cooldowns[service_name] = time.time()
                
                # Record event
                self._record_scaling_event(
                    service_name, 
                    'scale_down', 
                    current_count, 
                    new_count, 
                    f'CPU avg ({await self._get_service_avg_cpu(service_name)}%) <= threshold ({service_config.scale_down_threshold}%)'
                )
                
                # Update HAProxy configuration to remove the container from backend
                try:
                    updated_containers = await self.docker_manager.get_service_containers(service_name)
                    await self.haproxy_manager.update_backend_servers(service_name, updated_containers)
                    logger.info(f"HAProxy configuration updated for {service_name} after scaling down")
                except Exception as haproxy_error:
                    logger.error(f"Failed to update HAProxy after scaling down: {haproxy_error}")
                
                logger.info(f"Scaled DOWN {service_name} to {new_count} containers")
        
        except Exception as e:
            logger.error(f"Failed to scale down {service_name}: {e}")
    
    async def shutdown(self):
        """Shutdown the autoscaler"""
        self.is_scaling_active = False
        if self.scaling_loop_task:
            self.scaling_loop_task.cancel()
        
        logger.info("AutoScaler shutdown complete")