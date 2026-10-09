param([string]$RepoRoot = 'C:\dev\NConnect')
$ErrorActionPreference = 'Stop'
$outputDir = Join-Path $RepoRoot '.omx\monitoring\g_a074_eval'
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$checkedAt = Get-Date -Format o
try {
    git -C $RepoRoot fetch origin --quiet
    if ($LASTEXITCODE -ne 0) { throw 'git fetch failed' }
    $remoteCommit = git -C $RepoRoot rev-parse origin/master
    $ledger = git -C $RepoRoot show 'origin/master:workspace/_keep/pc2_handoff_ledger.tsv'
    if ($LASTEXITCODE -ne 0) { throw 'remote ledger unavailable' }
    $rows = @($ledger | Where-Object { $_ -match '^G-A07[46]\s' })
    $progressPath = 'workspace/_keep/go2_g_a074_eval_progress.tsv'
    $progressAvailable = [bool](git -C $RepoRoot ls-tree --name-only origin/master -- $progressPath)
    $progress = @()
    if ($progressAvailable) {
        $progress = git -C $RepoRoot show "origin/master:$progressPath"
        if ($LASTEXITCODE -ne 0) { throw 'remote progress file unreadable' }
    }
    $state = [ordered]@{
        checked_at = $checkedAt
        remote_commit = "$remoteCommit"
        training = 'G-A074 TRAIN_RC=0; 3000/3000 (100%); reuse iter2400'
        evaluation_progress = 'UNKNOWN: no published case count'
        remote_rows = $rows
        progress_rows = @()
    }
    if ($progressAvailable) {
        $state.progress_rows = @($progress)
        $state.evaluation_progress = 'See PC2 progress rows; no elapsed-time estimate'
    }
    $state | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'latest.json')
    "$checkedAt`t$remoteCommit`tCHECKED" | Add-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'checks.tsv')
} catch {
    "$checkedAt`tCHECK_FAILED`t$($_.Exception.Message)" | Add-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'checks.tsv')
    throw
}
