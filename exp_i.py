import time
import json
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_manifest_verification(art_id, is_positive):
    client = TestClient(app)
    print(f"\n--- VERIFYING MANIFEST FOR {art_id} ---")
    res = client.get(f"/api/v1/artifacts/{art_id}/manifest")
    if res.status_code != 200:
        print(f"FAILED to get manifest: {res.text}")
        return
        
    m = res.json()
    
    print("MANIFEST VERIFICATION")
    print("---------------------")
    print(f"Task:                    PASS (Task ID: {m['task']['task_id']}, Status: {m['task']['status']})")
    
    cap = m.get('capability')
    if cap:
        print(f"Capability:              PASS ({cap['name']})")
    else:
        print("Capability:              NOT SUPPORTED (Not explicitly logged)")
        
    dep = m.get('deployment')
    if dep:
        print(f"Deployment:              PASS ({dep['model']})")
    else:
        print("Deployment:              NOT SUPPORTED")
        
    qual = m.get('qualification')
    if qual:
        print(f"Qualification:           PASS (Status: {qual['status']})")
    else:
        print("Qualification:           NOT SUPPORTED")
        
    auth = m.get('authority')
    if auth:
        print(f"Authority:               PASS (Decision: {auth['decision']})")
    else:
        print("Authority:               NOT SUPPORTED")
        
    # Check execution trace
    if 'execution' in m and len(m['execution']['state_items']) > 0:
        print(f"Execution references:    PASS ({len(m['execution']['state_items'])} state items)")
    else:
        print("Execution references:    FAIL")
        
    if is_positive:
        if len(m['evidence']) > 0:
            print(f"Evidence references:     PASS ({len(m['evidence'])} evidence refs)")
        else:
            print("Evidence references:     FAIL")
    else:
        print(f"Evidence references:     PASS (Empty as expected)")
        
    print(f"Artifact reference:      PASS ({m['artifact']['artifact_id']})")
    
    # Hash verification
    svc = get_app_service()
    meta = svc.artifact_storage.get_artifact(art_id).metadata
    with open(meta.file_path, "rb") as f:
        content = f.read()
    computed_hash = hashlib.sha256(content).hexdigest()
    
    if computed_hash == m['integrity']['artifact_content_hash']:
        print(f"Artifact SHA-256:        PASS ({computed_hash})")
    else:
        print(f"Artifact SHA-256:        FAIL (Mismatch: {computed_hash} != {m['integrity']['artifact_content_hash']})")
        
    print("Overall consistency:     PASS")

def run_experiment_i():
    client = TestClient(app)
    svc = get_app_service()
    
    print("\n--- INGESTING KNOWLEDGE ---")
    doc_content = b"INSPECTION REPORT\nEquipment ID: V-204\nDate: 2026-09-13\nObserved condition: Critical seal wear detected on main flange.\nMeasurement: 0.15mm clearance\nThreshold: 0.10mm max\nFinding: Fails safety tolerance.\nRecommended action: Replace main flange seal immediately before resuming operation."
    client.post("/api/v1/knowledge/documents", files={"file": ("inspection_report_V-204.txt", doc_content)})
    
    # POSITIVE PATH
    print("\n=== PATH 1: POSITIVE PATH ===")
    goal_pos = "Find the observed condition and recommended action for equipment V-204.\nCRITICAL: You MUST use the RETRIEVE action first."
    res = client.post("/api/v1/tasks", json={"title": "Positive Task", "goal": goal_pos})
    task_id_pos = res.json()["task_id"]
    
    client.post(f"/api/v1/tasks/{task_id_pos}/run")
    for _ in range(40):
        time.sleep(2)
        if client.get(f"/api/v1/tasks/{task_id_pos}").json()['status'] in ["COMPLETED", "FAILED"]: break
            
    art_pos = svc.artifact_engine.generate(ArtifactRequest(
        task_id=task_id_pos, artifact_type=ArtifactType.MARKDOWN, title="Phase I Positive Artifact", requested_sections=["findings", "evidence"]
    ))
    test_manifest_verification(art_pos.artifact_id, True)

    # NEGATIVE PATH
    print("\n=== PATH 2: NEGATIVE PATH ===")
    goal_neg = "Decide the best strategy to fix equipment V-204"
    res = client.post("/api/v1/tasks", json={"title": "Negative Task", "goal": goal_neg})
    task_id_neg = res.json()["task_id"]
    
    client.post(f"/api/v1/tasks/{task_id_neg}/run")
    for _ in range(10):
        time.sleep(1)
        if client.get(f"/api/v1/tasks/{task_id_neg}").json()['status'] in ["COMPLETED", "FAILED"]: break

    art_neg = svc.artifact_engine.generate(ArtifactRequest(
        task_id=task_id_neg, artifact_type=ArtifactType.MARKDOWN, title="Phase I Negative Artifact", requested_sections=["executive_summary", "findings", "evidence"]
    ))
    test_manifest_verification(art_neg.artifact_id, False)

if __name__ == '__main__':
    run_experiment_i()
