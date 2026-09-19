from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.qualification.models import CapabilityContract, QualificationIdentity
from sovereign.core.runtime.models import ModelDeploymentConfig, InferenceRequest
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway

adapter = LlamaCppAdapter()
gateway = ModelGateway(adapter)

schema_reasoning = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                },
                "required": ["statement", "confidence"]
            }
        }
    },
    "required": ["findings"],
    "additionalProperties": False
}

model_qwen = ModelDeploymentConfig(
    model_name="Qwen2.5-3B-Instruct",
    model_path=r"C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct-GGUF\snapshots\7dabda4d13d513e3e842b20f0d435c732f172cbe\qwen2.5-3b-instruct-q4_k_m.gguf",
    device="Vulkan1", gpu_layers=20, context_size=8192
)
adapter.switch(model_qwen)

req = InferenceRequest(
    prompt="Extract the finding from this text: 'Inspection at 14:00 confirmed that valve 4 has severe corrosion.'",
    response_format=schema_reasoning,
    max_tokens=100
)

try:
    resp = gateway.generate(req)
    print(resp.text)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    adapter.unload()

