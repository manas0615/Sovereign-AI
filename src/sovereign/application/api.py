"""FastAPI application boundaries for Package 07."""

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from typing import List
import os
import tempfile

from sovereign.core.health import check_health, HealthStatus
from sovereign.core.knowledge.models import Document, DocumentStatus
from sovereign.core.knowledge.parser import OCRRequiredError
from sovereign.infrastructure.knowledge.parsers.pdf_parser import PDFParser
from sovereign.infrastructure.knowledge.parsers.text_parser import TextParser
from sovereign.infrastructure.knowledge.chunkers.structure_aware_chunker import StructureAwareChunker
from sovereign.infrastructure.paths import get_data_dir
from sovereign.core.exceptions import ContextBudgetExceeded, StateError, InfrastructureError

from sovereign.application.schemas import (
    TaskCreateRequest, TaskResponse, ArtifactMetadataResponse, DocumentIngestResponse,
    CapabilityPassportResponse, DocumentDetailResponse, DocumentChunkResponse,
    ChatRequest, ChatResponse, CodeExecuteRequest, CodeExecuteResponse
)
from sovereign.application.services import get_app_service
from sovereign.application.config import get_api_settings

# Setup API
app = FastAPI(title="Sovereign AI Workbench", version="1.0.0")
router = APIRouter(prefix="/api/v1")
settings = get_api_settings()


@router.get("/health")
def health_check():
    """Lightweight health check reusing Package 00."""
    result = check_health()
    if result.status == HealthStatus.UNHEALTHY:
        raise HTTPException(status_code=503, detail=result.model_dump(mode='json'))
    return result.model_dump(mode='json')

@router.get("/tasks", response_model=List[TaskResponse])
def list_tasks():
    """Retrieve all persisted tasks."""
    svc = get_app_service()
    return svc.list_tasks()

