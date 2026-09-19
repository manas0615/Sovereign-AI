"""Tests for artifact domain models."""
import pytest
from sovereign.core.artifacts.models import ArtifactType, ArtifactStatus, ArtifactRequest

def test_valid_artifact_request():
    req = ArtifactRequest(task_id="t1", artifact_type=ArtifactType.MARKDOWN, title="Report")
    assert req.task_id == "t1"
    assert req.artifact_type == ArtifactType.MARKDOWN
    assert req.title == "Report"
    assert "findings" in req.requested_sections
    
    # Should not raise
    req.validate_sections()

def test_invalid_artifact_request_sections():
    req = ArtifactRequest(task_id="t1", artifact_type=ArtifactType.MARKDOWN, title="Report", requested_sections=["invalid_section"])
    with pytest.raises(ValueError, match="Unknown section requested: invalid_section"):
        req.validate_sections()

def test_status_transitions():
    # Simple check on Enums
    assert ArtifactStatus.GENERATING.value == "GENERATING"
    assert ArtifactStatus.COMPLETED.value == "COMPLETED"
    assert ArtifactStatus.FAILED.value == "FAILED"
