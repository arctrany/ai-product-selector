@echo off
REM Chrome MCP Launcher Script for Windows
REM 启动Chrome浏览器，配置用户目录和调试端口，供Chrome DevTools MCP连接
REM 
REM 使用方法:
REM chrome-mcp-launcher.bat [options]
REM
REM 选项:
REM   --port PORT          设置调试端口 (默认: 9222)
REM   --profile PATH       设置用户目录路径 (默认: 自动检测)
REM   --headless          无头模式启动
REM   --help              显示帮助信息

setlocal EnableDelayedExpansion

REM 默认配置
set DEBUG_PORT=9222
set HEADLESS_MODE=false
set CUSTOM_PROFILE=
set SCRIPT_DIR=%~dp0
set LOG_FILE=%SCRIPT_DIR%chrome-mcp.log

REM 帮助信息
if "%1"=="--help" (
    echo Chrome MCP Launcher - 为Chrome DevTools MCP启动Chrome浏览器
    echo.
    echo 用法: %0 [选项]
    echo.
    echo 选项:
    echo     --port PORT          设置调试端口 ^(默认: 9222^)
    echo     --profile PATH       设置用户目录路径 ^(默认: 自动检测^)
    echo     --headless          启用无头模式
    echo     --help              显示此帮助信息
    echo.
    echo 示例:
    echo     %0                                    REM 使用默认配置启动
    echo     %0 --port 9223 --headless            REM 无头模式，自定义端口
    echo     %0 --profile C:\my-chrome-profile     REM 指定用户目录
    echo.
    echo 连接方法:
    echo     npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222
    echo.
    goto :eof
)

REM 解析命令行参数
:parse_args
if "%~1"=="" goto :args_done

if "%~1"=="--port" (
    set DEBUG_PORT=%~2
    shift
    shift
    goto :parse_args
)

if "%~1"=="--profile" (
    set CUSTOM_PROFILE=%~2
    shift
    shift
    goto :parse_args
)

if "%~1"=="--headless" (
    set HEADLESS_MODE=true
    shift
    goto :parse_args
)

echo [ERROR] 未知选项: %~1
goto :eof

:args_done

REM 日志函数
echo [INFO] Chrome MCP Launcher 启动中... | tee "%LOG_FILE%"
echo 日志时间: %date% %time% >> "%LOG_FILE%"

REM 查找Chrome可执行文件
set CHROME_EXECUTABLE=
for %%P in (
    "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
    "%PROGRAMFILES(x86)%\Google\Chrome\Application\chrome.exe"
    "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    "%PROGRAMFILES%\Chromium\Application\chrome.exe"
    "%PROGRAMFILES(x86)%\Chromium\Application\chrome.exe"
) do (
    if exist "%%~P" (
        set CHROME_EXECUTABLE=%%~P
        goto :chrome_found
    )
)

echo [ERROR] 未找到Chrome可执行文件 | tee -a "%LOG_FILE%"
pause
goto :eof

:chrome_found
echo [INFO] Chrome可执行文件: !CHROME_EXECUTABLE! | tee -a "%LOG_FILE%"

REM 确定用户目录
if defined CUSTOM_PROFILE (
    set PROFILE_DIR=!CUSTOM_PROFILE!
) else (
    set PROFILE_DIR=%LOCALAPPDATA%\Google\Chrome\User Data\Default
    if not exist "!PROFILE_DIR!" (
        set PROFILE_DIR=%USERPROFILE%\.chrome-mcp-profile
        echo [WARN] 默认Chrome目录不存在，将使用: !PROFILE_DIR! | tee -a "%LOG_FILE%"
    )
)

REM 创建用户目录
if not exist "!PROFILE_DIR!" mkdir "!PROFILE_DIR!"

echo [INFO] 用户数据目录: !PROFILE_DIR! | tee -a "%LOG_FILE%"
echo [INFO] 调试端口: !DEBUG_PORT! | tee -a "%LOG_FILE%"

