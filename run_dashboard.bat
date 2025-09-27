@echo off
REM ATS Dashboard Launcher
REM This script properly launches the Streamlit dashboard

echo Starting ATS Dashboard...
cd /d "%~dp0"

REM Check if virtual environment exists
if exist "ats_env\Scripts\activate.bat" (
    call ats_env\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found, using system Python
)

REM Run Streamlit dashboard
streamlit run dashboard.py

pause