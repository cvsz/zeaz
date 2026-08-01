@echo off
setlocal enabledelayedexpansion

title ZEAZ Windows 11 Master Installer

:: Select PowerShell Runtime
where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

echo ========================================================
echo       ZEAZ Windows 11 Master Installation Launcher
echo ========================================================
echo.

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0Install-ZEAZ-Windows11-Master.ps1" -Apply %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Installation failed. Press any key to exit.
    pause >nul
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] ZEAZ Windows 11 Master Installation finished.
echo.
pause
endlocal
