<#
.SYNOPSIS
    One-Click Master Installer for ZEAZ Platform & ZEAZ Provider on Windows 11.

.DESCRIPTION
    Installs both Full-Stack ZEAZ Platform and ZEAZ Provider component in a single command.
    Auto-detects Python 3.11+, Node.js (v18+), and NPM, builds isolated environments,
    links CLI launchers, and sets user environment variables.

.PARAMETER Apply
    Executes full installation. Default is DryRun mode.

.PARAMETER DryRun
    Simulates installation.
#>

[CmdletBinding(DefaultParameterSetName = 'DryRun')]
param (
    [Parameter(ParameterSetName = 'Apply')]
    [switch]$Apply,

    [Parameter(ParameterSetName = 'DryRun')]
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $color = switch ($Level) { "INFO" { "Cyan" } "SUCCESS" { "Green" } "ERROR" { "Red" } Default { "White" } }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

Write-Log "INFO" "=========================================================="
Write-Log "INFO" "     ZEAZ Windows 11 Master Installation Suite            "
Write-Log "INFO" "=========================================================="

$IsApply = $PSCmdlet.ParameterSetName -eq 'Apply'

# Determine Repository Paths
$ScriptDir = $PSScriptRoot
$ZeazDir = Resolve-Path "$ScriptDir\..\..\zeaz" -ErrorAction SilentlyContinue
if (-not $ZeazDir) { $ZeazDir = Resolve-Path "$ScriptDir\.." }
$ZeazProviderDir = Resolve-Path "$ScriptDir\..\..\zeaz-provider" -ErrorAction SilentlyContinue

Write-Log "INFO" "ZEAZ Platform Directory: $ZeazDir"
if ($ZeazProviderDir) { Write-Log "INFO" "ZEAZ Provider Directory: $ZeazProviderDir" }

# 1. Install Full-Stack ZEAZ Platform
$PlatformInstaller = Join-Path $ZeazDir "scripts\Install-ZEAZ-FullStack-Windows11.ps1"
if (Test-Path $PlatformInstaller) {
    Write-Log "INFO" "Installing ZEAZ Full-Stack Platform..."
    if ($IsApply) {
        & $PlatformInstaller -Apply
    } else {
        & $PlatformInstaller -DryRun
    }
}

# 2. Install ZEAZ Provider Component (if present)
if ($ZeazProviderDir) {
    $ProviderInstaller = Join-Path $ZeazProviderDir "scripts\Install-ZEAZ-Windows11.ps1"
    if (Test-Path $ProviderInstaller) {
        Write-Log "INFO" "Installing ZEAZ Provider Component..."
        if ($IsApply) {
            & $ProviderInstaller -Apply
        } else {
            & $ProviderInstaller -DryRun
        }
    }
}

Write-Log "SUCCESS" "=========================================================="
Write-Log "SUCCESS" "  Master Installation Completed Successfully!            "
Write-Log "SUCCESS" "=========================================================="
