$ErrorActionPreference = "Stop"

$stateDir = Join-Path $env:LOCALAPPDATA "TikTokContentFactory"
$envFile = Join-Path $stateDir "app.env"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

function Read-SecretText {
    param([string]$Prompt)
    $secure = Read-Host $Prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

$apiKey = Read-SecretText "Paste your OpenAI API key"
if (-not $apiKey) { throw "An OpenAI API key is required for live generation." }

$username = Read-Host "App login username [liam]"
if (-not $username) { $username = "liam" }
$password = Read-SecretText "Choose an app login password"
if (-not $password) { throw "An app login password is required for the HEX deployment." }

$lines = @(
    "OPENAI_API_KEY=$apiKey",
    "MOCK_OPENAI=false",
    "USE_WEB_CONTEXT=true",
    "AUTO_PREPARE_ENABLED=true",
    "AUTO_PREPARE_TIME=07:00",
    "AUTO_PREPARE_TIMEZONE=Europe/London",
    "AUTO_PREPARE_WEB_CONTEXT=true",
    "AUTO_PREPARE_MOCK=false",
    "APP_AUTH_USERNAME=$username",
    "APP_AUTH_PASSWORD=$password"
)
Set-Content -Path $envFile -Value $lines -Encoding UTF8
Write-Host "Saved HEX configuration to $envFile. Secret values were not printed."
