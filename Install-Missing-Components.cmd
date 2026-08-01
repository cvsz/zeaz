@echo off
setlocal enabledelayedexpansion

title ZEAZ Automated Missing Component Installer (Windows 11)

echo ========================================================
echo   ZEAZ Missing Component Auto-Installer (Windows 11)
echo ========================================================
echo.

where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\Install-Missing-Components.ps1" %*

echo.
echo Auto-Installer Execution Finished!
pause
endlocal