REM 检查端口是否被占用
netstat -an | findstr ":!DEBUG_PORT!" > nul
if !errorlevel! equ 0 (
    echo [WARN] 端口 !DEBUG_PORT! 可能已被占用 | tee -a "%LOG_FILE%"
)

REM 构建Chrome启动参数
set CHROME_ARGS=--remote-debugging-port=!DEBUG_PORT!
set CHROME_ARGS=!CHROME_ARGS! --user-data-dir="!PROFILE_DIR!"
set CHROME_ARGS=!CHROME_ARGS! --no-first-run
set CHROME_ARGS=!CHROME_ARGS! --no-default-browser-check
set CHROME_ARGS=!CHROME_ARGS! --disable-extensions-file-access-check
set CHROME_ARGS=!CHROME_ARGS! --disable-extensions-except
set CHROME_ARGS=!CHROME_ARGS! --disable-sync
set CHROME_ARGS=!CHROME_ARGS! --disable-translate
set CHROME_ARGS=!CHROME_ARGS! --disable-background-timer-throttling
set CHROME_ARGS=!CHROME_ARGS! --disable-backgrounding-occluded-windows
set CHROME_ARGS=!CHROME_ARGS! --disable-renderer-backgrounding
set CHROME_ARGS=!CHROME_ARGS! --disable-field-trial-config
set CHROME_ARGS=!CHROME_ARGS! --disable-ipc-flooding-protection
set CHROME_ARGS=!CHROME_ARGS! --disable-hang-monitor
set CHROME_ARGS=!CHROME_ARGS! --disable-prompt-on-repost
set CHROME_ARGS=!CHROME_ARGS! --disable-client-side-phishing-detection
set CHROME_ARGS=!CHROME_ARGS! --disable-component-extensions-with-background-pages
set CHROME_ARGS=!CHROME_ARGS! --disable-default-apps
set CHROME_ARGS=!CHROME_ARGS! --disable-dev-shm-usage
set CHROME_ARGS=!CHROME_ARGS! --disable-features=TranslateUI
set CHROME_ARGS=!CHROME_ARGS! --disable-blink-features=AutomationControlled
set CHROME_ARGS=!CHROME_ARGS! --exclude-switches=enable-automation
set CHROME_ARGS=!CHROME_ARGS! --no-sandbox

if "!HEADLESS_MODE!"=="true" (
    set CHROME_ARGS=!CHROME_ARGS! --headless --disable-gpu --virtual-time-budget=5000
    echo [INFO] 启用无头模式 | tee -a "%LOG_FILE%"
)

REM 启动Chrome
echo [INFO] 正在启动Chrome浏览器... | tee -a "%LOG_FILE%"
echo [INFO] 日志文件: !LOG_FILE! | tee -a "%LOG_FILE%"

start "Chrome MCP" "!CHROME_EXECUTABLE!" !CHROME_ARGS!

REM 等待Chrome启动
timeout /t 3 /nobreak > nul

REM 测试调试端口连接
curl -s "http://127.0.0.1:!DEBUG_PORT!/json/version" > nul 2>&1
if !errorlevel! equ 0 (
    echo [INFO] 调试端口连接测试成功 | tee -a "%LOG_FILE%"
    echo.
    echo [INFO] Chrome MCP连接就绪！ | tee -a "%LOG_FILE%"
    echo.
    echo [INFO] 连接命令: | tee -a "%LOG_FILE%"
    echo npx chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:!DEBUG_PORT!
    echo.
    echo [INFO] 或者在IDE中配置MCP连接到: http://127.0.0.1:!DEBUG_PORT! | tee -a "%LOG_FILE%"
    echo.
) else (
    echo [WARN] 调试端口连接测试失败，请稍后重试 | tee -a "%LOG_FILE%"
)

echo [INFO] Chrome已在后台启动，按任意键关闭此窗口...
pause > nul
