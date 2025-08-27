$ErrorActionPreference = "Stop"

try {
    $ver = & py -3.11 -c "import sys; print(sys.version)"
    Write-Host "Using Python 3.11: $ver" -ForegroundColor Cyan
} catch {
    Write-Host "Python 3.11 not found. Install it first: winget install Python.Python.3.11" -ForegroundColor Red
    exit 1
}

& py -3.11 -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
Write-Host "Environment ready. Run ./scripts/run_admin.ps1 to start the server." -ForegroundColor Green
