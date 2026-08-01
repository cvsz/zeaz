@echo off
setlocal enabledelayedexpansion

title ZEAZ Platform UAE Desktop Client Launcher (AED)

echo ========================================================
echo   ZEAZ Platform UAE Desktop Client (United Arab Emirates)
echo ========================================================
echo.
echo Region: United Arab Emirates (UAE)
echo Currency: AED (Dirham)
echo VAT Rate: 5%% (FTA Compliant)
echo.

set "ZEAZ_REGION=UAE"
set "ZEAZ_DEFAULT_CURRENCY=AED"
set "ZEAZ_VAT_RATE=0.05"

where pwsh.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PS_CMD=pwsh.exe"
) else (
    set "PS_CMD=powershell.exe"
)

%PS_CMD% -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\Build-ZEAZ-UAE.ps1" %*

echo.
echo Launching ZEAZ Desktop Client...
call "%~dp0ZEAZ-Client-Windows11.cmd"

endlocal
