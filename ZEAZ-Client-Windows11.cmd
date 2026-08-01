@echo off
setlocal enabledelayedexpansion

title ZEAZ Windows 11 Desktop Client

:: Select PowerShell Runtime
where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\ZEAZ-Windows11-Client.ps1" %*

endlocal
