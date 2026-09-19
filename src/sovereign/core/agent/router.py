"""Qualification-aware model routing for Agent Host (Package 05)."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, CapabilityPassport, QualificationIdentity
)
from sovereign.core.authority.evaluator import AuthorityEvaluator
from sovereign.core.authority.models import AuthorityOutcome, AuthorityDecision
from sovereign.core.state.repository import QualificationRepository
from sovereign.core.exceptions import ModelRuntimeError

class TaskCapabilityRequirement(BaseModel):
    capability_name: str
    min_contract_version: str = "1.0"
    rationale: str
    is_supported: bool = True

class TaskCharacterizer:
    """Deterministic characterization of tasks into bounded capability requirements."""
    
    # Supported capability contracts in the current frozen baseline
    SUPPORTED_CAPABILITIES = {
        "AgentDecision_v1": "General reasoning, multi-step planning, and structured agent decisions",
        "DocumentRetrieval_v1": "Grounded document retrieval and synthesis",
        "NumericalCalculation_v1": "Bounded, deterministic numerical evaluation and formula calculation using the governed calculate tool",
        "StructuredReasoning_v1": "Constrained structured output generation",
        "AutomatedCoding_v1": "Generates and executes Python code using restricted subprocess execution"
    }
    
    # Future / unsupported capabilities that must be rejected fail-closed
    UNSUPPORTED_CAPABILITIES = {
        "OCR": "Optical character recognition is not yet integrated in P03 baseline",
        "VLM": "Vision-language multimodal reasoning is not yet integrated in P01/P03 baseline",
        "MultimodalReasoning": "Multimodal analysis is not yet integrated",
        "SandboxedExecution": "Restricted execution sandbox is not yet integrated in P04 baseline",
        "OfficeArtifactRendering": "DOCX/XLSX/PPTX rendering is not yet integrated in P06 baseline"
    }

    @classmethod
    def characterize(cls, goal: str) -> TaskCapabilityRequirement:
        goal_lower = goal.lower()
        
        # 1. Detect unsupported capabilities first to ensure fail-closed governance
        if any(kw in goal_lower for kw in ["ocr", "scanned document", "scan image", "extract text from image"]):
            return TaskCapabilityRequirement(
                capability_name="OCR",
                rationale=cls.UNSUPPORTED_CAPABILITIES["OCR"],
                is_supported=False
            )
            
        if any(kw in goal_lower for kw in ["image reasoning", "vlm", "vision analysis", "chart image", "diagram image"]):
            return TaskCapabilityRequirement(
                capability_name="VLM",
                rationale=cls.UNSUPPORTED_CAPABILITIES["VLM"],
                is_supported=False
            )
            
        if any(kw in goal_lower for kw in ["sandbox execution", "run untrusted python", "isolated container", "os-level isolation", "hardened sandbox"]):
            return TaskCapabilityRequirement(
                capability_name="SandboxedExecution",
                rationale=cls.UNSUPPORTED_CAPABILITIES["SandboxedExecution"],
                is_supported=False
            )
            
        # 2. Map to automated coding capability
        if any(kw in goal_lower for kw in ["write a python function", "write python code", "generate python", "code a python script", "python script"]):
            return TaskCapabilityRequirement(
                capability_name="AutomatedCoding_v1",
                rationale="Task requires writing and executing Python code via restricted subprocess tool",
                is_supported=True
            )
            
        # 2. Map to calculation capability
        if any(kw in goal_lower for kw in [
            "calculate", "compute", "evaluate expression", "arithmetic",
            "numerical calculation", "evaluate formula", "formula calculation"
        ]):
            return TaskCapabilityRequirement(
                capability_name="NumericalCalculation_v1",
                rationale="Task requires bounded numerical evaluation and formula calculation",
                is_supported=True
            )
            
        # 3. Map to document retrieval capability
        if any(kw in goal_lower for kw in ["retrieve", "search knowledge", "look up document", "find evidence"]):
            return TaskCapabilityRequirement(
                capability_name="DocumentRetrieval_v1",
                rationale="Task requires document retrieval and grounded synthesis",
                is_supported=True
            )
            
        # Default supported standard agent capability
        return TaskCapabilityRequirement(
            capability_name="AgentDecision_v1",
            rationale="Standard structured agent decision and execution contract",
            is_supported=True
        )

class RoutingDecision(BaseModel):
    task_id: str
    required_capability: str
    selected_deployment: Optional[ModelDeploymentConfig] = None
    switch_required: bool = False
    authority_outcome: Optional[AuthorityOutcome] = None
    is_authorized: bool = False
    reason: str

class ModelRouter:
    """Deterministic, qualification-aware model router for Package 05."""
    
    def __init__(
        self,
        gateway: ModelGateway,
        authority_evaluator: AuthorityEvaluator,
        qualification_repository: QualificationRepository,
        registered_deployments: Optional[List[ModelDeploymentConfig]] = None,
        deployment_profiles: Optional[Dict[str, DeploymentProfile]] = None,
        contracts: Optional[Dict[str, CapabilityContract]] = None,
        characterizer: Optional[TaskCharacterizer] = None
    ):
        self.gateway = gateway
        self.authority_evaluator = authority_evaluator
        self.repo = qualification_repository
        self.registered_deployments = registered_deployments or []
        self.deployment_profiles = deployment_profiles or {}
        self.contracts = contracts or {
            "AgentDecision_v1": CapabilityContract(name="AgentDecision_v1", version="1.0"),
            "DocumentRetrieval_v1": CapabilityContract(name="DocumentRetrieval_v1", version="1.0"),
            "NumericalCalculation_v1": CapabilityContract(name="NumericalCalculation_v1", version="1.0"),
            "StructuredReasoning_v1": CapabilityContract(name="StructuredReasoning_v1", version="1.0"),
            "MultimodalInference_v1": CapabilityContract(name="MultimodalInference_v1", version="1.0"),
            "AutomatedCoding_v1": CapabilityContract(name="AutomatedCoding_v1", version="1.0"),
        }
        self.characterizer = characterizer or TaskCharacterizer()

    def characterize_task(self, goal: str) -> TaskCapabilityRequirement:
        return self.characterizer.characterize(goal)

    def route(self, task_id: str, goal: str) -> RoutingDecision:
        # Step 1: Characterize task
        req = self.characterize_task(goal)
        if not req.is_supported:
            return RoutingDecision(
                task_id=task_id,
                required_capability=req.capability_name,
                is_authorized=False,
                reason=f"Unsupported capability '{req.capability_name}': {req.rationale}"
            )
        
        return self.route_capability(req.capability_name, task_id)

    def route_capability(self, capability_name: str, task_id: str = "system") -> RoutingDecision:
        contract = self.contracts.get(capability_name)
        if not contract:
            return RoutingDecision(
                task_id=task_id,
                required_capability=capability_name,
                is_authorized=False,
                reason=f"No capability contract registered for '{capability_name}'"
            )

        # Step 2: Query P08 for qualified & authorized candidate deployments
        qualified_candidates: List[ModelDeploymentConfig] = []
        
        for dep in self.registered_deployments:
            profile = self.deployment_profiles.get(dep.model_name)
            if not profile:
                continue

            # Generate qualification identity using P08
            qual_id = QualificationIdentity.generate(profile, contract)
            
            # Lookup passport in P02/P08 persistence
            # Search by passport_id or list passports
            # The repository interface exposes get_passport(passport_id). We can also check if a passport exists with matching identity.
            # The repository interface exposes get_passport(passport_id) and get_passport_by_identity(qual_id).
            # The qual_id generated above is the qualification identity.
            passport_record = self.repo.get_passport_by_identity(qual_id)
            passport: Optional[CapabilityPassport] = None
            if passport_record:
                passport = CapabilityPassport(
                    passport_id=passport_record.passport_id,
                    qualification_identity=passport_record.qualification_identity,
                    deployment_identity=passport_record.deployment_identity,
                    capability_contract=passport_record.capability_contract,
                    result_id=passport_record.result_id,
                    qualification_status=passport_record.qualification_status,
                    qualification_timestamp=passport_record.qualification_timestamp,
                    invalidation_info=passport_record.invalidation_info,
                    metadata=passport_record.metadata
                )

            # Query P08 AuthorityEvaluator
            decision: AuthorityDecision = self.authority_evaluator.evaluate(
                deployment=profile,
                contract=contract,
                passport=passport
            )

            if decision.outcome == AuthorityOutcome.AUTHORITY_GRANTED:
                qualified_candidates.append(dep)

        # Step 3: Handle no qualified candidates (Fail-Closed)
        if not qualified_candidates:
            return RoutingDecision(
                task_id=task_id,
                required_capability=capability_name,
                is_authorized=False,
                authority_outcome=AuthorityOutcome.DENIED_CAPABILITY,
                reason=f"No qualified and authorized deployment found for capability '{capability_name}'."
            )

        # Step 4: Candidate Selection Policy (Runtime optimization among qualified candidates)
        active_dep = self.gateway.get_active_deployment()
        
        # 4a. If active deployment is among qualified candidates, reuse it (avoid swap latency)
        if active_dep is not None and any(c.model_name == active_dep.model_name for c in qualified_candidates):
            return RoutingDecision(
                task_id=task_id,
                required_capability=capability_name,
                selected_deployment=active_dep,
                switch_required=False,
                authority_outcome=AuthorityOutcome.AUTHORITY_GRANTED,
                is_authorized=True,
                reason=f"Reusing active qualified deployment '{active_dep.model_name}' without model swap."
            )

        # 4b. Deterministic tie-breaking: sort candidates canonically by model_name
        sorted_candidates = sorted(qualified_candidates, key=lambda d: d.model_name)
        target_dep = sorted_candidates[0]
        
        # Step 5: Instruct P01 to switch to selected deployment
        try:
            self.gateway.switch(target_dep)
        except Exception as e:
            return RoutingDecision(
                task_id=task_id,
                required_capability=capability_name,
                selected_deployment=target_dep,
                switch_required=True,
                authority_outcome=AuthorityOutcome.AUTHORITY_GRANTED,
                is_authorized=False,
                reason=f"P01 failed to load qualified deployment '{target_dep.model_name}': {e}"
            )

        return RoutingDecision(
            task_id=task_id,
            required_capability=capability_name,
            selected_deployment=target_dep,
            switch_required=True,
            authority_outcome=AuthorityOutcome.AUTHORITY_GRANTED,
            is_authorized=True,
            reason=f"Switched to qualified deployment '{target_dep.model_name}'."
        )
