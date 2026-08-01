<#
.SYNOPSIS
    ZEAZ Desktop Client Launcher for Windows 11.

.DESCRIPTION
    Launches the ZEAZ Full-Stack Desktop Client application on Windows 11.
    Starts the local background service engine if needed and opens the client GUI window.

.PARAMETER App
    Target desktop client module: 'Web' (Storefront & Ops), 'zERP' (Enterprise ERP), or 'All'. Default is 'All'.

.PARAMETER ServerUrl
    Target ZEAZ backend server URL. Defaults to 'http://localhost:8000'.
#>

[CmdletBinding()]
param (
    [ValidateSet('All', 'Web', 'zERP', 'AI')]
    [string]$App = 'All',

    [string]$ServerUrl = 'http://localhost:8000'
)

$ErrorActionPreference = 'Stop'

function Write-ClientLog {
    param([string]$Level, [string]$Message)
    $ts = (Get-Date).ToString("HH:mm:ss")
    Write-Host "[$ts] [ZEAZ-CLIENT-$Level] $Message" -ForegroundColor Cyan
}

$ScriptDir = $PSScriptRoot
$RepoRoot = Resolve-Path "$ScriptDir\.."

Write-ClientLog "INFO" "Initializing ZEAZ Windows 11 Desktop Client..."
Write-ClientLog "INFO" "Target Application: $App"
Write-ClientLog "INFO" "Backend Endpoint: $ServerUrl"

# Verify Python Engine (check isolated virtualenv first, then system PATH)
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonCmd = Get-Command python3.exe -ErrorAction SilentlyContinue
    if (-not $PythonCmd) { $PythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue }
    if ($PythonCmd) { $PythonExe = $PythonCmd.Source }
}

if (-not $PythonExe) {
    Write-ClientLog "ERROR" "Python engine not found. Please run Install-ZEAZ-Windows11-Master.cmd first."
    exit 1
}

# Start local server if not running
$ServerCheck = $false
try {
    $Tcp = New-Object System.Net.Sockets.TcpClient
    $Connect = $Tcp.BeginConnect("127.0.0.1", 8000, $null, $null)
    $ServerCheck = $Connect.AsyncWaitHandle.WaitOne(500, $false)
    if ($ServerCheck) { $Tcp.EndConnect($Connect) }
    $Tcp.Close()
} catch {
    $ServerCheck = $false
}

if (-not $ServerCheck) {
    Write-ClientLog "INFO" "Local ZEAZ backend service is not running. Starting background service engine..."
    Start-Process -FilePath $PythonExe -ArgumentList "app.py" -WorkingDirectory $RepoRoot -WindowStyle Hidden
    
    # Poll until server is ready (up to 10 seconds)
    $MaxWait = 10
    $Waited = 0
    while ($Waited -lt $MaxWait) {
        Start-Sleep -Seconds 1
        $Waited++
        try {
            $Tcp = New-Object System.Net.Sockets.TcpClient
            $Connect = $Tcp.BeginConnect("127.0.0.1", 8000, $null, $null)
            if ($Connect.AsyncWaitHandle.WaitOne(400, $false)) {
                $Tcp.EndConnect($Connect)
                $Tcp.Close()
                $ServerCheck = $true
                break
            }
            $Tcp.Close()
        } catch {}
    }
    if ($ServerCheck) {
        Write-ClientLog "INFO" "ZEAZ backend service started successfully on port 8000!"
    } else {
        Write-ClientLog "WARN" "ZEAZ backend service startup timed out. Attempting to open client window anyway..."
    }
} else {
    Write-ClientLog "INFO" "Connected to active ZEAZ backend service."
}

# Launch GUI Clients in Default Windows Browser / App Window
$Edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

if ($App -eq 'Web' -or $App -eq 'All') {
    Write-ClientLog "INFO" "Launching ZEAZ Storefront & Command Surface..."
    if (Test-Path $Edge) {
        Start-Process -FilePath $Edge -ArgumentList "--app=$ServerUrl"
    } else {
        Start-Process "$ServerUrl"
    }
}

if ($App -eq 'zERP' -or $App -eq 'All') {
    Write-ClientLog "INFO" "Launching zERP Enterprise Resource Planning Client..."
    $ZerpUrl = "$ServerUrl/platform/dashboard.html"
    if (Test-Path $Edge) {
        Start-Process -FilePath $Edge -ArgumentList "--app=$ZerpUrl"
    } else {
        Start-Process "$ZerpUrl"
    }
}

if ($App -eq 'AI') {
    Write-ClientLog "INFO" "Launching MooPiew AI Studio Client..."
    $AiUrl = "$ServerUrl/platform/ai.html"
    if (Test-Path $Edge) {
        Start-Process -FilePath $Edge -ArgumentList "--app=$AiUrl"
    } else {
        Start-Process "$AiUrl"
    }
}

Write-ClientLog "INFO" "ZEAZ Windows 11 Desktop Client launched successfully!"
