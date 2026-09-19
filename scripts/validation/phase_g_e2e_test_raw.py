import time
import os
import json
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_e2e():
    client = TestClient(app)
    
    # 1. Ingest document
    print("\n--- INGESTING KNOWLEDGE ---")
    doc_content = b"INSPECTION REPORT\nEquipment ID: V-204\nDate: 2026-09-13\nObserved condition: Critical seal wear detected on main flange.\nMeasurement: 0.15mm clearance\nThreshold: 0.10mm max\nFinding: Fails safety tolerance.\nRecommended action: Replace main flange seal immediately before resuming operation."
    
    res = client.post("/api/v1/knowledge/documents", files={"file": ("inspection_report_V-204.txt", doc_content)})
    assert res.status_code == 200
    print("Document ingested successfully.")
    
    print("\n=== PATH 1: NEGATIVE PATH (UNQUALIFIED CAPABILITY) ===")
    res = client.post("/api/v1/tasks", json={"title": "Strategy Task", "goal": "Decide the best strategy to fix equipment V-204"})
    assert res.status_code == 200
    task1_id = res.json()["task_id"]
    print(f"Created Task 1: {task1_id}")
    
    res = client.post(f"/api/v1/tasks/{task1_id}/run")
    assert res.status_code == 200
    
    time.sleep(3)
    
    res = client.get(f"/api/v1/tasks/{task1_id}")
    task1_data = res.json()
    print("Task 1 Data Keys:", task1_data.keys())
    print("Task 1 Status:", task1_data.get('status'))
    print("Task 1 State Items:", json.dumps(task1_data.get('execution_history', []), indent=2))
        
    print("\n=== PATH 2: POSITIVE PATH (QUALIFIED CAPABILITY) ===")
    res = client.post("/api/v1/tasks", json={"title": "Retrieval Task", "goal": "Retrieve the observed condition and recommended action for equipment V-204 from the inspection report."})
    assert res.status_code == 200
    task2_id = res.json()["task_id"]
    print(f"Created Task 2: {task2_id}")
    
    res = client.post(f"/api/v1/tasks/{task2_id}/run")
    assert res.status_code == 200
    
    print("Waiting for task to complete...")
    for _ in range(40):
        time.sleep(2)
        res = client.get(f"/api/v1/tasks/{task2_id}")
        task2_data = res.json()
        if task2_data['status'] in ["COMPLETED", "FAILED"]:
            break
            
    print("Task 2 Data Keys:", task2_data.keys())
    print("Task 2 Status:", task2_data.get('status'))
    print("Task 2 State Items:", json.dumps(task2_data.get('execution_history', []), indent=2))
    
    # Dump artifact if exists
    if task2_data.get('artifact_id'):
        print(f"Artifact generated: {task2_data['artifact_id']}")
        
if __name__ == '__main__':
    run_e2e()
