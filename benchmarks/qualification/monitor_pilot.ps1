param (
    [Parameter(Mandatory=$true)]
    [string]$RunDir,
    [int]$IntervalSeconds = 2
)

if (-not (Test-Path -Path $RunDir -PathType Container)) {
    throw "Run directory does not exist: $RunDir"
}

$ResolvedRunDir = (Resolve-Path -Path $RunDir).Path
$LogPath = Join-Path -Path $ResolvedRunDir -ChildPath "monitor_pilot.csv"
$ResolvedLogPath = [System.IO.Path]::GetFullPath($LogPath)

if (-not $ResolvedLogPath.StartsWith($ResolvedRunDir)) {
    throw "Path traversal detected."
}

if (Test-Path -Path $ResolvedLogPath) {
    throw "Output file already exists. Refusing to overwrite: $ResolvedLogPath"
}

Write-Host "Starting Sovereign AI Pilot Monitor"
Write-Host "Logging to $ResolvedLogPath with interval ${IntervalSeconds}s"

"Timestamp,VRAM_Used_MiB,VRAM_Free_MiB,System_RAM_Avail_MB,LlamaServer_PID,LlamaServer_WorkingSet_MB" | Out-File -FilePath $ResolvedLogPath -Encoding utf8 -ErrorAction Stop

try {
    while ($true) {
        $timestamp = (Get-Date).ToString("o")
        
        $vramUsed = "UNAVAILABLE"
        $vramFree = "UNAVAILABLE"
        try {
            $nvidiaOut = & nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits 2>&1
            if ($LASTEXITCODE -eq 0) {
                $parts = $nvidiaOut -split ','
                $vramUsed = $parts[0].Trim()
                $vramFree = $parts[1].Trim()
            }
        } catch {}

        $sysRam = "UNAVAILABLE"
        try {
            $os = Get-CimInstance Win32_OperatingSystem
            $sysRam = [math]::Round($os.FreePhysicalMemory / 1024, 2)
        } catch {}

        $llamaPid = "NONE"
        $llamaWs = "0"
        try {
            $procs = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
            if ($procs) {
                $llamaPid = ($procs.Id -join ';')
                $wsTotal = 0
                foreach ($p in $procs) { $wsTotal += $p.WorkingSet }
                $llamaWs = [math]::Round($wsTotal / 1MB, 2)
            }
        } catch {}

        $line = "$timestamp,$vramUsed,$vramFree,$sysRam,$llamaPid,$llamaWs"
        $line | Out-File -FilePath $ResolvedLogPath -Encoding utf8 -Append
        Write-Host $line
        
        Start-Sleep -Seconds $IntervalSeconds
    }
}
finally {
    Write-Host "Monitor stopped."
}
