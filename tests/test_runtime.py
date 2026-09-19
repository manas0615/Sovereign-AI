import pytest
import json
from sovereign.core.runtime.models import InferenceRequest, RuntimeStatus
from sovereign.core.exceptions import ContextOverflowError
from sovereign.infrastructure.runtime.llama_cpp.client import LlamaCppClient

def test_client_context_overflow(monkeypatch):
    import sovereign.infrastructure.config as config
    # Mock settings
    class MockSettings:
        server_host = "127.0.0.1"
        server_port = 8080
        context_size = 100
        
    monkeypatch.setattr("sovereign.infrastructure.runtime.llama_cpp.client.get_settings", lambda: MockSettings())
    client = LlamaCppClient()
    
    # 400 chars is roughly 100 tokens, plus max_tokens=10 => overflow
    request = InferenceRequest(prompt="a" * 600, max_tokens=10)
    
    with pytest.raises(ContextOverflowError) as exc_info:
        client._build_payload(request)
        
    assert "Estimated tokens exceed" in str(exc_info.value)

def test_normal_inference_payload():
    client = LlamaCppClient()
    request = InferenceRequest(prompt="Hello world", max_tokens=64, temperature=0.7, stop=["\n"])
    payload = json.loads(client._build_payload(request).decode("utf-8"))
    assert payload["prompt"] == "Hello world"
    assert payload["n_predict"] == 64
    assert payload["temperature"] == 0.7
    assert payload["stop"] == ["\n"]
    assert "messages" not in payload
    assert "response_format" not in payload

def test_structured_inference_payload():
    client = LlamaCppClient()
    custom_format = {"type": "json_object"}
    request = InferenceRequest(prompt="Hello JSON", max_tokens=128, temperature=0.2, response_format=custom_format)
    payload = json.loads(client._build_chat_payload(request).decode("utf-8"))
    assert payload["messages"] == [{"role": "user", "content": "Hello JSON"}]
    assert payload["max_tokens"] == 128
    assert payload["temperature"] == 0.2
    assert payload["response_format"] == custom_format
    assert "prompt" not in payload

def test_generate_routing_and_response_parsing(monkeypatch):
    import io
    client = LlamaCppClient()
    
    # 1. Test normal generate (response_format=None)
    called_urls = []
    def mock_urlopen_completion(req):
        called_urls.append(req.full_url)
        res_data = {
            "content": "normal text",
            "tokens_evaluated": 5,
            "tokens_predicted": 2,
            "stop_type": "limit"
        }
        return io.BytesIO(json.dumps(res_data).encode("utf-8"))
        
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_completion)
    req_norm = InferenceRequest(prompt="Hello")
    resp_norm = client.generate(req_norm)
    assert resp_norm.text == "normal text"
    assert resp_norm.usage == {"prompt_tokens": 5, "completion_tokens": 2}
    assert resp_norm.stop_reason == "limit"
    assert any("/completion" in url for url in called_urls)
    
    # 2. Test structured generate (response_format provided)
    called_urls.clear()
    def mock_urlopen_chat(req):
        called_urls.append(req.full_url)
        res_data = {
            "choices": [
                {
                    "message": {"content": '{"result": 123}'},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8
            }
        }
        return io.BytesIO(json.dumps(res_data).encode("utf-8"))
        
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_chat)
    req_struct = InferenceRequest(prompt="Hello", response_format={"type": "json_object"})
    resp_struct = client.generate(req_struct)
    assert resp_struct.text == '{"result": 123}'
    assert resp_struct.usage == {"prompt_tokens": 10, "completion_tokens": 8}
    assert resp_struct.stop_reason == "stop"
    assert any("/v1/chat/completions" in url for url in called_urls)

def test_package_01_has_no_agent_decision_coupling():
    import sovereign.core.runtime.models as m
    import sovereign.core.runtime.gateway as g
    import sovereign.infrastructure.runtime.llama_cpp.client as c
    import sovereign.infrastructure.runtime.llama_cpp.adapter as a
    
    for mod in [m, g, c, a]:
        source = open(mod.__file__, "r", encoding="utf-8").read()
        assert "AgentDecision" not in source
        assert "AGENT_DECISION" not in source

def test_multimodal_inference_payload():
    client = LlamaCppClient()
    request = InferenceRequest(
        prompt="Describe these images",
        images=["data:image/png;base64,AAA=", "data:image/jpeg;base64,BBB="]
    )
    payload = json.loads(client._build_chat_payload(request).decode("utf-8"))
    
    assert "messages" in payload
    messages = payload["messages"]
    assert len(messages) == 1
    content = messages[0]["content"]
    
    assert isinstance(content, list)
    assert len(content) == 3
    assert content[0] == {"type": "text", "text": "Describe these images"}
    assert content[1] == {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA="}}
    assert content[2] == {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,BBB="}}

def test_mmproj_absent_and_configured(monkeypatch):
    import subprocess
    from sovereign.core.runtime.models import ModelDeploymentConfig
    from sovereign.infrastructure.runtime.llama_cpp.lifecycle import LlamaServerLifecycle
    
    lifecycle = LlamaServerLifecycle()
    
    spawned_cmds = []
    
    class DummyProcess:
        def poll(self): return None
        def wait(self, timeout=None): pass
        def kill(self): pass
        def terminate(self): pass
        
    def mock_popen(cmd, *args, **kwargs):
        spawned_cmds.append(cmd)
        return DummyProcess()
        
    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    
    # Mock settings to bypass path validation
    import sovereign.infrastructure.config as config
    class MockSettings:
        llama_server_path = "mock-server.exe"
    monkeypatch.setattr("sovereign.infrastructure.runtime.llama_cpp.lifecycle.get_settings", lambda: MockSettings())
    
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    monkeypatch.setattr("shutil.which", lambda x: True)
    
    # Mock readiness check
    monkeypatch.setattr(lifecycle, "_is_server_responding", lambda h, p: True)
    
    # 1. Without mmproj
    deployment_no_mmproj = ModelDeploymentConfig(
        model_name="test-model",
        model_path="/fake/model.gguf"
    )
    lifecycle.load(deployment_no_mmproj)
    
    assert len(spawned_cmds) == 1
    cmd = spawned_cmds[0]
    assert "--mmproj" not in cmd
    
    # Reset
    lifecycle.unload()
    spawned_cmds.clear()
    
    # 2. With mmproj
    deployment_with_mmproj = ModelDeploymentConfig(
        model_name="test-vision-model",
        model_path="/fake/model.gguf",
        mmproj_path="/fake/projector.gguf"
    )
    lifecycle.load(deployment_with_mmproj)
    
    assert len(spawned_cmds) == 1
    cmd = spawned_cmds[0]
    assert "--mmproj" in cmd
    mmproj_idx = cmd.index("--mmproj")
    assert cmd[mmproj_idx + 1] == "/fake/projector.gguf"

