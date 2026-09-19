"""Local path abstractions."""

import os
from pathlib import Path
from sovereign.infrastructure.config import get_settings
from sovereign.core.exceptions import InfrastructureError

def get_workspace_root() -> Path:
    """Get the root directory of the workspace."""
    # Assuming the root is two directories up from infrastructure package (src/sovereign)
    # Wait, actually it's easier to find it relative to current working directory or explicit env var.
    # Let's assume the current working directory is the project root for Package 00.
    return Path.cwd().absolute()

def get_data_dir() -> Path:
    """Get the path to the application data directory."""
    settings = get_settings()
    if settings.sovereign_data_dir:
        path = Path(settings.sovereign_data_dir)
    else:
        path = get_workspace_root() / "local_data"
    
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise InfrastructureError(f"Failed to create data directory at {path}: {e}")
    return path

def get_log_dir() -> Path:
    """Get the path to the logging directory."""
    settings = get_settings()
    if settings.sovereign_log_dir:
        path = Path(settings.sovereign_log_dir)
    else:
        path = get_workspace_root() / "logs"
    
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise InfrastructureError(f"Failed to create log directory at {path}: {e}")
    return path

def get_artifact_dir() -> Path:
    """Get the path to the artifact generation directory."""
    settings = get_settings()
    path = get_workspace_root() / settings.artifact_dir_name
    
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise InfrastructureError(f"Failed to create artifact directory at {path}: {e}")
    return path
