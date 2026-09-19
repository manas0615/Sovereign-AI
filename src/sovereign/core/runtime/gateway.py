"""Gateway interface for abstracting inference providers."""

from abc import ABC, abstractmethod
from typing import Generator, Optional
from sovereign.core.runtime.models import (
    InferenceRequest,
    InferenceResponse,
    StreamingResponseChunk,
    ModelInfo,
    RuntimeStatus,
    ModelDeploymentConfig
)

class ModelAdapter(ABC):
    """Abstract interface for a specific model runtime (e.g., llama.cpp)."""
    
    @abstractmethod
    def get_status(self) -> RuntimeStatus:
        pass
        
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        pass
        
    @abstractmethod
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        pass
        
    @abstractmethod
    def stream(self, request: InferenceRequest) -> Generator[StreamingResponseChunk, None, None]:
        pass

    def load(self, deployment: ModelDeploymentConfig) -> None:
        """Loads a model deployment into the runtime."""
        pass

    def unload(self) -> None:
        """Unloads the currently active model deployment."""
        pass

    def get_active_deployment(self) -> Optional[ModelDeploymentConfig]:
        """Returns the currently active model deployment configuration if any."""
        return None

    def is_loaded(self) -> bool:
        """Returns True if a model deployment is currently loaded and ready."""
        return self.get_status() == RuntimeStatus.READY

    def switch(self, deployment: ModelDeploymentConfig) -> None:
        """Sequentially switches from current deployment to the target deployment."""
        self.unload()
        self.load(deployment)

class ModelGateway:
    """Entry point for the Agent Host to interact with models."""
    
    def __init__(self, adapter: ModelAdapter):
        self._adapter = adapter
        
    def get_status(self) -> RuntimeStatus:
        return self._adapter.get_status()
        
    def get_model_info(self) -> ModelInfo:
        return self._adapter.get_model_info()
        
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        return self._adapter.generate(request)
        
    def stream(self, request: InferenceRequest) -> Generator[StreamingResponseChunk, None, None]:
        return self._adapter.stream(request)

    def load(self, deployment: ModelDeploymentConfig) -> None:
        """Loads a model deployment sequentially."""
        self._adapter.load(deployment)

    def unload(self) -> None:
        """Unloads the active model deployment."""
        self._adapter.unload()

    def get_active_deployment(self) -> Optional[ModelDeploymentConfig]:
        """Returns active model deployment configuration."""
        return self._adapter.get_active_deployment()

    def is_loaded(self) -> bool:
        """Returns True if a model deployment is loaded and ready."""
        return self._adapter.is_loaded()

    def switch(self, deployment: ModelDeploymentConfig) -> None:
        """Sequentially switches to a new deployment."""
        self._adapter.switch(deployment)
