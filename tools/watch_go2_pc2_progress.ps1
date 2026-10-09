param(
    [string]$RepoRoot = 'C:\dev\NConnect',
    [string]$WorkId = 'G-A077',
    [string]$KeepRoot = 'C:\workspace\_keep\go2_g_a077_flat_orientation_m0p225',
    [switch]$Publish
)
$ErrorActionPreference = 'Stop'
$checkedAt = Get-Date -Format o
$trainingLog = Join-Path $KeepRoot 'logs\candidate_training.log'
$iteration = $null
if (Test-Path -LiteralPath $trainingLog) {
    $matchesFound = @(Get-Content -LiteralPath $trainingLog -Tail 500 | Select-String 'Learning iteration\s+(\d+)/3000')
    if ($matchesFound.Count) { $iteration = [int]$matchesFound[-1].Matches[0].Groups[1].Value + 1 }
}
$trainingStatus = Join-Path $KeepRoot 'training\TRAIN_STATUS.txt'
if ((Test-Path -LiteralPath $trainingStatus) -and (Select-String -LiteralPath $trainingStatus -Pattern '^TRAIN_RC=0$' -Quiet)) { $iteration = 3000 }
$caseRoot = Join-Path $KeepRoot 'evaluation\candidate\cases'
$caseCount = 0
if (Test-Path -LiteralPath $caseRoot) {
    foreach ($summary in Get-ChildItem -LiteralPath $caseRoot -Filter summary.json -Recurse -File) {
        try {
            $caseStatus = Join-Path $summary.DirectoryName 'STATUS.txt'
            if (!(Test-Path -LiteralPath $caseStatus) -or !(Select-String -LiteralPath $caseStatus -Pattern '^EVAL_RC=0$' -Quiet)) { continue }
            $null = Get-Content -Raw -LiteralPath $summary.FullName | ConvertFrom-Json
            $caseCount++
        } catch { }
    }
}
$videoRoot = Join-Path $KeepRoot 'evaluation\candidate\videos'
$videoCount = 0
if (Test-Path -LiteralPath $videoRoot) { $videoCount = @(Get-ChildItem -LiteralPath $videoRoot -Filter '*.mp4' -Recurse -File).Count }
$trainingProgress = 'UNKNOWN'
if ($null -ne $iteration) { $trainingProgress = "$iteration/3000 ($([math]::Round(100*$iteration/3000,2))%)" }
$runnerStatus = Join-Path $KeepRoot 'RUNNER_STATUS.txt'
$terminal = 'PENDING'
if (Test-Path -LiteralPath $runnerStatus) {
    $terminal = (@(Get-Content -LiteralPath $runnerStatus | Where-Object { $_ -match '^(RUNNER_RC|COLLECTION_STATUS)=' }) -join ';')
}
$state = [ordered]@{ checked_at=$checkedAt; work_id=$WorkId; training=$trainingProgress; telemetry="$caseCount/69"; evaluation_percent=[math]::Round(100*$caseCount/69,2); videos="$videoCount/10"; runner=$terminal; note='Observed file counts only; no behavior, adoption, or chat notification guarantee.' }
$outputDir = Join-Path $RepoRoot ".omx\monitoring\$($WorkId.ToLower().Replace('-','_'))"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$state | ConvertTo-Json | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'latest.json')
$relative = "workspace/_keep/$($WorkId.ToLower().Replace('-','_'))_progress.tsv"
$progressPath = Join-Path $RepoRoot $relative
"$checkedAt`t$WorkId`t$trainingProgress`t$caseCount/69`t$videoCount/10`t$terminal" | Add-Content -Encoding UTF8 -LiteralPath $progressPath
if ($Publish) {
    git -C $RepoRoot add -- $relative
    if ($LASTEXITCODE -ne 0) { throw 'progress stage failed' }
    # Commit only this monitor's file, preserving concurrently staged author work.
    git -C $RepoRoot commit --only -m "$WorkId observed 30-minute progress" -- $relative
    if ($LASTEXITCODE -ne 0) { throw 'progress commit failed' }
    git -C $RepoRoot push
    if ($LASTEXITCODE -ne 0) { throw 'progress push failed; local evidence retained' }
}
$state | ConvertTo-Json
