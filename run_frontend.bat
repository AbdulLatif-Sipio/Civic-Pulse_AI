@echo off
cd /d "%~dp0cleancity-frontend\cleancity-frontend"
echo ========================================================
echo Starting CleanCity Copilot Streamlit Citizen Portal...
echo Access at: http://localhost:8501
echo ========================================================
..\..\venv\Scripts\streamlit.exe run app.py --server.port 8501
pause
