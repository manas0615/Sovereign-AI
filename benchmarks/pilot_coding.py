import json
import time
import os
import uuid
import sys
from unittest.mock import patch

# Ensure we can import sovereign
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from sovereign.application.services import get_app_service
from sovereign.application.schemas import TaskCreateRequest
from sovereign.core.state.models import TaskStatus
from sovereign.infrastructure.tools.workspace import WorkspaceManager
from sovereign.core.coding.verifier import TrustedCodeVerifier

captured_codes = {}
current_task_id = None
original_verify = TrustedCodeVerifier.verify_submission

def mock_verify_submission(code, task_goal, workspace, boundary, **kwargs):
    global current_task_id
    if current_task_id:
        captured_codes.setdefault(current_task_id, []).append(code)
    # Call original with precise signature
    return original_verify(code, task_goal, workspace, boundary, **kwargs)

def execute_hidden_tests(generated_code: str, hidden_tests: str) -> dict:
    if not generated_code.strip():
        return {"success": False, "error": "Not evaluable (No code captured)"}
    combined = f"{generated_code}\n\n{hidden_tests}"
    local_env = {}
    try:
        exec(combined, local_env)
        return {"success": True, "error": None}
    except AssertionError as e:
        return {"success": False, "error": f"AssertionError: {e}"}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}"}

def run_pilot():
    global current_task_id
    print("Initializing Sovereign AppService...")
    start_init = time.time()
    svc = get_app_service()
    
    load_time = time.time() - start_init
    print(f"AppService init ready in {load_time:.2f}s")
    
    tasks = [
        {
            "id": "Pilot-Easy-1",
            "prompt": "Write a Python function sum_even_numbers(lst: list[int]) -> int that returns the sum of all even numbers in the list. If the list is empty or has no even numbers, return 0.",
            "hidden_tests": "assert sum_even_numbers([1, 2, 3, 4]) == 6\nassert sum_even_numbers([1, 3, 5]) == 0\nassert sum_even_numbers([]) == 0\n"
        },
        {
            "id": "Pilot-Medium-1",
            "prompt": "Write a Python function first_non_repeating_char(s: str) -> str that returns the first non-repeating character in a string. If all characters repeat or the string is empty, return an empty string ''.",
            "hidden_tests": "assert first_non_repeating_char('swiss') == 'w'\nassert first_non_repeating_char('aabbcc') == ''\nassert first_non_repeating_char('a') == 'a'\n"
        }
    ]
    
    results = []
    
    for tdef in tasks:
        current_task_id = tdef['id']
        print(f"\n--- Running Task: {current_task_id} ---")
        req = TaskCreateRequest(
            title=current_task_id,
            goal=tdef['prompt'],
            capability_requirement="AutomatedCoding_v1"
        )
        task_obj = svc.create_task(req)
        task_id = task_obj.task_id
        
        t0 = time.time()
        
        # Apply the instrumentation patch only during execution
        with patch.object(TrustedCodeVerifier, 'verify_submission', new=mock_verify_submission):
            svc.agent.run(task_id)
            
        total_latency = time.time() - t0
        
        final_task = svc.get_task(task_id)
        state_items = svc.repo.get_state_items(task_id)
        
        # Generation attempt: Anytime the parser ran (evidenced by state items)
        generation_attempts = sum(1 for item in state_items if hasattr(item, "decision"))
        
        tool_invocations = 0
        verifier_outcome = "NOT_INVOKED"
        terminal_reason = final_task.status.value if hasattr(final_task.status, 'value') else final_task.status
        
        for item in state_items:
            if hasattr(item, 'statement'):
                if "Tool 'execute_python' returned" in item.statement or "Tool 'execute_python' failed" in item.statement:
                    tool_invocations += 1
                if "Trusted Verification Result:" in item.statement:
                    verifier_outcome = item.statement.split("[")[1].split("]")[0]
                    
        if final_task.status == TaskStatus.FAILED:
            for item in state_items:
                if hasattr(item, 'decision') and item.decision == "FAIL":
                    terminal_reason = item.rationale
                    break
        
        # Get captured codes for this task
        task_codes = captured_codes.get(current_task_id, [])
        first_code = task_codes[0] if len(task_codes) > 0 else ""
        final_code = task_codes[-1] if len(task_codes) > 0 else ""
                
        first_gt_result = execute_hidden_tests(first_code, tdef['hidden_tests'])
        final_gt_result = execute_hidden_tests(final_code, tdef['hidden_tests'])
        
        res = {
            "task_id": current_task_id,
            "generation_attempts": generation_attempts,
            "tool_invocations": tool_invocations,
            "verifier_outcome": verifier_outcome,
            "captured_codes_count": len(task_codes),
            "final_code_length": len(final_code),
            "first_generation_success": first_gt_result['success'],
            "final_success": final_gt_result['success'],
            "ground_truth_error": final_gt_result['error'] if not final_gt_result['success'] else None,
            "terminal_reason": terminal_reason,
            "total_latency_s": round(total_latency, 2)
        }
        results.append(res)
        print(json.dumps(res, indent=2))
        
    print("\n--- PILOT RESULTS ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_pilot()
