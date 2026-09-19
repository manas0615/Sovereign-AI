import time
import os
import json
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_experiment_a():
    client = TestClient(app)
    svc = get_app_service()
    
    print("\n--- INGESTING KNOWLEDGE ---")
    doc_content = b"INSPECTION REPORT\nEquipment ID: V-204\nDate: 2026-09-13\nObserved condition: Critical seal wear detected on main flange.\nMeasurement: 0.15mm clearance\nThreshold: 0.10mm max\nFinding: Fails safety tolerance.\nRecommended action: Replace main flange seal immediately before resuming operation."
    
    res = client.post("/api/v1/knowledge/documents", files={"file": ("inspection_report_V-204.txt", doc_content)})
    doc_id = res.json()["document_id"]
    print(f"Document ingested: {doc_id}")
    
    print("\n=== PATH 2: POSITIVE PATH (QUALIFIED CAPABILITY) ===")
    goal = '''Find the observed condition and recommended action for equipment V-204.
CRITICAL: You MUST use the RETRIEVE action first. Do not guess.
Example: {"action": "RETRIEVE", "query": "V-204", "top_k": 5}
Only after you see the retrieved text in Current State should you output FINAL.
'''
    res = client.post("/api/v1/tasks", json={"title": "Retrieval Task", "goal": goal})
    task_id = res.json()["task_id"]
    print(f"Created Task: {task_id}")
    
    res = client.post(f"/api/v1/tasks/{task_id}/run")
    print("Waiting for task to complete...")
    for _ in range(40):
        time.sleep(2)
        res = client.get(f"/api/v1/tasks/{task_id}")
        if res.json()['status'] in ["COMPLETED", "FAILED"]:
            break
            
    print(f"Final Task Status: {res.json()['status']}")
    
    print("\n--- GENERATING ARTIFACT ---")
    req = ArtifactRequest(
        task_id=task_id,
        artifact_type=ArtifactType.MARKDOWN,
        title="Phase H Provenance Artifact",
        requested_sections=["findings", "evidence"]
    )
    art = svc.artifact_engine.generate(req)
    
    print(f"Generated Artifact ID: {art.artifact_id}")
    print(f"Task ID: {art.task_id}")
    print(f"Status: {art.status}")
    print(f"Source References: {art.source_references}")
    print(f"Metadata: {art.metadata}")
    
    # Read manifest
    with open("artifacts/manifest.json", "r") as f:
        manifest = json.load(f)
        print(f"\nManifest entry for {art.artifact_id}:")
        print(json.dumps(manifest.get(art.artifact_id, {}), indent=2))
        
    print(f"\nFile path: {art.metadata.file_path}")
    with open(art.metadata.file_path, "r") as f:
        print(f"File content:\n{f.read()}")
        
if __name__ == '__main__':
    run_experiment_a()
