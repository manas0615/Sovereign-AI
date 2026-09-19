"""Llama.cpp adapter implementation."""

from typing import Generator, Optional
from sovereign.core.runtime.gateway import ModelAdapter
from sovereign.core.runtime.models import (
    InferenceRequest,
    InferenceResponse,
    StreamingResponseChunk,
    ModelInfo,
    RuntimeStatus,
    LifecycleState,
    ModelDeploymentConfig
)
from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.runtime.llama_cpp.lifecycle import LlamaServerLifecycle
from sovereign.infrastructure.runtime.llama_cpp.client import LlamaCppClient
from sovereign.core.exceptions import ModelRuntimeError

class LlamaCppAdapter(ModelAdapter):
    """Adapter for local llama-server supporting sequential model swapping."""
    
    def __init__(self):
        self._lifecycle = LlamaServerLifecycle()
        self._client = LlamaCppClient()
        
    def get_status(self) -> RuntimeStatus:
        return self._lifecycle.get_status()
        
    def get_model_info(self) -> ModelInfo:
        active = self._lifecycle.active_deployment
        if active is not None:
            return ModelInfo(
                name=active.model_name,
                path=active.model_path,
                backend=active.backend,
                device=active.device,
                gpu_layers=active.gpu_layers,
                context_size=active.context_size
            )
        settings = get_settings()
        return ModelInfo(
            name=settings.model_name,
            path=settings.model_path,
            backend="llama.cpp",
            device=settings.model_device,
            gpu_layers=settings.gpu_layers,
            context_size=settings.context_size
        )

    def load(self, deployment: ModelDeploymentConfig) -> None:
        """Loads a model deployment into the runtime."""
        self._lifecycle.load(deployment)
        self._client.set_endpoint(deployment.server_host, deployment.server_port)

    def unload(self) -> None:
        """Unloads the active model deployment."""
        self._lifecycle.unload()

    def get_active_deployment(self) -> Optional[ModelDeploymentConfig]:
        """Returns the currently active deployment."""
        return self._lifecycle.active_deployment

    def is_loaded(self) -> bool:
        """Returns True if a model deployment is loaded and ready."""
        return self._lifecycle.lifecycle_state == LifecycleState.LOADED and self.get_status() == RuntimeStatus.READY

    def switch(self, deployment: ModelDeploymentConfig) -> None:
        """Sequentially switches from active deployment to target deployment."""
        self._lifecycle.switch(deployment)
        self._client.set_endpoint(deployment.server_host, deployment.server_port)
        
    def generate(self, request: InferenceRequest) -> InferenceResponse:
        status = self.get_status()
        if status != RuntimeStatus.READY:
            if self._lifecycle.active_deployment is None and status not in (RuntimeStatus.NOT_CONFIGURED, RuntimeStatus.MODEL_NOT_FOUND):
                # Try starting default configured model
                self._lifecycle.start()
                
            if self.get_status() != RuntimeStatus.READY:
                raise ModelRuntimeError(f"Cannot generate: Runtime status is {self.get_status().value}")
                
        active = self._lifecycle.active_deployment
        if active is not None:
            self._client.set_endpoint(active.server_host, active.server_port)
            return self._client.generate(request, context_size=active.context_size)
            
        return self._client.generate(request)
        
    def stream(self, request: InferenceRequest) -> Generator[StreamingResponseChunk, None, None]:
        status = self.get_status()
        if status != RuntimeStatus.READY:
            if self._lifecycle.active_deployment is None and status not in (RuntimeStatus.NOT_CONFIGURED, RuntimeStatus.MODEL_NOT_FOUND):
                self._lifecycle.start()
                
            if self.get_status() != RuntimeStatus.READY:
                raise ModelRuntimeError(f"Cannot stream: Runtime status is {self.get_status().value}")
                
        active = self._lifecycle.active_deployment
        if active is not None:
            self._client.set_endpoint(active.server_host, active.server_port)
            return self._client.stream(request, context_size=active.context_size)
            
        return self._client.stream(request)
