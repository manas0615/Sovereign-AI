import hashlib
"""Local Artifact Engine Implementation."""

import uuid
from typing import Dict, Type
from datetime import datetime

from sovereign.core.artifacts.engine import ArtifactEngine, ArtifactRenderer
from sovereign.core.artifacts.models import ArtifactRequest, Artifact, ArtifactStatus, ArtifactMetadata, ArtifactType
from sovereign.core.state.repository import TaskRepository
from sovereign.infrastructure.artifacts.renderers import MarkdownRenderer, JsonRenderer, DocxRenderer, XlsxRenderer, PptxRenderer, PdfRenderer
from sovereign.infrastructure.artifacts.storage import LocalArtifactStorage

class LocalArtifactEngine(ArtifactEngine):
    """ArtifactEngine that reads task state and generates output deterministically."""
    
    def __init__(self, repository: TaskRepository, storage: LocalArtifactStorage):
        self.repo = repository
        self.storage = storage
        self.renderers: Dict[ArtifactType, ArtifactRenderer] = {
            ArtifactType.MARKDOWN: MarkdownRenderer(),
            ArtifactType.JSON: JsonRenderer(),
            ArtifactType.DOCX: DocxRenderer(),
            ArtifactType.XLSX: XlsxRenderer(),
            ArtifactType.PPTX: PptxRenderer(),
            ArtifactType.PDF: PdfRenderer()
        }
        
    def generate(self, request: ArtifactRequest) -> Artifact:
        try:
            request.validate_sections()
        except ValueError as e:
            return self._fail_fast(request, str(e))
            
        task = self.repo.get_task(request.task_id)
        if not task:
            return self._fail_fast(request, f"Task {request.task_id} not found")
            
        state_items = self.repo.get_state_items(request.task_id)
        evidence = self.repo.get_evidence(request.task_id)
        
        # Determine renderer
        if request.artifact_type not in self.renderers:
            return self._fail_fast(request, f"Unsupported artifact type {request.artifact_type}")
            
        renderer = self.renderers[request.artifact_type]
        
        # Render
        try:
            content = renderer.render(task, state_items, evidence, request)
        except Exception as e:
            return self._fail_fast(request, f"Rendering failed: {e}")
            
        # Determine extension and version suffix
        if request.artifact_type == ArtifactType.MARKDOWN:
            ext = ".md"
        elif request.artifact_type == ArtifactType.JSON:
            ext = ".json"
        elif request.artifact_type == ArtifactType.DOCX:
            ext = ".docx"
        elif request.artifact_type == ArtifactType.XLSX:
            ext = ".xlsx"
        elif request.artifact_type == ArtifactType.PPTX:
            ext = ".pptx"
        elif request.artifact_type == ArtifactType.PDF:
            ext = ".pdf"
        else:
            ext = ".bin"

        
        artifact_id = f"art-{uuid.uuid4().hex[:8]}"
        filename = f"{request.task_id}_{artifact_id}{ext}"
        
        # Write to storage
        try:
            target_path = self.storage.write_artifact_file(filename, content)
        except Exception as e:
            return self._fail_fast(request, f"Storage failed: {e}")
            
        # Collect provenance for the artifact metadata
        sources = []
        ev_map = {e.evidence_id: e for e in evidence}
        for item in state_items:
            if hasattr(item, "evidence_refs"):
                for ref_id in item.evidence_refs:
                    if ref_id in ev_map:
                        e = ev_map[ref_id]
                        # Don't import here since we have it from models
                        from sovereign.core.artifacts.models import ArtifactSourceReference
                        sources.append(ArtifactSourceReference(
                            source_id=e.source_id,
                            locator=e.locator,
                            metadata=e.metadata
                        ))
                        
        # Deduplicate sources by source_id+locator
        seen = set()
        deduped_sources = []
        for s in sources:
            key = (s.source_id, s.locator)
            if key not in seen:
                seen.add(key)
                deduped_sources.append(s)
                
        # Build final artifact
        content_bytes = content.encode('utf-8') if isinstance(content, str) else content
        metadata = ArtifactMetadata(
            file_path=str(target_path),
            size_bytes=len(content_bytes),
            sections_rendered=request.requested_sections,
            content_hash=hashlib.sha256(content_bytes).hexdigest()
        )
        
        artifact = Artifact(
            artifact_id=artifact_id,
            task_id=request.task_id,
            title=request.title,
            type=request.artifact_type,
            status=ArtifactStatus.COMPLETED,
            metadata=metadata,
            source_references=deduped_sources
        )
        
        self.storage.save_artifact_metadata(artifact)
        return artifact
        
    def _fail_fast(self, request: ArtifactRequest, reason: str) -> Artifact:
        """Return a structured failure without persisting a corrupt file."""
        return Artifact(
            task_id=request.task_id,
            title=request.title,
            type=request.artifact_type,
            status=ArtifactStatus.FAILED,
            # We don't save failed metadata into the manifest necessarily, 
            # but we return it so the caller knows what happened.
            # Wait, maybe we should save it? The prompt says "A failed generation must not leave behind a misleading completed record."
            # Saving it as FAILED is fine.
        )
