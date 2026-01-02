#!/usr/bin/env python3
"""
Test script to verify that all modules can be imported and basic functionality works
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
APP_DIR = Path(__file__).parent / "app"
sys.path.insert(0, str(APP_DIR))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from config_model import load_and_validate_config, ConfigModel
        print("✓ config_model imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config_model: {e}")
        return False
    
    try:
        from autoscaler import AutoScaler
        print("✓ autoscaler imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import autoscaler: {e}")
        return False
    
    try:
        from scheduler import BusinessHoursScheduler
        print("✓ scheduler imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import scheduler: {e}")
        return False
    
    try:
        from haproxy_manager import HAProxyManager
        print("✓ haproxy_manager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import haproxy_manager: {e}")
        return False
    
    try:
        from docker_manager import DockerManager
        print("✓ docker_manager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import docker_manager: {e}")
        return False
    
    try:
        from service_config import ServiceConfig
        print("✓ service_config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import service_config: {e}")
        return False
    
    return True

def test_config_model():
    """Test basic config model functionality"""
    print("\nTesting config model...")
    
    # Test creating a minimal valid config
    from config_model import (
        ConfigModel, ServerConfig, ServiceConfigModel, HealthCheckConfig, 
        BusinessHoursConfig, AutoScalerSettings, MonitoringConfig
    )
    
    # Create minimal valid configuration
    health_check = HealthCheckConfig(
        path="/health",
        interval=10,
        timeout=5
    )
    
    service = ServiceConfigModel(
        image="test/image:latest",
        port=8080,
        min_replicas=1,
        max_replicas=5,
        scale_up_threshold=75,
        scale_down_threshold=25,
        cooldown_period=60,
        business_hours_only=True,
        health_check=health_check
    )
    
    server = ServerConfig(
        host="10.0.0.84",
        name="server1",
        ssh_user="test_user",
        ssh_port=22,
        ssh_key="/path/to/key",
        max_containers=12
    )
    
    business_hours = BusinessHoursConfig(
        start="09:00",
        end="17:00",
        timezone="UTC"
    )
    
    autoscaler_settings = AutoScalerSettings(
        check_interval=30,
        business_hours=business_hours,
        log_level="INFO",
        backup={"enabled": True, "path": "/backup"}
    )
    
    monitoring = MonitoringConfig(
        prometheus={"enabled": True, "port": 9090},
        grafana={"enabled": True, "port": 3000}
    )
    
    config = ConfigModel(
        load_balancer={"stats_port": 8404},
        servers=[server],
        services={"test_service": service},
        monitoring=monitoring,
        autoscaler=autoscaler_settings
    )
    
    # Validate the config
    config.validate_config()
    print("✓ Config model validation passed")
    
    return True

def main():
    print("Running module import tests...\n")
    
    if not test_imports():
        print("\n❌ Import tests failed")
        return 1
    
    if not test_config_model():
        print("\n❌ Config model tests failed")
        return 1
    
    print("\n✅ All tests passed! Modules can be imported and basic functionality works.")
    return 0

if __name__ == "__main__":
    exit(main())