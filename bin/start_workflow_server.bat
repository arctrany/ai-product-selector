@echo off
REM Workflow Engine Server Startup Script for Windows
echo Starting Workflow Engine Server...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONPATH=%CD%
set WORKFLOW_HOST=0.0.0.0
set WORKFLOW_PORT=8889

REM Start the server
echo Starting server on http://localhost:8889
python -m src_new.workflow_engine.api.server

pause
