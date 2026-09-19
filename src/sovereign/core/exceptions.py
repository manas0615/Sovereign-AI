"""Base exceptions for Sovereign AI Workbench."""

class SovereignError(Exception):
    """Base exception for all Sovereign errors."""
    pass

class ConfigurationError(SovereignError):
    """Raised when configuration is missing or invalid."""
    pass

class ValidationError(SovereignError):
    """Raised when data validation fails."""
    pass

class InfrastructureError(SovereignError):
    """Raised when underlying infrastructure (e.g., paths, OS) fails."""
    pass

class ModelRuntimeError(SovereignError):
    """Raised for errors in the local model runtime (e.g., server failed, missing file)."""
    pass

class ContextOverflowError(SovereignError):
    """Raised when a request explicitly exceeds the configured context budget in the gateway."""
    pass

class StateError(SovereignError):
    """Raised for issues with state persistence or transactions."""
    pass

class ContextBudgetExceeded(SovereignError):
    """Raised when REQUIRED context items exceed the available working budget."""
    pass
