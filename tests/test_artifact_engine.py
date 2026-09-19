"""Tests for LocalArtifactEngine."""
import pytest
from pathlib import Path
from sovereign.infrastructure.artifacts.storage import LocalArtifactStorage
from sovereign.infrastructure.artifacts.engine import LocalArtifactEngine
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType, ArtifactStatus
from sovereign.core.state.models import Task, Finding, EvidenceReference
from sovereign.infrastructure.config import get_settings

@pytest.fixture
def temp_db(tmp_path):
    return tmp_path / "test.db"

@pytest.fixture
def repo(temp_db):
    return SQLiteTaskRepository(db_path=temp_db)

@pytest.fixture
def engine(monkeypatch, tmp_path, repo):
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_dir_name", str(tmp_path / "artifacts"))
    storage = LocalArtifactStorage()
    return LocalArtifactEngine(repo, storage)

def test_engine_generation_and_isolation(engine, repo):
    # Create Task State
    task = Task(title="T1", goal="G1")
    repo.create_task(task)
    
    ev = EvidenceReference(source_id="d1", locator="p1", metadata={"text": "e1"})
    repo.add_evidence(task.task_id, ev)
    repo.add_state_item(task.task_id, Finding(statement="F1", confidence="high", evidence_refs=[ev.evidence_id]))
    
    # Take a snapshot of state before generation
    pre_items = repo.get_state_items(task.task_id)
    pre_ev = repo.get_evidence(task.task_id)
    
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.MARKDOWN, title="Report")
    
    # Generate
    artifact = engine.generate(req)
    
    assert artifact.status == ArtifactStatus.COMPLETED
    assert len(artifact.source_references) == 1
    assert artifact.source_references[0].source_id == "d1"
    assert artifact.source_references[0].locator == "p1"
    
    assert Path(artifact.metadata.file_path).exists()
    content = Path(artifact.metadata.file_path).read_text(encoding="utf-8")
    assert "F1" in content
    
    # Verify State Isolation (Task State is unmodified)
    post_items = repo.get_state_items(task.task_id)
    post_ev = repo.get_evidence(task.task_id)
    
    assert len(pre_items) == len(post_items)
    assert len(pre_ev) == len(post_ev)
    
def test_engine_no_fabrication(engine, repo):
    task = Task(title="T1", goal="G1")
    repo.create_task(task)
    # Finding with no evidence
    repo.add_state_item(task.task_id, Finding(statement="Floating fact", confidence="high"))
    
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.JSON, title="Report")
    artifact = engine.generate(req)
    
    assert artifact.status == ArtifactStatus.COMPLETED
    assert len(artifact.source_references) == 0  # No provenance fabricated
    
def test_engine_restart(engine, repo, monkeypatch, tmp_path):
    task = Task(title="T1", goal="G1")
    repo.create_task(task)
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.MARKDOWN, title="Report")
    
    art1 = engine.generate(req)
    assert art1.status == ArtifactStatus.COMPLETED
    
    # Destroy engine
    del engine
    
    # Recreate
    storage2 = LocalArtifactStorage()
    engine2 = LocalArtifactEngine(repo, storage2)
    
    art2 = storage2.get_artifact(art1.artifact_id)
    assert art2 is not None
    assert art2.title == "Report"
    assert Path(art2.metadata.file_path).exists()

def test_engine_handles_missing_task(engine):
    req = ArtifactRequest(task_id="invalid", artifact_type=ArtifactType.MARKDOWN, title="Missing")
    art = engine.generate(req)
    assert art.status == ArtifactStatus.FAILED
    assert art.metadata is None
