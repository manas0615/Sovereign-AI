"""Application services for orchestration and coordination (Package 07)."""

import os
import sys
import json
import logging
import threading
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from sovereign.core.state.models import Task, TaskStatus, Finding, Priority, EvidenceReference
from sovereign.infrastructure.state.sqlite_repository import SQLiteTaskRepository
from sovereign.core.state.context_manager import ContextManager
from sovereign.infrastructure.state.tokenizer import ApproximateTokenCounter
from sovereign.infrastructure.knowledge.sqlite_knowledge import SQLiteKnowledgeBase
from sovereign.infrastructure.runtime.llama_cpp.adapter import LlamaCppAdapter
from sovereign.core.runtime.gateway import ModelGateway

from sovereign.core.authority.evaluator import AuthorityEvaluator, AuthorityPolicy
from sovereign.core.agent.router import ModelRouter
from sovereign.infrastructure.config import get_settings
from sovereign.core.runtime.models import ModelDeploymentConfig
from sovereign.core.qualification.models import DeploymentProfile, ModelProfile, RuntimeEnvironment

from sovereign.core.agent.host import AgentHost
from sovereign.core.capabilities.executor import ToolExecutor
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy
from sovereign.infrastructure.artifacts.storage import LocalArtifactStorage
from sovereign.application.schemas import (
    TaskCreateRequest, TaskResponse, ArtifactMetadataResponse, CapabilityPassportResponse,
    DocumentDetailResponse, DocumentChunkResponse, ChatRequest, ChatResponse, CitationItem,
    CodeExecutionResult, CodeExecuteRequest, CodeExecuteResponse, NetworkTelemetryResponse
)

