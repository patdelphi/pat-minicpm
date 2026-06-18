Param(
    [string]$PyDir = "tools\\python311",
    [string]$EnvFile = "config\\local.env"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\\..").Path
Set-Location "$ProjectRoot"

. "$PSScriptRoot\\_load_env.ps1" -EnvFile "$EnvFile"

$PyExe = Join-Path "$PyDir" "python.exe"
if (!(Test-Path "$PyExe")) {
    throw "Python not found: $PyExe. Run scripts\\install.ps1 first."
}

# Use the project-local Python helper to compute the first available API and WebUI ports.
$LaunchPortsScript = Join-Path "$ProjectRoot" "aipython\\launch_ports.py"
$planJson = & "$PyExe" "$LaunchPortsScript"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to compute available ports."
}

$plan = $planJson | ConvertFrom-Json

$apiHost = [string]$plan.api_host
$apiPort = [int]$plan.api_port
$webuiHost = [string]$plan.webui_host
$webuiPort = [int]$plan.webui_port
$openaiBaseUrl = [string]$plan.openai_base_url

Write-Host "Selected API port: $apiPort"
Write-Host "Selected WebUI port: $webuiPort"
Write-Host "OpenAI Base URL: $openaiBaseUrl"

function Start-ManagedPythonProcess {
    Param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][hashtable]$EnvironmentOverrides
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = "$PyExe"
    $psi.WorkingDirectory = "$ProjectRoot"
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    # Windows PowerShell 5 does not support ProcessStartInfo.ArgumentList,
    # so we must build a single escaped argument string.
    $psi.Arguments = ($Arguments | ForEach-Object {
        '"' + (($_ -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
    }) -join " "

    foreach ($entry in $EnvironmentOverrides.GetEnumerator()) {
        $psi.EnvironmentVariables[$entry.Key] = [string]$entry.Value
    }
    $psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
    $psi.EnvironmentVariables["PYTHONUTF8"] = "1"
    $psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"
    $psi.EnvironmentVariables["TRAE_LOG_PREFIX"] = $Name

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    $process.EnableRaisingEvents = $true

    if (-not $process.Start()) {
        throw "Failed to start process: $Name"
    }
    return $process
}

function Flush-ManagedProcessOutput {
    Param(
        [System.Diagnostics.Process]$Process,
        [string]$Name
    )

    if ($null -eq $Process) {
        return
    }

    while ($Process.StandardOutput.Peek() -ge 0) {
        $line = $Process.StandardOutput.ReadLine()
        if ($null -ne $line -and $line -ne "") {
            Write-Host ("[{0}] {1}" -f $Name, $line)
        }
    }

    while ($Process.StandardError.Peek() -ge 0) {
        $line = $Process.StandardError.ReadLine()
        if ($null -ne $line -and $line -ne "") {
            Write-Host ("[{0}] {1}" -f $Name, $line)
        }
    }
}

function Stop-ManagedProcess {
    Param(
        [System.Diagnostics.Process]$Process,
        [string]$Name
    )

    if ($null -eq $Process) {
        return
    }
    if ($Process.HasExited) {
        return
    }

    Write-Host "Stopping $Name..."
    try {
        $Process.Kill($true)
    } catch {
        try {
            $Process.Kill()
        } catch {
            Write-Host ("Failed to stop {0}: {1}" -f $Name, $_.Exception.Message)
        }
    }
}

$apiProcess = $null
$webuiProcess = $null

try {
    $apiProcess = Start-ManagedPythonProcess `
        -Name "API" `
        -Arguments @("-m", "uvicorn", "api.app:app", "--host", "$apiHost", "--port", "$apiPort") `
        -EnvironmentOverrides @{
            "API_HOST" = "$apiHost"
            "API_PORT" = "$apiPort"
        }

    Start-Sleep -Seconds 2

    $webuiProcess = Start-ManagedPythonProcess `
        -Name "WEBUI" `
        -Arguments @("webui\\gradio_app.py") `
        -EnvironmentOverrides @{
            "WEBUI_HOST" = "$webuiHost"
            "WEBUI_PORT" = "$webuiPort"
            "OPENAI_BASE_URL" = "$openaiBaseUrl"
        }

    Write-Host "API starting on http://127.0.0.1:$apiPort/"
    Write-Host "WebUI starting on http://$webuiHost`:$webuiPort/"
    Write-Host "Press Ctrl+C to stop both services."

    while ($true) {
        Start-Sleep -Seconds 1
        Flush-ManagedProcessOutput -Process $apiProcess -Name "API"
        Flush-ManagedProcessOutput -Process $webuiProcess -Name "WEBUI"

        if ($apiProcess.HasExited) {
            Flush-ManagedProcessOutput -Process $apiProcess -Name "API"
            Write-Host "API exited with code $($apiProcess.ExitCode)."
            break
        }
        if ($webuiProcess.HasExited) {
            Flush-ManagedProcessOutput -Process $webuiProcess -Name "WEBUI"
            Write-Host "WebUI exited with code $($webuiProcess.ExitCode)."
            break
        }
    }
}
finally {
    Stop-ManagedProcess -Process $webuiProcess -Name "WebUI"
    Stop-ManagedProcess -Process $apiProcess -Name "API"
}
