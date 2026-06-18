Param(
    [string]$PyDir = "tools\\python311"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

$PyExe = Join-Path "$PyDir" "python.exe"
if (!(Test-Path "$PyExe")) {
    throw "Project-local Python not found: $PyExe. Run scripts\\install_python311.ps1 first."
}

Write-Output "$PyExe"
