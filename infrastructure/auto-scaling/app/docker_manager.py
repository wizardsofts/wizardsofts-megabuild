import asyncio
import docker
import paramiko
import yaml
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    host: str
    name: str
    ssh_user: str
    ssh_port: int
    ssh_key: str
    max_containers: int
    role: str

@dataclass
class ContainerInfo:
    id: str
    name: str
    status: str
    image: str
    ports: str
    created: str

class DockerManager:
    def __init__(self):
        self.config = None
        self.servers: Dict[str, ServerConfig] = {}
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self.docker_clients: Dict[str, docker.DockerClient] = {}
        
    async def initialize(self):
        """Initialize Docker manager with server configurations"""
        try:
            with open('/opt/autoscaler/config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Parse server configurations
            for server_data in self.config.get('servers', []):
                server = ServerConfig(
                    host=server_data['host'],
                    name=server_data['name'],
                    ssh_user=server_data['ssh_user'],
                    ssh_port=server_data.get('ssh_port', 22),
                    ssh_key=server_data['ssh_key'],
                    max_containers=server_data['max_containers'],
                    role=server_data.get('role', 'worker')
                )
                self.servers[server.host] = server
            
            # Initialize Docker clients
            await self._initialize_docker_clients()
            
            logger.info(f"Initialized Docker manager with {len(self.servers)} servers")
        except Exception as e:
            logger.error(f"Failed to initialize Docker manager: {e}")
            raise
    
    async def _initialize_docker_clients(self):
        """Initialize Docker clients for all servers"""
        for host, server in self.servers.items():
            try:
                # For remote Docker daemons, we need to use SSH tunneling or TCP sockets
                # Since we're on the same network, we'll connect directly to the Docker socket if possible
                # Or use SSH to execute Docker commands remotely
                
                # Create SSH client for this server
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Load SSH key
                try:
                    private_key = paramiko.RSAKey.from_private_key_file(server.ssh_key)
                except:
                    private_key = paramiko.Ed25519Key.from_private_key_file(server.ssh_key)
                
                ssh_client.connect(
                    hostname=host,
                    port=server.ssh_port,
                    username=server.ssh_user,
                    pkey=private_key,
                    timeout=10
                )
                
                self.ssh_clients[host] = ssh_client
                
                # For now, we'll just store the SSH client and execute Docker commands via SSH
                # A proper implementation would use Docker daemon directly if accessible
                
                logger.info(f"Connected to server {host} via SSH")
            except Exception as e:
                logger.error(f"Failed to connect to server {host}: {e}")
    
    def _execute_ssh_command(self, host: str, command: str) -> tuple:
        """Execute a command on a remote server via SSH"""
        if host not in self.ssh_clients:
            raise Exception(f"SSH client not available for {host}")
        
        try:
            stdin, stdout, stderr = self.ssh_clients[host].exec_command(command)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            return exit_status, output, error
        except Exception as e:
            logger.error(f"SSH command execution failed on {host}: {e}")
            raise
    
    async def get_service_container_count(self, service_name: str) -> int:
        """Get the total number of containers running for a specific service across all servers"""
        total_count = 0
        
        for host, server in self.servers.items():
            try:
                # List containers with name filter
                cmd = f"docker ps --filter name={service_name} --format '{{{{.ID}}}}'"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0:
                    container_ids = [line.strip() for line in output.strip().split('\n') if line.strip()]
                    total_count += len(container_ids)
                else:
                    logger.warning(f"Failed to get containers for {service_name} on {host}: {error}")
            except Exception as e:
                logger.error(f"Error getting container count for {service_name} on {host}: {e}")
        
        return total_count
    
    async def get_service_containers(self, service_name: str) -> List[Any]:
        """Get all containers running for a specific service across all servers"""
        all_containers = []
        
        # This is a simplified version - in a real implementation we would track containers
        # across all servers. For now, we'll return a placeholder structure.
        
        for host, server in self.servers.items():
            try:
                # Get detailed container information
                cmd = f"docker ps --filter name={service_name} --format '{{{{.ID}}}}\t{{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Image}}}}\t{{{{.Ports}}}}'"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0 and output.strip():
                    lines = output.strip().split('\n')
                    for line in lines:
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            container_info = {
                                'id': parts[0][:12],  # Short ID
                                'name': parts[1],
                                'status': parts[2],
                                'image': parts[3],
                                'ports': parts[4] if len(parts) > 4 else 'N/A',
                                'host': host,
                                'server_name': server.name
                            }
                            all_containers.append(container_info)
            except Exception as e:
                logger.error(f"Error getting containers for {service_name} on {host}: {e}")
        
        return all_containers
    
    async def deploy_container(self, service_config) -> Any:
        """Deploy a container for a service on an appropriate server"""
        # Find the least loaded server that has capacity
        target_server = await self._find_least_loaded_server(service_config.name)
        if not target_server:
            raise Exception(f"No available server found for service {service_config.name}")
        
        # Generate a unique name for the container
        import uuid
        container_name = f"{service_config.name}-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # Build the Docker run command
        cmd_parts = [
            "docker", "run", "-d",
            f"--name", container_name,
            f"-p", f"0:{service_config.port}",  # Use dynamic port mapping
        ]
        
        # Add volumes
        for volume in service_config.volumes:
            cmd_parts.extend(["-v", volume])
        
        # Add environment variables
        for env in service_config.environment:
            cmd_parts.extend(["-e", env])
        
        # Add restart policy
        cmd_parts.extend(["--restart", "unless-stopped"])
        
        # Add the image
        cmd_parts.append(service_config.image)
        
        docker_cmd = " ".join(cmd_parts)
        
        try:
            # Execute the Docker run command on the target server
            exit_status, output, error = self._execute_ssh_command(target_server.host, docker_cmd)
            
            if exit_status != 0:
                raise Exception(f"Failed to deploy container on {target_server.host}: {error}")
            
            container_id = output.strip()
            logger.info(f"Deployed container {container_id} for service {service_config.name} on {target_server.host}")
            
            # Return a mock container object
            class MockContainer:
                def __init__(self, cid, name):
                    self.id = cid
                    self.short_id = cid[:12]
                    self.name = name
                    self.status = "running"
            
            return MockContainer(container_id, container_name)
            
        except Exception as e:
            logger.error(f"Failed to deploy container for service {service_config.name}: {e}")
            raise
    
    async def _find_least_loaded_server(self, service_name: str) -> Optional[ServerConfig]:
        """Find the server with the least containers running for the specified service"""
        min_load = float('inf')
        selected_server = None
        
        for host, server in self.servers.items():
            try:
                # Get number of containers already running for this service on this server
                cmd = f"docker ps --filter name={service_name} --format '{{{{.ID}}}}'"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0:
                    container_count = len([line for line in output.strip().split('\n') if line.strip()])
                else:
                    logger.warning(f"Failed to get container count on {host}: {error}")
                    container_count = 0
                
                # Get total container count on the server
                cmd = "docker ps -q | wc -l"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                if exit_status == 0:
                    total_containers = int(output.strip()) if output.strip().isdigit() else 0
                else:
                    total_containers = 0
                
                # Check if server has capacity
                if total_containers < server.max_containers:
                    # Prefer servers with fewer containers of this service
                    if container_count < min_load:
                        min_load = container_count
                        selected_server = server
            except Exception as e:
                logger.error(f"Error checking load on server {host}: {e}")
        
        return selected_server
    
    async def stop_service_container(self, service_name: str, specific_container=None) -> Optional[Any]:
        """Stop a container for a service (typically the oldest one or specific container)"""
        if specific_container:
            # Stop the specific container
            host = specific_container.get('host')
            container_id = specific_container.get('id', specific_container.get('ID'))
            
            if host and container_id:
                try:
                    # Stop the container
                    stop_cmd = f"docker stop {container_id}"
                    exit_status, output, error = self._execute_ssh_command(host, stop_cmd)
                    
                    if exit_status == 0:
                        logger.info(f"Stopped specific container {container_id[:12]} on {host}")
                        
                        # Remove the container
                        rm_cmd = f"docker rm {container_id}"
                        self._execute_ssh_command(host, rm_cmd)
                        
                        # Return mock container object
                        class MockContainer:
                            def __init__(self, cid):
                                self.id = cid
                                self.short_id = cid[:12]
                        
                        return MockContainer(container_id)
                    else:
                        logger.error(f"Failed to stop specific container {container_id[:12]} on {host}: {error}")
                except Exception as e:
                    logger.error(f"Error stopping specific container {container_id[:12]} on {host}: {e}")
            
            return None
        
        # Default behavior: stop the oldest container for the service
        for host, server in self.servers.items():
            try:
                # Get containers for this service, sorted by creation date
                cmd = f"docker ps --filter name={service_name} --format '{{{{.ID}}}}\t{{{{.Names}}}}\t{{{{.CreatedAt}}}}' --latest"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0 and output.strip():
                    lines = output.strip().split('\n')
                    if lines:
                        # Take the most recently created container
                        parts = lines[0].split('\t')
                        if len(parts) >= 2:
                            container_id = parts[0]
                            container_name = parts[1]
                            
                            # Stop the container
                            stop_cmd = f"docker stop {container_id}"
                            exit_status, output, error = self._execute_ssh_command(host, stop_cmd)
                            
                            if exit_status == 0:
                                logger.info(f"Stopped container {container_name} ({container_id}) on {host}")
                                
                                # Remove the container
                                rm_cmd = f"docker rm {container_id}"
                                self._execute_ssh_command(host, rm_cmd)
                                
                                # Return mock container object
                                class MockContainer:
                                    def __init__(self, cid):
                                        self.id = cid
                                        self.short_id = cid[:12]
                                
                                return MockContainer(container_id)
                            else:
                                logger.error(f"Failed to stop container {container_id} on {host}: {error}")
                else:
                    logger.debug(f"No {service_name} containers found on {host}")
            except Exception as e:
                logger.error(f"Error stopping container for {service_name} on {host}: {e}")
        
        return None
    
    async def restart_service_containers(self, service_name: str) -> int:
        """Restart all containers for a service"""
        restarted_count = 0
        
        for host, server in self.servers.items():
            try:
                # Get all containers for this service
                cmd = f"docker ps --filter name={service_name} --format '{{{{.ID}}}}'"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0 and output.strip():
                    container_ids = [line.strip() for line in output.strip().split('\n') if line.strip()]
                    
                    for container_id in container_ids:
                        restart_cmd = f"docker restart {container_id}"
                        restart_exit, restart_out, restart_err = self._execute_ssh_command(host, restart_cmd)
                        
                        if restart_exit == 0:
                            restarted_count += 1
                            logger.info(f"Restarted container {container_id[:12]} on {host}")
                        else:
                            logger.error(f"Failed to restart container {container_id[:12]} on {host}: {restart_err}")
            except Exception as e:
                logger.error(f"Error restarting containers for {service_name} on {host}: {e}")
        
        return restarted_count
    
    async def get_all_servers_info(self) -> List[Dict[str, Any]]:
        """Get information about all servers"""
        servers_info = []
        
        for host, server in self.servers.items():
            try:
                # Get Docker info
                cmd = "docker info --format '{{json .}}'"
                exit_status, output, error = self._execute_ssh_command(host, cmd)
                
                if exit_status == 0:
                    import json
                    docker_info = json.loads(output.strip())
                    
                    # Get container count
                    cmd = "docker ps -q | wc -l"
                    _, container_output, _ = self._execute_ssh_command(host, cmd)
                    container_count = int(container_output.strip()) if container_output.strip().isdigit() else 0
                    
                    server_info = {
                        'host': host,
                        'name': server.name,
                        'ssh_user': server.ssh_user,
                        'ssh_port': server.ssh_port,
                        'max_containers': server.max_containers,
                        'current_containers': container_count,
                        'role': server.role,
                        'status': 'healthy',
                        'docker_version': docker_info.get('ServerVersion', 'unknown'),
                        'storage_driver': docker_info.get('Driver', 'unknown'),
                        'total_images': docker_info.get('Images', 0)
                    }
                else:
                    server_info = {
                        'host': host,
                        'name': server.name,
                        'ssh_user': server.ssh_user,
                        'ssh_port': server.ssh_port,
                        'max_containers': server.max_containers,
                        'current_containers': 0,
                        'role': server.role,
                        'status': 'unhealthy',
                        'error': error
                    }
                
                servers_info.append(server_info)
            except Exception as e:
                logger.error(f"Error getting server info for {host}: {e}")
                servers_info.append({
                    'host': host,
                    'name': server.name,
                    'ssh_user': server.ssh_user,
                    'ssh_port': server.ssh_port,
                    'max_containers': server.max_containers,
                    'current_containers': 0,
                    'role': server.role,
                    'status': 'error',
                    'error': str(e)
                })
        
        return servers_info
    
    async def cleanup(self):
        """Cleanup connections"""
        for client in self.ssh_clients.values():
            try:
                client.close()
            except:
                pass
        self.ssh_clients.clear()