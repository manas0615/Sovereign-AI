"""Local, atomic artifact storage engine."""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, Union

from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.paths import get_artifact_dir
from sovereign.core.artifacts.models import Artifact, ArtifactStatus
from sovereign.core.exceptions import InfrastructureError

class LocalArtifactStorage:
    """Manages the persistence of artifacts and their metadata manifest."""
    
    def __init__(self):
        self.artifact_dir = get_artifact_dir()
        self.settings = get_settings()
        self.manifest_path = self.artifact_dir / "manifest.json"
        self._ensure_manifest()
        
    def _ensure_manifest(self):
        if not self.manifest_path.exists():
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
                
    def _read_manifest(self) -> Dict[str, dict]:
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
            
    def _write_manifest(self, manifest: Dict[str, dict]):
        # Atomic write for manifest
        fd, temp_path = tempfile.mkstemp(dir=self.artifact_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            os.replace(temp_path, self.manifest_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise InfrastructureError(f"Failed to write artifact manifest: {e}")
            
    def save_artifact_metadata(self, artifact: Artifact):
        """Save artifact to the manifest."""
        manifest = self._read_manifest()
        manifest[artifact.artifact_id] = artifact.model_dump(mode='json')
        self._write_manifest(manifest)
        
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Retrieve artifact metadata by ID."""
        manifest = self._read_manifest()
        if artifact_id in manifest:
            return Artifact.model_validate(manifest[artifact_id])
        return None

    def list_all_artifacts(self) -> List[Artifact]:
        """Retrieve all registered artifacts sorted by creation date."""
        manifest = self._read_manifest()
        artifacts = []
        for aid, data in manifest.items():
            try:
                artifacts.append(Artifact.model_validate(data))
            except Exception:
                pass
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        return artifacts
        
    def resolve_secure_path(self, filename: str) -> Path:
        """Resolve filename ensuring it resides within artifact_dir."""
        # Explicitly reject directory separators and traversal patterns
        if "/" in filename or "\\" in filename or ".." in filename:
            raise InfrastructureError(f"Path traversal detected for filename: {filename}")
            
        target_path = (self.artifact_dir / filename).resolve()
        
        # Verify target is still within artifact_dir (defense in depth)
        if not str(target_path).startswith(str(self.artifact_dir.resolve())):
            raise InfrastructureError(f"Path traversal detected for filename: {filename}")
            
        return target_path

    def write_artifact_file(self, filename: str, content: Union[str, bytes]) -> Path:
        """Write content atomically to filename, enforcing limits."""
        target_path = self.resolve_secure_path(filename)
        
        # Ensure it doesn't overwrite an existing completed artifact file
        if target_path.exists():
            raise InfrastructureError(f"Artifact file {filename} already exists. Overwrite not allowed.")
        
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        if len(content_bytes) > self.settings.max_artifact_size_bytes:
            raise InfrastructureError(f"Artifact size ({len(content_bytes)} bytes) exceeds maximum limit ({self.settings.max_artifact_size_bytes} bytes).")
            
        # Atomic write
        fd, temp_path = tempfile.mkstemp(dir=self.artifact_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content_bytes)
            os.replace(temp_path, target_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise InfrastructureError(f"Failed to write artifact file {filename}: {e}")
            
        return target_path
