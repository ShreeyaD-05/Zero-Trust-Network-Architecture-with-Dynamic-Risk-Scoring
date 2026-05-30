@echo off
echo ========================================
echo   EquiMind Backend Test Suite
echo ========================================
echo.

echo Checking if backend is running...
curl -s http://localhost:8000/status >nul 2>&1
if errorlevel 1 (
    echo ERROR: Backend is not running!
    echo Please start the backend first: python main.py
    pause
    exit /b 1
)

echo Backend is running. Starting tests...
echo.

python test_backend.py

pause
