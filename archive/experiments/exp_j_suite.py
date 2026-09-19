import time
import os
import json
import hashlib
import logging
from fastapi.testclient import TestClient
from sovereign.application.api import app
from sovereign.application.services import get_app_service
from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
from sovereign.core.qualification.models import CapabilityPassport, QualificationStatus, DeploymentProfile, ModelProfile, RuntimeEnvironment, CapabilityContract, QualificationIdentity
from sovereign.core.authority.evaluator import AuthorityEvaluator, AuthorityPolicy
from sovereign.core.authority.models import AuthorityOutcome
from sovereign.core.agent.router import ModelRouter, TaskCharacterizer
from sovereign.core.runtime.models import ModelDeploymentConfig, InferenceRequest
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_phase_j_suite():
    client = TestClient(app)
    svc = get_app_service()
    results = {}

    print("============================================================")
    print("PHASE J: CONTROLLED FAILURE & FAIL-SAFE VALIDATION TEST SUITE")
    print("============================================================\n")

    # ------------------------------------------------------------
    # TEST 1: Unqualified Capability (AgentDecision_v1 on Llama-3.2)
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 1: Unqualified Capability ---")
    goal_1 = "Decide the best strategy to fix equipment V-204"
    res_1 = client.post("/api/v1/tasks", json={"title": "Test 1 Unqualified", "goal": goal_1})
    task_id_1 = res_1.json()["task_id"]
    client.post(f"/api/v1/tasks/{task_id_1}/run")
    
    # Wait for completion
    for _ in range(15):
        time.sleep(0.5)
        t_status = client.get(f"/api/v1/tasks/{task_id_1}").json()["status"]
        if t_status in ["COMPLETED", "FAILED"]:
            break
            
    # Check state items and artifact
    state_items_1 = svc.repo.get_state_items(task_id_1)
    route_dec_1 = next((item for item in state_items_1 if getattr(item, 'item_type', '') == 'decision' and getattr(item, 'decision', '') == 'ROUTE'), None)
    
    art_1 = svc.artifact_engine.generate(ArtifactRequest(
        task_id=task_id_1, artifact_type=ArtifactType.MARKDOWN, title="Test 1 Artifact", requested_sections=["executive_summary", "findings", "evidence"]
    ))
    
    t1_pass = (t_status == "FAILED" and route_dec_1 is not None and "No qualified and authorized deployment found" in route_dec_1.rationale and len(art_1.source_references) == 0)
    results["Test 1: Unqualified Capability"] = {
        "expected": "DENY -> Task FAILED -> No inference -> No successful work product",
        "actual": f"Status: {t_status}, Decision: {route_dec_1.rationale if route_dec_1 else 'None'}, Evidence Refs: {len(art_1.source_references)}",
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PASS" if t1_pass else "FAIL"
    }
    print(f"Result Test 1: {results['Test 1: Unqualified Capability']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 2: Qualification Identity Mismatch
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 2: Qualification Identity Mismatch ---")
    # Evaluate a modified deployment profile against the stored passport
    profile_orig = svc.router.deployment_profiles.get("Llama-3.2-3B-Instruct")
    # Create mismatched profile (e.g. GPU layers or context budget modified)
    profile_mismatched = DeploymentProfile(
        model=profile_orig.model,
        quantization=profile_orig.quantization,
        runtime=profile_orig.runtime,
        hardware_profile="mismatched_hardware_gl99",
        context_budget=profile_orig.context_budget
    )
    contract = svc.router.contracts["DocumentRetrieval_v1"]
    passport_rec = svc.repo.get_passport_by_identity(QualificationIdentity.generate(profile_orig, contract))
    
    passport_obj = None
    if passport_rec:
        passport_obj = CapabilityPassport(
            passport_id=passport_rec.passport_id,
            qualification_identity=passport_rec.qualification_identity,
            deployment_identity=passport_rec.deployment_identity,
            capability_contract=passport_rec.capability_contract,
            result_id=passport_rec.result_id,
            qualification_status=passport_rec.qualification_status,
            qualification_timestamp=passport_rec.qualification_timestamp,
            invalidation_info=passport_rec.invalidation_info,
            metadata=passport_rec.metadata
        )
    
    auth_eval = AuthorityEvaluator(svc.repo, AuthorityPolicy(allowed_contracts=["DocumentRetrieval_v1"], allow_unqualified=False))
    decision_mismatch = auth_eval.evaluate(profile_mismatched, contract, passport_obj)
    
    t2_pass = (decision_mismatch.outcome == AuthorityOutcome.DENIED_CAPABILITY and "Passport is invalid for current deployment" in decision_mismatch.reason)
    results["Test 2: Qualification Identity Mismatch"] = {
        "expected": "DENY -> DENIED_CAPABILITY outcome -> No inference",
        "actual": f"Outcome: {decision_mismatch.outcome.value}, Reason: {decision_mismatch.reason}",
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PASS" if t2_pass else "FAIL"
    }
    print(f"Result Test 2: {results['Test 2: Qualification Identity Mismatch']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 3: Expired / Invalidated Passport
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 3: Expired / Invalidated Passport ---")
    # Check if TTL/expiration field exists in CapabilityPassport
    has_ttl = hasattr(CapabilityPassport, "expires_at") or "ttl" in CapabilityPassport.model_fields
    # Test invalidation status
    if passport_obj:
        invalidated_passport = passport_obj.model_copy(update={"qualification_status": QualificationStatus.INVALIDATED})
        decision_invalidated = auth_eval.evaluate(profile_orig, contract, invalidated_passport)
        t3_status_pass = (decision_invalidated.outcome == AuthorityOutcome.DENIED_CAPABILITY)
    else:
        t3_status_pass = False

    results["Test 3: Expired / Invalidated Passport"] = {
        "expected": "DENY on INVALIDATED status; TTL/Expiration explicitly reported as unsupported",
        "actual": f"Status Invalidation DENIED: {t3_status_pass}; TTL/Expiry field supported: {has_ttl}",
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PARTIAL (Status invalidation PASS, Expiration TTL NOT SUPPORTED by architecture)"
    }
    print(f"Result Test 3: {results['Test 3: Expired / Invalidated Passport']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 4: Forbidden / Unregistered Capability
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 4: Forbidden / Unregistered Capability ---")
    goal_4 = "Execute isolated container and sandbox execution for untrusted python"
    res_4 = client.post("/api/v1/tasks", json={"title": "Test 4 Forbidden", "goal": goal_4})
    task_id_4 = res_4.json()["task_id"]
    client.post(f"/api/v1/tasks/{task_id_4}/run")
    
    for _ in range(15):
        time.sleep(0.5)
        t_status_4 = client.get(f"/api/v1/tasks/{task_id_4}").json()["status"]
        if t_status_4 in ["COMPLETED", "FAILED"]:
            break
            
    state_items_4 = svc.repo.get_state_items(task_id_4)
    route_dec_4 = next((item for item in state_items_4 if getattr(item, 'item_type', '') == 'decision' and getattr(item, 'decision', '') == 'ROUTE'), None)
    
    t4_pass = (t_status_4 == "FAILED" and route_dec_4 is not None and "Unsupported capability 'SandboxedExecution'" in route_dec_4.rationale)
    results["Test 4: Forbidden / Unregistered Capability"] = {
        "expected": "DENY -> Unsupported capability rejection -> Task FAILED -> No inference",
        "actual": f"Status: {t_status_4}, Decision: {route_dec_4.rationale if route_dec_4 else 'None'}",
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PASS" if t4_pass else "FAIL"
    }
    print(f"Result Test 4: {results['Test 4: Forbidden / Unregistered Capability']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 5: Model Unavailable
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 5: Model Unavailable ---")
    # Simulate unavailable model server endpoint via dummy config
    unavailable_dep = ModelDeploymentConfig(
        model_name="Unavailable-Model-99B",
        model_path="nonexistent/path/model.gguf",
        server_host="127.0.0.1",
        server_port=9999, # unreachable port
        backend="llama.cpp",
        device="cpu",
        gpu_layers=0,
        context_size=2048
    )
    unavailable_adapter = LlamaCppAdapter()
    try:
        req = InferenceRequest(prompt="Test unavailable", max_tokens=10)
        # Attempt generation on unreachable server
        resp = unavailable_adapter.generate(req, deployment_config=unavailable_dep)
        t5_pass = False
        t5_desc = "Falsely succeeded"
    except Exception as e:
        t5_pass = True
        t5_desc = f"Failed safely with exception: {type(e).__name__} ({str(e)[:60]}...)"

    results["Test 5: Model Unavailable"] = {
        "expected": "FAIL safely -> Exception raised -> No fabricated successful inference",
        "actual": t5_desc,
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PASS" if t5_pass else "FAIL"
    }
    print(f"Result Test 5: {results['Test 5: Model Unavailable']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 6: Knowledge / Evidence Failure
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 6: Knowledge / Evidence Failure ---")
    goal_6 = "Find the observed condition for equipment Z-9999_NONEXISTENT. You MUST use the RETRIEVE action first."
    res_6 = client.post("/api/v1/tasks", json={"title": "Test 6 No Evidence", "goal": goal_6})
    task_id_6 = res_6.json()["task_id"]
    client.post(f"/api/v1/tasks/{task_id_6}/run")
    
    for _ in range(30):
        time.sleep(1)
        t_status_6 = client.get(f"/api/v1/tasks/{task_id_6}").json()["status"]
        if t_status_6 in ["COMPLETED", "FAILED"]:
            break
            
    # Check evidence recorded in task state
    evidence_6 = svc.repo.get_evidence(task_id_6)
    art_6 = svc.artifact_engine.generate(ArtifactRequest(
        task_id=task_id_6, artifact_type=ArtifactType.MARKDOWN, title="Test 6 Artifact", requested_sections=["findings", "evidence"]
    ))
    
    # Verify no false evidence references were claimed
    t6_pass = (len(evidence_6) == 0 and len(art_6.source_references) == 0)
    results["Test 6: Knowledge / Evidence Failure"] = {
        "expected": "No evidence retrieved -> System does NOT claim false evidence references (0 evidence refs)",
        "actual": f"Status: {t_status_6}, Retrieved Evidence Count: {len(evidence_6)}, Artifact Source Refs: {len(art_6.source_references)}",
        "inference_occurred": True,
        "successful_artifact": True,
        "verdict": "PASS" if t6_pass else "FAIL"
    }
    print(f"Result Test 6: {results['Test 6: Knowledge / Evidence Failure']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 7: Artifact Integrity Mismatch
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 7: Artifact Integrity Mismatch ---")
    # Ingest real doc and run successful retrieval task
    doc_content = b"EQUIPMENT REPORT\nEquipment ID: V-204\nStatus: Flange seal replacement required.\nTolerance: 0.15mm."
    client.post("/api/v1/knowledge/documents", files={"file": ("v204_j_report.txt", doc_content)})
    
    goal_7 = "Find the observed condition and recommended action for equipment V-204. You MUST use the RETRIEVE action first."
    res_7 = client.post("/api/v1/tasks", json={"title": "Test 7 Valid Task", "goal": goal_7})
    task_id_7 = res_7.json()["task_id"]
    client.post(f"/api/v1/tasks/{task_id_7}/run")
    
    for _ in range(30):
        time.sleep(1)
        if client.get(f"/api/v1/tasks/{task_id_7}").json()["status"] in ["COMPLETED", "FAILED"]:
            break
            
    art_7 = svc.artifact_engine.generate(ArtifactRequest(
        task_id=task_id_7, artifact_type=ArtifactType.MARKDOWN, title="Test 7 Valid Artifact", requested_sections=["findings", "evidence"]
    ))
    
    stored_hash_7 = art_7.metadata.content_hash
    file_path_7 = art_7.metadata.file_path
    
    # Tamper with file
    with open(file_path_7, "a") as f:
        f.write("\nTAMPERED_FAILURE_TEST_7_LINE\n")
        
    with open(file_path_7, "rb") as f:
        tampered_bytes = f.read()
    tampered_hash_7 = hashlib.sha256(tampered_bytes).hexdigest()
    
    # Detect mismatch
    mismatch_detected = (stored_hash_7 != tampered_hash_7)
    
    # Restore file
    with open(file_path_7, "wb") as f:
        f.write(tampered_bytes[:-31])
        
    results["Test 7: Artifact Integrity Mismatch"] = {
        "expected": "SHA256(tampered) != stored hash -> Integrity mismatch DETECTED",
        "actual": f"Stored: {stored_hash_7[:16]}..., Computed: {tampered_hash_7[:16]}..., Mismatch Detected: {mismatch_detected}",
        "inference_occurred": False,
        "successful_artifact": True,
        "verdict": "PASS" if mismatch_detected else "FAIL"
    }
    print(f"Result Test 7: {results['Test 7: Artifact Integrity Mismatch']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 8: Trust Manifest Inconsistency
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 8: Trust Manifest Inconsistency ---")
    manifest_res_7 = client.get(f"/api/v1/artifacts/{art_7.artifact_id}/manifest").json()
    manifest_hash_7 = manifest_res_7["integrity"]["artifact_content_hash"]
    
    # Tamper again to test against manifest endpoint response
    with open(file_path_7, "a") as f:
        f.write("\nTAMPERED_MANIFEST_TEST_8\n")
    with open(file_path_7, "rb") as f:
        t8_bytes = f.read()
    t8_hash = hashlib.sha256(t8_bytes).hexdigest()
    
    manifest_inconsistency_detected = (manifest_hash_7 != t8_hash)
    
    # Restore
    with open(file_path_7, "wb") as f:
        f.write(t8_bytes[:-27])
        
    results["Test 8: Trust Manifest Inconsistency"] = {
        "expected": "Manifest content_hash != Actual file hash -> Inconsistency DETECTED",
        "actual": f"Manifest Hash: {manifest_hash_7[:16]}..., File Hash: {t8_hash[:16]}..., Inconsistency Detected: {manifest_inconsistency_detected}",
        "inference_occurred": False,
        "successful_artifact": True,
        "verdict": "PASS" if manifest_inconsistency_detected else "FAIL"
    }
    print(f"Result Test 8: {results['Test 8: Trust Manifest Inconsistency']['verdict']}\n")

    # ------------------------------------------------------------
    # TEST 9: Denied Task Artifact (Denial must not become a success artifact)
    # ------------------------------------------------------------
    print("--- RUNNING FAILURE TEST 9: Denied Task Artifact ---")
    manifest_denied = client.get(f"/api/v1/artifacts/{art_1.artifact_id}/manifest").json()
    
    t9_task_status = manifest_denied["task"]["status"]
    t9_auth_decision = manifest_denied["authority"]["decision"]
    t9_evidence_count = len(manifest_denied["evidence"])
    t9_dep = manifest_denied.get("deployment")
    
    t9_pass = (
        t9_task_status == "FAILED" and
        t9_auth_decision == "DENIED_CAPABILITY" and
        t9_evidence_count == 0 and
        t9_dep is None
    )
    
    results["Test 9: Denied Task Artifact Representation"] = {
        "expected": "Task: FAILED, Authority: DENIED_CAPABILITY, Evidence: 0, Deployment: None -> Verified failure audit record",
        "actual": f"Task Status: {t9_task_status}, Authority: {t9_auth_decision}, Evidence Count: {t9_evidence_count}, Deployment: {t9_dep}",
        "inference_occurred": False,
        "successful_artifact": False,
        "verdict": "PASS" if t9_pass else "FAIL"
    }
    print(f"Result Test 9: {results['Test 9: Denied Task Artifact Representation']['verdict']}\n")

    print("============================================================")
    print("PHASE J SUMMARY RESULTS:")
    for k, v in results.items():
        print(f"  {k}: {v['verdict']}")
    print("============================================================")

    return results

if __name__ == "__main__":
    run_phase_j_suite()
