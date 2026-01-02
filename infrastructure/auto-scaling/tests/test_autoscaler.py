import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.autoscaler import AutoScaler, ScalingEvent
from app.service_config import ServiceConfig
from app.config_model import BusinessHoursConfig, AutoScalerSettings


@pytest.fixture
def sample_service_config():
    return ServiceConfig(
        name="test_service",
        image="test/image:latest",
        port=8080,
        min_replicas=1,
        max_replicas=5,
        scale_up_threshold=75,
        scale_down_threshold=25,
        cooldown_period=60,
        business_hours_only=True,
        health_check={"path": "/health", "interval": 10, "timeout": 5},
        volumes=[],
        environment=[]
    )


@pytest.fixture
def mock_docker_manager():
    manager = Mock()
    manager.get_service_container_count = AsyncMock(return_value=2)
    manager.get_service_containers = AsyncMock(return_value=[])
    manager.deploy_container = AsyncMock()
    manager.stop_service_container = AsyncMock()
    return manager


@pytest.fixture
def mock_scheduler():
    scheduler = Mock()
    scheduler.is_business_hours = AsyncMock(return_value=True)
    return scheduler


@pytest.mark.asyncio
async def test_autoscaler_initialization(sample_service_config, mock_docker_manager, mock_scheduler):
    """Test that autoscaler initializes properly with mock components"""
    autoscaler = AutoScaler()
    autoscaler.docker_manager = mock_docker_manager
    autoscaler.scheduler = mock_scheduler
    
    # Mock config loading
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.check_interval = 30
    
    # Verify initialization sets up required attributes
    assert autoscaler.scaling_cooldowns == {}
    assert autoscaler.scaling_events == []
    assert autoscaler.is_scaling_active is True
    assert autoscaler.check_interval == 30


@pytest.mark.asyncio
async def test_can_scale_with_cooldown(sample_service_config):
    """Test that scaling respects cooldown periods"""
    autoscaler = AutoScaler()
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.scaling_cooldowns = {"test_service": asyncio.get_event_loop().time()}
    
    # Should not be able to scale immediately after cooldown starts
    can_scale = await autoscaler.can_scale("test_service")
    assert can_scale is False


@pytest.mark.asyncio
async def test_can_scale_during_business_hours(sample_service_config, mock_scheduler):
    """Test that scaling respects business hours"""
    autoscaler = AutoScaler()
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.scheduler = mock_scheduler
    
    # Business hours enabled and currently in business hours
    mock_scheduler.is_business_hours.return_value = True
    can_scale = await autoscaler.can_scale("test_service")
    assert can_scale is True
    
    # Business hours enabled but outside business hours
    mock_scheduler.is_business_hours.return_value = False
    can_scale = await autoscaler.can_scale("test_service")
    assert can_scale is False


def test_record_scaling_event():
    """Test that scaling events are properly recorded with metrics"""
    autoscaler = AutoScaler()
    autoscaler.services = {}
    
    # Record an event
    autoscaler._record_scaling_event("test_service", "scale_up", 2, 3, "test reason")
    
    # Check that the event was added
    assert len(autoscaler.scaling_events) == 1
    event = autoscaler.scaling_events[0]
    assert event.service_name == "test_service"
    assert event.action == "scale_up"
    assert event.from_count == 2
    assert event.to_count == 3
    assert event.reason == "test reason"


@pytest.mark.asyncio
async def test_get_recent_events():
    """Test retrieval of recent scaling events"""
    autoscaler = AutoScaler()
    
    # Add some events
    autoscaler.scaling_events = [
        ScalingEvent("service1", "scale_up", 1, 2, "test", datetime.now()),
        ScalingEvent("service2", "scale_down", 3, 2, "test", datetime.now()),
    ]
    
    events = await autoscaler.get_recent_events(10)
    assert len(events) == 2


@pytest.mark.asyncio
async def test_manual_scale_up(sample_service_config, mock_docker_manager):
    """Test manual scale up functionality"""
    autoscaler = AutoScaler()
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.docker_manager = mock_docker_manager
    
    # Test successful scale up
    result = await autoscaler.manual_scale_up("test_service")
    assert result['success'] is True
    mock_docker_manager.deploy_container.assert_called_once()


@pytest.mark.asyncio 
async def test_manual_scale_down(sample_service_config, mock_docker_manager):
    """Test manual scale down functionality"""
    autoscaler = AutoScaler()
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.docker_manager = mock_docker_manager
    
    # Test successful scale down
    mock_docker_manager.stop_service_container = AsyncMock(return_value=Mock(id="test_container"))
    result = await autoscaler.manual_scale_down("test_service")
    assert result['success'] is True


@pytest.mark.asyncio
async def test_get_service_stats(sample_service_config, mock_docker_manager):
    """Test retrieval of service statistics"""
    autoscaler = AutoScaler()
    autoscaler.services = {"test_service": sample_service_config}
    autoscaler.docker_manager = mock_docker_manager
    
    stats = await autoscaler.get_service_stats()
    assert "test_service" in stats
    assert stats["test_service"]["container_count"] == 2  # Mock value