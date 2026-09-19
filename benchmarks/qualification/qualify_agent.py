import json
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, ModelProfile, RuntimeEnvironment, QualificationStatus
)
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT

logging.basicConfig(level=logging.INFO)
repo = SQLiteTaskRepository()

# Remove the manually injected row
conn = repo._get_connection()
conn.execute("DELETE FROM capability_passports WHERE passport_id='psp-llama32-agent-v1'")
conn.commit()

model_llama = ModelDeploymentConfig(
    model_name="Llama-3.2-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_llama = DeploymentProfile(
    model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

contract_agent = CapabilityContract(
    name="AgentDecision_v1",
    version="1.0",
    expected_schema=AGENT_DECISION_RESPONSE_FORMAT,
    required_trials=2,
    pass_rate_threshold=1.0
)

def validate_agent_t1(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        return d.get("action") == "FINAL"
    except Exception:
        return False

def validate_agent_t2(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        return d.get("action") in ["TOOL", "RETRIEVE", "FINAL"]
    except Exception:
        return False

t1 = QualificationTestCase(
    "agent_t1",
    "You are a sovereign agent. The user says: Hello. Respond with a greeting. Output format: {\"action\": \"FINAL\", \"answer\": \"...\"}.",
    validate_agent_t1
)
t2 = QualificationTestCase(
    "agent_t2",
    "You are a sovereign agent. Output format: {\"action\": \"FINAL\", \"answer\": \"...\"}. Acknowledge receipt.",
    validate_agent_t2
)

if __name__ == "__main__":
    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)
    engine = QualificationEngine(gateway=gateway, repository=repo)

    print("--- Starting Empirical Qualification for AgentDecision_v1 ---")
    adapter.switch(model_llama)
    passport = engine.run_qualification(prof_llama, contract_agent, [t1, t2])

    print(f"Passport ID: {passport.passport_id}")
    print(f"Contract: {passport.capability_contract}")
    print(f"Status: {passport.qualification_status.value}")
    print(f"Qualification Identity: {passport.qualification_identity}")

    adapter.unload()
    print("--- Qualification Completed ---")
