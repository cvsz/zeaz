@echo off
setlocal enabledelayedexpansion

title ZEAZ Enterprise Production Master Installer (Windows 11)

echo ========================================================
echo   ZEAZ Platform Enterprise Production Installer v2.0
echo ========================================================
echo.

where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\Install-ZEAZ-Enterprise-Master.ps1" %*

echo.
echo Enterprise Installation Completed!
pause
endlocal
