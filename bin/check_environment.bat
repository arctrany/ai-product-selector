@echo off
REM Environment Check Script for Windows
echo Checking environment...

echo.
echo Python Version:
python --version

echo.
echo Python Path:
python -c "import sys; print('\n'.join(sys.path))"

echo.
echo Environment Variables:
echo PYTHONPATH=%PYTHONPATH%
echo PATH=%PATH%

echo.
echo Checking required packages...
python -c "
import sys
packages = ['fastapi', 'uvicorn', 'pathlib', 'asyncio']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} - OK')
    except ImportError:
        print(f'❌ {pkg} - Missing')
"

pause
