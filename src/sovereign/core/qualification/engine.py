import json
import uuid
import jsonschema
from typing import List, Dict, Any, Callable
from datetime import datetime, timezone
from sovereign.core.qualification.models import (
    DeploymentProfile, CapabilityContract, QualificationIdentity,
    QualificationTrial, QualificationResult, CapabilityPassport,
    QualificationStatus
)
from sovereign.core.state.repository import (
    QualificationRepository, QualificationTrialRecord, 
    QualificationResultRecord, CapabilityPassportRecord
)
from sovereign.core.runtime.models import InferenceRequest
from sovereign.core.runtime.gateway import ModelGateway

class QualificationTestCase:
    def __init__(self, test_id: str, prompt: str, validator: Callable[[str, Dict], bool]):
        self.test_id = test_id
        self.prompt = prompt
        self.validator = validator

class QualificationEngine:
    def __init__(self, gateway: ModelGateway, repository: QualificationRepository):
        self.gateway = gateway
        self.repository = repository

    def run_qualification(
        self, 
        deployment: DeploymentProfile, 
        contract: CapabilityContract,
        test_cases: List[QualificationTestCase]
    ) -> CapabilityPassport:
        
        qual_identity = QualificationIdentity.generate(deployment, contract)
        
        passed_trials = 0
        failed_trials = 0
        
        # We will record trials and push them to repository
        for test_case in test_cases:
            start_time = datetime.now(timezone.utc)
            
            # Formulate inference request (using structured generation if schema provided)
            request = InferenceRequest(
                prompt=test_case.prompt,
                response_format=contract.expected_schema if contract.expected_schema else None,
                max_tokens=contract.timeout_ms // 100  # rough proxy or use config
            )
            
            success = False
            validation_outcome = "PENDING"
            failure_category = None
            
            try:
                # Issue generating request
                # Depending on the backend, this is synchronous
                response = self.gateway.generate(request)
                
                # Check outcome against validator
                is_valid = test_case.validator(response.text, contract.expected_schema)
                if is_valid:
                    success = True
                    validation_outcome = "PASS"
                    passed_trials += 1
                else:
                    validation_outcome = "FAIL_VALIDATION"
                    failure_category = "CONTENT_MISMATCH"
                    failed_trials += 1
            except Exception as e:
                validation_outcome = "FAIL_EXCEPTION"
                failure_category = "RUNTIME_ERROR"
                failed_trials += 1
                
            # Create and save Trial Record
            trial_id = str(uuid.uuid4())
            trial = QualificationTrialRecord(
                trial_id=trial_id,
                qualification_identity=qual_identity,
                test_id=test_case.test_id,
                prompt_reference=test_case.prompt[:50] + "...",
                timestamp=datetime.now(timezone.utc),
                success=success,
                validation_outcome=validation_outcome,
                failure_category=failure_category,
                resource_metrics={}, # would be populated from actual system metrics
                metadata={}
            )
            self.repository.save_trial(trial)
            
        total_trials = passed_trials + failed_trials
        pass_rate = (passed_trials / total_trials) if total_trials > 0 else 0.0
        
        qual_status = QualificationStatus.UNQUALIFIED
        if pass_rate >= contract.pass_rate_threshold and total_trials >= contract.required_trials:
            qual_status = QualificationStatus.QUALIFIED
            
        # Create and save Qualification Result
        result_id = str(uuid.uuid4())
        result_record = QualificationResultRecord(
            result_id=result_id,
            qualification_identity=qual_identity,
            capability_contract=contract.name,
            deployment_identity=deployment.generate_identity(),
            trial_counts={"passed": passed_trials, "failed": failed_trials},
            compliance_metrics={"pass_rate": pass_rate},
            resource_stability="STABLE",
            threshold_evaluation="PASS" if qual_status == QualificationStatus.QUALIFIED else "FAIL",
            qualification_status=qual_status.value,
            timestamp=datetime.now(timezone.utc),
            metadata={}
        )
        self.repository.save_result(result_record)
        
        # Create and save Passport
        passport_id = str(uuid.uuid4())
        passport_record = CapabilityPassportRecord(
            passport_id=passport_id,
            qualification_identity=qual_identity,
            deployment_identity=deployment.generate_identity(),
            capability_contract=contract.name,
            result_id=result_id,
            qualification_status=qual_status.value,
            qualification_timestamp=datetime.now(timezone.utc),
            invalidation_info={},
            metadata={}
        )
        self.repository.save_passport(passport_record)
        
        return CapabilityPassport(
            passport_id=passport_id,
            qualification_identity=qual_identity,
            deployment_identity=deployment.generate_identity(),
            capability_contract=contract.name,
            result_id=result_id,
            qualification_status=qual_status,
            qualification_timestamp=passport_record.qualification_timestamp,
            invalidation_info={},
            metadata={}
        )
