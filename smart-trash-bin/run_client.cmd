@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Project Python environment missing. See setup_client.ps1 or README.md.
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0raspberry\hardware\test_serial.py" %*
exit /b %errorlevel%
