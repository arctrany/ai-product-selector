@echo off
REM 选评自动化CLI应用可执行入口 (Windows批处理版本)
REM 使用方法: xp.bat [命令] [选项]
REM
REM 功能特性:
REM - 自动检测并安装缺失依赖
REM - 支持环境变量 XP_SKIP_DEP_CHECK=1 跳过依赖检查
REM
REM 设置代码页为UTF-8以支持中文输出
chcp 65001 >nul 2>&1

setlocal EnableDelayedExpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 查找 Python 解释器
set "PYTHON_CMD="

REM 优先检查 py launcher (Windows Python Launcher)
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
    goto :found_python
)

REM 检查 python3 命令
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python3"
    goto :found_python
)

REM 检查 python 命令
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
    goto :found_python
)

REM 未找到 Python
echo [错误] 未找到 Python 解释器
echo.
echo 请安装 Python 3.8 或更高版本:
echo   1. 访问 https://www.python.org/downloads/
echo   2. 下载并安装 Python 3.8+
echo   3. 安装时勾选 "Add Python to PATH"
echo.
exit /b 1

:found_python
REM 检查 Python 版本
%PYTHON_CMD% -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] Python 版本过低，需要 Python 3.8+
    %PYTHON_CMD% --version
    exit /b 1
)

REM 运行主脚本（已包含依赖检测逻辑）
%PYTHON_CMD% "%SCRIPT_DIR%xp" %*
exit /b %ERRORLEVEL%
