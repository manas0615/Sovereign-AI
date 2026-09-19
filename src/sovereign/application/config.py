"""Configuration strictly for the Application Boundary (Package 07)."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class AppConfig(BaseSettings):
    """Configuration for the FastAPI API layer."""
    # 50 MB default upload size
    max_upload_size_bytes: int = 50 * 1024 * 1024
    
    # API Binding
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_prefix="SOVEREIGN_APP_",
        env_file=".env",
        extra="ignore"
    )

@lru_cache()
def get_api_settings() -> AppConfig:
    return AppConfig()
