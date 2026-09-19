"""Capability models for Tool execution."""

from enum import Enum
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

def _now() -> datetime:
    return datetime.now(timezone.utc)

class CapabilityType(str, Enum):
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"
    DESTRUCTIVE = "DESTRUCTIVE"

class SecurityMode(str, Enum):
    ISOLATED = "ISOLATED"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"

class ToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    capability: CapabilityType
    enabled: bool = True
    
class ToolResult(BaseModel):
    execution_id: str
    tool_name: str
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    security_mode: Optional[SecurityMode] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class ToolImplementation(BaseModel):
    """Internal model linking a definition to its actual python callable."""
    definition: ToolDefinition
    handler: Any  # Callable[[Dict[str, Any]], Any]
    input_model: Type[BaseModel]
