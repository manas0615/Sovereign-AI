import time
import os
import json
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_e2e():
    client = TestClient(app)
    svc = get_app_service()
    
    # 1. Ingest document
    print("\n--- INGESTING KNOWLEDGE ---")
    doc_content = b"INSPECTION REPORT\nEquipment ID: V-204\nDate: 2026-09-13\nObserved condition: Critical seal wear detected on main flange.\nMeasurement: 0.15mm clearance\nThreshold: 0.10mm max\nFinding: Fails safety tolerance.\nRecommended action: Replace main flange seal immediately before resuming operation."
    
    res = client.post("/api/v1/knowledge/documents", files={"file": ("inspection_report_V-204.txt", doc_content)})
    doc_id = res.json()["document_id"]
    print(f"Document ingested successfully: {doc_id}")
    
    print("\n=== PATH 2: POSITIVE PATH (QUALIFIED CAPABILITY) ===")
    goal = '''Find the observed condition and recommended action for equipment V-204.
CRITICAL: You MUST use the RETRIEVE action first. Do not guess.
Example: {"action": "RETRIEVE", "query": "V-204", "top_k": 5}
Only after you see the retrieved text in Current State should you output FINAL.
'''
    res = client.post("/api/v1/tasks", json={"title": "Retrieval Task", "goal": goal})
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
            
    print(f"Final Task Status: {task2_data['status']}")
    
    print("\nTask 2 State Items:")
    state_items2 = svc.repo.get_state_items(task2_id)
    for item in state_items2:
        val = getattr(item, 'statement', getattr(item, 'rationale', getattr(item, 'content', getattr(item, 'error_message', ''))))
        print(f" - [{item.created_at}] {item.item_type}: {val}")
            
if __name__ == '__main__':
    run_e2e()
