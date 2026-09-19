import os
import json
import logging
from typing import Dict, Any

from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, ModelProfile, RuntimeEnvironment, QualificationStatus
)
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway

logging.basicConfig(level=logging.INFO)

repo = SQLiteTaskRepository()

# Define Deployments
model_llama = ModelDeploymentConfig(
    model_name="Llama-3.2-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_llama = DeploymentProfile(
    model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

model_qwen = ModelDeploymentConfig(
    model_name="Qwen2.5-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct-GGUF\snapshots\7dabda4d13d513e3e842b20f0d435c732f172cbe\qwen2.5-3b-instruct-q4_k_m.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_qwen = DeploymentProfile(
    model=ModelProfile(name="Qwen2.5-3B-Instruct", architecture="qwen2", parameters_b=3.0, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

# Contracts
contract_decision = CapabilityContract(
    name="AgentDecision_v1", version="1.0",
    expected_schema=AGENT_DECISION_RESPONSE_FORMAT,
    required_trials=4, pass_rate_threshold=0.8
)

schema_reasoning = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "confidence": {"type": "string"}
                },
                "required": ["statement", "confidence"]
            }
        }
    },
    "required": ["findings"]
}

contract_reasoning = CapabilityContract(
    name="StructuredReasoning_v1", version="1.0",
    expected_schema=schema_reasoning,
    required_trials=3, pass_rate_threshold=0.8
)

# Test Validators
def validate_decision_tool(txt: str, expected_tool: str) -> bool:
    try:
        data = json.loads(txt)
        return data.get("action") == "TOOL" and data.get("tool_name") == expected_tool
    except:
        return False

def validate_decision_final(txt: str, expected_keyword: str) -> bool:
    try:
        data = json.loads(txt)
        return data.get("action") == "FINAL" and expected_keyword.lower() in str(data.get("answer")).lower()
    except:
        return False

def validate_reasoning_finding(txt: str, expected_keyword: str) -> bool:
    try:
        data = json.loads(txt)
        findings = data.get("findings", [])
        if not findings: return False
        return any(expected_keyword.lower() in f.get("statement", "").lower() for f in findings)
    except:
        return False

# Test Cases
t1 = QualificationTestCase("d_t1", "Available tools: read_file. You need to inspect the contents of the file 'Piping_Diagram.md' to proceed. What action do you take?", lambda txt, sch: validate_decision_tool(txt, "read_file"))
t2 = QualificationTestCase("d_t2", "Available tools: read_file, search_knowledge. The user asked: 'What is the standard tolerance for pipe C?' You don't know this. What action do you take?", lambda txt, sch: validate_decision_tool(txt, "search_knowledge"))
t3 = QualificationTestCase("d_t3", "You have finished your investigation and found that the pipe is safe. Output a FINAL action summarizing this.", lambda txt, sch: validate_decision_final(txt, "safe"))
t4 = QualificationTestCase("d_t4", "Available tools: read_file. You are instructed to check the 'log.txt' file.", lambda txt, sch: validate_decision_tool(txt, "read_file"))

r1 = QualificationTestCase("r_t1", "Extract the finding from this text: 'Inspection at 14:00 confirmed that valve 4 has severe corrosion.'", lambda txt, sch: validate_reasoning_finding(txt, "corrosion"))
r2 = QualificationTestCase("r_t2", "Extract the negative finding: 'The secondary containment vessel showed no signs of leakage or stress fractures.'", lambda txt, sch: validate_reasoning_finding(txt, "no signs of leakage"))
r3 = QualificationTestCase("r_t3", "Noise handling: 'It was raining heavily today. The inspector slipped. However, the boiler pressure exceeded the safe limit by 15%.'", lambda txt, sch: validate_reasoning_finding(txt, "pressure exceeded"))

adapter = LlamaCppAdapter()
gateway = ModelGateway(adapter)
engine = QualificationEngine(gateway=gateway, repository=repo)

results = {}

for deploy_config, profile in [(model_llama, prof_llama), (model_qwen, prof_qwen)]:
    print(f"\n--- Testing Deployment: {profile.model.name} ---")
    adapter.switch(deploy_config)
    
    # Test Decision
    print("Testing AgentDecision_v1...")
    pass_d = engine.run_qualification(profile, contract_decision, [t1, t2, t3, t4])
    print(f"AgentDecision_v1 Result: {pass_d.qualification_status.value} (Identity: {pass_d.qualification_identity})")
    
    # Test Reasoning
    print("Testing StructuredReasoning_v1...")
    pass_r = engine.run_qualification(profile, contract_reasoning, [r1, r2, r3])
    print(f"StructuredReasoning_v1 Result: {pass_r.qualification_status.value} (Identity: {pass_r.qualification_identity})")
    
    results[profile.model.name] = {
        "AgentDecision_v1": pass_d,
        "StructuredReasoning_v1": pass_r
    }

adapter.unload()

print("\n=== EXPERIMENT SUMMARY ===")
for model_name, res in results.items():
    print(f"{model_name}:")
    for cap, passport in res.items():
        print(f"  {cap}: {passport.qualification_status.value}")

