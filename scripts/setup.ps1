$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$python = Join-Path $venv "Scripts\python.exe"

Push-Location $root
try {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python 3.11+ is not installed or is not on PATH."
    }
    if (-not (Test-Path $python)) {
        Write-Host "Creating Python virtual environment..."
        & python -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw "Could not create the virtual environment." }
    }
    Write-Host "Installing TikTok Content Factory dependencies..."
    & $python -m pip install --upgrade pip
    & $python -m pip install -e .
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
    Write-Host "Setup complete."
}
finally {
    Pop-Location
}
