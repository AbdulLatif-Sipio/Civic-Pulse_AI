@echo off
cd /d "C:\Users\Admin\Documents\AI HACKATHON"
echo ===================================================
echo  Pushing CivicPulse AI to Hugging Face Spaces
echo ===================================================
echo.
set /p SPACE_NAME=Enter your Space name (Press Enter for 'civicpulse-ai'): 
if "%SPACE_NAME%"=="" set SPACE_NAME=civicpulse-ai

git remote remove space 2>nul
git remote add space https://huggingface.co/spaces/abdullatif778/%SPACE_NAME%

echo.
echo Pushing to: https://huggingface.co/spaces/abdullatif778/%SPACE_NAME%
echo NOTE: If Git asks for credentials:
echo   - Username: abdullatif778
echo   - Password: Your Hugging Face password or Access Token (from huggingface.co/settings/tokens)
echo.

git push --force space main

echo.
echo ===================================================
echo  Deployment pushed!
echo  View your live Space at:
echo  https://huggingface.co/spaces/abdullatif778/%SPACE_NAME%
echo ===================================================
pause
