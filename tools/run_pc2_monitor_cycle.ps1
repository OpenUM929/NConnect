param(
    [string]$RepoRoot = 'C:\dev\NConnect',
    [Parameter(Mandatory=$true)][string]$ThreadId,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($ThreadId -notmatch '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$') { throw 'Explicit conversation UUID required' }
$promptPath = Join-Path $RepoRoot 'tools\pc2_hourly_monitor_prompt.md'
if (!(Test-Path -LiteralPath $promptPath)) { throw 'Monitor instructions missing' }
$pythonCommand = (Get-Command python.exe -ErrorAction Stop).Source
$dispatcher = Join-Path $RepoRoot 'tools\pc2_monitor_dispatch.py'
$arguments = @('-X','utf8',$dispatcher,'--thread-id',$ThreadId)
if ($DryRun) {
    [ordered]@{ executable=$pythonCommand; arguments=$arguments; repo=$RepoRoot; delivery='Running app-server queue, not CLI resume; queued is not delivered' } | ConvertTo-Json -Depth 4
    exit 0
}
$logRoot = Join-Path $RepoRoot '.omx\monitoring\pc2_cycles'
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$cycleStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$log = Join-Path $logRoot "$cycleStamp.log"
$statusPath = Join-Path $logRoot 'latest.json'
$cycleLock = $null
$rc = 1
try {
    try {
        $cycleLock = [System.IO.File]::Open((Join-Path $logRoot 'cycle.lock'),[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
    } catch {
        "$(Get-Date -Format o) SKIPPED_ALREADY_RUNNING" | Out-File -Encoding utf8 -LiteralPath $log
        exit 0
    }
    $started = Get-Date -Format o
    [ordered]@{started_at=$started; thread_id=$ThreadId; state='RUNNING'; log=$log} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $statusPath
    Push-Location -LiteralPath $RepoRoot
    try {
        # Native stderr warnings must be logged, not terminate PowerShell before rc capture.
        $ErrorActionPreference = 'Continue'
        & $pythonCommand @arguments 2>&1 | Out-File -Encoding utf8 -LiteralPath $log
        $rc = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
    } finally { Pop-Location }
    $dispatchResult = $null
    if ($rc -eq 0) { $dispatchResult = Get-Content -Raw -LiteralPath $log | ConvertFrom-Json }
    [ordered]@{started_at=$started; checked_at=(Get-Date -Format o); thread_id=$ThreadId; state=$(if($rc -eq 0){$dispatchResult.state}else{'FAILED'}); exit_code=$rc; log=$log; dispatch=$dispatchResult} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath $statusPath
} catch {
    $_ | Out-String | Add-Content -Encoding UTF8 -LiteralPath $log
    [ordered]@{checked_at=(Get-Date -Format o); thread_id=$ThreadId; state='FAILED'; exit_code=1; error=$_.Exception.Message; log=$log} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $statusPath
    $rc = 1
} finally { if ($null -ne $cycleLock) { $cycleLock.Dispose() } }
exit $rc
