"""Centralized configuration management."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

class AppSettings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    
    # Environment
    sovereign_env: str = "development"
    
    # Logging
    sovereign_log_level: str = "INFO"
    
    # Paths (optional overrides)
    sovereign_data_dir: Optional[str] = None
    sovereign_log_dir: Optional[str] = None
    
    # State Persistence Configuration
    db_filename: str = "sovereign.db"
    
    # Artifact Configuration
    artifact_dir_name: str = "artifacts"
    max_artifact_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    
    # Model Gateway Configuration
    llama_server_path: str = "llama-server"
    model_path: str = "model.gguf"
    model_name: str = "default_model"
    model_device: str = "Vulkan1"
    gpu_layers: int = 20
    context_size: int = 8192
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    
    # Context Budget Configuration
    reserved_system_tokens: int = 1024
    reserved_output_tokens: int = 1024
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
_settings = None

def get_settings() -> AppSettings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
