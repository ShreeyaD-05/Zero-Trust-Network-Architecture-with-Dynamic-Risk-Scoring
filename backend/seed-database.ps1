#!/usr/bin/env pwsh
# EquiMind Database Seeding Script

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EquiMind Database Seeding Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

$venvPython = Join-Path $scriptPath "..\venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please ensure venv exists at: $venvPython" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Running seed script..." -ForegroundColor Green
Write-Host ""

& $venvPython seed_database.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Seeding complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Read-Host "Press Enter to exit"
