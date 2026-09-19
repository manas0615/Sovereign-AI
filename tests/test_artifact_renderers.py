"""Tests for deterministic renderers."""
import json
from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
from sovereign.infrastructure.artifacts.renderers import MarkdownRenderer, JsonRenderer

def test_markdown_renderer_deterministic():
    task = Task(title="Test Task", goal="Do testing", status=TaskStatus.ACTIVE)
    ev = EvidenceReference(source_id="d1", locator="p1", metadata={"text": "fact"})
    f1 = Finding(statement="The sky is blue", confidence="high", evidence_refs=[ev.evidence_id])
    d1 = Decision(decision="Yes", rationale="Why not")
    
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.MARKDOWN, title="Test Report", requested_sections=["findings", "evidence", "decisions"])
    
    renderer = MarkdownRenderer()
    md1 = renderer.render(task, [f1, d1], [ev], req)
    md2 = renderer.render(task, [f1, d1], [ev], req)
    
    assert md1 == md2  # Deterministic
    assert "The sky is blue" in md1
    assert "d1:p1" in md1
    assert "**Decision:** Yes" in md1
    assert "Why not" in md1
    assert "Executive Summary" not in md1  # not requested

def test_json_renderer_deterministic():
    task = Task(title="Test Task", goal="Do testing", status=TaskStatus.ACTIVE)
    ev = EvidenceReference(source_id="d1", locator="p1", metadata={"text": "fact"})
    f1 = Finding(statement="The sky is blue", confidence="high", evidence_refs=[ev.evidence_id])
    
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.JSON, title="Test Report")
    
    renderer = JsonRenderer()
    json_str = renderer.render(task, [f1], [ev], req)
    
    data = json.loads(json_str)
    assert data["task_id"] == task.task_id
    assert data["title"] == task.title
    assert len(data["findings"]) == 1
    assert data["findings"][0]["statement"] == "The sky is blue"
    assert data["findings"][0]["sources"][0]["source_id"] == "d1"
    assert data["findings"][0]["sources"][0]["locator"] == "p1"
    
    # Internal fields like database rows or hidden properties should NOT be in the parsed output
    # `item_id` and `priority` are internal Task State fields, not explicitly exposed in PublicFinding
    assert "item_id" not in data["findings"][0]

def test_markdown_empty_sections():
    task = Task(title="Empty Task", goal="Nothing")
    req = ArtifactRequest(task_id=task.task_id, artifact_type=ArtifactType.MARKDOWN, title="Empty")
    
    renderer = MarkdownRenderer()
    md = renderer.render(task, [], [], req)
    
    assert "*No findings recorded.*" in md
    assert "*No evidence recorded.*" in md
    assert "*No decisions recorded.*" in md
