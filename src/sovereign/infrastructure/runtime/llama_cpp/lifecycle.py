"""Llama-server process lifecycle management."""

import os
import subprocess
import time
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
import shutil

from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.logging import get_logger
from sovereign.core.runtime.models import RuntimeStatus, LifecycleState, ModelDeploymentConfig
from sovereign.core.exceptions import ModelRuntimeError, ConfigurationError

logger = get_logger("sovereign.llama_cpp.lifecycle")

class LlamaServerLifecycle:
    """Manages the lifecycle of the local llama-server process with sequential model swapping."""
    
    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._active_deployment: Optional[ModelDeploymentConfig] = None
        self._lifecycle_state: LifecycleState = LifecycleState.UNLOADED
        self._lock = threading.RLock()
        
    def _is_server_responding(self, host: str, port: int) -> bool:
        url = f"http://{host}:{port}/health"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1) as response:
                return response.status == 200
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            return False

    @property
    def lifecycle_state(self) -> LifecycleState:
        with self._lock:
            return self._lifecycle_state

    @property
    def active_deployment(self) -> Optional[ModelDeploymentConfig]:
        with self._lock:
            return self._active_deployment
            
    def get_status(self) -> RuntimeStatus:
        with self._lock:
            settings = get_settings()
            
            # If we have an active deployment, check against it
            if self._active_deployment is not None:
                host = self._active_deployment.server_host
                port = self._active_deployment.server_port
                if self._is_server_responding(host, port):
                    return RuntimeStatus.READY
                if self._process is not None and self._process.poll() is None:
                    return RuntimeStatus.STARTING
                if self._process is not None and self._process.poll() is not None:
                    return RuntimeStatus.ERROR
                if self._lifecycle_state == LifecycleState.FAILED:
                    return RuntimeStatus.ERROR
                return RuntimeStatus.SERVER_NOT_RUNNING
                
            # Default / unconfigured checks
            if not settings.llama_server_path or not settings.model_path:
                return RuntimeStatus.NOT_CONFIGURED
                
            executable = Path(settings.llama_server_path)
            if not executable.exists() and not shutil.which(settings.llama_server_path):
                return RuntimeStatus.NOT_CONFIGURED
                 
            model_file = Path(settings.model_path)
            if not model_file.exists():
                return RuntimeStatus.MODEL_NOT_FOUND
                
            if self._is_server_responding(settings.server_host, settings.server_port):
                return RuntimeStatus.READY
                
            if self._process is not None and self._process.poll() is None:
                return RuntimeStatus.STARTING
                
            if self._process is not None and self._process.poll() is not None:
                return RuntimeStatus.ERROR
                
            if self._lifecycle_state == LifecycleState.FAILED:
                return RuntimeStatus.ERROR
                
            return RuntimeStatus.SERVER_NOT_RUNNING

    def _validate_deployment_config(self, deployment: ModelDeploymentConfig) -> None:
        """Validates that deployment configuration is well-formed and files exist."""
        settings = get_settings()
        exec_path = settings.llama_server_path
        if not exec_path:
            raise ConfigurationError("llama_server_path is not configured.")
            
        executable = Path(exec_path)
        if not executable.exists() and not shutil.which(exec_path):
            raise ConfigurationError(f"llama-server executable not found at: {exec_path}")
            
        model_file = Path(deployment.model_path)
        if not model_file.exists():
            raise ModelRuntimeError(f"Model file not found: {deployment.model_path}")

    def load(self, deployment: ModelDeploymentConfig) -> None:
        """Sequentially loads a model deployment."""
        with self._lock:
            # 1. Validate requested deployment configuration
            self._validate_deployment_config(deployment)
            
            # If already active and healthy, no-op
            if (self._active_deployment == deployment and 
                self._lifecycle_state == LifecycleState.LOADED and
                self._is_server_responding(deployment.server_host, deployment.server_port)):
                logger.info(f"Deployment '{deployment.model_name}' is already active and healthy.")
                return
                
            # 2. Stop any existing server cleanly
            self._unload_internal()
            
            # 3. Transition to LOADING
            self._lifecycle_state = LifecycleState.LOADING
            settings = get_settings()
            executable = settings.llama_server_path
            
            cmd = [
                executable,
                "-m", str(deployment.model_path),
                "--port", str(deployment.server_port),
                "--host", deployment.server_host,
                "-c", str(deployment.context_size),
                "-ngl", str(deployment.gpu_layers)
            ]
            
            if deployment.mmproj_path:
                cmd.extend(["--mmproj", str(deployment.mmproj_path)])
                
            logger.info(f"Loading deployment '{deployment.model_name}' with command: {' '.join(cmd)}")
            
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                self._lifecycle_state = LifecycleState.FAILED
                self._active_deployment = None
                self._process = None
                logger.error(f"Failed to spawn llama-server process: {e}")
                raise ModelRuntimeError(f"Failed to spawn llama-server for deployment '{deployment.model_name}': {e}") from e

            # 4. Wait for readiness
            timeout = 30
            start_time = time.time()
            ready = False
            while time.time() - start_time < timeout:
                if self._is_server_responding(deployment.server_host, deployment.server_port):
                    ready = True
                    break
                if self._process.poll() is not None:
                    break
                time.sleep(0.5)
                
            if ready:
                self._active_deployment = deployment
                self._lifecycle_state = LifecycleState.LOADED
                logger.info(f"Deployment '{deployment.model_name}' loaded successfully and is ready.")
            else:
                self._unload_internal()
                self._active_deployment = None
                self._lifecycle_state = LifecycleState.FAILED
                logger.error(f"Failed to initialize deployment '{deployment.model_name}'.")
                raise ModelRuntimeError(f"Failed to initialize deployment '{deployment.model_name}' (process exited or timed out).")

    def unload(self) -> None:
        """Unloads the active model deployment."""
        with self._lock:
            self._unload_internal()

    def _unload_internal(self) -> None:
        """Internal helper to stop process and reset active deployment."""
        if self._process is not None:
            self._lifecycle_state = LifecycleState.UNLOADING
            logger.info("Stopping active llama-server deployment...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)
            self._process = None
            logger.info("llama-server stopped.")
            
        self._active_deployment = None
        self._lifecycle_state = LifecycleState.UNLOADED

    def switch(self, deployment: ModelDeploymentConfig) -> None:
        """Sequentially switches from active deployment to target deployment."""
        with self._lock:
            # Step 1: Pre-validate target deployment before touching active deployment
            self._validate_deployment_config(deployment)
            
            # Step 2: Unload and load new deployment
            logger.info(f"Switching deployment to '{deployment.model_name}'...")
            self.load(deployment)

    def start(self) -> None:
        """Starts the default configured model deployment for backward compatibility."""
        with self._lock:
            if self.get_status() == RuntimeStatus.READY:
                return
            settings = get_settings()
            default_deployment = ModelDeploymentConfig(
                model_name=settings.model_name,
                model_path=settings.model_path,
                device=settings.model_device,
                gpu_layers=settings.gpu_layers,
                context_size=settings.context_size,
                server_host=settings.server_host,
                server_port=settings.server_port
            )
            self.load(default_deployment)

    def stop(self) -> None:
        """Stops the local server."""
        with self._lock:
            self.unload()
