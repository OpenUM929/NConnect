param(
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$Name = 'llm42',
    [ValidateSet('nearest','flat_safe','score_rate')][string]$Strategy = 'score_rate',
    [ValidateRange(1,180)][int]$Duration = 180,
    [int]$MapSeed = 42,
    [ValidateSet('h1','go2')][string]$Robot = 'h1',
    [switch]$Llm,
    [switch]$DualLlm,
    [switch]$Record
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
$resultRoot = Join-Path $repoRoot 'workspace/server_returns/H-FINALS-PRACTICE-20261010'
if ($Robot -eq 'go2') { $resultRoot = Join-Path $repoRoot 'workspace/server_returns/G-FINALS-PRACTICE-20261011' }
$runOutput = Join-Path $resultRoot $Name
if (Test-Path -LiteralPath $runOutput) { throw 'Existing results are immutable; choose a fresh Name.' }
$runLog = Join-Path $resultRoot ($Name + '.log')
$runArgs = @('-u','tools/run_h1_finals_practice.py','--out',$runOutput,'--duration',"$Duration",'--map-seed',"$MapSeed",'--strategy',$Strategy,'--headless','--kit_args=--/app/settings/loadUserConfig=false --/app/vulkan=false --/renderer/multiGpu/enabled=false --/renderer/multiGpu/autoEnable=false --/renderer/activeGpu=1')
if ($Llm) { $runArgs += @('--llm','--prompt-file',(Join-Path $resultRoot 'strategy.txt')) }
if ($DualLlm) {
    $strategyFile = if ($Robot -eq 'go2') { 'strategy.txt' } else { 'strategy_dual.txt' }
    $runArgs += @('--dual-llm','--prompt-file',(Join-Path $resultRoot $strategyFile))
}
if ($Robot -eq 'go2') {
    $go2ModelRoot = 'C:/workspace/_keep/go2_g_a077_flat_orientation_m0p225'
    $runArgs += @('--robot','go2','--robot-root',"$go2ModelRoot/training/source",'--policy-path',"$go2ModelRoot/evaluation/candidate/policy.pt",'--checkpoint-path',"$go2ModelRoot/training/model_iter2400.pt",'--expected-checkpoint-sha','23c08ab15617b0001ee90d20c2682cf78041d80058bd83c1d090fdf94d756ca1')
}
if ($Record) { $runArgs += '--record' }
$env:OMNI_KIT_ACCEPT_EULA = 'YES'
$env:PYTHONIOENCODING = 'utf-8'
# Windows PowerShell treats native stderr as errors; preserve it in the log.
$ErrorActionPreference = 'Continue'
& C:/workspace/isaaclab_venv/Scripts/python.exe @runArgs *> $runLog
$nativeExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
Write-Output "NATIVE_EXIT=$nativeExit LOG=$runLog"
$summaryPath = Join-Path $runOutput 'summary.json'
if (Test-Path -LiteralPath (Join-Path $runOutput 'ERROR.txt')) {
    Get-Content -LiteralPath (Join-Path $runOutput 'ERROR.txt') -Encoding UTF8
    exit 1
}
if (!(Test-Path -LiteralPath $summaryPath)) { Write-Error 'No summary; simulation incomplete.'; exit 1 }
$runSummary = Get-Content -LiteralPath $summaryPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (!$runSummary.completed -or [Math]::Abs($runSummary.simulated_seconds-$Duration) -gt .021) { Write-Error 'Partial simulation'; exit 1 }
Get-Content -LiteralPath $summaryPath -Raw -Encoding UTF8
exit 0
