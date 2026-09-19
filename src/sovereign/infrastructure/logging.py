"""Logging configuration foundation."""

import logging
from logging.handlers import RotatingFileHandler
from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.paths import get_log_dir

_logger_initialized = False

def setup_logging():
    """Initializes standard Python logging."""
    global _logger_initialized
    if _logger_initialized:
        return
        
    settings = get_settings()
    log_dir = get_log_dir()
    log_file = log_dir / "sovereign.log"
    
    numeric_level = getattr(logging, settings.sovereign_log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers if any
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (Rotating, max 5MB, 3 backups)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    _logger_initialized = True
    
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger."""
    if not _logger_initialized:
        setup_logging()
    return logging.getLogger(name)
