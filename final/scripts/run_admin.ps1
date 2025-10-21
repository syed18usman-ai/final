# VTU Study Assistant - Admin Panel Server
$ErrorActionPreference = "Stop"

Write-Host "[INFO] Starting VTU Study Assistant - Admin Panel..." -ForegroundColor Green

# Activate virtual environment
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "[ERROR] Virtual environment not found. Please run setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Check if port 8003 is available
$port = 8003
$connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($connections) {
    Write-Host "[WARN] Port $port is already in use. Stopping existing process..." -ForegroundColor Yellow
    foreach ($conn in $connections) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Run the admin panel server
Write-Host "[INFO] Starting server on http://localhost:$port" -ForegroundColor Green
Write-Host "[INFO] Admin Panel: http://localhost:$port" -ForegroundColor Cyan
Write-Host "[INFO] Press Ctrl+C to stop the server" -ForegroundColor Yellow

python -m uvicorn src.admin.app:app --reload --host 0.0.0.0 --port $port
