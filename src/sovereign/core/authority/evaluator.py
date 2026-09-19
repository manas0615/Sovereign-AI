from typing import Optional, List
from pydantic import BaseModel
from sovereign.core.qualification.models import (
    CapabilityPassport, QualificationStatus, DeploymentProfile, CapabilityContract
)
from sovereign.core.authority.models import AuthorityDecision, AuthorityOutcome
from sovereign.core.state.repository import QualificationRepository

class AuthorityPolicy(BaseModel):
    allowed_contracts: List[str]
    allow_unqualified: bool = False

class AuthorityEvaluator:
    def __init__(self, repository: QualificationRepository, policy: AuthorityPolicy):
        self.repository = repository
        self.policy = policy

    def evaluate(
        self, 
        deployment: DeploymentProfile, 
        contract: CapabilityContract,
        passport: Optional[CapabilityPassport] = None
    ) -> AuthorityDecision:
        
        # 1. Check Policy
        if contract.name not in self.policy.allowed_contracts:
            return AuthorityDecision(
                outcome=AuthorityOutcome.DENIED_POLICY,
                reason=f"Policy forbids contract: {contract.name}"
            )
            
        # 2. Check Qualification
        if passport is None:
            # Policy might allow unqualified runs? The USP says "fail-closed governance", "deny rather than grant"
            if not self.policy.allow_unqualified:
                return AuthorityDecision(
                    outcome=AuthorityOutcome.DENIED_CAPABILITY,
                    reason="No passport provided and policy forbids unqualified execution."
                )
            else:
                return AuthorityDecision(
                    outcome=AuthorityOutcome.AUTHORITY_GRANTED,
                    reason="No passport provided, but policy explicitly allows unqualified execution."
                )
                
        # We have a passport, check validity
        if not passport.is_valid(deployment):
            return AuthorityDecision(
                outcome=AuthorityOutcome.DENIED_CAPABILITY,
                reason="Passport is invalid for current deployment or status is not QUALIFIED.",
                passport_id=passport.passport_id
            )
            
        # 3. Everything checks out
        return AuthorityDecision(
            outcome=AuthorityOutcome.AUTHORITY_GRANTED,
            reason="Passport is valid and policy permits.",
            passport_id=passport.passport_id
        )
