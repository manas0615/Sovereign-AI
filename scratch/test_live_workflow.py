import httpx
import time
import json
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_hdr(msg):
    print(f"\n{'='*50}\n[+] {msg}\n{'='*50}")

def run_workflow():
    try:
        # Check health
        res = httpx.get(f"{BASE_URL}/health")
        if res.status_code != 200:
            print("Backend not running. Please start the backend server.")
            return
        
        # Ingest Document (OCR via real PDF)
        print_hdr("1. Ingesting Document (OCR)")
        pdf_path = r"docs\v204_scanned_inspection.pdf"
        with open(pdf_path, 'rb') as f:
            files = {'file': ('v204_scanned_inspection.pdf', f, 'application/pdf')}
            res = httpx.post(f"{BASE_URL}/knowledge/documents", files=files, timeout=30.0)
        doc_data = res.json()
        print(json.dumps(doc_data, indent=2))
        
        # Create Task
        print_hdr("2. Creating RAG Task")
        task_payload = {
            "title": "Analyze V-204",
            "goal": "Read the inspection report for V-204. What is the seal wear measurement, the threshold, and the difference?"
        }
        res = httpx.post(f"{BASE_URL}/tasks", json=task_payload)
        task_data = res.json()
        task_id = task_data["task_id"]
        print(f"Task ID: {task_id}")
        
        # Run Task
        print_hdr("3. Executing Agent Workflow")
        res = httpx.post(f"{BASE_URL}/tasks/{task_id}/run")
        print(res.json())
        
        print("Waiting for agent execution to complete...")
        for _ in range(15):
            time.sleep(2)
            res = httpx.get(f"{BASE_URL}/tasks/{task_id}")
            status = res.json().get("status")
            print(f"Status: {status}")
            if status in ["COMPLETED", "FAILED"]:
                break
                
        task_result = httpx.get(f"{BASE_URL}/tasks/{task_id}").json()
        print_hdr("Agent Execution Result")
        print(json.dumps(task_result, indent=2))
        
        # Generate DOCX Artifact
        print_hdr("Generating DOCX Approval Note")
        art_payload = {
            "task_id": task_id,
            "artifact_type": "DOCX",
            "title": "Approval Note: V-204",
            "requested_sections": ["findings", "evidence"]
        }
        res = httpx.post(f"{BASE_URL}/tasks/{task_id}/artifacts", json=art_payload)
        print(res.json())
        
        # Check artifacts
        res = httpx.get(f"{BASE_URL}/tasks/{task_id}/artifacts")
        print_hdr("Generated Artifacts")
        print(json.dumps(res.json(), indent=2))
        
        # Check Math Task (Live Dispatch 2)
        print_hdr("4. Creating Calculation Task")
        calc_payload = {
            "title": "Corrosion Calculation",
            "goal": "calculate remaining life (allowance divided by corrosion rate) if corrosion rate is 0.5 and allowance is 3.0"
        }
        res = httpx.post(f"{BASE_URL}/tasks", json=calc_payload)
        calc_task_id = res.json()["task_id"]
        
        res = httpx.post(f"{BASE_URL}/tasks/{calc_task_id}/run")
        print("Waiting for calculation execution to complete...")
        for _ in range(10):
            time.sleep(2)
            res = httpx.get(f"{BASE_URL}/tasks/{calc_task_id}")
            status = res.json().get("status")
            print(f"Status: {status}")
            if status in ["COMPLETED", "FAILED"]:
                break
                
        calc_result = httpx.get(f"{BASE_URL}/tasks/{calc_task_id}").json()
        print_hdr("Calculation Task Result")
        print(json.dumps(calc_result, indent=2))
        
    except Exception as e:
        print(f"Error running workflow: {e}")

if __name__ == "__main__":
    run_workflow()
