Param(
    [string]$PyDir = "tools\\python311",
    [string]$EnvFile = "config\\local.env",
    [switch]$UseExistingEnv
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

. "$PSScriptRoot\\_load_env.ps1" -EnvFile "$EnvFile" -PreferExistingEnv:$UseExistingEnv

$PyExe = Join-Path "$PyDir" "python.exe"
$TransformersExe = Join-Path "$PyDir" "Scripts\\transformers.exe"
if (!(Test-Path "$PyExe")) {
    throw "Python not found: $PyExe. Run scripts\\install.ps1 first."
}

Write-Host "Start API (FastAPI): $Env:API_HOST`:$Env:API_PORT"

& "$PyExe" -m uvicorn "api.app:app" --host "$Env:API_HOST" --port "$Env:API_PORT"
