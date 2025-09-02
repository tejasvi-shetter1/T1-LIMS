@echo off
title NEPL LIMS - All Services

echo Starting NEPL LIMS local development environment...

REM Start Redis (if using Memurai)
REM start "" "C:\Program Files\Memurai\memurai.exe"

REM Start backend in new window
echo Starting FastAPI backend...
start "NEPL Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
timeout /t 3

REM Start frontend in new window  
echo Starting React frontend...
start "NEPL Frontend" cmd /k "cd frontend && npm run dev"

echo All services starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:3000
echo API Docs: http://127.0.0.1:8000/docs

echo Press any key to stop all services...
pause

REM Stop services (this is basic - you might need to close windows manually)
taskkill /f /im "uvicorn.exe" 2>nul
taskkill /f /im "node.exe" 2>nul
