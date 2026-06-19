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

function Get-DescendantProcessIds {
    Param(
        [int]$RootProcessId
    )

    try {
        $allProcesses = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    } catch {
        Write-Host ("Failed to query child processes for PID {0}: {1}" -f $RootProcessId, $_.Exception.Message)
        return @()
    }

    $childrenByParent = @{}
    foreach ($proc in $allProcesses) {
        $parentId = [int]$proc.ParentProcessId
        if (-not $childrenByParent.ContainsKey($parentId)) {
            $childrenByParent[$parentId] = New-Object System.Collections.Generic.List[int]
        }
        $childrenByParent[$parentId].Add([int]$proc.ProcessId)
    }

    $orderedChildIds = New-Object System.Collections.Generic.List[int]

    function Add-ChildProcessIds {
        Param(
            [int]$ParentId
        )

        if (-not $childrenByParent.ContainsKey($ParentId)) {
            return
        }

        foreach ($childId in $childrenByParent[$ParentId]) {
            Add-ChildProcessIds -ParentId $childId
            $orderedChildIds.Add($childId)
        }
    }

    Add-ChildProcessIds -ParentId $RootProcessId
    return @($orderedChildIds)
}

function Stop-ManagedProcessTree {
    Param(
        [System.Diagnostics.Process]$Process,
        [string]$Name
    )

    if ($null -eq $Process) {
        return
    }

    $rootProcessId = 0
    try {
        $rootProcessId = [int]$Process.Id
    } catch {
        return
    }

    foreach ($childProcessId in (Get-DescendantProcessIds -RootProcessId $rootProcessId)) {
        try {
            Stop-Process -Id $childProcessId -Force -ErrorAction Stop
            Write-Host ("Stopped child process {0} for {1}." -f $childProcessId, $Name)
        } catch {
            # Ignore already-exited children and continue clearing the process tree.
        }
    }

    Stop-ManagedProcess -Process $Process -Name $Name
}

$apiProcess = $null
$webuiProcess = $null
$cleanupDone = $false
$cleanupEvent = $null
$managedProcessIds = New-Object System.Collections.Generic.HashSet[int]

function Add-ManagedProcessId {
    Param(
        [int]$ProcessId
    )

    if ($ProcessId -le 0) {
        return
    }

    $null = $managedProcessIds.Add($ProcessId)
}

function Update-ManagedProcessIds {
    Param(
        [System.Diagnostics.Process]$RootProcess
    )

    if ($null -eq $RootProcess) {
        return
    }

    try {
        Add-ManagedProcessId -ProcessId ([int]$RootProcess.Id)
    } catch {
        return
    }

    foreach ($childProcessId in (Get-DescendantProcessIds -RootProcessId $RootProcess.Id)) {
        Add-ManagedProcessId -ProcessId $childProcessId
    }
}

function Stop-RecordedManagedProcesses {
    $processIdsToStop = @($managedProcessIds | Sort-Object -Descending)

    foreach ($processId in $processIdsToStop) {
        try {
            $process = Get-Process -Id $processId -ErrorAction Stop
        } catch {
            continue
        }

        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host ("Stopped recorded managed process {0} ({1})." -f $processId, $process.ProcessName)
        } catch {
            Write-Host ("Failed to stop recorded managed process {0}: {1}" -f $processId, $_.Exception.Message)
        }
    }
}

function Invoke-ManagedCleanup {
    if ($cleanupDone) {
        return
    }

    $script:cleanupDone = $true
    Update-ManagedProcessIds -RootProcess $webuiProcess
    Update-ManagedProcessIds -RootProcess $apiProcess
    Stop-ManagedProcessTree -Process $webuiProcess -Name "WebUI"
    Stop-ManagedProcessTree -Process $apiProcess -Name "API"
    Stop-RecordedManagedProcesses
}

$cleanupEvent = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Invoke-ManagedCleanup
}

try {
    $apiProcess = Start-ManagedPythonProcess `
        -Name "API" `
        -Arguments @("-m", "uvicorn", "api.app:app", "--host", "$apiHost", "--port", "$apiPort") `
        -EnvironmentOverrides @{
            "API_HOST" = "$apiHost"
            "API_PORT" = "$apiPort"
        }
    Update-ManagedProcessIds -RootProcess $apiProcess

    Start-Sleep -Seconds 2

    $webuiProcess = Start-ManagedPythonProcess `
        -Name "WEBUI" `
        -Arguments @("webui\\gradio_app.py") `
        -EnvironmentOverrides @{
            "WEBUI_HOST" = "$webuiHost"
            "WEBUI_PORT" = "$webuiPort"
            "OPENAI_BASE_URL" = "$openaiBaseUrl"
        }
    Update-ManagedProcessIds -RootProcess $webuiProcess

    Write-Host "API starting on http://127.0.0.1:$apiPort/"
    Write-Host "WebUI starting on http://$webuiHost`:$webuiPort/"
    Write-Host "Press Ctrl+C to stop both services."

    while ($true) {
        Start-Sleep -Seconds 1
        Update-ManagedProcessIds -RootProcess $apiProcess
        Update-ManagedProcessIds -RootProcess $webuiProcess
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
    Invoke-ManagedCleanup
    if ($null -ne $cleanupEvent) {
        Unregister-Event -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue
        Remove-Job -Id $cleanupEvent.Id -Force -ErrorAction SilentlyContinue
    }
}
