from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    name: str
    image: str
    port: int
    min_replicas: int
    max_replicas: int
    scale_up_threshold: int
    scale_down_threshold: int
    cooldown_period: int  # in seconds
    business_hours_only: bool
    health_check: Dict
    volumes: List[str]
    environment: List[str]