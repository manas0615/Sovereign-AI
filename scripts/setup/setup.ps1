param (
    [switch]$InstallDev = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up Sovereign AI Workbench environment..." -ForegroundColor Cyan

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment in .venv..." -ForegroundColor Green
    python -m venv .venv
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate virtual environment
$activateScript = ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $activateScript
} else {
    Write-Error "Could not find virtual environment activation script."
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install requirements
Write-Host "Installing production requirements..." -ForegroundColor Green
pip install -r requirements.txt

if ($InstallDev) {
    Write-Host "Installing development requirements..." -ForegroundColor Green
    pip install -r requirements-dev.txt
}

Write-Host "Setup complete!" -ForegroundColor Cyan
Write-Host "To activate the environment in the future, run: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
