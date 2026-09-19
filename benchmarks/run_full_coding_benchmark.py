import json
import time
import os
import sys
import uuid
from unittest.mock import patch

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

def run_benchmark():
    global current_task_id
    
    with open("benchmarks/tasks.json", "r") as f:
        tasks = json.load(f)
        
    print("Initializing Sovereign AppService...")
    start_init = time.time()
    svc = get_app_service()
    
    # Warm up model
    t_load = time.time()
    try:
        # We can just initialize the model gateway
        from sovereign.core.runtime.gateway import ModelGateway
        gw = ModelGateway()
        gw.start_deployment("Llama-3.2-3B-Instruct")
    except Exception as e:
        print("Warmup error:", e)
        
    model_load_time = time.time() - t_load
    print(f"AppService init & Model load ready in {time.time() - start_init:.2f}s (Model load: {model_load_time:.2f}s)")
    
    results = []
    
    # 50 tasks x 3 trials = 150 trials
    trial_count = 0
    
    for tdef in tasks:
        for trial in range(3):
            trial_count += 1
            current_task_id = f"{tdef['task_id']}-T{trial+1}"
            print(f"\n[{trial_count}/150] Running: {current_task_id}")
            
            req = TaskCreateRequest(
                title=current_task_id,
                goal=tdef['prompt'],
                capability_requirement="AutomatedCoding_v1"
            )
            task_obj = svc.create_task(req)
            task_id = task_obj.task_id
            
            captured_codes[current_task_id] = []
            
            t0 = time.time()
            with patch.object(TrustedCodeVerifier, 'verify_submission', new=mock_verify_submission):
                svc.agent.run(task_id)
            total_latency = time.time() - t0
            
            final_task = svc.get_task(task_id)
            state_items = svc.repo.get_state_items(task_id)
            
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
            
            task_codes = captured_codes.get(current_task_id, [])
            first_code = task_codes[0] if len(task_codes) > 0 else ""
            final_code = task_codes[-1] if len(task_codes) > 0 else ""
            
            first_gt = execute_hidden_tests(first_code, tdef['hidden_tests'])
            final_gt = execute_hidden_tests(final_code, tdef['hidden_tests'])
            
            ground_truth_evaluable = len(task_codes) > 0
            first_captured_submission_passed = first_gt['success']
            final_captured_submission_passed = final_gt['success']
            
            # Did the first generation pass? It only passed if we captured code on generation attempt 1.
            first_model_generation_passed = (generation_attempts == 1 and first_captured_submission_passed)
            
            agent_workflow_success = (final_task.status == TaskStatus.COMPLETED and verifier_outcome == "Passed")
            
            res = {
                "task_id": tdef['task_id'],
                "trial": trial + 1,
                "trial_id": current_task_id,
                "difficulty": tdef['difficulty'],
                "generation_attempts": generation_attempts,
                "tool_invocations": tool_invocations,
                "verifier_outcome": verifier_outcome,
                "terminal_reason": terminal_reason,
                "ground_truth_evaluable": ground_truth_evaluable,
                "first_model_generation_passed": first_model_generation_passed,
                "first_captured_submission_passed": first_captured_submission_passed,
                "final_captured_submission_passed": final_captured_submission_passed,
                "agent_workflow_success": agent_workflow_success,
                "final_error": final_gt['error'],
                "latency_s": round(total_latency, 2)
            }
            results.append(res)
            
            with open("benchmarks/results_full.jsonl", "a") as f:
                f.write(json.dumps(res) + "\n")
                
    # Aggregate Metrics
    total = len(results)
    evaluable = sum(1 for r in results if r["ground_truth_evaluable"])
    first_gen_pass = sum(1 for r in results if r["first_model_generation_passed"])
    first_cap_pass = sum(1 for r in results if r["first_captured_submission_passed"])
    final_cap_pass = sum(1 for r in results if r["final_captured_submission_passed"])
    agent_success = sum(1 for r in results if r["agent_workflow_success"])
    
    summary = {
        "total_trials": total,
        "model_load_time_s": round(model_load_time, 2),
        "ground_truth_evaluable": evaluable,
        "first_model_generation_passed": first_gen_pass,
        "first_captured_submission_passed": first_cap_pass,
        "final_captured_submission_passed": final_cap_pass,
        "agent_workflow_success": agent_success
    }
    
    with open("benchmarks/summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n--- SUMMARY ---")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    run_benchmark()
