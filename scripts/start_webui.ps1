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
if (!(Test-Path "$PyExe")) {
    throw "Python not found: $PyExe. Run scripts\\install.ps1 first."
}

Write-Host "Start WebUI: $Env:WEBUI_HOST`:$Env:WEBUI_PORT  ->  API=$Env:OPENAI_BASE_URL"

& "$PyExe" "webui\\gradio_app.py"
