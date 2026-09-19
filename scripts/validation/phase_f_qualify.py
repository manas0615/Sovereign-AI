import logging
from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, ModelProfile, RuntimeEnvironment
)
from sovereign.core.qualification.engine import QualificationEngine, QualificationTestCase
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway

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

contract_retrieval = CapabilityContract(
    name="DocumentRetrieval_v1", version="1.0",
    expected_schema={}, # Unstructured
    required_trials=4, pass_rate_threshold=0.8
)

def validate_retrieval(txt: str, expected_keyword: str) -> bool:
    return expected_keyword.lower() in txt.lower()

t1 = QualificationTestCase("dr_t1", "Document: The boiler operating pressure is 150 PSI. Question: What is the boiler pressure?", lambda txt, sch: validate_retrieval(txt, "150"))
t2 = QualificationTestCase("dr_t2", "Document: Pipe 4 is made of Titanium. Question: What material is Pipe 4?", lambda txt, sch: validate_retrieval(txt, "titanium"))
t3 = QualificationTestCase("dr_t3", "Document: The inspection occurred on October 12th. Question: What date was the inspection?", lambda txt, sch: validate_retrieval(txt, "october 12"))
t4 = QualificationTestCase("dr_t4", "Document: The status of the valve is closed. Question: What is the valve status?", lambda txt, sch: validate_retrieval(txt, "closed"))

adapter = LlamaCppAdapter()
gateway = ModelGateway(adapter)
engine = QualificationEngine(gateway=gateway, repository=repo)

adapter.switch(model_llama)
print("Testing DocumentRetrieval_v1 for Qualification...")
pass_r = engine.run_qualification(prof_llama, contract_retrieval, [t1, t2, t3, t4])
print(f"DocumentRetrieval_v1 Result: {pass_r.qualification_status.value} (Identity: {pass_r.qualification_identity})")

adapter.unload()
