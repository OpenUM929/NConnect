param(
    [string]$RepoRoot = 'C:\dev\NConnect',
    [Parameter(Mandatory=$true)][string]$ThreadId,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
if ($ThreadId -notmatch '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$') { throw 'Explicit conversation UUID required' }
$promptPath = Join-Path $RepoRoot 'tools\pc2_hourly_monitor_prompt.md'
if (!(Test-Path -LiteralPath $promptPath)) { throw 'Monitor instructions missing' }
$codexCommand = (Get-Command codex.cmd -ErrorAction Stop).Source
$prompt = @"
30-minute scheduled monitoring turn requested by the user in THIS conversation.
Inspect live A077/H1 state now, report observed percentages and blockers in Korean
in your final response to this conversation, and execute any now-ready next step.
Read tools/pc2_hourly_monitor_prompt.md and follow its latest H1 priority (step 10).
Do not stop at a progress-file commit when recovery/readout/H1 continuation is ready.
Do not repeat completed training or P0. Do not create an extra monitoring session.
This turn is a bounded monitoring/continuation cycle, not permission to alter limits.
"@
$arguments = @('--sandbox','danger-full-access','--ask-for-approval','never','exec','resume',$ThreadId,'-')
if ($DryRun) {
    [ordered]@{ executable=$codexCommand; arguments=$arguments; repo=$RepoRoot; prompt=$prompt; delivery='Explicit existing conversation resume; verify actual delivery after first scheduled run' } | ConvertTo-Json -Depth 4
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
        $prompt | & $codexCommand @arguments 2>&1 | Out-File -Encoding utf8 -LiteralPath $log
        $rc = $LASTEXITCODE
        $ErrorActionPreference = 'Stop'
    } finally { Pop-Location }
    [ordered]@{started_at=$started; checked_at=(Get-Date -Format o); thread_id=$ThreadId; state=$(if($rc -eq 0){'COMPLETED'}else{'FAILED'}); exit_code=$rc; log=$log} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $statusPath
} catch {
    $_ | Out-String | Add-Content -Encoding UTF8 -LiteralPath $log
    [ordered]@{checked_at=(Get-Date -Format o); thread_id=$ThreadId; state='FAILED'; exit_code=1; error=$_.Exception.Message; log=$log} | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath $statusPath
    $rc = 1
} finally { if ($null -ne $cycleLock) { $cycleLock.Dispose() } }
exit $rc
