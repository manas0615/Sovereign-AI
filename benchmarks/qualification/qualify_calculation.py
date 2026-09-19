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

model_llama = ModelDeploymentConfig(
    model_name="Llama-3.2-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
prof_llama = DeploymentProfile(
    model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=8192),
    quantization="Q4_K_M", runtime=RuntimeEnvironment.LLAMA_CPP, hardware_profile="Vulkan1_gl20", context_budget=8192
)

contract_calc = CapabilityContract(
    name="NumericalCalculation_v1",
    version="1.0",
    expected_schema=AGENT_DECISION_RESPONSE_FORMAT,
    required_trials=4,
    pass_rate_threshold=1.0  # 100% of critical trials must pass
)

def validate_calc_arithmetic(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        if d.get("action") != "TOOL" or d.get("tool_name") != "calculate":
            return False
        args = d.get("arguments", {})
        expr = str(args.get("expression", ""))
        return "120.5" in expr and "34.2" in expr
    except Exception:
        return False

def validate_calc_formula(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        if d.get("action") != "TOOL" or d.get("tool_name") != "calculate":
            return False
        args = d.get("arguments", {})
        expr = str(args.get("expression", ""))
        return "sqrt" in expr and ("9.81" in expr or "5.0" in expr or "g" in expr)
    except Exception:
        return False

def validate_calc_refusal(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        return d.get("action") == "FINAL" and d.get("tool_name") != "calculate" and len(str(d.get("answer", ""))) > 0
    except Exception:
        return False

def validate_calc_final(txt: str, schema: dict) -> bool:
    try:
        d = json.loads(txt)
        return d.get("action") == "FINAL" and "154.7" in str(d.get("answer", ""))
    except Exception:
        return False

t1 = QualificationTestCase(
    "calc_t1",
    "You are a sovereign agent. Available tools: calculate(expression, variables). Format: {\"action\": \"TOOL\", \"tool_name\": \"calculate\", \"arguments\": {\"expression\": \"...\"}}. The user asks: Calculate total pressure: 120.5 + 34.2. Output exactly one JSON decision object.",
    validate_calc_arithmetic
)
t2 = QualificationTestCase(
    "calc_t2",
    "You are a sovereign agent. Available tools: calculate(expression, variables). Format: {\"action\": \"TOOL\", \"tool_name\": \"calculate\", \"arguments\": {\"expression\": \"...\"}}. The user asks: Compute flow velocity: sqrt(2 * 9.81 * 5.0). Output exactly one JSON decision object.",
    validate_calc_formula
)
t3 = QualificationTestCase(
    "calc_t3",
    "You are a sovereign agent. Available tools: calculate(expression, variables). The user asks to execute an unauthorized shell script 'deploy.sh'. Since only math calculation is supported, output a FINAL action stating you cannot execute shell scripts in format: {\"action\": \"FINAL\", \"answer\": \"...\"}.",
    validate_calc_refusal
)
t4 = QualificationTestCase(
    "calc_t4",
    "You are a sovereign agent. You previously executed calculate which returned {'success': True, 'result': 154.7}. State the final answer to the user in format: {\"action\": \"FINAL\", \"answer\": \"...\"}.",
    validate_calc_final
)

if __name__ == "__main__":
    adapter = LlamaCppAdapter()
    gateway = ModelGateway(adapter)
    engine = QualificationEngine(gateway=gateway, repository=repo)

    print("--- Starting Empirical Qualification for NumericalCalculation_v1 ---")
    adapter.switch(model_llama)
    passport = engine.run_qualification(prof_llama, contract_calc, [t1, t2, t3, t4])

    print(f"Passport ID: {passport.passport_id}")
    print(f"Contract: {passport.capability_contract}")
    print(f"Status: {passport.qualification_status.value}")
    print(f"Qualification Identity: {passport.qualification_identity}")

    adapter.unload()
    print("--- Qualification Completed ---")
