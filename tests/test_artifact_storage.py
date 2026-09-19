"""Tests for LocalArtifactStorage."""
import pytest
from pathlib import Path
from sovereign.infrastructure.artifacts.storage import LocalArtifactStorage
from sovereign.core.exceptions import InfrastructureError
from sovereign.infrastructure.config import get_settings
from sovereign.core.artifacts.models import Artifact, ArtifactStatus, ArtifactType, ArtifactMetadata

@pytest.fixture
def storage(monkeypatch, tmp_path):
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_dir_name", str(tmp_path / "artifacts"))
    monkeypatch.setattr(settings, "max_artifact_size_bytes", 1024) # 1 KB
    return LocalArtifactStorage()

def test_storage_initialization(storage):
    assert storage.artifact_dir.exists()
    assert storage.manifest_path.exists()
    
def test_path_traversal_rejection(storage):
    with pytest.raises(InfrastructureError, match="Path traversal detected"):
        storage.resolve_secure_path("../../../windows/system32/cmd.exe")
        
def test_unc_path_rejection(storage):
    with pytest.raises(InfrastructureError, match="Path traversal detected"):
        storage.resolve_secure_path("\\\\localhost\\C$\\windows")

def test_write_artifact_success(storage):
    path = storage.write_artifact_file("test1.md", "hello world")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "hello world"

def test_atomic_failure_cleanup(storage, monkeypatch):
    import os
    original_replace = os.replace
    def mock_replace(src, dst):
        raise OSError("Simulated write failure")
        
    monkeypatch.setattr(os, "replace", mock_replace)
    
    with pytest.raises(InfrastructureError, match="Simulated write failure"):
        storage.write_artifact_file("fail.md", "content")
        
    # Ensure no partial file exists
    assert not (storage.artifact_dir / "fail.md").exists()
    
    # Check that temp file was cleaned up (storage dir should only contain manifest.json)
    files = list(storage.artifact_dir.iterdir())
    assert len(files) == 1
    assert files[0].name == "manifest.json"

def test_size_limit_rejection(storage):
    content = "a" * 1025 # Exceeds 1 KB
    with pytest.raises(InfrastructureError, match="exceeds maximum limit"):
        storage.write_artifact_file("large.md", content)
        
    assert not (storage.artifact_dir / "large.md").exists()

def test_no_overwrite(storage):
    storage.write_artifact_file("unique.md", "v1")
    with pytest.raises(InfrastructureError, match="already exists"):
        storage.write_artifact_file("unique.md", "v2")

def test_manifest_metadata(storage):
    metadata = ArtifactMetadata(file_path="foo.md", size_bytes=10)
    art = Artifact(task_id="t1", title="A", type=ArtifactType.MARKDOWN, status=ArtifactStatus.COMPLETED, metadata=metadata)
    
    storage.save_artifact_metadata(art)
    
    loaded = storage.get_artifact(art.artifact_id)
    assert loaded is not None
    assert loaded.title == "A"
    assert loaded.metadata.file_path == "foo.md"