@router.post("/tasks", response_model=TaskResponse)
def create_task(req: TaskCreateRequest):
    """Create a new task."""
    svc = get_app_service()
    try:
        return svc.create_task(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Retrieve details for a specific task."""
    svc = get_app_service()
    task = svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks/{task_id}/state")
def get_task_state(task_id: str):
    """Retrieve all state items (decisions, findings, etc) for a task."""
    svc = get_app_service()
    task = svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    items = svc.repo.get_state_items(task_id)
    return [item.model_dump() for item in items]


@router.post("/tasks/{task_id}/run")
def run_task(task_id: str, background_tasks: BackgroundTasks):
    """Start or resume task execution in background."""
    svc = get_app_service()
    try:
        svc.schedule_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    except ValueError as e:
        err_msg = str(e)
        if "already actively running" in err_msg:
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)
        
    background_tasks.add_task(svc.execute_task_background, task_id)
    return {"status": "ACCEPTED", "task_id": task_id}

@router.get("/artifacts", response_model=List[ArtifactMetadataResponse])
def list_all_artifacts():
    """Retrieve all generated artifacts across all tasks."""
    svc = get_app_service()
    return svc.list_all_artifacts()

@router.get("/tasks/{task_id}/artifacts", response_model=List[ArtifactMetadataResponse])
def list_artifacts(task_id: str):
    """Read-only artifact listing for a task."""
    svc = get_app_service()
    return svc.list_artifacts(task_id)

@router.get("/artifacts/{artifact_id}/details", response_model=ArtifactMetadataResponse)
def get_artifact_details(artifact_id: str):
    """Retrieve full metadata and provenance for an artifact."""
    svc = get_app_service()
    all_arts = svc.list_all_artifacts()
    for art in all_arts:
        if art.artifact_id == artifact_id:
            return art
    raise HTTPException(status_code=404, detail="Artifact not found")

@router.get("/artifacts/{artifact_id}/download")
@router.get("/artifacts/{artifact_id}")
def download_artifact(artifact_id: str):
    """Secure ID-based artifact download with correct MIME type and content disposition."""
    svc = get_app_service()
    artifact = svc.artifact_storage.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if not artifact.metadata or not artifact.metadata.file_path:
        raise HTTPException(status_code=404, detail="Artifact metadata missing file_path")
        
    try:
        filename = os.path.basename(artifact.metadata.file_path)
        file_path = svc.artifact_storage.resolve_secure_path(filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Artifact file missing from disk")
        fn_lower = filename.lower()
        if fn_lower.endswith(".docx"):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif fn_lower.endswith(".xlsx"):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif fn_lower.endswith(".pptx"):
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        elif fn_lower.endswith(".pdf"):
            media_type = "application/pdf"
        elif fn_lower.endswith(".md"):
            media_type = "text/markdown; charset=utf-8"
        elif fn_lower.endswith(".json"):
            media_type = "application/json; charset=utf-8"
        elif fn_lower.endswith(".csv"):
            media_type = "text/csv; charset=utf-8"
        elif fn_lower.endswith(".py"):
            media_type = "text/x-python; charset=utf-8"
        elif fn_lower.endswith(".txt"):
            media_type = "text/plain; charset=utf-8"
        else:
            media_type = "application/octet-stream"
        return FileResponse(path=file_path, filename=filename, media_type=media_type)
    except InfrastructureError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge/documents", response_model=DocumentIngestResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document into the global knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
        
    ext = os.path.splitext(file.filename)[1].lower().strip('.')
    if ext not in ['txt', 'md', 'pdf', 'png', 'jpg', 'jpeg']:
        raise HTTPException(status_code=400, detail="Unsupported file format. Allowed: txt, md, pdf, png, jpg, jpeg")
        
    svc = get_app_service()
    
    # 1. Bounded Streaming Upload
    import hashlib
    hasher = hashlib.sha256()
    fd, temp_path = tempfile.mkstemp(dir=get_data_dir(), suffix=f".{ext}")
    accumulated_bytes = 0
    try:
        with os.fdopen(fd, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                accumulated_bytes += len(chunk)
                if accumulated_bytes > settings.max_upload_size_bytes:
                    raise HTTPException(status_code=413, detail=f"File exceeds maximum upload size of {settings.max_upload_size_bytes} bytes")
                f.write(chunk)
                hasher.update(chunk)
                
        # 2. Register Document
        doc = Document(
            filename=file.filename,
            source_path=file.filename,
            document_type=ext,
            file_size=accumulated_bytes,
            content_hash=hasher.hexdigest(),
            status=DocumentStatus.REGISTERED
        )
        svc.kb.register_document(doc)
        
        # 3. Parse and Chunk
        from sovereign.infrastructure.knowledge.parsers.ocr_parser import OCRParser
        from sovereign.infrastructure.knowledge.parsers.multimodal_parser import MultimodalParser
        
        ocr_parser = OCRParser()
        if ext == 'pdf':
            parser = PDFParser(ocr_parser=ocr_parser)
        elif ext in ('png', 'jpg', 'jpeg'):
            parser = None # handled in the extraction block
        else:
            parser = TextParser()
            
        if ext in ('png', 'jpg', 'jpeg'):
            # Multimodal parser requires capability-governed gateway
            with svc._execution_lock:
                routing_decision = svc.router.route_capability("MultimodalInference_v1")
                if not routing_decision.is_authorized:
                    raise HTTPException(status_code=403, detail=f"Multimodal inference unauthorized/unqualified: {routing_decision.reason}")
                
                parser = MultimodalParser(gateway=svc.gateway)
                with open(temp_path, "rb") as f:
                    blocks = parser.parse(doc, f)
        else:
            with open(temp_path, "rb") as f:
                blocks = parser.parse(doc, f)
            
        chunker = StructureAwareChunker(tokenizer=svc.tokenizer)
        chunks = chunker.chunk(doc, blocks)
        
        # 4. Save to KB
        svc.kb.save_chunks(chunks)
        
        doc.status = DocumentStatus.INGESTED
        svc.kb.update_document(doc)
        
        return DocumentIngestResponse(document_id=doc.document_id, status=doc.status.value)
        
    except HTTPException:
        raise
    except OCRRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/knowledge/documents", response_model=List[DocumentDetailResponse])
def list_documents():
    """Retrieve all registered/ingested documents in the knowledge base."""
    svc = get_app_service()
    return svc.list_documents()

@router.get("/knowledge/documents/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(document_id: str):
    """Retrieve raw chunks for a specific document."""
    svc = get_app_service()
    return svc.get_document_chunks(document_id)

@router.post("/chat", response_model=ChatResponse)
def chat_interaction(req: ChatRequest):
    """Conversational RAG and coding endpoint grounded in local models and knowledge."""
    svc = get_app_service()
    try:
        return svc.chat(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {e}")

@router.post("/code/execute", response_model=CodeExecuteResponse)
def execute_code_snippet(req: CodeExecuteRequest):
    """Executes bounded Python code inside the P04 governed execution boundary."""
    svc = get_app_service()
    try:
        return svc.execute_code(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code execution error: {e}")

@router.get("/artifacts/{artifact_id}/manifest")
def get_trust_manifest(artifact_id: str):
    """Retrieve the Verifiable Execution Receipt for an artifact."""
    svc = get_app_service()
    manifest = svc.get_trust_manifest(artifact_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Manifest not found")
    return manifest.model_dump(mode='json')

@router.get("/qualifications/passports", response_model=List[CapabilityPassportResponse])
def list_passports():
    """Retrieve all registered capability passports."""
    svc = get_app_service()
    return svc.list_passports()

# Global Exception Handlers
@app.exception_handler(ContextBudgetExceeded)
async def context_budget_exceeded_handler(request, exc):
    return HTTPException(status_code=422, detail="Task requires more context than the model's configured limit.")

@app.exception_handler(StateError)
async def state_error_handler(request, exc):
    return HTTPException(status_code=500, detail="Internal state or database transaction error.")

app.include_router(router)

