Param(
    [string]$PyDir = "tools\\python311",
    [string]$ModelDir = "models\\MiniCPM-V-4.6-Thinking",
    [string]$OutputDir = "models\\MiniCPM-V-4.6-Thinking-int4"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

$PyExe = Join-Path "$PyDir" "python.exe"
if (!(Test-Path "$PyExe")) {
    throw "Python not found: $PyExe. Run scripts\\install.ps1 first."
}

if (!(Test-Path "$ModelDir")) {
    throw "Model dir not found: $ModelDir. Run scripts\\download_model.ps1 first."
}

Write-Host "Quantize int4: $ModelDir -> $OutputDir"
& "$PyExe" "aipython\\quantize_bnb_int4.py" --model-dir "$ModelDir" --output-dir "$OutputDir"

