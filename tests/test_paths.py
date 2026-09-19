import os
from pathlib import Path
from sovereign.infrastructure.paths import get_data_dir, get_log_dir, get_workspace_root

def test_get_workspace_root():
    root = get_workspace_root()
    assert isinstance(root, Path)

def test_get_data_dir_default():
    import sovereign.infrastructure.config as config
    config._settings = None # reset
    
    data_dir = get_data_dir()
    assert isinstance(data_dir, Path)
    assert data_dir.name == "local_data"
    assert data_dir.exists()
    assert data_dir.is_dir()

def test_get_log_dir_default():
    import sovereign.infrastructure.config as config
    config._settings = None # reset
    
    log_dir = get_log_dir()
    assert isinstance(log_dir, Path)
    assert log_dir.name == "logs"
    assert log_dir.exists()
    assert log_dir.is_dir()
