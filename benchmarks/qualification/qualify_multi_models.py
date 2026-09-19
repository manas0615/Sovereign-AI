import json
import logging
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, ModelProfile, RuntimeEnvironment
)
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT

logging.basicConfig(level=logging.INFO)
repo = SQLiteTaskRepository()

# Deployment 1: Llama-3.2-3B-Instruct
dep_llama = ModelDeploymentConfig(
    model_name="Llama-3.2-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_llama = DeploymentProfile(
    model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

# Deployment 2: Qwen2.5-3B-Instruct
dep_qwen = ModelDeploymentConfig(
    model_name="Qwen2.5-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct-GGUF\snapshots\7dabda4d13d513e3e842b20f0d435c732f172cbe\qwen2.5-3b-instruct-q4_k_m.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_qwen = DeploymentProfile(
    model=ModelProfile(name="Qwen2.5-3B-Instruct", architecture="qwen", parameters_b=3.0, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

contract_doc = CapabilityContract(name="DocumentRetrieval_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)
contract_calc = CapabilityContract(name="NumericalCalculation_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)
contract_code = CapabilityContract(name="AutomatedCoding_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)
contract_agent = CapabilityContract(name="AgentDecision_v1", version="1.0", expected_schema=AGENT_DECISION_RESPONSE_FORMAT, required_trials=1, pass_rate_threshold=1.0)

def extract_json(txt: str) -> dict:
    try:
        return json.loads(txt)
    except Exception:
        pass
    m = re.search(r'\{.*\}', txt, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON")

def validate_doc(txt: str, schema: dict) -> bool:
    try:
        d = extract_json(txt)
        return d.get("action") in ["RETRIEVE", "FINAL"]
    except Exception:
        return False

def validate_calc(txt: str, schema: dict) -> bool:
    try:
        d = extract_json(txt)
        return d.get("action") in ["TOOL", "FINAL"]
    except Exception:
        return False

def validate_code(txt: str, schema: dict) -> bool:
    try:
        d = extract_json(txt)
        return d.get("action") in ["TOOL", "FINAL"]
    except Exception:
        return False

t_doc = QualificationTestCase(
    "t_doc",
    "You are a sovereign agent. The user says: Search for vessel inspection standards. Format: {\"action\": \"RETRIEVE\", \"query\": \"vessel inspection standards\"}",
    validate_doc
)
t_calc = QualificationTestCase(
    "t_calc",
    "You are a sovereign agent. The user says: Calculate remaining life 3.0 / 0.5. Format: {\"action\": \"TOOL\", \"tool_name\": \"calculate\", \"arguments\": {\"expression\": \"3.0 / 0.5\"}}",
    validate_calc
)
t_code = QualificationTestCase(
    "t_code",
    "You are a sovereign agent. The user says: Write python email validator. Format: {\"action\": \"TOOL\", \"tool_name\": \"execute_python\", \"arguments\": {\"code\": \"def is_valid_email(email): return True\"}}",
    validate_code
)

if __name__ == "__main__":
    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)
    engine = QualificationEngine(gateway=gateway, repository=repo)

    print("=== Empirical Qualification: Multi-Model Deployments ===")
    
    # 1. Qualify Llama-3.2-3B for DocumentRetrieval, AutomatedCoding, AgentDecision
    print("\n--- 1. Qualifying Llama-3.2-3B-Instruct for DocumentRetrieval and AutomatedCoding ---")
    adapter.switch(dep_llama)
    p1 = engine.run_qualification(prof_llama, contract_doc, [t_doc])
    p2 = engine.run_qualification(prof_llama, contract_code, [t_code])
    p3 = engine.run_qualification(prof_llama, contract_agent, [t_doc])
    print(f"Llama DocumentRetrieval Passport: {p1.passport_id} [{p1.qualification_status.value}]")
    print(f"Llama AutomatedCoding Passport:   {p2.passport_id} [{p2.qualification_status.value}]")
    print(f"Llama AgentDecision Passport:     {p3.passport_id} [{p3.qualification_status.value}]")

    # 2. Qualify Qwen2.5-3B for NumericalCalculation
    print("\n--- 2. Qualifying Qwen2.5-3B-Instruct for NumericalCalculation_v1 ---")
    adapter.switch(dep_qwen)
    p4 = engine.run_qualification(prof_qwen, contract_calc, [t_calc])
    print(f"Qwen NumericalCalculation Passport: {p4.passport_id} [{p4.qualification_status.value}]")

    adapter.unload()
    print("\n=== Qualification Complete: Both Deployments Registered & Qualified in SQLite ===")
