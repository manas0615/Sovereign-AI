import time
import os
import json
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def run_experiment_f():
    client = TestClient(app)
    svc = get_app_service()
    
    print("\n=== PATH 1: NEGATIVE PATH (UNQUALIFIED CAPABILITY) ===")
    goal = "Decide the best strategy to fix equipment V-204"
    res = client.post("/api/v1/tasks", json={"title": "Decision Task", "goal": goal})
    task_id = res.json()["task_id"]
    print(f"Created Task: {task_id}")
    
    res = client.post(f"/api/v1/tasks/{task_id}/run")
    print("Waiting for task to complete...")
    for _ in range(20):
        time.sleep(1)
        res = client.get(f"/api/v1/tasks/{task_id}")
        if res.json()['status'] in ["COMPLETED", "FAILED"]:
            break
            
    print(f"Final Task Status: {res.json()['status']}")
    
    print("\n--- GENERATING ARTIFACT ---")
    req = ArtifactRequest(
        task_id=task_id,
        artifact_type=ArtifactType.MARKDOWN,
        title="Phase H Negative Artifact",
        requested_sections=["findings", "evidence"]
    )
    art = svc.artifact_engine.generate(req)
    
    print(f"Generated Artifact ID: {art.artifact_id}")
    print(f"Status: {art.status}")
    
if __name__ == '__main__':
    run_experiment_f()
