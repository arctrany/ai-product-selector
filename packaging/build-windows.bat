@echo off
REM AI选品自动化系统 - Windows 构建脚本
REM 使用 PyInstaller 打包为 Windows 可执行文件

setlocal enabledelayedexpansion

echo ========================================
echo AI选品自动化系统 - Windows 构建
echo ========================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 显示 Python 版本
echo 🐍 Python 版本:
python --version

REM 检查必需文件
if not exist "requirements.txt" (
    echo ❌ 错误: 未找到 requirements.txt 文件
    pause
    exit /b 1
)

if not exist "build.spec" (
    echo ❌ 错误: 未找到 build.spec 文件
    pause
    exit /b 1
)

if not exist "cli\main.py" (
    echo ❌ 错误: 未找到 cli\main.py 文件
    pause
    exit /b 1
)

echo ✓ 必需文件检查通过

REM 创建虚拟环境（可选）
set CREATE_VENV=0
if "%1"=="--venv" set CREATE_VENV=1

if %CREATE_VENV%==1 (
    echo 📦 创建虚拟环境...
    python -m venv build-env
    call build-env\Scripts\activate.bat
    echo ✓ 虚拟环境已激活
)

REM 升级 pip
echo 📦 升级 pip...
python -m pip install --upgrade pip

REM 安装依赖
echo 📦 安装项目依赖...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 错误: 安装依赖失败
    pause
    exit /b 1
)

REM 安装 Playwright 浏览器
echo 🌐 安装 Playwright 浏览器...
python -m playwright install chromium
if errorlevel 1 (
    echo ⚠ 警告: Playwright 浏览器安装失败，请手动运行: playwright install chromium
)

REM 清理旧的构建文件
echo 🧹 清理构建目录...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo ✓ 构建目录已清理

REM 运行 PyInstaller
echo 🔨 开始 PyInstaller 构建...
python -m PyInstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo ❌ 错误: PyInstaller 构建失败
    pause
    exit /b 1
)

REM 检查构建结果
if not exist "dist\ai-product-selector.exe" (
    echo ❌ 错误: 构建的可执行文件不存在
    pause
    exit /b 1
)

REM 创建分发目录
set PLATFORM_TAG=win-x64
if "%PROCESSOR_ARCHITECTURE%"=="ARM64" set PLATFORM_TAG=win-arm64
if "%PROCESSOR_ARCHITECTURE%"=="x86" set PLATFORM_TAG=win-x86

set DIST_NAME=ai-product-selector-%PLATFORM_TAG%
set DIST_DIR=dist\%DIST_NAME%

echo 📦 创建分发包...
mkdir "%DIST_DIR%"

REM 复制可执行文件
copy "dist\ai-product-selector.exe" "%DIST_DIR%\"

REM 复制配置文件
if exist "config.json" copy "config.json" "%DIST_DIR%\"
if exist "example_config.json" copy "example_config.json" "%DIST_DIR%\"

REM 创建使用说明
echo 创建使用说明...
(
echo # AI选品自动化系统 - Windows 版本
echo.
echo ## 使用方法
echo.
echo ### 1. 准备配置文件
echo 复制 example_config.json 为 user_config.json 并根据需要修改配置。
echo.
echo ### 2. 运行程序
echo ```cmd
echo ai-product-selector.exe start --data user_data.json --config user_config.json
echo ```
echo.
echo ### 3. 查看帮助
echo ```cmd
echo ai-product-selector.exe --help
echo ```
echo.
echo ## 系统要求
echo - Windows 10/11 ^(x64/ARM64^)
echo - 无需安装 Python 环境
echo.
echo ## 版本信息
echo - 构建时间: %date% %time%
echo - 平台: %PLATFORM_TAG%
) > "%DIST_DIR%\README.txt"

REM 创建 ZIP 压缩包
echo 📦 创建 ZIP 压缩包...
powershell -command "Compress-Archive -Path 'dist\%DIST_NAME%' -DestinationPath 'dist\%DIST_NAME%.zip' -Force"

if exist "dist\%DIST_NAME%.zip" (
    echo ✓ ZIP 压缩包已创建: dist\%DIST_NAME%.zip
) else (
    echo ⚠ 警告: ZIP 压缩包创建失败，请手动压缩 dist\%DIST_NAME% 目录
)

REM 显示构建结果
echo.
echo ========================================
echo 🎉 Windows 构建完成！
echo ========================================
echo 📁 构建目录: dist\%DIST_NAME%
echo 📦 压缩包: dist\%DIST_NAME%.zip
echo 🚀 可执行文件: %DIST_NAME%\ai-product-selector.exe
echo.
echo 💡 使用方法:
echo    cd dist\%DIST_NAME%
echo    ai-product-selector.exe --help
echo.

REM 停用虚拟环境
if %CREATE_VENV%==1 (
    deactivate
    echo ✓ 虚拟环境已停用
)

echo 按任意键退出...
pause >nul
