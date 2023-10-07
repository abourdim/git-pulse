@echo off
REM ──────────────────────────────────────────
REM  GitPulse — Portable USB Launcher (Windows)
REM  No installation required. No admin needed.
REM ──────────────────────────────────────────
setlocal

set "SCRIPT_DIR=%~dp0"
set "GHM_CONFIG=%SCRIPT_DIR%config"

REM Try embedded WinPython first
if exist "%SCRIPT_DIR%python\python.exe" (
    set "PYTHON=%SCRIPT_DIR%python\python.exe"
    goto run
)

REM Try system Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python"
    goto run
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON=python3"
    goto run
)

echo.
echo  ERROR: Python not found.
echo  Download WinPython and extract to %SCRIPT_DIR%python\
echo  https://winpython.github.io/
echo.
pause
exit /b 1

:run
echo.
echo  GitPulse — Portable Mode
echo  Config: %GHM_CONFIG%
echo.

REM Check for requests
%PYTHON% -c "import requests" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo  Installing requests...
    %PYTHON% -m pip install --user requests --quiet
)

REM CLI or Web mode
if "%1"=="--web" (
    %PYTHON% "%SCRIPT_DIR%gitpulse.py" --web
) else (
    %PYTHON% "%SCRIPT_DIR%gitpulse.py"
)

endlocal
