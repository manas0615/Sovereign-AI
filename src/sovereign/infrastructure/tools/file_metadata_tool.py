"""Secure get_file_metadata tool."""

from pydantic import BaseModel, Field
from typing import Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import os

from sovereign.core.capabilities.models import ToolDefinition, ToolImplementation, CapabilityType
from sovereign.infrastructure.paths import get_workspace_root, get_data_dir

class FileMetadataInput(BaseModel):
    filepath: str = Field(description="The path to the file to inspect.")
    
def get_file_metadata_handler(inputs: FileMetadataInput) -> Dict[str, Any]:
    requested_path = Path(inputs.filepath)
    
    # 1. Canonicalize the path. Path.resolve() resolves symlinks and normalizes '..'.
    try:
        resolved_path = requested_path.resolve(strict=True)
    except Exception as e:
        # File doesn't exist or permissions error resolving it
        raise ValueError(f"Path cannot be resolved or does not exist: {e}")
        
    # 2. Check roots
    allowed_roots = [
        get_workspace_root().resolve(),
        get_data_dir().resolve()
    ]
    
    is_safe = False
    for root in allowed_roots:
        try:
            if resolved_path.is_relative_to(root):
                is_safe = True
                break
        except Exception:
            pass
            
    if not is_safe:
        raise PermissionError(f"Access Denied: Path {resolved_path} is outside allowed boundary roots.")
        
    # 3. Prevent UNC paths implicitly (though is_relative_to usually catches this if the root is on C:)
    # Explicitly verify the drive matches the allowed root drive.
    if resolved_path.drive not in [r.drive for r in allowed_roots]:
         raise PermissionError("Access Denied: UNC or Cross-Drive paths are forbidden.")

    # 4. Fetch bounded metadata
    stat = resolved_path.stat()
    
    return {
        "filename": resolved_path.name,
        "extension": resolved_path.suffix,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    }

def get_file_metadata_tool() -> ToolImplementation:
    definition = ToolDefinition(
        tool_id="core-fs-001",
        name="get_file_metadata",
        description="Returns safe metadata for a permitted workspace file.",
        input_schema=FileMetadataInput.model_json_schema(),
        output_schema={
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "extension": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "modified_at": {"type": "string"}
            }
        },
        capability=CapabilityType.READ_ONLY
    )
    return ToolImplementation(
        definition=definition,
        handler=get_file_metadata_handler,
        input_model=FileMetadataInput
    )
