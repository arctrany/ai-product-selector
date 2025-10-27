@echo off
REM Workflow Engine Server Control Script for Windows
REM Usage: workflow_server.bat [start|stop|restart|status|install|logs|apps|test]

setlocal enabledelayedexpansion

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Load environment variables from .env file if it exists
call :load_env_vars

set "SERVER_MODULE=workflow_engine.api.server"
set "PID_FILE=%PROJECT_DIR%\.workflow_server.pid"
set "LOG_FILE=%PROJECT_DIR%\workflow_server.log"
if not defined WORKFLOW_SOURCE_DIR set "WORKFLOW_SOURCE_DIR=src_new"
if not defined WORKFLOW_PORT set "WORKFLOW_PORT=8889"

REM Colors for output (Windows doesn't support ANSI colors in cmd by default)
set "INFO_PREFIX=[INFO]"
set "WARN_PREFIX=[WARN]"
set "ERROR_PREFIX=[ERROR]"

REM Function to load environment variables from .env file
:load_env_vars
set "ENV_FILE=%SCRIPT_DIR%.env"
if exist "%ENV_FILE%" (
    echo %INFO_PREFIX% Loading environment variables from %ENV_FILE%
    for /f "usebackq tokens=1,2 delims==" %%a in ("%ENV_FILE%") do (
        set "LINE=%%a"
        REM Skip empty lines and comments
        if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" (
            set "KEY=%%a"
            set "VALUE=%%b"
            REM Remove quotes from value
            set "VALUE=!VALUE:"=!"
            REM Only set if not already defined
            if not defined !KEY! (
                set "!KEY!=!VALUE!"
            )
        )
    )
) else (
    echo %INFO_PREFIX% No .env file found at %ENV_FILE%
)
goto :eof

REM Function to print status messages
:print_status
echo %INFO_PREFIX% %~1
goto :eof

:print_warning
echo %WARN_PREFIX% %~1
goto :eof

:print_error
echo %ERROR_PREFIX% %~1
goto :eof

REM Function to check if server is running
:is_running
if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>nul | find /I "!PID!" >nul
    if !errorlevel! equ 0 (
        exit /b 0
    ) else (
        del /f "%PID_FILE%" 2>nul
        exit /b 1
    )
)
exit /b 1

REM Function to install dependencies
:install_deps
call :print_status "Installing Python dependencies..."

REM Check if Python is installed
python --version >nul 2>&1
if !errorlevel! neq 0 (
    call :print_error "Python is not installed or not in PATH"
    call :print_error "Please install Python 3.8+ from https://python.org"
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if !errorlevel! neq 0 (
    call :print_error "pip is not available"
    exit /b 1
)

REM Install requirements
if exist "%PROJECT_DIR%\%WORKFLOW_SOURCE_DIR%\requirements.txt" (
    call :print_status "Installing from requirements.txt..."
    pip install -r "%PROJECT_DIR%\%WORKFLOW_SOURCE_DIR%\requirements.txt"
    if !errorlevel! neq 0 (
        call :print_error "Failed to install dependencies"
        exit /b 1
    )
) else (
    call :print_error "requirements.txt not found at %PROJECT_DIR%\%WORKFLOW_SOURCE_DIR%\requirements.txt"
    exit /b 1
)

REM Install Playwright browsers
call :print_status "Installing Playwright browsers..."
playwright install
if !errorlevel! neq 0 (
    call :print_warning "Failed to install Playwright browsers automatically"
    call :print_status "You may need to run 'playwright install' manually"
)

call :print_status "Dependencies installed successfully"
exit /b 0

REM Function to kill processes on specific ports
:kill_port_processes
for %%p in (8000 8888 8001 8889) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| find ":%%p "') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)
exit /b 0

REM Function to start the server
:start_server
call :is_running
if !errorlevel! equ 0 (
    set /p PID=<"%PID_FILE%"
    call :print_warning "Server is already running (PID: !PID!)"
    exit /b 1
)

call :print_status "Starting Workflow Engine Server..."

REM Kill any processes using our ports
call :print_status "Cleaning up ports 8000, 8888, 8001, 8889..."
call :kill_port_processes

REM Change to project directory and start server
cd /d "%PROJECT_DIR%\%WORKFLOW_SOURCE_DIR%"

REM Start server in background
call :print_status "Starting server process..."
start /b python -m %SERVER_MODULE% > "%LOG_FILE%" 2>&1

REM Get the PID of the started process (Windows specific approach)
timeout /t 2 /nobreak >nul

REM Find the Python process running our module
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find "python.exe"') do (
    set "TEMP_PID=%%i"
    set "TEMP_PID=!TEMP_PID:"=!"
    REM Save the first Python PID we find (not ideal but works for simple cases)
    if not defined SERVER_PID set "SERVER_PID=!TEMP_PID!"
)

