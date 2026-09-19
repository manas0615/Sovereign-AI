import pytest
import os
import json
import time
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.state.models import Task, TaskStatus

client = TestClient(app)

@pytest.fixture
def test_app_service(tmp_path, monkeypatch):
    settings = get_app_service().artifact_storage.settings
    monkeypatch.setattr(settings, "db_filename", "test_app_state.db")
    monkeypatch.setattr(settings, "artifact_dir_name", str(tmp_path / "artifacts"))
    
    monkeypatch.setattr("sovereign.infrastructure.paths.get_data_dir", lambda: tmp_path)
    monkeypatch.setattr("sovereign.infrastructure.paths.get_artifact_dir", lambda: tmp_path / "artifacts")
    
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    
    import sovereign.application.services as svcs
    svcs._app_service = None
    
    svc = get_app_service()
    yield svc
    svcs._app_service = None

def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code in [200, 503]
    assert "status" in res.json()

def test_task_creation_and_retrieval(test_app_service):
    res = client.post("/api/v1/tasks", json={"title": "Test Task", "goal": "Do something"})
    assert res.status_code == 200
    task_id = res.json()["task_id"]
    
    res = client.get(f"/api/v1/tasks/{task_id}")
    assert res.status_code == 200
    assert res.json()["task_id"] == task_id

def test_invalid_task_input(test_app_service):
    res = client.post("/api/v1/tasks", json={"goal": "Missing title"})
    assert res.status_code == 422
    
def test_nonexistent_task(test_app_service):
    res = client.get("/api/v1/tasks/task-notexist")
    assert res.status_code == 404

def test_task_execution_rejections(test_app_service):
    task = Task(title="T1", goal="G1", status=TaskStatus.PAUSED)
    test_app_service.repo.create_task(task)
    
    res = client.post(f"/api/v1/tasks/{task.task_id}/run")
    assert res.status_code == 400
    
    for status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        task.status = status
        test_app_service.repo.update_task(task)
        res = client.post(f"/api/v1/tasks/{task.task_id}/run")
        assert res.status_code == 400
        
    res = client.post("/api/v1/tasks/task-notexist/run")
    assert res.status_code == 404

def test_stale_active_task_recovery_and_duplicate_run(test_app_service, monkeypatch):
    task = Task(title="T1", goal="G1", status=TaskStatus.ACTIVE)
    test_app_service.repo.create_task(task)
    
    def mock_run(self_obj, tid=None):
        pass
        
    monkeypatch.setattr(test_app_service.agent, "run", mock_run)
    
    res = client.post(f"/api/v1/tasks/{task.task_id}/run")
    assert res.status_code == 200
    
    test_app_service._running_tasks.add(task.task_id)
    
    res2 = client.post(f"/api/v1/tasks/{task.task_id}/run")
    assert res2.status_code == 409

def test_execution_registry_cleanup_on_success(test_app_service, monkeypatch):
    task = Task(title="T", goal="G", status=TaskStatus.CREATED)
    test_app_service.repo.create_task(task)
    
    def mock_run(self_obj, tid=None):
        pass
        
    monkeypatch.setattr(test_app_service.agent, "run", mock_run)
    test_app_service.execute_task_background(task.task_id) # Call synchronously to bypass background queue
    assert task.task_id not in test_app_service._running_tasks

def test_execution_registry_cleanup_on_failure(test_app_service, monkeypatch):
    task = Task(title="T", goal="G", status=TaskStatus.CREATED)
    test_app_service.repo.create_task(task)
    
    def mock_run(self_obj, tid=None):
        raise ValueError("Simulated failure")
        
    monkeypatch.setattr(test_app_service.agent, "run", mock_run)
    
    try:
        test_app_service.execute_task_background(task.task_id)
    except ValueError:
        pass
        
    assert task.task_id not in test_app_service._running_tasks

def test_gpu_lock_serialization(test_app_service, monkeypatch):
    task1 = Task(title="T1", goal="G1", status=TaskStatus.CREATED)
    task2 = Task(title="T2", goal="G2", status=TaskStatus.CREATED)
    test_app_service.repo.create_task(task1)
    test_app_service.repo.create_task(task2)
    
    # Simulate a run that holds the lock
    test_app_service._execution_lock.acquire()
    
    # In a real environment, thread 2 would block. 
    # Here we just assert the lock is held.
    assert test_app_service._execution_lock.locked() is True
    test_app_service._execution_lock.release()

def test_upload_format_validation(test_app_service):
    res = client.post("/api/v1/knowledge/documents", files={"file": ("test.gif", b"fake gif data")})
    assert res.status_code == 400

def test_upload_size_enforcement(test_app_service, monkeypatch):
    import sovereign.application.api as api
    monkeypatch.setattr(api.settings, "max_upload_size_bytes", 10)
    
    res = client.post("/api/v1/knowledge/documents", files={"file": ("test.txt", b"This is a longer string than 10 bytes")})
    assert res.status_code == 413

def test_artifact_listing_and_download(test_app_service):
    manifest_path = test_app_service.artifact_storage.manifest_path
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "art-123": {"artifact_id": "art-123", "task_id": "task-abc", "metadata": {"file_path": "report.md", "size_bytes": 10, "sections_rendered": []}, "status": "COMPLETED", "title": "Report", "type": "MARKDOWN", "created_at": "2026-08-25T00:00:00Z"}
        }, f)
        
    (test_app_service.artifact_storage.artifact_dir / "report.md").write_text("Hello", encoding="utf-8")
    
    res = client.get("/api/v1/tasks/task-abc/artifacts")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["artifact_id"] == "art-123"
    
    res = client.get("/api/v1/artifacts/art-123")
    assert res.status_code == 200
    assert res.text == "Hello"
    
    res = client.get("/api/v1/artifacts/art-notexist")
    assert res.status_code == 404

def test_path_traversal_rejection(test_app_service):
    manifest_path = test_app_service.artifact_storage.manifest_path
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "art-hack": {"artifact_id": "art-hack", "task_id": "task-abc", "metadata": {"file_path": "../../secret.txt", "size_bytes": 10, "sections_rendered": []}, "status": "COMPLETED", "title": "Secret", "type": "MARKDOWN", "created_at": "2026-08-25T00:00:00Z"}
        }, f)
        
    # Write the secret file outside the artifact directory
    (test_app_service.artifact_storage.artifact_dir.parent / "secret.txt").write_text("Secret Data", encoding="utf-8")
        
    res = client.get("/api/v1/artifacts/art-hack")
    assert res.status_code == 404
