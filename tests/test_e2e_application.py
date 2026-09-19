import pytest
import time
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service

client = TestClient(app)

@pytest.fixture
def e2e_app_service(tmp_path, monkeypatch):
    svc = get_app_service()
    settings = svc.artifact_storage.settings
    
    monkeypatch.setattr(settings, "db_filename", "e2e_state.db")
    monkeypatch.setattr(settings, "artifact_dir_name", str(tmp_path / "artifacts"))
    monkeypatch.setattr("sovereign.infrastructure.paths.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sovereign.infrastructure.paths.get_artifact_dir", lambda: tmp_path / "artifacts")
    
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    
    import sovereign.application.services as svcs
    svcs._app_service = None
    svc = get_app_service()
    
    from sovereign.core.runtime.models import InferenceRequest, InferenceResponse

    class MockGateway:
        def __init__(self, *args, **kwargs):
            pass
        def generate(self, request: InferenceRequest) -> InferenceResponse:
            return InferenceResponse(text='{"action": "FINAL", "answer": "The valve is closed.", "rationale": "I found the info."}', usage={}, stop_reason="stop")
        def get_status(self):
            from sovereign.core.runtime.models import RuntimeStatus
            return RuntimeStatus.READY
        def get_model_info(self):
            from sovereign.core.runtime.models import ModelInfo
            return ModelInfo(name="mock", path="mock", backend="mock", device="mock", gpu_layers=0, context_size=8192)
            
    svc.gateway = MockGateway()
    svc.agent.model = svc.gateway
    
    yield svc
    svcs._app_service = None

def test_synthetic_e2e_workflow(e2e_app_service):
    e2e_app_service.authority_evaluator.policy.allow_unqualified = True
    res = client.post("/api/v1/tasks", json={"title": "E2E Task", "goal": "Check the valve"})
    assert res.status_code == 200
    task_id = res.json()["task_id"]

    res = client.post("/api/v1/knowledge/documents", files={"file": ("valve.txt", b"The valve is currently closed.")})
    assert res.status_code == 200
    assert "document_id" in res.json()
    assert res.json()["status"] == "INGESTED"

    res = client.post(f"/api/v1/tasks/{task_id}/run")
    assert res.status_code == 200
    assert res.json()["status"] == "ACCEPTED"

    # Wait for background thread
    time.sleep(1)

    res = client.get(f"/api/v1/tasks/{task_id}")
    assert res.status_code == 200
    task_data = res.json()
    assert task_data["status"] == "COMPLETED"
    assert task_data["latest_decision"] == "FINAL"
    assert task_data["findings_count"] == 1

    from sovereign.infrastructure.artifacts.engine import LocalArtifactEngine
    from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType

    engine = LocalArtifactEngine(e2e_app_service.repo, e2e_app_service.artifact_storage)
    req = ArtifactRequest(
        task_id=task_id,
        artifact_type=ArtifactType.MARKDOWN,
        title="E2E Report",
        requested_sections=["findings"]
    )
    artifact = engine.generate(req)

    res = client.get(f"/api/v1/tasks/{task_id}/artifacts")
    assert res.status_code == 200
    artifacts = res.json()
    assert any(a["artifact_id"] == artifact.artifact_id for a in artifacts)
    
    # Verify auto-generated DOCX deliverable exists and has correct MIME type
    docx_artifacts = [a for a in artifacts if a.get("type") == "DOCX"]
    assert len(docx_artifacts) >= 1
    docx_art = docx_artifacts[0]
    
    res_docx = client.get(f"/api/v1/artifacts/{docx_art['artifact_id']}")
    assert res_docx.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in res_docx.headers.get("content-type", "")
    assert res_docx.content.startswith(b"PK\x03\x04")  # Valid Zip / OOXML signature

    res = client.get(f"/api/v1/artifacts/{artifact.artifact_id}")
    assert res.status_code == 200
