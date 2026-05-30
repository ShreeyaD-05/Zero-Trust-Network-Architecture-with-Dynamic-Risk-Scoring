@echo off
echo ============================================================
echo EquiMind Database Seeding Script
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "..\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run from the project root or ensure venv exists.
    pause
    exit /b 1
)

echo Running seed script...
echo.

..\venv\Scripts\python.exe seed_database.py

echo.
echo ============================================================
echo Seeding complete!
echo ============================================================
pause
