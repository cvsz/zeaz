<#
.SYNOPSIS
    Cross-Platform Automated Build & Deployment Script for macOS / Linux / Windows 11.

.DESCRIPTION
    Detects local host environment (macOS / Linux / Windows 11), installs dependencies,
    compiles ZEAZ Platform workspaces, and sets up cross-platform launcher binaries.

.PARAMETER TargetOS
    Target OS profile: 'Windows', 'Mac', 'Linux', or 'Auto'. Default is 'Auto'.
#>

[CmdletBinding()]
param (
    [ValidateSet('Auto', 'Windows', 'Mac', 'Linux')]
    [string]$TargetOS = 'Auto'
)

$ErrorActionPreference = 'Stop'

function Write-ZeazLog {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "[$ts] [$Level] $Message"
}

if ($TargetOS -eq 'Auto') {
    if ($IsMacOS) { $TargetOS = 'Mac' }
    elseif ($IsLinux) { $TargetOS = 'Linux' }
    else { $TargetOS = 'Windows' }
}

Write-ZeazLog "INFO" "Target Platform Profile: $TargetOS"
Write-ZeazLog "INFO" "Supported Platforms: Windows 11 | macOS | Android (PWA) | iOS (PWA)"

$RepoRoot = Resolve-Path "$PSScriptRoot\.."

# Node & Python Prerequisite Verification
$Node = Get-Command node -ErrorAction SilentlyContinue
$Npm = Get-Command npm -ErrorAction SilentlyContinue
$Python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }

if (-not $Node -or -not $Npm -or -not $Python) {
    Write-ZeazLog "ERROR" "Prerequisite check failed. Please ensure Node.js (v18+) and Python 3.11+ are installed."
    exit 1
}

Write-ZeazLog "INFO" "Node.js: $(& $Node.Source --version)"
Write-ZeazLog "INFO" "Python: $(& $Python.Source --version)"

# Workspace Installation
Push-Location $RepoRoot
try {
    Write-ZeazLog "INFO" "Installing Node Monorepo Dependencies..."
    & $Npm.Source install

    Write-ZeazLog "INFO" "Compiling Full-Stack Workspaces..."
    & $Npm.Source run build
    Write-ZeazLog "SUCCESS" "Build completed cleanly for $TargetOS!"
} finally {
    Pop-Location
}
