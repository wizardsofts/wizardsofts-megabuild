import sys
import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
# Add the app directory to Python path to allow imports
sys.path.append(str(Path(__file__).parent))

from docker_manager import DockerManager
import yaml

logger = logging.getLogger(__name__)

class HAProxyManager:
    def __init__(self):
        self.config = None
        self.docker_manager = DockerManager()
        self.haproxy_config_path = '/opt/autoscaler/haproxy/haproxy.cfg'
        self.services: Dict[str, Dict] = {}
        self.backend_servers: Dict[str, List[Dict]] = {}  # service_name: list of servers with ports
        
    async def initialize(self):
        """Initialize HAProxy manager"""
        try:
            with open('/opt/autoscaler/config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Initialize services from config
            self.services = self.config.get('services', {})
            
            # Initialize backend servers tracking
            for service_name in self.services:
                self.backend_servers[service_name] = []
            
            logger.info("HAProxy manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize HAProxy manager: {e}")
            raise
    
    async def update_backend_servers(self, service_name: str, container_list: List[Dict]):
        """Update the backend servers for a specific service based on running containers"""
        try:
            # Get the current HAProxy config
            with open(self.haproxy_config_path, 'r') as f:
                config_content = f.read()
            
            # Extract the backend section for this service
            # This is a simplified approach - a real implementation would be more robust
            backend_start = f"backend {service_name}_backend"
            new_backend_section = self._generate_backend_config(service_name, container_list)
            
            # Replace the backend section in the config
            updated_config = self._replace_backend_section(config_content, service_name, new_backend_section)
            
            # Write the updated config
            with open(self.haproxy_config_path, 'w') as f:
                f.write(updated_config)
            
            # Update internal tracking
            self.backend_servers[service_name] = container_list
            
            # Reload HAProxy configuration
            await self._reload_haproxy()
            
            logger.info(f"Updated HAProxy backend for {service_name} with {len(container_list)} servers")
            
        except Exception as e:
            logger.error(f"Failed to update HAProxy backend for {service_name}: {e}")
            raise
    
    def _generate_backend_config(self, service_name: str, container_list: List[Dict]) -> str:
        """Generate HAProxy backend configuration for a service"""
        service_config = self.services[service_name]
        
        backend_lines = [
            f"backend {service_name}_backend",
            "    balance roundrobin",
            f"    option httpchk GET {service_config['health_check']['path']}",
            "    http-check expect status 200"
        ]
        
        for i, container in enumerate(container_list):
            # Extract host and port from container information
            # In a real implementation, we'd get the actual mapped ports
            # For now, we'll assume containers are running with the port specified in config
            host = container.get('host', '127.0.0.1')
            
            # Get the actual port from container - this is simplified
            # Real implementation would need to inspect the actual port mapping
            port = service_config['port']
            
            # Extract the actual mapped port from Docker port info
            if 'ports' in container and container['ports'] != 'N/A':
                # Parse Docker port mapping like "0.0.0.0:32770->11434/tcp" 
                import re
                port_match = re.search(r'->(\d+)', container['ports'])
                if port_match:
                    port = port_match.group(1)
            
            backend_lines.append(f"    server {service_name}_{i}_{container['id'][:8]} {host}:{port} check")
        
        return '\n'.join(backend_lines)
    
    def _replace_backend_section(self, config_content: str, service_name: str, new_backend: str) -> str:
        """Replace a backend section in the HAProxy config"""
        # Find and replace the backend section for the service
        pattern = rf'backend\s+{service_name}_backend.*?(?=^backend|\z)'
        updated_content = re.sub(
            pattern, 
            new_backend, 
            config_content, 
            flags=re.MULTILINE | re.DOTALL
        )
        
        # If the backend doesn't exist in the config, append it
        if f"backend {service_name}_backend" not in updated_content:
            updated_content += f"\n{new_backend}\n"
        
        return updated_content
    
    async def _reload_haproxy(self):
        """Reload HAProxy configuration with graceful restart"""
        try:
            # Method 1: Try graceful reload using the -sf flag (recommended)
            import subprocess
            import tempfile
            import os
            
            # First, validate the new configuration
            result = subprocess.run([
                'docker', 'exec', 'haproxy', 'haproxy', '-c', '-f', '/usr/local/etc/haproxy/haproxy.cfg'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"HAProxy config validation failed: {result.stderr}")
                raise Exception(f"Invalid HAProxy configuration: {result.stderr}")
            
            # If config is valid, attempt graceful reload
            # Get the current HAProxy master process PID
            pid_result = subprocess.run([
                'docker', 'exec', 'haproxy', 'cat', '/tmp/haproxy.pid'
            ], capture_output=True, text=True)
            
            if pid_result.returncode == 0:
                master_pid = pid_result.stdout.strip()
                # Perform graceful reload: start new process, send old process the SIGTERM
                result = subprocess.run([
                    'docker', 'exec', 'haproxy', 'haproxy', '-f', '/usr/local/etc/haproxy/haproxy.cfg',
                    '-sf', master_pid
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"HAProxy graceful reload failed: {result.stderr}")
                    # Fallback to container restart if graceful reload fails
                    logger.warning("Attempting HAProxy container restart as fallback...")
                    subprocess.run(['docker', 'restart', 'haproxy'], capture_output=True)
                else:
                    logger.info("HAProxy configuration reloaded successfully")
            else:
                # If we can't get the PID, restart the container
                logger.warning("Could not retrieve HAProxy PID, restarting container...")
                subprocess.run(['docker', 'restart', 'haproxy'], capture_output=True)
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reload HAProxy: {e}")
            if hasattr(e, 'stdout'):
                logger.error(f"HAProxy stdout: {e.stdout}")
            if hasattr(e, 'stderr'):
                logger.error(f"HAProxy stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            # Docker command not found, HAProxy might not be running as container
            logger.warning("Docker command not found, HAProxy may be running directly on the system")
            # In this case, we'd need to reload HAProxy differently
            # Try system service if available
            try:
                subprocess.run(['sudo', 'systemctl', 'reload', 'haproxy'], capture_output=True)
            except:
                logger.warning("Could not reload system HAProxy service, container restart may be needed")
                pass
        except Exception as e:
            logger.error(f"Unexpected error reloading HAProxy: {e}")
            raise
    
    async def add_server_to_backend(self, service_name: str, host: str, port: int, server_id: Optional[str] = None):
        """Add a server to a backend"""
        if server_id is None:
            import time
            server_id = f"{service_name}_{int(time.time())}"
        
        # This is a simplified implementation
        # In practice, you'd need to update the entire backend configuration
        # as HAProxy doesn't support dynamic server addition at runtime
        # without the Enterprise version
        
        # Update internal tracking
        if service_name not in self.backend_servers:
            self.backend_servers[service_name] = []
        
        server_info = {
            'id': server_id,
            'host': host,
            'port': port,
            'status': 'active'
        }
        
        self.backend_servers[service_name].append(server_info)
        
        logger.info(f"Added server {server_id} ({host}:{port}) to {service_name} backend")
    
    async def remove_server_from_backend(self, service_name: str, server_id: str):
        """Remove a server from a backend"""
        if service_name not in self.backend_servers:
            return
        
        self.backend_servers[service_name] = [
            server for server in self.backend_servers[service_name] 
            if server['id'] != server_id
        ]
        
        logger.info(f"Removed server {server_id} from {service_name} backend")
    
    async def get_backend_status(self, service_name: str) -> Dict:
        """Get the status of servers in a backend"""
        if service_name not in self.backend_servers:
            return {'service': service_name, 'servers': [], 'total': 0}
        
        return {
            'service': service_name,
            'servers': self.backend_servers[service_name],
            'total': len(self.backend_servers[service_name])
        }
    
    async def sync_with_docker(self):
        """Sync HAProxy configuration with running Docker containers"""
        try:
            for service_name in self.services:
                # Get all containers for this service
                containers = await self.docker_manager.get_service_containers(service_name)
                
                # Update HAProxy backend configuration
                await self.update_backend_servers(service_name, containers)
            
            logger.info("HAProxy configuration synced with Docker containers")
        except Exception as e:
            logger.error(f"Failed to sync HAProxy with Docker: {e}")
            raise