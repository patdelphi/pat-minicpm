Param(
    [string]$PyDir = "tools\\python311",
    [string]$DownloadsDir = "tools\\downloads"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

New-Item -ItemType Directory -Force -Path "$DownloadsDir" | Out-Null
New-Item -ItemType Directory -Force -Path "$PyDir" | Out-Null

$PyExe = Join-Path "$PyDir" "python.exe"
if (Test-Path "$PyExe") {
    Write-Host "Python already exists: $PyExe"
    exit 0
}

$PyZip = Join-Path "$DownloadsDir" "python-3.11.9-embed-amd64.zip"
$PyZipUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"

Write-Host "Download Python embeddable: $PyZipUrl"
Invoke-WebRequest -Uri "$PyZipUrl" -OutFile "$PyZip"

Write-Host "Extract to: $PyDir"
Expand-Archive -Path "$PyZip" -DestinationPath "$PyDir" -Force

$PthFile = Join-Path "$PyDir" "python311._pth"
if (!(Test-Path "$PthFile")) {
    throw "缺少 python311._pth：$PthFile"
}

$pth = Get-Content "$PthFile"
$pth = $pth | ForEach-Object { $_.Replace("import site", "#import site") }

if (($pth | Where-Object { $_ -eq "Lib" }).Count -eq 0) { $pth = @("Lib") + $pth }
if (($pth | Where-Object { $_ -eq "Lib\\site-packages" }).Count -eq 0) { $pth = @("Lib\\site-packages") + $pth }

Set-Content -Path "$PthFile" -Value $pth -Encoding Ascii

$GetPip = Join-Path "$PyDir" "get-pip.py"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

Write-Host "Download get-pip.py: $GetPipUrl"
Invoke-WebRequest -Uri "$GetPipUrl" -OutFile "$GetPip"

Write-Host "Install pip"
& "$PyExe" "$GetPip"

Write-Host "Done: $PyExe"
