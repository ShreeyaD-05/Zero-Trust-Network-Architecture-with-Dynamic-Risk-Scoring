@echo off
echo ============================================================
echo EquiMind Supabase Integration Tests
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "..\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run from the project root or ensure venv exists.
    pause
    exit /b 1
)

echo Running Supabase tests...
echo.

..\venv\Scripts\python.exe test_supabase.py

echo.
pause
