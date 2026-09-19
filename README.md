# Sovereign AI Workbench - Package 00

## Development Foundation

This package establishes the stable engineering foundation for the Sovereign AI Workbench. It strictly adheres to a native Windows runtime with no Docker, cloud, or external network dependencies.

### Features
- Native Windows environment setup
- Centralized configuration (via Pydantic)
- Shared path management
- Centralized standard Python logging
- Foundational error definitions
- Minimal health check

### Setup

```powershell
# Create venv and install dependencies
.\scripts\setup.ps1 -InstallDev
```

### Testing

```powershell
# Run unit tests
.\scripts\test.ps1
```

### Architecture
- `src/sovereign/core`: Domain models, exceptions, health checks.
- `src/sovereign/infrastructure`: Implementations of config, logging, paths.
