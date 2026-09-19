$ErrorActionPreference = "Stop"

# Ensure we are in the project root (assuming script is run from project root or scripts dir)
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($projectRoot -match "scripts$") {
    $projectRoot = Split-Path -Parent $projectRoot
}
Set-Location $projectRoot

# Check if virtual environment is active
if (-not $env:VIRTUAL_ENV) {
    $activateScript = ".venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        Write-Host "Activating virtual environment..." -ForegroundColor Green
        & $activateScript
    } else {
        Write-Error "Virtual environment not found. Please run scripts\setup.ps1 -InstallDev first."
        exit 1
    }
}

# Set PYTHONPATH to include src directory so pytest can find sovereign package
$env:PYTHONPATH = "src"

Write-Host "Running tests..." -ForegroundColor Cyan
pytest tests/

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Tests failed!" -ForegroundColor Red
}
exit $LASTEXITCODE