if defined SERVER_PID (
    echo !SERVER_PID! > "%PID_FILE%"
    call :print_status "Server started successfully (PID: !SERVER_PID!)"
) else (
    call :print_warning "Server started but PID detection failed"
    echo unknown > "%PID_FILE%"
)

call :print_status "Server running on: http://0.0.0.0:%WORKFLOW_PORT%"
call :print_status "Log file: %LOG_FILE%"
exit /b 0

REM Function to stop the server
:stop_server
call :is_running
if !errorlevel! neq 0 (
    call :print_warning "Server is not running"
    exit /b 1
)

set /p PID=<"%PID_FILE%"
call :print_status "Stopping server (PID: %PID%)..."

REM Try to kill the process
if "%PID%" neq "unknown" (
    taskkill /f /pid %PID% >nul 2>&1
)

REM Also kill any Python processes running our module
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV 2^>nul ^| find "python.exe"') do (
    set "TEMP_PID=%%i"
    set "TEMP_PID=!TEMP_PID:"=!"
    taskkill /f /pid !TEMP_PID! >nul 2>&1
)

REM Clean up
del /f "%PID_FILE%" 2>nul

REM Also clean up any remaining processes on our ports
call :kill_port_processes

call :print_status "Server stopped"
exit /b 0

REM Function to restart the server
:restart_server
call :print_status "Restarting Workflow Engine Server..."
call :stop_server
timeout /t 2 /nobreak >nul
call :start_server
exit /b 0

REM Function to show server status
:show_status
call :is_running
if !errorlevel! equ 0 (
    set /p PID=<"%PID_FILE%"
    call :print_status "Server is running (PID: !PID!)"
    call :print_status "Server URL: http://0.0.0.0:%WORKFLOW_PORT%"
    call :print_status "Apps page: http://localhost:%WORKFLOW_PORT%/apps"

    echo.
    echo Port usage:
    netstat -an | find ":%WORKFLOW_PORT%"
    
    REM Show recent log entries
    if exist "%LOG_FILE%" (
        echo.
        echo Recent log entries:
        powershell "Get-Content '%LOG_FILE%' | Select-Object -Last 5"
    )
) else (
    call :print_warning "Server is not running"
)
exit /b 0

REM Function to show logs
:show_logs
if exist "%LOG_FILE%" (
    call :print_status "Showing server logs (Press Ctrl+C to exit):"
    powershell "Get-Content '%LOG_FILE%' -Wait"
) else (
    call :print_error "Log file not found: %LOG_FILE%"
)
exit /b 0

REM Function to open apps page
:open_apps
call :is_running
if !errorlevel! equ 0 (
    call :print_status "Opening apps page in browser..."
    start http://localhost:%WORKFLOW_PORT%/apps
) else (
    call :print_error "Server is not running. Start it first with: %~nx0 start"
)
exit /b 0

REM Function to test apps
:test_apps
call :is_running
if !errorlevel! neq 0 (
    call :print_error "Server is not running. Start it first with: %~nx0 start"
    exit /b 1
)

call :print_status "Testing application pages..."

set "BASE_URL=http://localhost:%WORKFLOW_PORT%"

call :print_status "Testing endpoints:"
echo   Main page: %BASE_URL%/
echo   Apps list: %BASE_URL%/apps
echo   Sample app: %BASE_URL%/apps/sample_app
echo   Sample console: %BASE_URL%/console/sample_app
echo   API docs: %BASE_URL%/docs

call :print_status "Opening key pages in browser..."
start %BASE_URL%/apps
timeout /t 1 /nobreak >nul
start %BASE_URL%/apps/sample_app
timeout /t 1 /nobreak >nul
start %BASE_URL%/console/sample_app
exit /b 0

REM Main script logic
if "%~1"=="start" (
    call :start_server
) else if "%~1"=="stop" (
    call :stop_server
) else if "%~1"=="restart" (
    call :restart_server
) else if "%~1"=="status" (
    call :show_status
) else if "%~1"=="install" (
    call :install_deps
) else if "%~1"=="logs" (
    call :show_logs
) else if "%~1"=="apps" (
    call :open_apps
) else if "%~1"=="test" (
    call :test_apps
) else (
    echo Usage: %~nx0 {start^|stop^|restart^|status^|install^|logs^|apps^|test}
    echo.
    echo Commands:
    echo   install - Install Python dependencies and Playwright browsers
    echo   start   - Start the workflow engine server
    echo   stop    - Stop the workflow engine server
    echo   restart - Restart the workflow engine server
    echo   status  - Show server status
    echo   logs    - Show server logs ^(real-time^)
    echo   apps    - Open apps page in browser
    echo   test    - Test and open all app pages
    echo.
    echo Server will run on: http://0.0.0.0:%WORKFLOW_PORT%
    echo Apps page: http://localhost:%WORKFLOW_PORT%/apps
    echo.
    echo First time setup: %~nx0 install
    exit /b 1
)

endlocal