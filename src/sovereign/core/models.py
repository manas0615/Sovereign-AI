"""Shared data models for the Workbench."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

class HealthStatus(str, Enum):
    """Basic health status states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNINITIALIZED = "uninitialized"

class HealthCheckResult(BaseModel):
    """Result of a minimal health check."""
    status: HealthStatus
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
