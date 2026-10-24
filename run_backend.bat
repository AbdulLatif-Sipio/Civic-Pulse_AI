@echo off
cd /d "%~dp0"
echo ========================================================
echo Starting CleanCity Copilot / CivicPulse AI Backend...
echo Access at: http://127.0.0.1:8000
echo ========================================================
venv\Scripts\python.exe master_backend.py
pause
