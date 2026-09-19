import pytest
import io
import json
import threading
import time
from pathlib import Path
from sovereign.core.runtime.models import (
    InferenceRequest, InferenceResponse, ModelDeploymentConfig,
    LifecycleState, RuntimeStatus, ModelInfo
)
from sovereign.core.runtime.gateway import ModelGateway, ModelAdapter
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.infrastructure.runtime.llama_cpp.lifecycle import LlamaServerLifecycle
from sovereign.core.exceptions import ModelRuntimeError, ConfigurationError

class MockSequentialAdapter(ModelAdapter):
    """Mock adapter to test sequential swapping state machine deterministically."""
    def __init__(self):
        self._active_deployment = None
        self._state = LifecycleState.UNLOADED
        self._lock = threading.RLock()
        self._fail_load = False

    def get_status(self) -> RuntimeStatus:
        with self._lock:
            if self._state == LifecycleState.LOADED:
                return RuntimeStatus.READY
            if self._state == LifecycleState.LOADING:
                return RuntimeStatus.STARTING
            if self._state == LifecycleState.FAILED:
                return RuntimeStatus.ERROR
            return RuntimeStatus.SERVER_NOT_RUNNING

    def get_model_info(self) -> ModelInfo:
        with self._lock:
            if self._active_deployment:
                d = self._active_deployment
                return ModelInfo(
                    name=d.model_name,
                    path=d.model_path,
                    backend=d.backend,
                    device=d.device,
                    gpu_layers=d.gpu_layers,
                    context_size=d.context_size
                )
            return ModelInfo(
                name="none",
                path="none",
                backend="none",
                device="none",
                gpu_layers=0,
                context_size=0
            )

    def load(self, deployment: ModelDeploymentConfig) -> None:
        with self._lock:
            if not Path(deployment.model_path).exists() and not deployment.model_path.startswith("mock://"):
                self._state = LifecycleState.FAILED
                raise ModelRuntimeError(f"Model file not found: {deployment.model_path}")
            
            if self._fail_load:
                self._state = LifecycleState.FAILED
                self._active_deployment = None
                raise ModelRuntimeError("Simulated load failure")

            self.unload()
            self._state = LifecycleState.LOADING
            # simulate load
            self._active_deployment = deployment
            self._state = LifecycleState.LOADED

    def unload(self) -> None:
        with self._lock:
            self._active_deployment = None
            self._state = LifecycleState.UNLOADED

    def get_active_deployment(self):
        with self._lock:
            return self._active_deployment

    def is_loaded(self) -> bool:
        with self._lock:
            return self._state == LifecycleState.LOADED

    def switch(self, deployment: ModelDeploymentConfig) -> None:
        with self._lock:
            if not Path(deployment.model_path).exists() and not deployment.model_path.startswith("mock://"):
                raise ModelRuntimeError(f"Model file not found: {deployment.model_path}")
            self.load(deployment)

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        with self._lock:
            if not self.is_loaded():
                raise ModelRuntimeError("Cannot generate: No valid active deployment is loaded.")
            return InferenceResponse(
                text=f"Response from {self._active_deployment.model_name}: {request.prompt}",
                usage={"prompt_tokens": 5, "completion_tokens": 10},
                stop_reason="stop"
            )

    def stream(self, request: InferenceRequest):
        pass


def test_sequential_swapping_full_lifecycle(tmp_path):
    # Setup dummy model files
    model_a_file = tmp_path / "model_a.gguf"
    model_a_file.write_bytes(b"MODEL_A_BYTES")
    model_b_file = tmp_path / "model_b.gguf"
    model_b_file.write_bytes(b"MODEL_B_BYTES")

    dep_a = ModelDeploymentConfig(
        model_name="Model_A_3B",
        model_path=str(model_a_file),
        context_size=4096,
        gpu_layers=10
    )
    dep_b = ModelDeploymentConfig(
        model_name="Model_B_8B",
        model_path=str(model_b_file),
        context_size=8192,
        gpu_layers=20
    )

    adapter = MockSequentialAdapter()
    gateway = ModelGateway(adapter)

    # 1. Initial unloaded state
    assert not gateway.is_loaded()
    assert gateway.get_active_deployment() is None
    assert gateway.get_status() == RuntimeStatus.SERVER_NOT_RUNNING

    # 13. Inference while unloaded must fail
    with pytest.raises(ModelRuntimeError) as exc:
        gateway.generate(InferenceRequest(prompt="Hello"))
    assert "No valid active deployment" in str(exc.value)

    # 2. Load deployment A
    gateway.load(dep_a)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model_A_3B"
    assert gateway.get_model_info().name == "Model_A_3B"
    assert gateway.get_status() == RuntimeStatus.READY

    # 3. Inference using A
    resp_a = gateway.generate(InferenceRequest(prompt="Test prompt 1"))
    assert "Response from Model_A_3B" in resp_a.text

    # 4. Unload A
    gateway.unload()

    # 5. Verify unloaded state
    assert not gateway.is_loaded()
    assert gateway.get_active_deployment() is None
    assert gateway.get_status() == RuntimeStatus.SERVER_NOT_RUNNING

    # 6. Load deployment B
    gateway.load(dep_b)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model_B_8B"
    assert gateway.get_model_info().context_size == 8192

    # 7. Inference using B
    resp_b = gateway.generate(InferenceRequest(prompt="Test prompt 2"))
    assert "Response from Model_B_8B" in resp_b.text

    # 8. Unload B
    gateway.unload()
    assert not gateway.is_loaded()

    # 9. Reload A (using switch directly or load)
    gateway.switch(dep_a)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model_A_3B"

    # 10. Inference using A after reload
    resp_a2 = gateway.generate(InferenceRequest(prompt="Test prompt 3"))
    assert "Response from Model_A_3B" in resp_a2.text

    # 11. Invalid deployment configuration (non-existent file)
    bad_dep = ModelDeploymentConfig(
        model_name="BadModel",
        model_path=str(tmp_path / "non_existent.gguf")
    )
    with pytest.raises(ModelRuntimeError) as exc_info:
        gateway.switch(bad_dep)
    assert "not found" in str(exc_info.value)

    # 12 & 14. Failed model load and failed switch handling
    adapter._fail_load = True
    with pytest.raises(ModelRuntimeError):
        gateway.load(dep_b)
    
    # Ensure system does NOT report B as active when load fails!
    assert not gateway.is_loaded()
    assert gateway.get_active_deployment() is None
    assert gateway.get_status() == RuntimeStatus.ERROR

    # 15. Lifecycle state consistency
    adapter._fail_load = False
    gateway.load(dep_a)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model_A_3B"
    gateway.unload()
    assert not gateway.is_loaded()


