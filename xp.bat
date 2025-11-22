@echo off
REM 选评自动化CLI应用可执行入口 (Windows批处理版本)
REM 使用方法: xp.bat [命令] [选项]

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 尝试使用 python3，如果不存在则使用 python
python "%~dp0xp" %* 2>nul
if %ERRORLEVEL% NEQ 0 (
    python3 "%~dp0xp" %*
)

