param(
    [switch]$NoBrowser,
    [switch]$SkipPull
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$stateDir = Join-Path $env:LOCALAPPDATA "TikTokContentFactory"
$logDir = Join-Path $stateDir "logs"
$envFile = Join-Path $stateDir "app.env"
$pidFile = Join-Path $stateDir "app.pid"
$port = 8787

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $output = & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git $($Arguments -join ' ') failed." }
    return $output
}

function Import-AppEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    foreach ($line in Get-Content $Path) {
        if (-not $line -or $line.TrimStart().StartsWith("#")) { continue }
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2 -and $parts[0]) {
            [Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
        }
    }
}

function Stop-Factory {
    if (Test-Path $pidFile) {
        $savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($savedPid -and $savedPid -match '^\d+$') {
            Stop-Process -Id ([int]$savedPid) -Force -ErrorAction SilentlyContinue
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

function Wait-ForUrl {
    param([string]$Url, [int]$Attempts = 40)
    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return $true }
        }
        catch { Start-Sleep -Milliseconds 500 }
    }
    return $false
}

function Get-TailscaleUrl {
    if (-not (Get-Command tailscale -ErrorAction SilentlyContinue)) { return $null }
    try {
        $status = (& tailscale status --json | ConvertFrom-Json)
        $dnsName = ([string]$status.Self.DNSName).TrimEnd('.')
        if ($dnsName) { return "http://${dnsName}:$port" }
    }
    catch { }
    return $null
}

Push-Location $root
try {
    $changedFiles = @()
    if (-not $SkipPull -and (Test-Path (Join-Path $root ".git"))) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            throw "Git is not installed or is not on PATH."
        }
        $trackedChanges = Invoke-Git status --porcelain --untracked-files=no
        if ($trackedChanges) {
            throw "Local tracked changes detected. Commit or stash them before updating. Nothing was changed."
        }
        $branch = (Invoke-Git branch --show-current).Trim()
        if (-not $branch) { $branch = "main" }
        Invoke-Git fetch origin $branch --quiet | Out-Null
        $oldCommit = (Invoke-Git rev-parse HEAD).Trim()
        Invoke-Git pull --ff-only origin $branch | Out-Null
        $newCommit = (Invoke-Git rev-parse HEAD).Trim()
        if ($oldCommit -ne $newCommit) {
            Write-Host "Updated Content Factory: $($oldCommit.Substring(0, 7)) -> $($newCommit.Substring(0, 7))"
            $changedFiles = @(Invoke-Git diff --name-only "$oldCommit..$newCommit")
        }
    }

    $needsSetup = (-not (Test-Path $python)) -or ($changedFiles -contains "pyproject.toml") -or ($changedFiles -contains "scripts/setup.ps1")
    if ($needsSetup) {
        & (Join-Path $PSScriptRoot "setup.ps1")
    }

    Import-AppEnv $envFile
    if (-not $env:OPENAI_API_KEY) {
        Write-Warning "OPENAI_API_KEY is not set in $envFile. The UI will run, but live generation will not work until the key is added."
    }

    Stop-Factory
    $outLog = Join-Path $logDir "app.out.log"
    $errLog = Join-Path $logDir "app.err.log"
    Remove-Item $outLog, $errLog -Force -ErrorAction SilentlyContinue

    $process = Start-Process -FilePath $python -WorkingDirectory $root -ArgumentList @(
        "-m", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "$port"
    ) -PassThru -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    Set-Content -Path $pidFile -Value $process.Id

    if (-not (Wait-ForUrl "http://127.0.0.1:$port/health")) {
        Stop-Factory
        throw "TikTok Content Factory did not start. Check $errLog"
    }

    $mobileUrl = Get-TailscaleUrl
    Write-Host "TikTok Content Factory is running: http://localhost:$port"
    if ($mobileUrl) { Write-Host "Mobile/Tailscale:                  $mobileUrl" }
    Write-Host "Persistent env:                    $envFile"
    Write-Host "Logs:                              $logDir"

    if (-not $NoBrowser) { Start-Process "http://localhost:$port" }
}
finally {
    Pop-Location
}
