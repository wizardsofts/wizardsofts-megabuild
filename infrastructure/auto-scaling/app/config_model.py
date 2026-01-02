import sys
from pathlib import Path
# Add the app directory to Python path to allow imports
sys.path.append(str(Path(__file__).parent))

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import time
import yaml


class ServerConfig(BaseModel):
    host: str
    name: str
    ssh_user: str
    ssh_port: int = Field(22, ge=1, le=65535)
    ssh_key: str
    max_containers: int = Field(ge=1, le=100)  # Reasonable limits
    role: str = "worker"  # "control" or "worker"


class HealthCheckConfig(BaseModel):
    path: str
    interval: int = Field(ge=1, le=300)  # 1 to 300 seconds
    timeout: int = Field(ge=1, le=60)    # 1 to 60 seconds


class ServiceConfigModel(BaseModel):
    image: str
    port: int = Field(ge=1, le=65535)
    min_replicas: int = Field(ge=0)
    max_replicas: int = Field(ge=1)
    scale_up_threshold: int = Field(ge=1, le=100)
    scale_down_threshold: int = Field(ge=0, le=99)
    cooldown_period: int = Field(ge=0)  # seconds
    business_hours_only: bool = True
    health_check: HealthCheckConfig
    volumes: List[str] = []
    environment: List[str] = []
    
    class Config:
        # Allow extra fields for flexibility while validating core fields
        extra = "allow"
    
    def validate_replica_constraints(self):
        """Validate that min_replicas <= max_replicas"""
        if self.min_replicas > self.max_replicas:
            raise ValueError(f"min_replicas ({self.min_replicas}) cannot be greater than max_replicas ({self.max_replicas})")


class BusinessHoursConfig(BaseModel):
    start: str  # Format: "HH:MM"
    end: str    # Format: "HH:MM"
    timezone: str = "UTC"
    
    def validate_time_format(self):
        """Validate that time strings are in HH:MM format"""
        import re
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, self.start) or not re.match(time_pattern, self.end):
            raise ValueError("Time format must be HH:MM")
        
        # Also validate that start and end times are valid
        try:
            time.fromisoformat(self.start)
            time.fromisoformat(self.end)
        except ValueError:
            raise ValueError("Invalid time format, must be HH:MM")


class MonitoringConfig(BaseModel):
    prometheus: Dict[str, Any]
    grafana: Dict[str, Any]


class AutoScalerSettings(BaseModel):
    check_interval: int = Field(ge=1, le=3600)  # 1 second to 1 hour
    business_hours: BusinessHoursConfig
    log_level: str = "INFO"
    backup: Dict[str, Any]


class ConfigModel(BaseModel):
    load_balancer: Dict[str, Any]
    servers: List[ServerConfig]
    services: Dict[str, ServiceConfigModel]
    monitoring: MonitoringConfig
    autoscaler: AutoScalerSettings
    
    def validate_config(self):
        """Run comprehensive validation on the entire config"""
        # Validate business hours
        self.autoscaler.business_hours.validate_time_format()
        
        # Validate server configs
        for server in self.servers:
            if server.ssh_port < 1 or server.ssh_port > 65535:
                raise ValueError(f"Invalid SSH port {server.ssh_port} for server {server.name}")
        
        # Validate service configs
        for service_name, service in self.services.items():
            service.validate_replica_constraints()
            
            # Validate thresholds make sense
            if service.scale_up_threshold <= service.scale_down_threshold:
                raise ValueError(
                    f"scale_up_threshold ({service.scale_up_threshold}) must be greater than "
                    f"scale_down_threshold ({service.scale_down_threshold}) for service {service_name}"
                )
        
        return True


def load_and_validate_config(config_path: str) -> ConfigModel:
    """
    Load and validate configuration from YAML file
    """
    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Validate the config
        config = ConfigModel(**config_dict)
        config.validate_config()
        
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file {config_path}: {e}")
    except Exception as e:
        raise ValueError(f"Config validation failed: {e}")


if __name__ == "__main__":
    # Example usage for testing
    try:
        config = load_and_validate_config('/opt/autoscaler/config.yaml')
        print("Configuration is valid!")
        print(f"Loaded {len(config.servers)} servers and {len(config.services)} services")
    except Exception as e:
        print(f"Configuration validation failed: {e}")