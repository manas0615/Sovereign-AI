"""Secure Tool Executor."""

from typing import Dict, Any, Optional
import time
import uuid
import concurrent.futures

from sovereign.core.capabilities.models import ToolResult, ToolDefinition, SecurityMode
from sovereign.core.capabilities.registry import ToolRegistry
from sovereign.core.capabilities.policy import ToolPolicy

class ToolExecutor:
    def __init__(self, registry: ToolRegistry, policy: ToolPolicy, default_timeout: float = 10.0):
        self.registry = registry
        self.policy = policy
        self.default_timeout = default_timeout
        
    def execute(self, tool_name: str, inputs: Dict[str, Any], timeout: Optional[float] = None) -> ToolResult:
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        actual_timeout = timeout if timeout is not None else self.default_timeout
        
        # 1. Lookup Tool
        tool_impl = self.registry.get(tool_name)
        if not tool_impl:
            return ToolResult(
                execution_id=execution_id,
                tool_name=tool_name,
                success=False,
                error="ToolNotFound: The requested tool does not exist.",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
        # 2. Policy Authorization
        if not self.policy.is_allowed(tool_impl):
            return ToolResult(
                execution_id=execution_id,
                tool_name=tool_name,
                success=False,
                error="ToolNotAllowed: The tool is denied by policy.",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
        # 3. Input Validation
        try:
            validated_input = self.policy.validate_inputs(tool_impl, inputs)
        except ValueError as e:
            return ToolResult(
                execution_id=execution_id,
                tool_name=tool_name,
                success=False,
                error=f"ToolInputValidationError: {e}",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            
        # 4. Bounded Execution
        output = None
        error = None
        success = False
        security_mode = None
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(tool_impl.handler, validated_input)
        
        try:
            output = future.result(timeout=actual_timeout)
            success = True
            if isinstance(output, dict) and "security_mode" in output:
                try:
                    security_mode = SecurityMode(output["security_mode"])
                except Exception:
                    pass
        except concurrent.futures.TimeoutError:
            error = f"ToolTimeout: Execution exceeded the {actual_timeout}s boundary."
            success = False
        except Exception as e:
            error = f"ToolExecutionError: {str(e)}"
            success = False
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
                
        # 5. Audit Metadata
        metadata = {
            "policy_decision": "ALLOWED",
            "timestamp": time.time(),
        }
                
        return ToolResult(
            execution_id=execution_id,
            tool_name=tool_name,
            success=success,
            output=output if success else None,
            error=error,
            duration_ms=int((time.time() - start_time) * 1000),
            security_mode=security_mode,
            metadata=metadata
        )

