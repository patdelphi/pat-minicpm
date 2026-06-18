Param(
    [string]$PyDir = "tools\\python311",
    [string]$ModelId = "OpenBMB/MiniCPM-V-4.6-Thinking",
    [string]$OutputDir = "models\\MiniCPM-V-4.6-Thinking"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

$PyExe = Join-Path "$PyDir" "python.exe"
if (!(Test-Path "$PyExe")) {
    throw "Python not found: $PyExe. Run scripts\\install.ps1 first."
}

& "$PyExe" -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('modelscope') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Install modelscope"
    & "$PyExe" -m pip install modelscope
}

New-Item -ItemType Directory -Force -Path "models" | Out-Null

Write-Host "Download from ModelScope: $ModelId -> $OutputDir"
& "$PyExe" "aipython\\ms_download.py" --model-id "$ModelId" --output-dir "$OutputDir"

