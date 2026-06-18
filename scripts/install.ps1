Param(
    [string]$PyDir = "tools\\python311"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

if (!(Test-Path (Join-Path "$PyDir" "python.exe"))) {
    & "scripts\\install_python311.ps1" -PyDir "$PyDir"
}

$PyExe = & "scripts\\_python.ps1" -PyDir "$PyDir"

Write-Host "Upgrade pip"
& "$PyExe" -m pip install --upgrade pip

Write-Host "Install torch (auto CUDA index)"
$CudaVer = ""
try {
    $CudaVer = (& nvidia-smi) -join "`n"
} catch {
    $CudaVer = ""
}

$TorchIndex = "https://download.pytorch.org/whl/cu121"
if ($CudaVer -match "CUDA Version:\s*12\.4") { $TorchIndex = "https://download.pytorch.org/whl/cu124" }
if ($CudaVer -match "CUDA Version:\s*12\.1") { $TorchIndex = "https://download.pytorch.org/whl/cu121" }
if ($CudaVer -match "CUDA Version:\s*11\.8") { $TorchIndex = "https://download.pytorch.org/whl/cu118" }

& "$PyExe" -m pip install --index-url "$TorchIndex" torch

Write-Host "Install project requirements"
& "$PyExe" -m pip install -r "requirements_local.txt"

Write-Host "Done. Next: run scripts\\start_api.ps1 and scripts\\start_webui.ps1"
