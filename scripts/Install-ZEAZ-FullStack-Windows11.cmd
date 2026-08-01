@echo off
setlocal enabledelayedexpansion

title ZEAZ Full-Stack Windows 11 Installer

:: Check for PowerShell 7 or Windows PowerShell
where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

echo =======================================================
echo    ZEAZ Full-Stack Automated Installer (Windows 11)
echo =======================================================
echo.

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0Install-ZEAZ-FullStack-Windows11.ps1" -Apply %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Full-Stack Installation failed. Press any key to exit.
    pause >nul
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Full-Stack Installation completed successfully.
echo.
pause
endlocal
