[CmdletBinding()]
param(
    [string]$KeyName = "id_ed25519_github",
    [string]$KeyComment = "cvsz@windows",
    [string]$GitHubTitle = "Windows cvsz",
    [switch]$NoPassphrase,
    [switch]$SkipGitHubUpload,
    [switch]$SkipConnectionTest
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Require-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command was not found: $Name"
    }
}

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string[]]$Arguments,
        [string]$FailureMessage = "Command failed."
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage Exit code: $LASTEXITCODE"
    }
}

function Get-PublicKeyIdentity {
    param([Parameter(Mandatory)][string]$PublicKey)

    $parts = $PublicKey.Trim() -split "\s+"
    if ($parts.Count -lt 2) {
        throw "The public key is not in OpenSSH format."
    }

    return "$($parts[0]) $($parts[1])"
}

Require-Command -Name "ssh-keygen"
Require-Command -Name "ssh"

$sshDirectory = Join-Path $env:USERPROFILE ".ssh"
$privateKeyPath = Join-Path $sshDirectory $KeyName
$publicKeyPath = "$privateKeyPath.pub"
$configPath = Join-Path $sshDirectory "config"
$configDirectory = Join-Path $sshDirectory "config.d"
$githubConfigPath = Join-Path $configDirectory "github-codex.conf"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

New-Item -ItemType Directory -Force -Path $sshDirectory | Out-Null
New-Item -ItemType Directory -Force -Path $configDirectory | Out-Null

$originalKeyPath = Join-Path $sshDirectory "id_ed25519"
if (Test-Path -LiteralPath $originalKeyPath) {
    & ssh-keygen -y -f $originalKeyPath *> $null
    if ($LASTEXITCODE -ne 0) {
        $invalidKeyBackup = Join-Path $sshDirectory "id_ed25519.invalid-$timestamp"
        Copy-Item -LiteralPath $originalKeyPath -Destination $invalidKeyBackup
        Write-Host "Backed up the unreadable original key to: $invalidKeyBackup"
    }
}

if (Test-Path -LiteralPath $privateKeyPath) {
    & ssh-keygen -y -f $privateKeyPath *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "The target key already exists but is unreadable: $privateKeyPath"
    }

    Write-Host "Using the existing valid key: $privateKeyPath"
}
else {
    $keygenArguments = @(
        "-t", "ed25519",
        "-a", "100",
        "-f", $privateKeyPath,
        "-C", $KeyComment
    )

    if ($NoPassphrase) {
        $keygenArguments += @("-N", "")
    }

    Invoke-NativeCommand `
        -Command "ssh-keygen" `
        -Arguments $keygenArguments `
        -FailureMessage "SSH key generation failed."
}

if (-not (Test-Path -LiteralPath $publicKeyPath)) {
    $derivedPublicKey = & ssh-keygen -y -f $privateKeyPath
    if ($LASTEXITCODE -ne 0) {
        throw "Could not derive the public key."
    }

    Set-Content -LiteralPath $publicKeyPath -Value "$derivedPublicKey $KeyComment" -Encoding ascii
}

$validatedPublicKey = & ssh-keygen -y -f $privateKeyPath
if ($LASTEXITCODE -ne 0) {
    throw "Private key validation failed."
}

$githubHostConfig = @"
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/$KeyName
    IdentitiesOnly yes
"@

Set-Content -LiteralPath $githubConfigPath -Value $githubHostConfig -Encoding ascii

$includeDirective = "Include config.d/*.conf"
if (Test-Path -LiteralPath $configPath) {
    $configBackupPath = "$configPath.backup-$timestamp"
    Copy-Item -LiteralPath $configPath -Destination $configBackupPath
    $configContent = Get-Content -LiteralPath $configPath -Raw

    if ($configContent -notmatch "(?m)^\s*Include\s+config\.d/\*\.conf\s*$") {
        $existingConfigBytes = [System.IO.File]::ReadAllBytes($configPath)
        $includeBytes = [System.Text.Encoding]::ASCII.GetBytes("$includeDirective`r`n")
        $updatedConfigBytes = New-Object byte[] ($includeBytes.Length + $existingConfigBytes.Length)
        [System.Buffer]::BlockCopy($includeBytes, 0, $updatedConfigBytes, 0, $includeBytes.Length)
        [System.Buffer]::BlockCopy(
            $existingConfigBytes,
            0,
            $updatedConfigBytes,
            $includeBytes.Length,
            $existingConfigBytes.Length
        )
        [System.IO.File]::WriteAllBytes($configPath, $updatedConfigBytes)
    }
}
else {
    Set-Content -LiteralPath $configPath -Value $includeDirective -Encoding ascii
}

$publicKey = (Get-Content -LiteralPath $publicKeyPath -Raw).Trim()
$publicKeyIdentity = Get-PublicKeyIdentity -PublicKey $publicKey

if (-not $SkipGitHubUpload) {
    Require-Command -Name "gh"
    Invoke-NativeCommand `
        -Command "gh" `
        -Arguments @("auth", "status", "--hostname", "github.com") `
        -FailureMessage "GitHub CLI authentication is required. Run: gh auth login"

    $registeredKeys = @(
        & gh api user/keys --paginate --jq ".[].key"
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read the registered GitHub SSH keys."
    }

    $alreadyRegistered = $false
    foreach ($registeredKey in $registeredKeys) {
        if ((Get-PublicKeyIdentity -PublicKey $registeredKey) -eq $publicKeyIdentity) {
            $alreadyRegistered = $true
            break
        }
    }

    if ($alreadyRegistered) {
        Write-Host "The public key is already registered with GitHub."
    }
    else {
        Invoke-NativeCommand `
            -Command "gh" `
            -Arguments @("ssh-key", "add", $publicKeyPath, "--title", $GitHubTitle, "--type", "authentication") `
            -FailureMessage "Could not upload the public key to GitHub."
        Write-Host "Uploaded the public key to GitHub."
    }
}

Set-Clipboard -Value $publicKey
Write-Host "Copied the public key to the clipboard."

if (-not $SkipConnectionTest) {
    $sshOutput = (& ssh -T -o "StrictHostKeyChecking=accept-new" git@github.com 2>&1) -join "`n"
    if ($sshOutput -notmatch "successfully authenticated") {
        Write-Host $sshOutput
        throw "GitHub SSH authentication test failed."
    }

    Write-Host $sshOutput
}

Write-Host ""
Write-Host "GitHub SSH setup completed."
Write-Host "Private key: $privateKeyPath"
Write-Host "Public key:  $publicKeyPath"
Write-Host "SSH config:  $githubConfigPath"
