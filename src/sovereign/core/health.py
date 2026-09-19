"""Minimal application health bootstrap check."""

from sovereign.core.models import HealthCheckResult, HealthStatus
from sovereign.infrastructure.config import get_settings
from sovereign.infrastructure.paths import get_data_dir, get_log_dir
from sovereign.infrastructure.logging import setup_logging, get_logger

def check_health() -> HealthCheckResult:
    """Verifies basic Package 00 infrastructure health."""
    details = {}
    try:
        # Check config
        settings = get_settings()
        details["env"] = settings.sovereign_env
        details["config_loaded"] = True
        
        # Check paths
        data_dir = get_data_dir()
        log_dir = get_log_dir()
        details["paths_accessible"] = True
        details["data_dir"] = str(data_dir)
        
        # Check logging
        setup_logging()
        logger = get_logger("sovereign.health")
        logger.debug("Health check executed.")
        details["logging_initialized"] = True
        
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            details=details
        )
    except Exception as e:
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            details=details,
            error=str(e)
        )
