import pytest
from sovereign.core.exceptions import SovereignError, ConfigurationError, ValidationError, InfrastructureError

def test_exception_hierarchy():
    assert issubclass(ConfigurationError, SovereignError)
    assert issubclass(ValidationError, SovereignError)
    assert issubclass(InfrastructureError, SovereignError)

def test_exception_raising():
    with pytest.raises(ConfigurationError) as exc_info:
        raise ConfigurationError("Invalid configuration")
    assert "Invalid configuration" in str(exc_info.value)
