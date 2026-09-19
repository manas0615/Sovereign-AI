import os
from sovereign.application.services import get_app_service
from sovereign.core.qualification.models import CapabilityContract, QualificationIdentity

svc = get_app_service()
profile = svc.router.deployment_profiles[svc.router.registered_deployments[0].model_name]

print(f"Recorded Deployment Profile:")
print(f"  Model: {profile.model.name} (arch: {profile.model.architecture}, param_b: {profile.model.parameters_b}, ctx: {profile.model.context_length})")
print(f"  Quantization: {profile.quantization}")
print(f"  Runtime: {profile.runtime.value}")
print(f"  Hardware: {profile.hardware_profile}")
print(f"  Context Budget: {profile.context_budget}")

dep_identity = profile.generate_identity()
print(f"\nDeployment Identity Hash: {dep_identity}")

contract = CapabilityContract(name="AgentDecision_v1", version="1.0")
qual_identity = QualificationIdentity.generate(profile, contract)
print(f"Qualification Identity (AgentDecision_v1): {qual_identity}")

print("\nRunning real inference through gateway...")
from sovereign.core.runtime.models import InferenceRequest
from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT

req = InferenceRequest(prompt="You are operating inside a sovereign local AI system.\nSupported actions: FINAL\n\nTask: Output action FINAL with answer 'IDENTITY_TEST'", response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=100)

svc.model_adapter._lifecycle.start()
try:
    resp = svc.gateway.generate(req)
    print(f"\nInference Result:\n{resp.text}")
    print(f"\nReported Runtime Deployment Identity via Provider: {resp.provider.model_name}")
finally:
    svc.model_adapter._lifecycle.stop()

print("\nDone.")