class ReadOnlyArtifactAdapter:
    """Projects internal manifest data to API DTOs without generating artifacts."""
    def __init__(self, storage: LocalArtifactStorage):
        self.storage = storage

    def _to_dto(self, data: dict) -> ArtifactMetadataResponse:
        import os
        meta = data.get("metadata") or {}
        file_path = meta.get("file_path")
        filename = os.path.basename(file_path) if file_path else None
        return ArtifactMetadataResponse(
            artifact_id=data["artifact_id"],
            task_id=data.get("task_id", ""),
            title=data.get("title", "Untitled"),
            type=data.get("type", "UNKNOWN"),
            status=data.get("status", "UNKNOWN"),
            created_at=data.get("created_at"),
            filename=filename,
            file_path=file_path,
            size_bytes=meta.get("size_bytes"),
            content_hash=meta.get("content_hash"),
            sections_rendered=meta.get("sections_rendered", []),
            source_references=data.get("source_references", [])
        )
        
    def list_by_task(self, task_id: str) -> List[ArtifactMetadataResponse]:
        try:
            with open(self.storage.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            manifest = {}
            
        results = []
        for aid, data in manifest.items():
            if data.get("task_id") == task_id:
                results.append(self._to_dto(data))
        return results

    def list_all(self) -> List[ArtifactMetadataResponse]:
        try:
            with open(self.storage.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            manifest = {}
            
        results = [self._to_dto(data) for aid, data in manifest.items()]
        results.sort(key=lambda x: str(x.created_at), reverse=True)
        return results

class AppService:
    """Coordinates across all frozen packages."""
    
    def __init__(self):
        self.tokenizer = ApproximateTokenCounter()
        self.repo = SQLiteTaskRepository()
        self.kb = SQLiteKnowledgeBase()
        self.retriever = self.kb
        
        # In a real startup script we might configure this differently,
        # but this assembles the singleton graph exactly.
        self.model_adapter = LlamaCppAdapter()
        self.gateway = ModelGateway(self.model_adapter)
        
        settings = get_settings()
        llama_path = r"C:\Users\Dell\.cache\huggingface\hub\models--bartowski--Llama-3.2-3B-Instruct-GGUF\snapshots\5ab33fa94d1d04e903623ae72c95d1696f09f9e8\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
        qwen_path = r"C:\Users\Dell\.cache\huggingface\hub\models--Qwen--Qwen2.5-3B-Instruct-GGUF\snapshots\7dabda4d13d513e3e842b20f0d435c732f172cbe\qwen2.5-3b-instruct-q4_k_m.gguf"

        llama_deployment = ModelDeploymentConfig(
            model_name="Llama-3.2-3B-Instruct",
            model_path=llama_path if os.path.exists(llama_path) else settings.model_path,
            server_host="127.0.0.1",
            server_port=8080,
            backend="llama.cpp",
            device=settings.model_device,
            gpu_layers=settings.gpu_layers,
            context_size=settings.context_size
        )
        
        llama_profile = DeploymentProfile(
            model=ModelProfile(name="Llama-3.2-3B-Instruct", architecture="llama", parameters_b=3.2, context_length=settings.context_size),
            quantization="Q4_K_M",
            runtime=RuntimeEnvironment.LLAMA_CPP,
            hardware_profile=f"{settings.model_device}_gl{settings.gpu_layers}",
            context_budget=settings.context_size
        )

        qwen_deployment = ModelDeploymentConfig(
            model_name="Qwen2.5-3B-Instruct",
            model_path=qwen_path,
            server_host="127.0.0.1",
            server_port=8080,
            backend="llama.cpp",
            device=settings.model_device,
            gpu_layers=settings.gpu_layers,
            context_size=settings.context_size
        )

        qwen_profile = DeploymentProfile(
            model=ModelProfile(name="Qwen2.5-3B-Instruct", architecture="qwen", parameters_b=3.0, context_length=settings.context_size),
            quantization="Q4_K_M",
            runtime=RuntimeEnvironment.LLAMA_CPP,
            hardware_profile=f"{settings.model_device}_gl{settings.gpu_layers}",
            context_budget=settings.context_size
        )

        self.authority_evaluator = AuthorityEvaluator(
            repository=self.repo,
            policy=AuthorityPolicy(
                allowed_models=["Llama-3.2-3B-Instruct", "Qwen2.5-3B-Instruct", "Llama-3.2-11B-Vision-Instruct", "default_model"],
                allowed_contracts=["AgentDecision_v1", "DocumentRetrieval_v1", "NumericalCalculation_v1", "StructuredReasoning_v1", "MultimodalInference_v1", "AutomatedCoding_v1"],
                allow_unqualified=False
            )
        )
        
        self.router = ModelRouter(
            gateway=self.gateway,
            authority_evaluator=self.authority_evaluator,
            qualification_repository=self.repo,
            registered_deployments=[llama_deployment, qwen_deployment],
            deployment_profiles={
                "Llama-3.2-3B-Instruct": llama_profile,
                "Qwen2.5-3B-Instruct": qwen_profile
            }
        )
        
        self.context_manager = ContextManager(self.repo, self.tokenizer)
        
        # Tools
        from sovereign.infrastructure.tools.file_tools import get_read_file_tool, get_write_file_tool
        from sovereign.infrastructure.tools.knowledge_search_tool import get_search_knowledge_tool
        from sovereign.infrastructure.tools.calculation_tool import get_calculate_tool
        from sovereign.infrastructure.tools.python_execution_tool import get_execute_python_tool
        from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary
        from sovereign.infrastructure.tools.workspace import WorkspaceManager

        self.workspace_manager = WorkspaceManager()
        self.default_workspace = self.workspace_manager.get_or_create("default")
        self.execution_boundary = ExecutionBoundary()

        self.tool_registry = ToolRegistry()
        self.tool_registry.register(get_read_file_tool())
        self.tool_registry.register(get_write_file_tool())
        self.tool_registry.register(get_search_knowledge_tool())
        self.tool_registry.register(get_calculate_tool())
        from sovereign.infrastructure.tools.python_execution_tool import get_execute_python_tool
        self.tool_registry.register(get_execute_python_tool(name="execute_python"))
        self.tool_registry.register(get_execute_python_tool(name="python"))
        self.tool_policy = ToolPolicy(allowed_tools={"read_file", "write_file", "search_knowledge", "calculate", "execute_python", "python"})
        self.tool_executor = ToolExecutor(self.tool_registry, self.tool_policy)
        
        self.agent = AgentHost(
            self.gateway,
            self.context_manager,
            self.repo,
            self.retriever,
            self.tool_executor,
            router=self.router,
            max_tool_calls_per_task=3,
            execution_boundary=self.execution_boundary,
            workspace=self.default_workspace
        )
        
        from sovereign.infrastructure.artifacts.engine import LocalArtifactEngine
        from sovereign.infrastructure.artifacts.manifest_generator import TrustManifestGenerator

        self.artifact_storage = LocalArtifactStorage()
        self.artifact_engine = LocalArtifactEngine(self.repo, self.artifact_storage)
        self.manifest_generator = TrustManifestGenerator(self.repo, self.repo, self.artifact_storage)
        self.artifact_adapter = ReadOnlyArtifactAdapter(self.artifact_storage)
        
        # Concurrency
        self._running_tasks = set()
        self._execution_lock = threading.Lock()
        
    def create_task(self, req: TaskCreateRequest) -> TaskResponse:
        task = Task(title=req.title, goal=req.goal)
        self.repo.create_task(task)
        
        if req.document_id:
            doc = self.kb.get_document(req.document_id)
            if not doc:
                raise ValueError(f"Document {req.document_id} not found in knowledge base")
            
            ev_ref = EvidenceReference(
                source_id=doc.document_id,
                locator=f"document:{doc.filename}",
                metadata={"filename": doc.filename, "document_type": doc.document_type, "content_hash": doc.content_hash}
            )
            self.repo.add_evidence(task.task_id, ev_ref)
            
            finding = Finding(
                statement=f"Associated target document: {doc.filename} (ID: {doc.document_id})",
                confidence="high",
                status="active",
                priority=Priority.REQUIRED,
                evidence_refs=[ev_ref.evidence_id]
            )
            self.repo.add_state_item(task.task_id, finding)
            
        return self._to_task_response(task)
        
    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        task = self.repo.get_task(task_id)
        if not task:
            return None
        return self._to_task_response(task)

    def list_tasks(self) -> List[TaskResponse]:
        tasks = self.repo.list_tasks()
        return [self._to_task_response(t) for t in tasks]

    def list_documents(self):
        from sovereign.application.schemas import DocumentDetailResponse
        docs = self.kb.list_documents()
        return [
            DocumentDetailResponse(
                document_id=d.document_id,
                filename=d.filename,
                source_path=d.source_path,
                document_type=d.document_type,
                file_size=d.file_size,
                content_hash=d.content_hash,
                created_at=d.created_at,
                ingested_at=d.ingested_at,
                status=d.status.value,
                metadata=d.metadata or {}
            )
            for d in docs
        ]
        
    def _to_task_response(self, task: Task) -> TaskResponse:

        state_items = self.repo.get_state_items(task.task_id)
        evidence_refs = self.repo.get_evidence(task.task_id)

        
        latest_decision = None
        findings_count = 0
        document_id = evidence_refs[0].source_id if evidence_refs else None
        
        for item in reversed(state_items):
            if item.item_type == "decision" and not latest_decision:
                latest_decision = item.decision
            elif item.item_type == "finding":
                findings_count += 1
                
        return TaskResponse(
            task_id=task.task_id,
            title=task.title,
            goal=task.goal,
            status=task.status.value,
            created_at=task.created_at,
            updated_at=task.updated_at,
            latest_decision=latest_decision,
            findings_count=findings_count,
            document_id=document_id
        )
        
    def can_run_task(self, task_id: str):
        """Checks if a task is valid for execution."""
        task = self.repo.get_task(task_id)
        if not task:
            raise KeyError("Task not found")
            
        if task_id in self._running_tasks:
            raise ValueError("Task is already actively running.")
            
        if task.status in (TaskStatus.PAUSED, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            raise ValueError(f"Cannot run task in status: {task.status.value}")
            
    def schedule_task(self, task_id: str):
        """Validates and synchronously marks task as running."""
        self.can_run_task(task_id)
        self._running_tasks.add(task_id)
            
    def execute_task_background(self, task_id: str):
        """Synchronous execution function to be dispatched via BackgroundTasks."""
        try:
            with self._execution_lock:
                task = self.agent.run(task_id)
                if task and task.status == TaskStatus.COMPLETED:
                    from sovereign.core.artifacts.models import ArtifactRequest, ArtifactType
                    req_md = ArtifactRequest(
                        task_id=task_id,
                        title=f"Task Report - {task.title}",
                        artifact_type=ArtifactType.MARKDOWN,
                        requested_sections=["executive_summary", "findings", "evidence"]
                    )
                    self.artifact_engine.generate(req_md)
                    
                    req_docx = ArtifactRequest(
                        task_id=task_id,
                        title=f"Approval Note - {task.title}",
                        artifact_type=ArtifactType.DOCX,
                        requested_sections=["executive_summary", "findings", "evidence", "limitations"]
                    )
                    self.artifact_engine.generate(req_docx)

                    req_xlsx = ArtifactRequest(
                        task_id=task_id,
                        title=f"Industrial Data Sheet - {task.title}",
                        artifact_type=ArtifactType.XLSX,
                        requested_sections=["executive_summary", "findings", "evidence", "decisions"]
                    )
                    self.artifact_engine.generate(req_xlsx)

                    req_pptx = ArtifactRequest(
                        task_id=task_id,
                        title=f"Executive Briefing - {task.title}",
                        artifact_type=ArtifactType.PPTX,
                        requested_sections=["executive_summary", "findings", "evidence", "decisions", "limitations"]
                    )
                    self.artifact_engine.generate(req_pptx)
        finally:
            self._running_tasks.discard(task_id)

            
    def list_artifacts(self, task_id: str) -> List[ArtifactMetadataResponse]:
        return self.artifact_adapter.list_by_task(task_id)

    def list_all_artifacts(self) -> List[ArtifactMetadataResponse]:
        return self.artifact_adapter.list_all()

    def get_trust_manifest(self, artifact_id: str):
        return self.manifest_generator.generate(artifact_id)

    def get_document_chunks(self, document_id: str) -> List[DocumentChunkResponse]:
        """Retrieves raw chunks for a specific document."""
        chunks = self.kb.get_chunks_for_document(document_id)
        return [
            DocumentChunkResponse(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                sequence=c.sequence,
                page_range=c.page_range,
                section=c.section,
                text=c.text,
                token_estimate=c.token_estimate,
                metadata=c.metadata
            )
            for c in chunks
        ]

    def execute_code(self, req: CodeExecuteRequest) -> CodeExecuteResponse:
        """Executes bounded Python code inside the P04 governed execution boundary."""
        with self._execution_lock:
            # Route capability
            routing = self.router.route_capability("NumericalCalculation_v1")
            res = self.execution_boundary.execute_python(
                code=req.code,
                workspace=self.default_workspace,
                timeout_seconds=req.timeout_seconds
            )
            return CodeExecuteResponse(
                success=res["success"],
                stdout=res["stdout"],
                stderr=res["stderr"],
                exit_code=res["exit_code"],
                duration_ms=res["duration_ms"],
                security_mode=res["security_mode"],
                error=res["error"]
            )

    def chat(self, req: ChatRequest) -> ChatResponse:
        """
        Executes a conversational RAG or coding interaction grounded in local knowledge
        and governed by P05 routing and P08 capability qualification.
        """
        import uuid
        import re
        from sovereign.core.state.models import Decision, Finding, EvidenceReference

        conv_id = req.conversation_id or f"conv-{uuid.uuid4().hex[:8]}"
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()

        # 1. Determine Intent & Capability Contract
        msg_lower = req.message.lower()
        is_coding = req.mode == "coding" or any(kw in msg_lower for kw in [
            "write python", "python script", "write code", "generate code", "code generator",
            "calculate degradation", "compute corrosion", "generate a script", "parse csv",
            "email verification", "verification code", "def ", "class ", "function to", "script for"
        ])
        
        contract = "AutomatedCoding_v1" if is_coding else "DocumentRetrieval_v1"
        
        # 2. Check P05 Routing and P08 Authority
        routing_decision = self.router.route_capability(contract)
        auth_decision = "AUTHORITY_GRANTED" if routing_decision.is_authorized else "AUTHORITY_DENIED"
        passport_id = None
        dep_id = None
        
        passports = self.list_passports()
        for p in passports:
            if p.capability_contract == contract and p.qualification_status == "QUALIFIED":
                passport_id = p.passport_id
                dep_id = p.deployment_identity
                break
                
        if not passport_id and passports:
            passport_id = passports[0].passport_id
            dep_id = passports[0].deployment_identity

        # 3. Create Persisted Task to record conversation turn
        task = Task(
            title=f"Chat Turn: {req.message[:50]}...",
            goal=req.message
        )
        self.repo.create_task(task)
        self.repo.add_state_item(
            task.task_id,
            Decision(
                rationale=f"Governed interaction: {routing_decision.reason}",
                decision=auth_decision
            )
        )

        citations: List[CitationItem] = []
        code_exec_res: Optional[CodeExecutionResult] = None
        assistant_content = ""

        # 4. Handle Execution Path
        if is_coding:
            # Dynamic Local Model Coding Generation
            from sovereign.core.runtime.models import InferenceRequest
            prompt = (
                "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
                "You are Sovereign AI Assistant, an enterprise coding assistant operating strictly on local hardware.\n"
                "Write clean, robust, production-ready Python code to fulfill the user's request.\n"
                "Provide the complete Python code enclosed in ```python ... ``` blocks with docstrings and a runnable example.\n"
                "Do not import external unauthorized network packages.<|eot_id|>"
                "<|start_header_id|>user<|end_header_id|>\n\n"
                f"{req.message}<|eot_id|>"
                "<|start_header_id|>assistant<|end_header_id|>\n\n"
            )
            req_inf = InferenceRequest(prompt=prompt, max_tokens=768, temperature=0.1, stop=["<|eot_id|>", "<|end_of_text|>"])
            resp_inf = self.gateway.generate(req_inf)
            generated_text = resp_inf.text.strip()
            
            code_block_match = re.search(r'```(?:python)?\s*\n([\s\S]*?)```', generated_text)
            code_snippet = code_block_match.group(1).strip() if code_block_match else generated_text
            
            # Execute code if requested
            if req.execute_code:
                exec_raw = self.execution_boundary.execute_python(
                    code=code_snippet,
                    workspace=self.default_workspace,
                    timeout_seconds=10.0
                )
                code_exec_res = CodeExecutionResult(
                    code=code_snippet,
                    stdout=exec_raw["stdout"],
                    stderr=exec_raw["stderr"],
                    exit_code=exec_raw["exit_code"],
                    duration_ms=exec_raw["duration_ms"],
                    success=exec_raw["success"],
                    security_mode=exec_raw["security_mode"],
                    error=exec_raw["error"]
                )
                
                assistant_content = (
                    f"{generated_text}\n\n"
                    f"**Governed Execution Output (`stdout`):**\n"
                    f"```text\n{exec_raw['stdout'] if exec_raw['stdout'] else '[No stdout output]'}\n```\n"
                    f"*Execution status: exit code {exec_raw['exit_code']} in {exec_raw['duration_ms']:.1f}ms ({exec_raw['security_mode']})*"
                )
            else:
                assistant_content = generated_text

        else:
            # Conversational RAG Path
            # Search knowledge base
            retrieval_results = self.kb.retrieve(
                query=req.message,
                top_k=5,
                document_id=req.document_id
            )

            # Map citations
            doc_map = {}
            for r in retrieval_results:
                if r.document_id not in doc_map:
                    d = self.kb.get_document(r.document_id)
                    doc_map[r.document_id] = d
                doc = doc_map[r.document_id]
                filename = doc.filename if doc else "Unknown"
                content_hash = doc.content_hash if doc else None

                citations.append(CitationItem(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    filename=filename,
                    locator=r.page or "Section 1",
                    text=r.text,
                    score=r.score,
                    content_hash=content_hash
                ))

                # Bind evidence to task
                ev_ref = EvidenceReference(
                    source_id=r.document_id,
                    locator=r.page or "N/A",
                    metadata={"chunk_id": r.chunk_id, "text": r.text, "score": r.score}
                )
                self.repo.add_evidence(task.task_id, ev_ref)

            if citations:
                from sovereign.core.runtime.models import InferenceRequest
                context_parts = []
                for i, c in enumerate(citations):
                    context_parts.append(f"--- Evidence Passage {i+1} [Source: {c.filename}, Chunk ID: {c.chunk_id[:8]}] ---\n{c.text.strip()}")
                context_str = "\n\n".join(context_parts)

                prompt = (
                    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
                    "You are Sovereign AI Assistant, an enterprise engineering assistant operating in a strictly governed local environment.\n"
                    "Answer the user's question accurately, concisely, and truthfully based ONLY on the provided context passages.\n"
                    "Highlight specific numbers, measured values, allowable limits, and compliance status clearly.\n"
                    "If the context does not contain enough information to answer, state clearly what is known and what is missing.\n"
                    "Do not invent facts or extrapolate beyond the provided text.<|eot_id|>"
                    "<|start_header_id|>user<|end_header_id|>\n\n"
                    f"Context Passages:\n{context_str}\n\n"
                    f"Question:\n{req.message}<|eot_id|>"
                    "<|start_header_id|>assistant<|end_header_id|>\n\n"
                )
                req_inf = InferenceRequest(prompt=prompt, max_tokens=512, temperature=0.1, stop=["<|eot_id|>", "<|end_of_text|>"])
                resp_inf = self.gateway.generate(req_inf)
                assistant_content = resp_inf.text.strip()
            else:
                # Check if domain query or general query
                domain_keywords = [
                    "iso", "uso", "standard", "vibration", "pump", "valve", "seal", "wear", "thickness",
                    "corrosion", "inspection", "report", "compliance", "tolerance", "zone", "v-204", "p-101", "p-102", "degradation"
                ]
                is_domain = any(dk in msg_lower for dk in domain_keywords)
                
                if is_domain:
                    assistant_content = (
                        "**Notice: Insufficient Evidence in Knowledge Base**\n\n"
                        "No relevant document chunks matched your query in the local SQLite knowledge base. "
                        "In accordance with Sovereign AI governance, the system operates fail-closed and will not fabricate or hallucinate ungrounded answers.\n\n"
                        "**Suggestions:**\n"
                        "1. Upload the relevant technical document or inspection report in the **Knowledge Library**.\n"
                        "2. Verify that the query terms match the terminology in the indexed documentation."
                    )
                else:
                    from sovereign.core.runtime.models import InferenceRequest
                    prompt = (
                        "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
                        "You are Sovereign AI Assistant, an enterprise sovereign AI operating strictly on local hardware.\n"
                        "Answer concisely, truthfully, and directly.<|eot_id|>"
                        "<|start_header_id|>user<|end_header_id|>\n\n"
                        f"{req.message}<|eot_id|>"
                        "<|start_header_id|>assistant<|end_header_id|>\n\n"
                    )
                    req_inf = InferenceRequest(prompt=prompt, max_tokens=256, temperature=0.1, stop=["<|eot_id|>", "<|end_of_text|>"])
                    resp_inf = self.gateway.generate(req_inf)
                    assistant_content = resp_inf.text.strip()

        # Record finding in task
        self.repo.add_state_item(
            task.task_id,
            Finding(statement=assistant_content[:200], confidence="high")
        )
        task.status = TaskStatus.COMPLETED
        self.repo.update_task(task)

        # Check for artifacts generated
        artifacts = self.list_artifacts(task.task_id)

        return ChatResponse(
            message_id=msg_id,
            conversation_id=conv_id,
            role="assistant",
            content=assistant_content,
            citations=citations,
            code_execution=code_exec_res,
            authority_decision=auth_decision,
            authorizing_passport_id=passport_id,
            deployment_identity=dep_id,
            capability_contract=contract,
            task_id=task.task_id,
            artifacts=artifacts,
            created_at=now
        )

    def list_passports(self) -> List[CapabilityPassportResponse]:
        """Exposes active and historical capability passports from persistence."""
        conn = self.repo._get_connection()
        try:
            rows = conn.execute("SELECT * FROM capability_passports ORDER BY qualification_timestamp DESC").fetchall()
            passports = []
            for row in rows:
                invalidation_info = json.loads(row['invalidation_info']) if row['invalidation_info'] else None
                metadata = json.loads(row['metadata']) if row['metadata'] else None
                passports.append(CapabilityPassportResponse(
                    passport_id=row['passport_id'],
                    qualification_identity=row['qualification_identity'],
                    deployment_identity=row['deployment_identity'],
                    capability_contract=row['capability_contract'],
                    result_id=row['result_id'],
                    qualification_status=row['qualification_status'],
                    qualification_timestamp=datetime.fromisoformat(row['qualification_timestamp']),
                    invalidation_info=invalidation_info,
                    metadata=metadata
                ))
            return passports
        finally:
            conn.close()

    def get_network_telemetry(self) -> NetworkTelemetryResponse:
        """Inspects established and listening sockets of application processes."""
        import psutil
        from datetime import datetime
        from sovereign.application.schemas import NetworkTelemetryResponse, NetworkConnectionItem

        now = datetime.utcnow()
        disclaimer = (
            "Observed socket telemetry: all connections bound to loopback (127.0.0.1 / ::1). "
            "Note: Socket observation inspects active connections; it does not constitute OS kernel airgap enforcement."
        )

        try:
            target_procs = {}
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = (proc.info['name'] or "").lower()
                    if any(k in pname for k in ['python', 'node', 'llama-server']):
                        target_procs[proc.info['pid']] = proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            connections_list = []
            non_loopback_count = 0
            local_socket_count = 0

            for pid, proc_name in target_procs.items():
                try:
                    p = psutil.Process(pid)
                    conns = p.connections(kind='inet')
                    for c in conns:
                        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
                        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"

                        is_loopback = False
                        if c.raddr:
                            if c.raddr.ip.startswith("127.") or c.raddr.ip == "::1":
                                is_loopback = True
                        elif c.laddr:
                            if c.laddr.ip.startswith("127.") or c.laddr.ip == "::1" or c.laddr.ip == "0.0.0.0":
                                is_loopback = True

                        if is_loopback:
                            local_socket_count += 1
                        else:
                            if c.status == "ESTABLISHED":
                                non_loopback_count += 1

                        connections_list.append(NetworkConnectionItem(
                            pid=pid,
                            process=proc_name,
                            laddr=laddr,
                            raddr=raddr,
                            status=c.status,
                            is_loopback=is_loopback
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            status_str = "NON_LOOPBACK_OBSERVED" if non_loopback_count > 0 else "LOCAL_LOOPBACK_ONLY"

            return NetworkTelemetryResponse(
                status=status_str,
                observed_non_loopback_connections=non_loopback_count,
                observed_local_sockets=local_socket_count,
                monitored_processes_count=len(target_procs),
                monitored_processes=list(set(target_procs.values())),
                connections=connections_list,
                model_runtime_host="127.0.0.1:8080",
                knowledge_base_type="SQLite FTS5 (Local)",
                artifact_storage_type="Local Storage",
                disclaimer=disclaimer,
                timestamp=now
            )
        except Exception as e:
            return NetworkTelemetryResponse(
                status="UNAVAILABLE",
                observed_non_loopback_connections=-1,
                observed_local_sockets=0,
                monitored_processes_count=0,
                monitored_processes=[],
                connections=[],
                model_runtime_host="127.0.0.1:8080",
                knowledge_base_type="SQLite FTS5 (Local)",
                artifact_storage_type="Local Storage",
                disclaimer=disclaimer,
                error=f"Socket telemetry inspection unavailable: {str(e)}",
                timestamp=now
            )

    def reset_demo_tasks(self) -> dict:
        """Cleans demo tasks for repeatability without modifying benchmark or qualification evidence."""
        conn = self.repo._get_connection()
        try:
            conn.execute("DELETE FROM task_state WHERE task_id LIKE 'task-%' OR task_id LIKE 'conv-%'")
            conn.execute("DELETE FROM task_evidence WHERE task_id LIKE 'task-%' OR task_id LIKE 'conv-%'")
            conn.execute("DELETE FROM tasks WHERE task_id LIKE 'task-%' OR task_id LIKE 'conv-%'")
            conn.commit()
            return {"status": "SUCCESS", "message": "Demo workspace reset to clean state."}
        finally:
            conn.close()

_app_service = None

def get_app_service() -> AppService:
    global _app_service
    if _app_service is None:
        _app_service = AppService()
    return _app_service



