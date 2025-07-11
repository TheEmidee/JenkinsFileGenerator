# PowerShell script to set up Python virtual environment and install requirements
# Usage: .\setup-env.ps1

param(
    [string]$VenvName = ".venv",
    [string]$RequirementsFile = "requirements.txt",
    [switch]$Force
)

Write-Host "Setting up Python virtual environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if requirements.txt exists
if (!(Test-Path $RequirementsFile)) {
    Write-Host "Warning: $RequirementsFile not found in current directory" -ForegroundColor Yellow
    $response = Read-Host "Continue without installing requirements? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Remove existing virtual environment if Force flag is used
if ($Force -and (Test-Path $VenvName)) {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvName
}

# Create virtual environment if it doesn't exist
if (!(Test-Path $VenvName)) {
    Write-Host "Creating virtual environment '$VenvName'..." -ForegroundColor Yellow
    python -m venv $VenvName
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
} else {
    Write-Host "Virtual environment '$VenvName' already exists" -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\$VenvName\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements if file exists
if (Test-Path $RequirementsFile) {
    Write-Host "Installing packages from $RequirementsFile..." -ForegroundColor Yellow
    pip install -r $RequirementsFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All packages installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Error: Some packages failed to install" -ForegroundColor Red
    }
} else {
    Write-Host "Skipping package installation - no requirements file found" -ForegroundColor Yellow
}

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "Virtual environment is now active." -ForegroundColor Green
Write-Host "To deactivate later, run: deactivate" -ForegroundColor Cyan
Write-Host "To activate again, run: .\$VenvName\Scripts\Activate.ps1" -ForegroundColor Cyan