import os
import sys
import time
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from sovereign.core.capabilities.models import SecurityMode
from sovereign.infrastructure.tools.workspace import TaskWorkspace

class ExecutionBoundary:
    """Governed execution boundary for controlled code execution."""

    def __init__(self, preferred_mode: Optional[SecurityMode] = None, default_timeout_seconds: float = 10.0, max_output_bytes: int = 65536):
        self.default_timeout = default_timeout_seconds
        self.max_output_bytes = max_output_bytes
        self._security_mode = preferred_mode or self._detect_security_mode()

    def _detect_security_mode(self) -> SecurityMode:
        """
        Detects whether OS-level isolation is functional.
        Currently, native subprocess execution on Windows is strictly DEGRADED
        as it does not provide OS-level filesystem or network isolation.
        """
        # Do not falsely claim ISOLATED simply because WSL is present,
        # since this boundary executes code natively on the host.
        return SecurityMode.DEGRADED

    @property
    def security_mode(self) -> SecurityMode:
        return self._security_mode

    def _sanitize_environment(self) -> Dict[str, str]:
        """
        Builds a strictly sanitized environment dict for the subprocess.
        Explicitly removes API keys, credentials, tokens, and sensitive host environment variables.
        """
        safe_keys = {
            "PATH", "SYSTEMROOT", "TEMP", "TMP", "PYTHONPATH", "PYTHONHOME",
            "HOMEPATH", "USERPROFILE", "COMSPEC", "PATHEXT", "WINDIR"
        }
        sanitized = {}
        for k, v in os.environ.items():
            k_upper = k.upper()
            # Block sensitive keywords
            if any(secret in k_upper for secret in ["SECRET", "KEY", "TOKEN", "PASSWORD", "AUTH", "CREDENTIAL", "SOVEREIGN", "AWS", "AZURE", "OPENAI", "GEMINI"]):
                continue
            if k_upper in safe_keys:
                sanitized[k] = v

        # Add sovereign sandbox marker
        sanitized["SOVEREIGN_SANDBOX_MODE"] = self._security_mode.value
        return sanitized

    def execute_python(
        self,
        code: str,
        workspace: TaskWorkspace,
        timeout_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes bounded Python code inside the task workspace.
        Enforces timeout, output size ceilings, and clean process teardown.
        """
        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout
        # Cap timeout at 30 seconds
        timeout = min(timeout, 30.0)

        # Write code to a temporary execution script in the dedicated workspace
        script_path = workspace.resolve_safe_path("__task_exec__.py")
        normalized_code = code
        if isinstance(code, str):
            normalized_code = normalized_code.replace('\\"', '"').replace("\\'", "'")
            if "\n" not in normalized_code and "\\n" in normalized_code:
                normalized_code = normalized_code.replace("\\n", "\n").replace("\\t", "\t")
            # Repair unclosed single line quotes
            lines = normalized_code.split("\n")
            fixed_lines = []
            for line in lines:
                stripped = line.rstrip()
                if stripped.count('"""') % 2 == 0 and stripped.count("'''") % 2 == 0:
                    if stripped.count('"') % 2 == 1:
                        line = line + '"'
                    elif stripped.count("'") % 2 == 1:
                        line = line + "'"
                fixed_lines.append(line)
            normalized_code = "\n".join(fixed_lines)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(normalized_code)

        start_time = time.time()
        env = self._sanitize_environment()
        python_exec = sys.executable

        proc = None
        stdout_data = ""
        stderr_data = ""
        success = False
        error_msg = None
        exit_code = -1

        try:
            # Spawn in workspace directory with sanitized environment
            kwargs = {
                "cwd": str(workspace.root_path),
                "env": env,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True
            }
            if os.name == "nt":
                # Create a new process group so we can terminate the entire tree on Windows
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

            proc = subprocess.Popen(
                [python_exec, str(script_path)],
                **kwargs
            )

            try:
                stdout_data, stderr_data = proc.communicate(timeout=timeout)
                exit_code = proc.returncode
                success = (exit_code == 0)
                if not success:
                    error_msg = f"Execution exited with non-zero code {exit_code}."
            except subprocess.TimeoutExpired:
                # Hard process termination & cleanup
                if os.name == "nt":
                    # Taskkill /T terminates the tree, /F forces it
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        
                success = False
                error_msg = f"ExecutionTimeout: Script execution exceeded hard limit of {timeout}s."
                exit_code = -9

        except Exception as e:
            success = False
            error_msg = f"ExecutionError: {e}"
        finally:
            # Clean up the temporary execution file
            if script_path.exists():
                try:
                    script_path.unlink(missing_ok=True)
                except Exception:
                    pass

        duration_ms = int((time.time() - start_time) * 1000)

        # Truncate output to bounded maximum bytes
        if len(stdout_data.encode("utf-8")) > self.max_output_bytes:
            stdout_data = stdout_data[:self.max_output_bytes] + "\n[Output Truncated: Exceeded Maximum Output Size]"
        if len(stderr_data.encode("utf-8")) > self.max_output_bytes:
            stderr_data = stderr_data[:self.max_output_bytes] + "\n[Output Truncated: Exceeded Maximum Output Size]"

        return {
            "success": success,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "security_mode": self._security_mode.value,
            "error": error_msg
        }
