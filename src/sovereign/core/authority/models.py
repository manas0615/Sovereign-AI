from enum import Enum
from pydantic import BaseModel
from typing import Optional
from sovereign.core.qualification.models import CapabilityPassport

class AuthorityOutcome(str, Enum):
    AUTHORITY_GRANTED = "AUTHORITY_GRANTED"
    DENIED_CAPABILITY = "DENIED_CAPABILITY"
    DENIED_POLICY = "DENIED_POLICY"

class AuthorityDecision(BaseModel):
    outcome: AuthorityOutcome
    reason: str
    passport_id: Optional[str] = None
