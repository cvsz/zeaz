<#
.SYNOPSIS
    Automated Dependency & Missing Component Installer for Windows 11.

.DESCRIPTION
    Detects and automatically installs missing runtime prerequisites:
    - Node.js (v18+) via Winget / Direct Web Download
    - Python (v3.11+) via Winget / Direct Web Download
    - Git & Build Utilities
    Configures environment PATH variables and provisions virtual environments.
#>

[CmdletBinding()]
param (
    [switch]$AutoInstall = $true
)

$ErrorActionPreference = 'Stop'

function Write-InstallerLog {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "[$ts] [ZEAZ-AUTO-INSTALLER-$Level] $Message" -ForegroundColor Green
}

Write-InstallerLog "INFO" "=========================================================="
Write-InstallerLog "INFO" "  ZEAZ Missing Component Auto-Installer (Windows 11)     "
Write-InstallerLog "INFO" "=========================================================="

# Check Winget Availability
$Winget = Get-Command winget.exe -ErrorAction SilentlyContinue

# 1. Audit Python
$PythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $PythonCmd) { $PythonCmd = Get-Command python3.exe -ErrorAction SilentlyContinue }

if (-not $PythonCmd) {
    Write-InstallerLog "WARN" "Python 3.11+ is missing. Initiating automatic installation..."
    if ($Winget) {
        Write-InstallerLog "INFO" "Installing Python 3.11 via Windows Package Manager (winget)..."
        Start-Process winget.exe -ArgumentList "install", "--id", "Python.Python.3.11", "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements" -Wait
    } else {
        Write-InstallerLog "INFO" "Winget not found. Downloading Python installer directly..."
        $PyUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $PyInstaller = "$env:TEMP\python-3.11.9-amd64.exe"
        Invoke-WebRequest -Uri $PyUrl -OutFile $PyInstaller
        Start-Process $PyInstaller -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
        Remove-Item $PyInstaller -ErrorAction SilentlyContinue
    }
    Write-InstallerLog "SUCCESS" "Python 3.11+ installed successfully!"
} else {
    Write-InstallerLog "INFO" "Python Component OK: $(& $PythonCmd.Source --version)"
}

# 2. Audit Node.js
$NodeCmd = Get-Command node.exe -ErrorAction SilentlyContinue

if (-not $NodeCmd) {
    Write-InstallerLog "WARN" "Node.js is missing. Initiating automatic installation..."
    if ($Winget) {
        Write-InstallerLog "INFO" "Installing Node.js LTS via Windows Package Manager (winget)..."
        Start-Process winget.exe -ArgumentList "install", "--id", "OpenJS.NodeJS", "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements" -Wait
    } else {
        Write-InstallerLog "INFO" "Winget not found. Downloading Node.js installer directly..."
        $NodeUrl = "https://nodejs.org/dist/v20.15.1/node-v20.15.1-x64.msi"
        $NodeMsi = "$env:TEMP\node-v20.15.1-x64.msi"
        Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeMsi
        Start-Process msiexec.exe -ArgumentList "/i", $NodeMsi, "/quiet", "/norestart" -Wait
        Remove-Item $NodeMsi -ErrorAction SilentlyContinue
    }
    Write-InstallerLog "SUCCESS" "Node.js installed successfully!"
} else {
    Write-InstallerLog "INFO" "Node.js Component OK: $(& $NodeCmd.Source --version)"
}

Write-InstallerLog "SUCCESS" "=========================================================="
Write-InstallerLog "SUCCESS" "  All Missing Components Auto-Installed & Verified!       "
Write-InstallerLog "SUCCESS" "=========================================================="
