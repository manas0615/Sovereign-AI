import time
import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_hdr(text: str):
    print("\n" + "="*50)
    print(f"[+] {text}")
    print("="*50)

def run():
    print_hdr("1. Checking Backend Health")
    try:
        res = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        print(f"Health: {res.json()}")
    except httpx.RequestError:
        print("Backend not running. Please start the backend server.")
        return
        
    print_hdr("2. Creating Automated Coding Task")
    payload = {
        "title": "Email Validator Coding",
        "goal": "Write a Python function is_valid_email(email) that returns True for a valid email format and False otherwise. Include tests for normal valid and invalid examples. Run the tests and explain the result."
    }
    res = httpx.post(f"{BASE_URL}/tasks", json=payload)
    task_id = res.json()["task_id"]
    print(f"Created Task: {task_id}")
    
    print_hdr("3. Starting Live Agent Run")
    res = httpx.post(f"{BASE_URL}/tasks/{task_id}/run", timeout=120.0)
    print("Agent started...")
    
    print_hdr("4. Polling Task Execution (up to 120s)")
    for _ in range(40):
        time.sleep(3)
        res = httpx.get(f"{BASE_URL}/tasks/{task_id}")
        status = res.json()["status"]
        print(f"Status: {status}")
        if status in ["COMPLETED", "FAILED"]:
            break
            
    print_hdr("5. Execution Result & State Trace")
    res = httpx.get(f"{BASE_URL}/tasks/{task_id}/state")
    state = res.json()
    for s in state:
        typ = s.get("type", "Unknown")
        content = s.get("rationale") or s.get("statement") or s.get("decision")
        print(f"\n[{typ}]\n{content}")
        
    print_hdr("6. Final Status")
    res = httpx.get(f"{BASE_URL}/tasks/{task_id}")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    run()
