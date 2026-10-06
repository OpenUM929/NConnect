#!/usr/bin/env bash
# Watches for the fake svchost.exe (no registered service) pattern, traces its
# live parent process, logs path+args, then kills both child and parent.
LOG="/c/workspace/_keep/svchost_watcher.log"
PS='
$svchosts = Get-Process svchost -ErrorAction SilentlyContinue
foreach ($p in $svchosts) {
    $svc = Get-CimInstance Win32_Service -Filter "ProcessId=$($p.Id)" -ErrorAction SilentlyContinue
    if (-not $svc) {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)"
        $parentId = $proc.ParentProcessId
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$parentId" -ErrorAction SilentlyContinue
        if ($parent.Name -ne "services.exe") {
            Write-Output "FAKE_SVCHOST pid=$($p.Id) parent_pid=$parentId parent_name=$($parent.Name) parent_path=$($parent.ExecutablePath) parent_cmd=$($parent.CommandLine)"
            $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$($p.Id)"
            foreach ($c in $children) {
                Write-Output "  CHILD pid=$($c.ProcessId) name=$($c.Name) path=$($c.ExecutablePath) cmd=$($c.CommandLine)"
                Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue
            }
            Stop-Process -Id $($p.Id) -Force -ErrorAction SilentlyContinue
            if ($parentId -and $parentId -ne 0) { Stop-Process -Id $parentId -Force -ErrorAction SilentlyContinue }
            Write-Output "  KILLED pid=$($p.Id) and parent_pid=$parentId"
        }
    }
}
'
while true; do
  out="$(powershell.exe -NoProfile -NonInteractive -Command "$PS" 2>&1)"
  if [ -n "$out" ]; then
    ts="$(date -Is)"
    echo "[$ts] $out" | tee -a "$LOG"
  fi
  sleep 3
done
