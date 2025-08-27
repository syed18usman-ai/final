# VTU Study Assistant - Student UI Server
Write-Host "🎓 Starting VTU Study Assistant - Student UI..." -ForegroundColor Green

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "❌ Virtual environment not found. Please run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Check if port 8001 is available
$port = 8001
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($process) {
    Write-Host "⚠️  Port $port is already in use. Stopping existing process..." -ForegroundColor Yellow
    Stop-Process -Id $process.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Run the student UI server
Write-Host "🚀 Starting server on http://localhost:$port" -ForegroundColor Green
Write-Host "📱 Student Interface: http://localhost:$port" -ForegroundColor Cyan
Write-Host "🔧 Admin Interface: http://localhost:8000" -ForegroundColor Cyan
Write-Host "⏹️  Press Ctrl+C to stop the server" -ForegroundColor Yellow

python -m uvicorn src.student_ui.app:app --host 0.0.0.0 --port $port
