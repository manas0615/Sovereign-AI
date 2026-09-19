from sovereign.core.health import check_health
from sovereign.core.models import HealthStatus

def test_check_health():
    result = check_health()
    assert result.status == HealthStatus.HEALTHY
    assert result.details["config_loaded"] is True
    assert result.details["paths_accessible"] is True
    assert result.details["logging_initialized"] is True
    assert "data_dir" in result.details
