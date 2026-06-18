@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

cd /d "%PROJECT_ROOT%"

echo Starting local API and WebUI...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "& '%SCRIPT_DIR%start_stack.ps1'"

set "EXIT_CODE=%errorlevel%"
echo.
if not "%EXIT_CODE%"=="0" (
    echo Failed to start the local stack.
    echo.
)
echo Press any key to close this window.
pause >nul
exit /b %EXIT_CODE%
