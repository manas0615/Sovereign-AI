"""Agent Host / Bounded Orchestrator."""

import time
import json
from typing import Optional, List, Dict, Any

from sovereign.core.agent.models import AgentStatus, AgentAction, AgentDecision
from sovereign.core.agent.parser import ModelOutputParser
from sovereign.core.state.models import Task, TaskStatus, Finding, Decision, EvidenceReference, UnresolvedQuestion, ContextSnapshot, Checkpoint
from sovereign.core.state.repository import TaskRepository
from sovereign.core.state.context_manager import ContextManager
from sovereign.core.runtime.gateway import ModelGateway
from sovereign.core.knowledge.retriever import Retriever
from sovereign.core.capabilities.executor import ToolExecutor
from sovereign.core.exceptions import ContextBudgetExceeded

from sovereign.core.agent.router import ModelRouter

class AgentHost:
    def __init__(self,
                 model_gateway: ModelGateway,
                 context_manager: ContextManager,
                 task_repository: TaskRepository,
                 retriever: Retriever,
                 tool_executor: ToolExecutor,
                 max_iterations: int = 8,
                 max_tool_calls_per_task: int = 5,
                 max_retrieval_results: int = 20,
                 router: Optional[ModelRouter] = None,
                 execution_boundary: Optional[Any] = None,
                 workspace: Optional[Any] = None):
        self.model = model_gateway
        self.context_manager = context_manager
        self.repo = task_repository
        self.retriever = retriever
        self.tool_executor = tool_executor
        self.router = router
        self.execution_boundary = execution_boundary
        self.workspace = workspace
        
        self.max_iterations = max_iterations
        self.max_tool_calls = max_tool_calls_per_task
        self.max_retrieval_results = max_retrieval_results
        
    def create_task(self, description: str) -> Task:
        task = Task(title="Agent Task", goal=description, status=TaskStatus.CREATED)
        self.repo.create_task(task)
        return task
        
    def _system_prompt(self, capability: str = "") -> str:
        base = (
            "You are operating inside a sovereign local AI system.\n"
            "You must output exactly one JSON object representing your decision.\n"
            "Supported actions: FINAL, RETRIEVE, TOOL, CLARIFY, CONTINUE.\n"
            "Do not invent evidence or claim tools were used without executing them.\n"
            "If you need facts, use RETRIEVE.\n"
            "If you need numerical calculations, use TOOL with tool_name 'calculate' and arguments {'expression': '<math_expr>', 'variables': {...}}.\n"
        )
        if capability == "AutomatedCoding_v1":
            base += (
                "For coding tasks, use action: 'TOOL', tool_name: 'execute_python', and arguments: {'code': '<python_code>', 'timeout_seconds': 10.0}.\n"
                "Your implementation will be independently evaluated by the system's trusted verification test harness.\n"
                "Do NOT attempt to self-verify with print statements. The system's trusted test harness decides pass or fail.\n"
                "If verification checks fail, review the feedback, correct the code, and submit again using 'TOOL'.\n"
            )
        else:
            base += "If you need file or knowledge capabilities, use TOOL.\n"
            
        base += "If you are finished and the task is verified, use FINAL and provide the 'answer'.\n"
        return base
        
    def run(self, task_id: str) -> Task:
        task = self.repo.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")
            
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.PAUSED]:
            return task
            
        task.status = TaskStatus.ACTIVE
        self.repo.update_task(task)
        
        # 0. Qualification-Aware Model Routing
        if self.router is not None:
            routing_decision = self.router.route(task.task_id, task.goal)
            self.repo.add_state_item(
                task.task_id,
                Decision(
                    rationale=f"Qualification-aware routing: {routing_decision.reason}",
                    decision="ROUTE"
                )
            )
            if not routing_decision.is_authorized:
                task.status = TaskStatus.FAILED
                self.repo.add_state_item(
                    task.task_id,
                    Decision(
                        rationale=f"Model routing failed: {routing_decision.reason}",
                        decision="FAIL"
                    )
                )
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_ROUTING"))
                return task
        
        iteration = 0
        tool_calls = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # 1. Build Context
            try:
                snapshot = self.context_manager.assemble_context(task.task_id, task.goal)
            except ContextBudgetExceeded:
                # If budget exceeded, task cannot safely proceed. Fail cleanly.
                task.status = TaskStatus.FAILED
                self.repo.add_state_item(task.task_id, Decision(rationale="Context budget exceeded.", decision="FAIL"))
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_CONTEXT_BUDGET"))
                return task
                
            # Materialize state
            materialized_state = []
            
            all_items = self.repo.get_state_items(task.task_id)
            for item in all_items:
                if item.item_id in snapshot.selected_item_ids:
                    materialized_state.append(item.model_dump_json())
                    
            all_evs = self.repo.get_evidence(task.task_id)
            for ev in all_evs:
                if ev.evidence_id in snapshot.selected_evidence_ids:
                    materialized_state.append(ev.model_dump_json())
                    
            state_str = "\n".join(materialized_state)

            # 2. Invoke Model
            # The prompt combines system instructions, the materialized state, and current user instruction.
            capability = routing_decision.required_capability if (self.router is not None and 'routing_decision' in locals()) else ""
            prompt = f"{self._system_prompt(capability)}\n\nTask:\n{task.goal}\n\nCurrent State:\n{state_str}\n\nContext Snapshot:\n{snapshot.model_dump_json(indent=2)}"
            
            try:
                from sovereign.core.runtime.models import InferenceRequest
                from sovereign.core.agent.models import AGENT_DECISION_RESPONSE_FORMAT
                request = InferenceRequest(prompt=prompt, response_format=AGENT_DECISION_RESPONSE_FORMAT, max_tokens=768, temperature=0.2)
                response = self.model.generate(request)
                raw_response = response.text

            except Exception as e:
                task.status = TaskStatus.FAILED
                self.repo.add_state_item(task.task_id, Decision(rationale=f"Model invocation failed: {e}", decision="FAIL"))
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_MODEL_INVOCATION"))
                return task
                
            # 3. Parse Decision
            try:
                decision = ModelOutputParser.parse_decision(raw_response)
            except ValueError as e:
                # Malformed output -> structured failure, no automatic retry loops in MVP
                task.status = TaskStatus.FAILED
                self.repo.add_state_item(task.task_id, Decision(rationale=f"Malformed model output: {e}", decision="FAIL"))
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_MALFORMED_OUTPUT"))
                return task
                
            # Log the decision to task state
            rationale_msg = decision.rationale if decision.rationale else "No rationale provided."
            self.repo.add_state_item(task.task_id, Decision(rationale=rationale_msg, decision=decision.action.value))
            
            # 4. Execute Action
            if decision.action == AgentAction.FINAL:
                if capability == "AutomatedCoding_v1":
                    # Check task state items for structured verified status
                    current_items = self.repo.get_state_items(task.task_id)
                    verified = False
                    inconclusive = False
                    for item in reversed(current_items):
                        if isinstance(item, Finding) and "verification_status" in getattr(item, "metadata", {}):
                            status_val = item.metadata["verification_status"]
                            if status_val == "Verification Passed":
                                verified = True
                                break
                            elif status_val == "Verification Inconclusive":
                                inconclusive = True
                                break
                            elif status_val == "Verification Failed":
                                break
                            # Any other status is treated as failure. Break to prevent older results from authorising.
                            break
                        # Spoofable string fallback removed to ensure model-generated text cannot forge success.
                    
                    if verified:
                        task.status = TaskStatus.COMPLETED
                        self.repo.add_state_item(task.task_id, Finding(statement=f"Trusted Verification Confirmed. {decision.answer}", confidence="high"))
                    elif inconclusive:
                        # If inconclusive, it's not a success, but we don't treat it as a hard failure 
                        # that the agent explicitly ignored. It's just unverified.
                        task.status = TaskStatus.FAILED
                        self.repo.add_state_item(task.task_id, Decision(rationale="Task marked FINAL but verification was inconclusive. No trusted tests available.", decision="FAIL"))
                    else:
                        task.status = TaskStatus.FAILED
                        self.repo.add_state_item(task.task_id, Decision(rationale="Task marked FINAL without passing independent trusted verification checks.", decision="FAIL"))
                else:
                    task.status = TaskStatus.COMPLETED
                    # In MVP, we just store the answer as a finding or update the task
                    self.repo.add_state_item(task.task_id, Finding(statement=decision.answer, confidence="high"))
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="COMPLETED" if task.status == TaskStatus.COMPLETED else "FAILED_VERIFICATION"))
                return task
                
            elif decision.action == AgentAction.CLARIFY:
                task.status = TaskStatus.PAUSED
                self.repo.add_state_item(task.task_id, UnresolvedQuestion(question=decision.question))
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="PAUSED_CLARIFY"))
                return task
                
            elif decision.action == AgentAction.RETRIEVE:
                top_k = min(decision.top_k or 5, self.max_retrieval_results)
                try:
                    results = self.retriever.retrieve(query=decision.query, top_k=top_k)
                    ev_ids = []
                    for r in results:
                        ev = EvidenceReference(
                            source_id=r.document_id,
                            locator=r.page or "N/A",
                            metadata={"chunk_id": r.chunk_id, "text": r.text, "score": r.score}
                        )
                        self.repo.add_evidence(task.task_id, ev)
                        ev_ids.append(ev.evidence_id)
                    
                    if not results:
                         self.repo.add_state_item(task.task_id, Finding(statement=f"No results found for query: {decision.query}", confidence="high"))
                    else:
                         self.repo.add_state_item(task.task_id, Finding(statement=f"Retrieved {len(results)} results for query: {decision.query}", confidence="high", evidence_refs=ev_ids))
                         
                except Exception as e:
                    # Retrieval failure -> FAILED
                    task.status = TaskStatus.FAILED
                    self.repo.add_state_item(task.task_id, Decision(rationale=f"Retrieval failed: {e}", decision="FAIL"))
                    self.repo.update_task(task)
                    self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_RETRIEVAL"))
                    return task
                    
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="AFTER_RETRIEVE"))
                
            elif decision.action == AgentAction.TOOL:
                if tool_calls >= self.max_tool_calls:
                    task.status = TaskStatus.FAILED
                    self.repo.add_state_item(task.task_id, Decision(rationale="Tool call limit exceeded.", decision="FAIL"))
                    self.repo.update_task(task)
                    self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_TOOL_LIMIT"))
                    return task
                    
                tool_calls += 1
                
                try:
                    tool_result = self.tool_executor.execute(tool_name=decision.tool_name, inputs=decision.arguments or {})
                    
                    # If execute_python was invoked, also perform independent trusted verification
                    if decision.tool_name == "execute_python":
                        from sovereign.core.coding.verifier import TrustedCodeVerifier, CodeVerificationStatus
                        from sovereign.infrastructure.tools.execution_boundary import ExecutionBoundary
                        from sovereign.infrastructure.tools.workspace import WorkspaceManager
                        
                        boundary = self.execution_boundary or ExecutionBoundary()
                        ws = self.workspace or WorkspaceManager().get_or_create("default")
                        submitted_code = (decision.arguments or {}).get("code", "")
                        
                        v_report = TrustedCodeVerifier.verify_submission(
                            code=submitted_code,
                            task_goal=task.goal,
                            workspace=ws,
                            boundary=boundary
                        )
                        
                        # Add execution result statement
                        if tool_result.success:
                            exec_msg = f"Tool 'execute_python' returned: {tool_result.output}"
                        else:
                            exec_msg = f"Tool 'execute_python' failed: {tool_result.error}"
                        self.repo.add_state_item(task.task_id, Finding(statement=exec_msg, confidence="high", evidence_refs=[]))
                        
                        # Add trusted verification finding
                        v_msg = f"Trusted Verification Result: [{v_report.status.value}] Passed {v_report.passed_checks}/{v_report.total_checks} checks. {v_report.failure_reason or ''}".strip()
                        self.repo.add_state_item(task.task_id, Finding(
                            statement=v_msg, 
                            confidence="high", 
                            evidence_refs=[], 
                            metadata={"verification_status": v_report.status.value}
                        ))
                        
                        if v_report.status == CodeVerificationStatus.VERIFICATION_FAILED:
                            failed_details = [c.model_dump() for c in v_report.check_results if not c.passed]
                            self.repo.add_state_item(task.task_id, Finding(statement=f"Failed Checks Detail: {json.dumps(failed_details)}", confidence="high"))
                    else:
                        # Standard tool handling
                        if tool_result.success:
                             finding_statement = f"Tool '{decision.tool_name}' returned: {tool_result.output}"
                        else:
                             finding_statement = f"Tool '{decision.tool_name}' failed: {tool_result.error}"
                        self.repo.add_state_item(task.task_id, Finding(statement=finding_statement, confidence="high", evidence_refs=[]))
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    self.repo.add_state_item(task.task_id, Decision(rationale=f"Tool executor exception: {e}", decision="FAIL"))
                    self.repo.update_task(task)
                    self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_TOOL"))
                    return task
                    
                self.repo.update_task(task)
                self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="AFTER_TOOL"))
                
            elif decision.action == AgentAction.CONTINUE:
                # Do nothing extra, just loop again
                self.repo.update_task(task)
                
        # If we exited loop by hitting iteration limits
        task.status = TaskStatus.FAILED
        self.repo.add_state_item(task.task_id, Decision(rationale="Max iterations exceeded.", decision="FAIL"))
        self.repo.update_task(task)
        self.repo.create_checkpoint(Checkpoint(task_id=task.task_id, description="FAILED_MAX_ITERATIONS"))
        
        return task
