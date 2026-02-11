@echo off
title Flight Scout
echo Starting Flight Scout...
echo.

:: Start backend
echo [1/2] Starting backend (FastAPI)...
start "Flight Scout - Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --port 8000"

:: Wait a moment for backend to initialize
timeout /t 2 /nobreak >nul

:: Start frontend
echo [2/2] Starting frontend (Vite)...
start "Flight Scout - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both services started in separate windows.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo.
echo Close this window or press any key to exit.
pause >nul
