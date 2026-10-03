$log = Get-ChildItem -Path 'C:\workspace\_keep' -Recurse -Filter candidate_training.log -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match 'go2_g_a060_pc2_' } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $log) {
    Write-Host '[NONE] candidate_training.log not found under C:\workspace\_keep\go2_g_a060_pc2_*'
    exit 1
}

Write-Host ('[LOG] ' + $log.FullName)
Write-Host ('[LAST WRITE] ' + $log.LastWriteTime)
Write-Host ''

$text = Get-Content -LiteralPath $log.FullName -Raw
$blocks = [regex]::Matches($text, 'Iteration time:\s*([\d\.]+)s\s*\r?\n\s*Time elapsed:\s*([\d:]+)\s*\r?\n\s*ETA:\s*([\d:]+)')

if ($blocks.Count -eq 0) {
    Write-Host '[NONE] No Iteration time block found yet (training may not have logged its first interval).'
    exit 0
}

$times = $blocks | ForEach-Object { [double]$_.Groups[1].Value }

Write-Host ('[TOTAL INTERVALS LOGGED] ' + $blocks.Count)
Write-Host ''
Write-Host '[LAST 5 INTERVALS]'
$blocks | Select-Object -Last 5 | ForEach-Object {
    Write-Host ('  iter time=' + $_.Groups[1].Value + 's  elapsed=' + $_.Groups[2].Value + '  ETA=' + $_.Groups[3].Value)
}
Write-Host ''

$recentAvg = ($times | Select-Object -Last 20 | Measure-Object -Average).Average
$overallAvg = ($times | Measure-Object -Average).Average
$first = $times[0]

Write-Host ('[SPEED] overall avg = {0:N2}s/iter  |  last-20 avg = {1:N2}s/iter  |  first (warmup) = {2:N2}s' -f $overallAvg, $recentAvg, $first)

if ($recentAvg -gt $overallAvg * 1.3) {
    $pct = [Math]::Round(($recentAvg / $overallAvg - 1) * 100, 0)
    Write-Host ("[WARN] Recent iterations are running ${pct}% SLOWER than the run average - possible slowdown.")
} elseif ($recentAvg -lt $overallAvg * 0.7) {
    Write-Host '[INFO] Recent iterations are notably faster than the run average (expected if early iterations included warmup).'
} else {
    Write-Host '[OK] Recent speed is in line with the run average - no slowdown detected.'
}
