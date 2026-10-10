param(
    [string]$RepoRoot = 'C:\dev\NConnect',
    [string]$KeepRoot = 'C:\workspace\_keep\H_A002_ACTION_RATE_M0P002',
    [switch]$Publish
)
$ErrorActionPreference = 'Stop'
$checkedAt = Get-Date -Format o
$arms = @()
foreach ($arm in @('control', 'candidate')) {
    $root = Join-Path $KeepRoot $arm
    $iteration = 0
    $log = Join-Path $root 'train.log'
    if (Test-Path -LiteralPath $log) {
        $observed = @(Get-Content -LiteralPath $log -Tail 500 | Select-String 'Learning iteration\s+(\d+)/1000')
        if ($observed.Count) { $iteration = [int]$observed[-1].Matches[0].Groups[1].Value + 1 }
    }
    $status = Join-Path $root 'TRAIN_STATUS.txt'
    if ((Test-Path -LiteralPath $status) -and (Select-String -LiteralPath $status -Pattern '^TRAIN_RC=0$' -Quiet)) { $iteration = 1000 }
    $cases = 0
    $evalRoot = Join-Path $root 'evaluation'
    if (Test-Path -LiteralPath $evalRoot) {
        foreach ($summary in Get-ChildItem -LiteralPath $evalRoot -Filter summary.json -Recurse -File) {
            try {
                $caseStatus = Join-Path $summary.DirectoryName 'STATUS.txt'
                $data = Get-Content -Raw -LiteralPath $summary.FullName | ConvertFrom-Json
                if ($data.completed -eq $true -and (Test-Path -LiteralPath $caseStatus) -and (Select-String -LiteralPath $caseStatus -Pattern '^EVAL_RC=0$' -Quiet)) { $cases++ }
            } catch { }
        }
    }
    $videoRoot = Join-Path $root 'videos'
    $videos = 0
    if (Test-Path -LiteralPath $videoRoot) { $videos = @(Get-ChildItem -LiteralPath $videoRoot -Filter '*.mp4' -Recurse -File).Count }
    $arms += [ordered]@{ arm=$arm; iteration=$iteration; training_total=1000; training_percent=[math]::Round(100*$iteration/1000,2); completed_cases=$cases; case_total=57; videos=$videos; video_total=10 }
}
$terminal = 'PENDING'
$runner = Join-Path $KeepRoot 'RUNNER_STATUS.txt'
if (Test-Path -LiteralPath $runner) { $terminal = (@(Get-Content -LiteralPath $runner | Where-Object { $_ -match '^(RUNNER_RC|EVAL_CASES|VIDEOS|REPORTS)=' }) -join ';') }
$state = [ordered]@{ checked_at=$checkedAt; work_id='H-A002'; arms=$arms; runner=$terminal; note='Observed counts only; files do not prove behavior or official performance.' }
$outputDir = Join-Path $RepoRoot '.omx\monitoring\h_a002'
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$state | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $outputDir 'latest.json')
$relative = 'workspace/_keep/h_a002_progress.tsv'
"$checkedAt`tH-A002`t$($arms[0].iteration)/1000`t$($arms[1].iteration)/1000`t$($arms[0].completed_cases + $arms[1].completed_cases)/114`t$($arms[0].videos + $arms[1].videos)/20`t$terminal" | Add-Content -Encoding UTF8 -LiteralPath (Join-Path $RepoRoot $relative)
if ($Publish) {
    git -C $RepoRoot add -- $relative
    if ($LASTEXITCODE -ne 0) { throw 'H1 progress stage failed' }
    git -C $RepoRoot commit --only -m 'H-A002 observed 30-minute progress' -- $relative
    if ($LASTEXITCODE -ne 0) { throw 'H1 progress commit failed' }
    git -C $RepoRoot push
    if ($LASTEXITCODE -ne 0) { throw 'H1 progress push failed; evidence retained' }
}
$state | ConvertTo-Json -Depth 5
