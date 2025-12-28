@echo off
title STR Investment Model Dashboard
color 0A
echo ========================================
echo   STR Investment Model Dashboard
echo   Refinement Workbench
echo ========================================
echo.
echo Starting Streamlit server...
echo Browser will open automatically at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Launch Streamlit with localhost binding
streamlit run ui/app.py --server.port 8501 --server.address localhost --browser.serverAddress localhost

REM If Streamlit exits with error, pause to show error
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Failed to start dashboard
    echo ========================================
    pause
)
