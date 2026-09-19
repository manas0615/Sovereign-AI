"""Data models for the Model Gateway."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum

class LifecycleState(str, Enum):
    """Operational lifecycle state of a model deployment."""
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    UNLOADING = "UNLOADING"
    FAILED = "FAILED"

class RuntimeStatus(str, Enum):
    """Lifecycle status of the model runtime."""
    NOT_CONFIGURED = "NOT_CONFIGURED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    SERVER_NOT_RUNNING = "SERVER_NOT_RUNNING"
    STARTING = "STARTING"
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"
    ERROR = "ERROR"

class ModelDeploymentConfig(BaseModel):
    """Runtime configuration for a specific model deployment."""
    model_name: str
    model_path: str
    backend: str = "llama.cpp"
    device: str = "Vulkan1"
    gpu_layers: int = 20
    context_size: int = 8192
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    mmproj_path: Optional[str] = None
    extra_params: Dict[str, Any] = {}

class ModelInfo(BaseModel):
    """Metadata about the currently configured model."""
    name: str
    path: str
    backend: str
    device: str
    gpu_layers: int
    context_size: int

class InferenceRequest(BaseModel):
    """Abstract inference request."""
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.8
    stop: Optional[List[str]] = None
    stream: bool = False
    response_format: Optional[Dict[str, Any]] = None
    images: Optional[List[str]] = None

class InferenceResponse(BaseModel):
    """Abstract inference response."""
    text: str
    usage: Dict[str, int]
    stop_reason: str

class StreamingResponseChunk(BaseModel):
    """A chunk of streamed inference."""
    text: str
    is_done: bool
    usage: Optional[Dict[str, int]] = None
    stop_reason: Optional[str] = None
