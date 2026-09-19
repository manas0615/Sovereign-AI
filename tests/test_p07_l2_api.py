"""
Phase L2 Tests: P07 Backend API Polish, Passports Endpoint, and Document-to-Task Coherence.
"""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.knowledge.models import Document, DocumentStatus
from sovereign.core.state.repository import QualificationResultRecord, CapabilityPassportRecord
from sovereign.core.qualification.models import QualificationStatus


@pytest.fixture
def client():
    return TestClient(app)


def test_list_passports_empty_and_populated(client):
    """Verify GET /api/v1/qualifications/passports returns capability passports correctly."""
    svc = get_app_service()
    
    unique_suffix = uuid.uuid4().hex[:6]
    result_id = f"res-qual-{unique_suffix}"
    passport_id = f"psp-test-{unique_suffix}"
    
    # 1. Save qualification result first (foreign key dependency)
    res_record = QualificationResultRecord(
        result_id=result_id,
        qualification_identity=f"qual-id-llama32-{unique_suffix}",
        capability_contract="DocumentRetrieval_v1",
        deployment_identity="deploy-llama-3.2-3b-vulkan1",
        trial_counts={"total": 20, "passed": 19, "failed": 1},
        compliance_metrics={"pass_rate": 0.95},
        resource_stability="STABLE",
        threshold_evaluation="PASSED",
        qualification_status="QUALIFIED",
        timestamp=datetime.now(timezone.utc),
        metadata={"tested_by": "PhaseL2Test"}
    )
    svc.repo.save_result(res_record)
    
    # 2. Save capability passport in persistence
    passport = CapabilityPassportRecord(
        passport_id=passport_id,
        qualification_identity=f"qual-id-llama32-{unique_suffix}",
        deployment_identity="deploy-llama-3.2-3b-vulkan1",
        capability_contract="DocumentRetrieval_v1",
        result_id=result_id,
        qualification_status="QUALIFIED",
        qualification_timestamp=datetime.now(timezone.utc),
        invalidation_info={},
        metadata={"pass_rate": 0.95, "evaluated_trials": 20}
    )
    svc.repo.save_passport(passport)
    
    response = client.get("/api/v1/qualifications/passports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    matched = [p for p in data if p["passport_id"] == passport_id]
    assert len(matched) == 1
    p = matched[0]
    assert p["capability_contract"] == "DocumentRetrieval_v1"
    assert p["qualification_status"] == "QUALIFIED"
    assert p["deployment_identity"] == "deploy-llama-3.2-3b-vulkan1"
    assert p["metadata"]["pass_rate"] == 0.95


def test_task_creation_with_document_association(client):
    """Verify document-to-task coherence: creating a task with a valid document_id binds context."""
    svc = get_app_service()
    
    unique_doc_id = f"doc_v204_{uuid.uuid4().hex[:8]}"
    
    # Register a test document in the knowledge base
    doc = Document(
        document_id=unique_doc_id,
        filename="v204_inspection.pdf",
        source_path="v204_inspection.pdf",
        document_type="pdf",
        file_size=1024,
        content_hash=f"hash_v204_report_{uuid.uuid4().hex[:8]}",
        status=DocumentStatus.INGESTED
    )
    svc.kb.register_document(doc)
    
    # Create task specifying document_id
    payload = {
        "title": "V-204 Inspection Analysis",
        "goal": "Review critical seal wear and generate executive approval note.",
        "document_id": unique_doc_id
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 200
    data = response.json()
    task_id = data["task_id"]
    
    assert data["title"] == "V-204 Inspection Analysis"
    assert data["document_id"] == unique_doc_id
    assert data["status"] == "CREATED"
    
    # Verify persistence: evidence reference and context finding
    evidence_refs = svc.repo.get_evidence(task_id)
    assert len(evidence_refs) >= 1
    assert evidence_refs[0].source_id == unique_doc_id
    assert "v204_inspection.pdf" in evidence_refs[0].locator
    
    state_items = svc.repo.get_state_items(task_id)
    target_findings = [i for i in state_items if i.item_type == "finding" and "v204_inspection.pdf" in i.statement]
    assert len(target_findings) == 1
    assert target_findings[0].priority.name == "REQUIRED"
    
    # Verify GET /api/v1/tasks/{task_id} preserves document_id
    get_res = client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["document_id"] == unique_doc_id


def test_task_creation_with_invalid_document_id_fails(client):
    """Verify that specifying a non-existent document_id returns a 400 Bad Request."""
    payload = {
        "title": "Invalid Document Task",
        "goal": "Attempt to process non-existent document.",
        "document_id": "non_existent_doc_id_99999"
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 400
    assert "not found in knowledge base" in response.json()["detail"]


def test_standard_task_creation_without_document_still_works(client):
    """Verify backwards compatibility: creating a task without document_id succeeds cleanly."""
    payload = {
        "title": "Standard Task Without Document",
        "goal": "Perform general analysis."
    }
    response = client.post("/api/v1/tasks", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] is None
    assert data["status"] == "CREATED"
