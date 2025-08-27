@echo off
echo 🎓 Starting VTU Study Assistant - Student UI...

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ❌ Virtual environment not found. Please run setup.ps1 first.
    pause
    exit /b 1
)

REM Run the student UI server
echo 🚀 Starting server on http://localhost:8001
echo 📱 Student Interface: http://localhost:8001
echo 🔧 Admin Interface: http://localhost:8000
echo ⏹️  Press Ctrl+C to stop the server

python -m uvicorn src.student_ui.app:app --host 0.0.0.0 --port 8001
