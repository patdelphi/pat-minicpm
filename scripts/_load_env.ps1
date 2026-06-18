Param(
    [Parameter(Mandatory=$true)][string]$EnvFile,
    [switch]$PreferExistingEnv
)

$ErrorActionPreference = "Stop"

if (!(Test-Path "$EnvFile")) {
    throw "Env file not found: $EnvFile"
}

Get-Content "$EnvFile" | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0) { return }
    if ($line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -le 0) { return }
    $k = $line.Substring(0, $idx).Trim().TrimStart([char]0xFEFF)
    $v = $line.Substring($idx + 1).Trim()
    if ($k.Length -eq 0) { return }
    if ($PreferExistingEnv -and $null -ne (Get-Item -Path "Env:$k" -ErrorAction SilentlyContinue)) {
        return
    }
    Set-Item -Path "Env:$k" -Value $v
}
