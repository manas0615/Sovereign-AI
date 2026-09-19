import time
import os
import json
import logging
import sqlite3
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service

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
    
    print("\n--- REQUESTING ARTIFACT ---")
    res = client.post(f"/api/v1/tasks/{task_id}/artifacts", json={
        "artifact_type": "JSON",
        "title": "Phase H Provenance Artifact",
        "requested_sections": ["findings", "evidence"]
    })
    
    print(res.status_code, res.text)
    
    # 2. Inspect Artifact Table
    conn = sqlite3.connect('local_data/sovereign.db')
    c = conn.cursor()
    c.execute("SELECT artifact_id, task_id, type, status, metadata, source_references FROM artifacts WHERE task_id = ?", (task_id,))
    rows = c.fetchall()
    print(f"\nFound {len(rows)} artifacts in DB:")
    for row in rows:
        print(f"Artifact ID: {row[0]}")
        print(f"Task ID: {row[1]}")
        print(f"Type: {row[2]}")
        print(f"Status: {row[3]}")
        print(f"Metadata: {row[4]}")
        print(f"Source References: {row[5]}")

if __name__ == '__main__':
    run_experiment_a()
