import os
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from sovereign.infrastructure.paths import get_data_dir

class TaskWorkspace:
    """Dedicated task workspace enforcing filesystem confinement boundaries."""

    def __init__(
        self,
        workspace_id: Optional[str] = None,
        root_dir: Optional[Path] = None,
        root_path: Optional[Path] = None,
        max_file_size_bytes: int = 5 * 1024 * 1024,
        max_files: int = 1000
    ):
        self.workspace_id = workspace_id or f"ws-{uuid.uuid4().hex[:12]}"
        if root_path is not None:
            self.root_path = Path(root_path).resolve()
        else:
            base_dir = root_dir or (get_data_dir() / "workspaces")
            self.root_path = (base_dir / self.workspace_id).resolve()
        self.max_file_size_bytes = max_file_size_bytes
        self.max_files = max_files
        self.root_path.mkdir(parents=True, exist_ok=True)

    def resolve_safe_path(self, relative_or_subpath: str) -> Path:
        """
        Resolves a user/agent provided subpath strictly within the workspace root.
        Rejects:
        - Parent directory traversal ('..') escaping the workspace
        - Absolute host paths outside the workspace
        - Windows cross-drive or UNC network paths
        - Symlinks pointing outside the workspace boundary
        """
        if not relative_or_subpath or relative_or_subpath.strip() == "":
            return self.root_path

        # Reject UNC paths explicitly
        if relative_or_subpath.startswith("\\\\") or relative_or_subpath.startswith("//"):
            raise PermissionError(f"Access Denied: UNC or network paths are forbidden ({relative_or_subpath}).")

        raw_path = Path(relative_or_subpath)

        # If an absolute path is passed, ensure it is within workspace root
        if raw_path.is_absolute():
            try:
                candidate = raw_path.resolve()
            except Exception as e:
                raise PermissionError(f"Access Denied: Cannot resolve path: {e}")
            if not candidate.is_relative_to(self.root_path):
                raise PermissionError(f"Access Denied: Absolute path {relative_or_subpath} is outside workspace boundary.")
            target = candidate
        else:
            # Relative path: resolve relative to workspace root
            target = (self.root_path / raw_path).resolve()

        # Strict containment check
        try:
            if not target.is_relative_to(self.root_path):
                raise PermissionError(f"Access Denied: Path traversal detected outside workspace boundary.")
        except AttributeError:
            # Fallback for Python versions where is_relative_to behaves differently
            if not str(target).startswith(str(self.root_path)):
                raise PermissionError(f"Access Denied: Path traversal detected outside workspace boundary.")

        # Symlink escape verification
        if target.is_symlink():
            real_target = target.resolve()
            if not real_target.is_relative_to(self.root_path):
                raise PermissionError("Access Denied: Symlink points outside the workspace boundary.")

        return target

    def read_file(self, relative_path: str, max_bytes: int = 100000) -> Dict[str, Any]:
        path = self.resolve_safe_path(relative_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        if not path.is_file():
            raise ValueError(f"Path is a directory, not a file: {relative_path}")

        stat = path.stat()
        if stat.st_size > self.max_file_size_bytes:
            raise ValueError(f"File size ({stat.st_size} bytes) exceeds workspace limit of {self.max_file_size_bytes} bytes.")

        read_limit = min(max_bytes, self.max_file_size_bytes)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(read_limit)

        truncated = stat.st_size > len(content)
        return {
            "filepath": str(path.relative_to(self.root_path)),
            "content": content,
            "size_bytes": stat.st_size,
            "truncated": truncated
        }

    def write_file(self, relative_path: str, content: str, mode: str = "w") -> Dict[str, Any]:
        if mode not in ["w", "a"]:
            raise ValueError(f"Invalid write mode '{mode}'. Must be 'w' or 'a'.")

        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self.max_file_size_bytes:
            raise ValueError(f"Content size ({len(content_bytes)} bytes) exceeds workspace limit of {self.max_file_size_bytes} bytes.")

        path = self.resolve_safe_path(relative_path)
        if not path.exists():
            existing_count = sum(1 for p in self.root_path.rglob("*") if p.is_file())
            if existing_count >= self.max_files:
                raise RuntimeError(f"Maximum file count limit ({self.max_files}) reached for workspace.")

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "filepath": str(path.relative_to(self.root_path)),
            "bytes_written": len(content_bytes)
        }

    def create_file(self, relative_path: str, content: str = "") -> Dict[str, Any]:
        path = self.resolve_safe_path(relative_path)
        if path.exists():
            raise FileExistsError(f"File already exists: {relative_path}")
        return self.write_file(relative_path, content, mode="w")

    def list_files(self, subpath: str = "") -> List[Dict[str, Any]]:
        dir_path = self.resolve_safe_path(subpath)
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {subpath}")

        results = []
        for item in dir_path.iterdir():
            rel = str(item.relative_to(self.root_path))
            is_dir = item.is_dir()
            size = item.stat().st_size if not is_dir else 0
            results.append({
                "name": item.name,
                "relative_path": rel,
                "is_directory": is_dir,
                "size_bytes": size
            })
        return results

    def cleanup(self) -> None:
        """Removes the workspace directory and all contained files."""
        if self.root_path.exists():
            shutil.rmtree(self.root_path, ignore_errors=True)


class WorkspaceManager:
    """Factory and lifecycle manager for task workspaces."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or (get_data_dir() / "workspaces")
        self._workspaces: Dict[str, TaskWorkspace] = {}

    def get_or_create(self, workspace_id: Optional[str] = None) -> TaskWorkspace:
        ws_id = workspace_id or f"ws-{uuid.uuid4().hex[:12]}"
        if ws_id not in self._workspaces:
            self._workspaces[ws_id] = TaskWorkspace(workspace_id=ws_id, root_dir=self.base_dir)
        return self._workspaces[ws_id]

    def cleanup_workspace(self, workspace_id: str) -> None:
        if workspace_id in self._workspaces:
            self._workspaces[workspace_id].cleanup()
            del self._workspaces[workspace_id]
