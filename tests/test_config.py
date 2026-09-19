import os
import pytest
from sovereign.infrastructure.config import get_settings, AppSettings

def test_default_config(monkeypatch):
    monkeypatch.delenv('SOVEREIGN_ENV', raising=False)
    monkeypatch.delenv('SOVEREIGN_LOG_LEVEL', raising=False)
    # We must reset the global settings for testing
    import sovereign.infrastructure.config as config
    config._settings = None
    
    settings = get_settings()
    assert settings.sovereign_env == "development"
    assert settings.sovereign_log_level == "INFO"

def test_override_config(monkeypatch):
    monkeypatch.setenv('SOVEREIGN_ENV', 'production')
    monkeypatch.setenv('SOVEREIGN_LOG_LEVEL', 'DEBUG')
    import sovereign.infrastructure.config as config
    config._settings = None
    
    settings = get_settings()
    assert settings.sovereign_env == "production"
    assert settings.sovereign_log_level == "DEBUG"
