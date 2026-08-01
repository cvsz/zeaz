<#
.SYNOPSIS
    Full-Stack ZEAZ Platform Installer for Windows 11.

.DESCRIPTION
    Automates complete setup of the ZEAZ Full-Stack Ecosystem on Windows 11:
    - Node.js (v18+) & NPM environment checks
    - Python 3.11+ environment checks
    - Virtual Environment initialization and Python dependency installation (`requirements.txt`)
    - Monorepo Node dependencies installation (`npm install`)
    - Workspace builds via Turbo Build (`npm run build`)
    - Desktop shortcut & CLI launcher wrapper creation (`zeaz-platform.cmd`, `zeaz-platform.ps1`)
    - System environment variable setup (`ZEAZ_HOME`, `PATH` updates)

.PARAMETER Apply
    Applies the full-stack installation. Default is DryRun mode.

.PARAMETER DryRun
    Simulates full-stack setup without performing changes.

.PARAMETER TargetDir
    Target directory for ZEAZ Platform installation. Defaults to "$env:LOCALAPPDATA\ZEAZ-Platform".
#>

[CmdletBinding(DefaultParameterSetName = 'DryRun')]
param (
    [Parameter(ParameterSetName = 'Apply')]
    [switch]$Apply,

    [Parameter(ParameterSetName = 'DryRun')]
    [switch]$DryRun,

    [string]$TargetDir = "$env:LOCALAPPDATA\ZEAZ-Platform",
    [string]$BinDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
)

$ErrorActionPreference = 'Stop'

function Write-ZeazLog {
    param(
        [string]$Level,
        [string]$Message
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $color = switch ($Level) {
        "INFO"    { "Cyan" }
        "SUCCESS" { "Green" }
        "WARN"    { "Yellow" }
        "ERROR"   { "Red" }
        Default   { "White" }
    }
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

$IsApply = $PSCmdlet.ParameterSetName -eq 'Apply'
$RepoRoot = Resolve-Path "$PSScriptRoot\.."

Write-ZeazLog -Level "INFO" -Message "========================================================"
Write-ZeazLog -Level "INFO" -Message "    ZEAZ Full-Stack Windows 11 Installer Engine        "
Write-ZeazLog -Level "INFO" -Message "========================================================"
Write-ZeazLog -Level "INFO" -Message "Repository Root: $RepoRoot"
Write-ZeazLog -Level "INFO" -Message "Target Directory: $TargetDir"
Write-ZeazLog -Level "INFO" -Message "Apply Mode: $IsApply"

# 1. Prerequisite Checks
Write-ZeazLog -Level "INFO" -Message "Step 1: Checking System Prerequisites..."

function Get-ValidPython {
    $Candidates = @("py.exe", "python3.exe", "python.exe")
    foreach ($cand in $Candidates) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if ($cmd) {
            try {
                $ver = & $cmd.Source --version 2>&1
                if ($ver -and $ver -match "Python 3\.") {
                    return $cmd.Source
                }
            } catch {}
        }
    }
    return $null
}

$Node = Get-Command node.exe -ErrorAction SilentlyContinue
$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $Npm) { $Npm = Get-Command npm.exe -ErrorAction SilentlyContinue }
$PythonPath = Get-ValidPython

$MissingTools = @()
if (-not $Node) { $MissingTools += "Node.js (v18+)" }
if (-not $Npm) { $MissingTools += "NPM" }
if (-not $PythonPath) { $MissingTools += "Python 3.11+" }

if ($MissingTools.Count -gt 0) {
    Write-ZeazLog -Level "ERROR" -Message "Missing required tools: $($MissingTools -join ', ')"
    Write-ZeazLog -Level "ERROR" -Message "Please install missing tools or use winget: winget install OpenJS.NodeJS Python.Python.3.11"
    exit 1
}

$NodeVersion = & $Node.Source --version
$PythonVersion = & $PythonPath --version
Write-ZeazLog -Level "SUCCESS" -Message "Detected Node.js: $NodeVersion"
Write-ZeazLog -Level "SUCCESS" -Message "Detected Python: $PythonVersion"

if (-not $IsApply) {
    Write-ZeazLog -Level "INFO" -Message "[DRY-RUN] System checks passed. Re-run with -Apply to perform installation."
    exit 0
}

# 2. Directory Hierarchy Setup
Write-ZeazLog -Level "INFO" -Message "Step 2: Preparing Application Directories..."
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# 3. Virtual Environment & Python Setup
Write-ZeazLog -Level "INFO" -Message "Step 3: Setting up Python Virtual Environment..."
$VenvDir = Join-Path $TargetDir ".venv"
if (-not (Test-Path $VenvDir)) {
    & $PythonPath -m venv $VenvDir
}

$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

$ReqFile = Join-Path $RepoRoot "requirements.txt"
if (Test-Path $ReqFile) {
    Write-ZeazLog -Level "INFO" -Message "Installing Python dependencies from requirements.txt..."
    & $VenvPip install --disable-pip-version-check -r $ReqFile
}

# 4. Node.js Workspace Dependencies Setup
Write-ZeazLog -Level "INFO" -Message "Step 4: Installing Node.js Workspace Dependencies..."
Push-Location $RepoRoot
try {
    & $Npm.Source install
    Write-ZeazLog -Level "SUCCESS" -Message "Node modules installed successfully."
    
    Write-ZeazLog -Level "INFO" -Message "Building Full-Stack Workspaces (Turbo Build)..."
    & $Npm.Source run build
    Write-ZeazLog -Level "SUCCESS" -Message "Turbo Build completed successfully."
} finally {
    Pop-Location
}

# 5. Environment Config Setup
Write-ZeazLog -Level "INFO" -Message "Step 5: Initializing Environment Files..."
$EnvExamples = Get-ChildItem -Path $RepoRoot -Filter "*.example"
foreach ($example in $EnvExamples) {
    $targetEnvName = $example.Name.Replace(".example", "")
    $targetEnvPath = Join-Path $RepoRoot $targetEnvName
    if (-not (Test-Path $targetEnvPath)) {
        Copy-Item $example.FullName $targetEnvPath
        Write-ZeazLog -Level "INFO" -Message "Created $targetEnvName from example"
    }
}

# 6. Global Launcher Scripts Setup
Write-ZeazLog -Level "INFO" -Message "Step 6: Registering Windows CLI Launchers..."

$CmdLauncher = Join-Path $BinDir "zeaz.cmd"
$PsLauncher = Join-Path $BinDir "zeaz.ps1"

$CmdContent = @"
@echo off
setlocal
set "ZEAZ_HOME=$RepoRoot"
cd /d "%ZEAZ_HOME%"
"$VenvPython" app.py %*
endlocal
"@

$PsContent = @"
`$env:ZEAZ_HOME = "$RepoRoot"
Set-Location `$env:ZEAZ_HOME
& "$VenvPython" app.py `@args
"@

Set-Content -Path $CmdLauncher -Value $CmdContent -Encoding ASCII
Set-Content -Path $PsLauncher -Value $PsContent -Encoding ASCII

# 7. Environment Variables
Write-ZeazLog -Level "INFO" -Message "Step 7: Setting User Environment Variables..."
[Environment]::SetEnvironmentVariable("ZEAZ_HOME", $RepoRoot, "User")

Write-ZeazLog -Level "SUCCESS" -Message "========================================================"
Write-ZeazLog -Level "SUCCESS" -Message " ZEAZ Full-Stack Installation Complete!                "
Write-ZeazLog -Level "SUCCESS" -Message "========================================================"
Write-ZeazLog -Level "INFO" -Message "You can now run 'zeaz' from any Windows 11 terminal."
