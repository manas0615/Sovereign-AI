from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class ManifestArtifactInfo(BaseModel):
    artifact_id: str
    content_hash: str
    artifact_type: str
    status: str

class ManifestTaskInfo(BaseModel):
    task_id: str
    status: str
    goal: str

class ManifestCapabilityInfo(BaseModel):
    name: str

class ManifestDeploymentInfo(BaseModel):
    deployment_identity: str
    model: str
    # runtime and context may not be readily available in the DB, only in config.

class ManifestQualificationInfo(BaseModel):
    qualification_identity: str
    passport_id: str
    status: str

class ManifestAuthorityInfo(BaseModel):
    decision: str
    reason: str

class ManifestExecutionInfo(BaseModel):
    trace_reference: str
    state_items: List[Dict[str, Any]]

class ManifestEvidenceInfo(BaseModel):
    source_id: str
    chunk_id: Optional[str]
    locator: str

class ManifestIntegrityInfo(BaseModel):
    algorithm: str = "SHA-256"
    artifact_content_hash: str

class TrustManifest(BaseModel):
    manifest_version: str = "1.0"
    artifact: ManifestArtifactInfo
    task: ManifestTaskInfo
    capability: Optional[ManifestCapabilityInfo]
    deployment: Optional[ManifestDeploymentInfo]
    qualification: Optional[ManifestQualificationInfo]
    authority: Optional[ManifestAuthorityInfo]
    execution: ManifestExecutionInfo
    evidence: List[ManifestEvidenceInfo]
    integrity: ManifestIntegrityInfo