def test_concurrent_lifecycle_protection(tmp_path):
    # 16. Concurrent lifecycle protection
    model_file = tmp_path / "model.gguf"
    model_file.write_bytes(b"BYTES")

    dep = ModelDeploymentConfig(model_name="ConcurrentTest", model_path=str(model_file))
    adapter = MockSequentialAdapter()
    gateway = ModelGateway(adapter)

    errors = []
    def worker_load():
        try:
            for _ in range(10):
                gateway.load(dep)
                time.sleep(0.01)
                gateway.unload()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker_load) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert not gateway.is_loaded()


def test_llama_cpp_adapter_and_lifecycle_mocked(tmp_path, monkeypatch):
    model_file_1 = tmp_path / "model1.gguf"
    model_file_1.write_bytes(b"MODEL1")
    model_file_2 = tmp_path / "model2.gguf"
    model_file_2.write_bytes(b"MODEL2")

    dep1 = ModelDeploymentConfig(
        model_name="Model1",
        model_path=str(model_file_1),
        server_host="127.0.0.1",
        server_port=8080,
        context_size=2048,
        gpu_layers=10
    )
    dep2 = ModelDeploymentConfig(
        model_name="Model2",
        model_path=str(model_file_2),
        server_host="127.0.0.1",
        server_port=8081,
        context_size=4096,
        gpu_layers=20
    )

    class MockProcess:
        def __init__(self):
            self.terminated = False
            self.killed = False

        def poll(self):
            return None if not self.terminated and not self.killed else 0

        def terminate(self):
            self.terminated = True

        def kill(self):
            self.killed = True

        def wait(self, timeout=None):
            return 0

    running_servers = set()

    def mock_popen(cmd, *args, **kwargs):
        # find port in cmd
        port = int(cmd[cmd.index("--port") + 1])
        running_servers.add(port)
        return MockProcess()

    def mock_is_server_responding(self, host, port):
        return port in running_servers

    monkeypatch.setattr("subprocess.Popen", mock_popen)
    monkeypatch.setattr(LlamaServerLifecycle, "_is_server_responding", mock_is_server_responding)

    def mock_urlopen(req, *args, **kwargs):
        # Return completion response
        res_data = {
            "content": "Inference output",
            "tokens_evaluated": 5,
            "tokens_predicted": 10,
            "stop_type": "limit"
        }
        return io.BytesIO(json.dumps(res_data).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)

    # 1. Initially unloaded
    assert not gateway.is_loaded()

    # 2. Load dep1
    gateway.load(dep1)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model1"
    info1 = gateway.get_model_info()
    assert info1.name == "Model1"
    assert info1.context_size == 2048

    # 3. Generate on dep1
    resp1 = gateway.generate(InferenceRequest(prompt="Test dep1"))
    assert resp1.text == "Inference output"

    # 4. Switch to dep2
    gateway.switch(dep2)
    assert gateway.is_loaded()
    assert gateway.get_active_deployment().model_name == "Model2"
    info2 = gateway.get_model_info()
    assert info2.name == "Model2"
    assert info2.context_size == 4096

    # 5. Generate on dep2
    resp2 = gateway.generate(InferenceRequest(prompt="Test dep2"))
    assert resp2.text == "Inference output"

    # 6. Unload
    gateway.unload()
    assert not gateway.is_loaded()
    assert gateway.get_active_deployment() is None

