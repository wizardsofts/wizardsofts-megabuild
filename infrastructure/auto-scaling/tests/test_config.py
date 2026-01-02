import pytest
import tempfile
import os
from pydantic import ValidationError

from app.config_model import (
    load_and_validate_config, 
    ConfigModel, 
    ServerConfig, 
    ServiceConfigModel, 
    HealthCheckConfig,
    BusinessHoursConfig,
    AutoScalerSettings,
    MonitoringConfig
)


def test_server_config_validation():
    """Test server configuration validation"""
    # Valid config
    server = ServerConfig(
        host="10.0.0.84",
        name="server1",
        ssh_user="test_user",
        ssh_port=22,
        ssh_key="/path/to/key",
        max_containers=12,
        role="control"
    )
    assert server.host == "10.0.0.84"
    assert server.max_containers == 12
    
    # Test invalid port
    with pytest.raises(ValidationError):
        ServerConfig(
            host="10.0.0.84",
            name="server1",
            ssh_user="test_user",
            ssh_port=99999,  # Invalid port
            ssh_key="/path/to/key",
            max_containers=12
        )


def test_service_config_validation():
    """Test service configuration validation"""
    health_check = HealthCheckConfig(
        path="/health",
        interval=10,
        timeout=5
    )
    
    # Valid service config
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
    
    assert service.image == "test/image:latest"
    assert service.min_replicas == 1
    assert service.max_replicas <= 5
    
    # Test invalid replica constraints
    with pytest.raises(ValueError):
        service.validate_replica_constraints()  # This should pass as min < max
        # Now test the failure case by creating a bad config
        bad_service = ServiceConfigModel(
            image="test/image:latest",
            port=8080,
            min_replicas=10,  # Greater than max
            max_replicas=5,
            scale_up_threshold=75,
            scale_down_threshold=25,
            cooldown_period=60,
            business_hours_only=True,
            health_check=health_check
        )
        bad_service.validate_replica_constraints()


def test_business_hours_config_validation():
    """Test business hours configuration validation"""
    # Valid config
    bh = BusinessHoursConfig(
        start="09:00",
        end="17:00",
        timezone="UTC"
    )
    
    bh.validate_time_format()
    
    # Test invalid time format
    with pytest.raises(ValueError):
        bad_bh = BusinessHoursConfig(
            start="25:00",  # Invalid hour
            end="17:00",
            timezone="UTC"
        )
        bad_bh.validate_time_format()
    
    with pytest.raises(ValueError):
        bad_bh2 = BusinessHoursConfig(
            start="09:00",
            end="invalid",  # Invalid format
            timezone="UTC"
        )
        bad_bh2.validate_time_format()


def test_config_model_validation():
    """Test full config model validation"""
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
    
    # Valid config
    config = ConfigModel(
        load_balancer={"stats_port": 8404},
        servers=[server],
        services={"test_service": service},
        monitoring=monitoring,
        autoscaler=autoscaler_settings
    )
    
    config.validate_config()
    assert len(config.servers) == 1
    assert "test_service" in config.services


def test_threshold_validation():
    """Test that scale up threshold is greater than scale down threshold"""
    health_check = HealthCheckConfig(
        path="/health",
        interval=10,
        timeout=5
    )
    
    # This should raise an error because up <= down
    service = ServiceConfigModel(
        image="test/image:latest",
        port=8080,
        min_replicas=1,
        max_replicas=5,
        scale_up_threshold=60,  # Greater than down - this is OK
        scale_down_threshold=70,  # Greater than up - this should cause validation error
        cooldown_period=60,
        business_hours_only=True,
        health_check=health_check
    )
    
    # Create a config with this service to trigger validation
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
    
    with pytest.raises(ValueError, match="scale_up_threshold.*must be greater than.*scale_down_threshold"):
        config.validate_config()


def test_config_loading():
    """Test loading configuration from YAML file"""
    # Create a temporary config file
    config_yaml = """
load_balancer:
  stats_port: 8404

servers:
  - host: 10.0.0.84
    name: server1
    ssh_user: wizardsofts
    ssh_port: 22
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12
    role: control

services:
  test_service:
    image: test/image:latest
    port: 8080
    min_replicas: 1
    max_replicas: 5
    scale_up_threshold: 75
    scale_down_threshold: 25
    cooldown_period: 60
    business_hours_only: true
    health_check:
      path: /health
      interval: 10
      timeout: 5
    volumes: []
    environment: []

monitoring:
  prometheus:
    enabled: true
    port: 9090
  grafana:
    enabled: true
    port: 3000

autoscaler:
  check_interval: 30
  business_hours:
    start: "09:00"
    end: "17:00"
    timezone: "UTC"
  log_level: INFO
  backup:
    enabled: true
    path: /opt/autoscaler/backup
    retention_days: 7
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_yaml)
        temp_path = f.name
    
    try:
        # Load and validate the config
        config = load_and_validate_config(temp_path)
        assert config is not None
        assert len(config.servers) == 1
        assert "test_service" in config.services
        assert config.autoscaler.check_interval == 30
    finally:
        os.unlink(temp_path)


def test_config_loading_invalid_yaml():
    """Test handling of invalid YAML"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: [")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_and_validate_config(temp_path)
    finally:
        os.unlink(temp_path)


def test_config_loading_validation_error():
    """Test handling of validation errors"""
    # Create config with validation error (scale_up <= scale_down)
    config_yaml = """
load_balancer:
  stats_port: 8404

servers:
  - host: 10.0.0.84
    name: server1
    ssh_user: wizardsofts
    ssh_port: 22
    ssh_key: /root/.ssh/id_rsa
    max_containers: 12

services:
  test_service:
    image: test/image:latest
    port: 8080
    min_replicas: 1
    max_replicas: 5
    scale_up_threshold: 60  # Less than scale_down - invalid
    scale_down_threshold: 70
    cooldown_period: 60
    business_hours_only: true
    health_check:
      path: /health
      interval: 10
      timeout: 5

monitoring:
  prometheus:
    enabled: true
    port: 9090
  grafana:
    enabled: true
    port: 3000

autoscaler:
  check_interval: 30
  business_hours:
    start: "09:00"
    end: "17:00"
    timezone: "UTC"
  log_level: INFO
  backup:
    enabled: true
    path: /opt/autoscaler/backup
    retention_days: 7
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_yaml)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Config validation failed"):
            load_and_validate_config(temp_path)
    finally:
        os.unlink(temp_path)