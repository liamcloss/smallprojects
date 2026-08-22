$ErrorActionPreference = "Stop"
$stateDir = Join-Path $env:LOCALAPPDATA "TikTokContentFactory"
$pidFile = Join-Path $stateDir "app.pid"
if (Test-Path $pidFile) {
    $savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($savedPid -and $savedPid -match '^\d+$') {
        Stop-Process -Id ([int]$savedPid) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}
Write-Host "TikTok Content Factory stopped."
