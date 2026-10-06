#!/usr/bin/env bash
# GO2 PC2 리소스/이상 프로세스 감시 (2026-10-03)
# 짐작(=="Isaac Lab 버그") 대신 실측으로 판단한다:
#   1) GPU를 쓰는 프로세스가 우리가 아는 학습/평가 python인지 확인
#   2) 서비스 없는 svchost(가짜 svchost 패턴) 재발 감시
#   3) 학습/평가 로그가 멈췄는데 해당 프로세스는 살아있는지(진짜 멈춤 vs 느림 구분)
# 상태는 매 주기 로그 파일에 쌓고, 이상 신호만 stdout에 찍어 Monitor가 바로 알리게 한다.
set -uo pipefail

NVSMI="/c/Windows/System32/DriverStore/FileRepository/nv_dispig.inf_amd64_f4c7a2fd13e0f763/nvidia-smi.exe"
LOG=/c/dev/NConnect/workspace/_keep/go2_g_a060_pc2_resource_monitor.log
POINT_LOG_DIR=/c/workspace/_keep/go2_g_a060_pc2_points/logs
KNOWN_RE='isaaclab_venv|uv.python.cpython'
STALL_THRESHOLD_S=180
INTERVAL_S=20

mkdir -p "$(dirname "$LOG")"

latest_point_log() { ls -t "$POINT_LOG_DIR"/*.log 2>/dev/null | head -1; }

check_fake_svchost() {
  powershell.exe -NoProfile -Command '
    # Query services once.  The former per-svchost Get-CimInstance call could
    # block a monitor cycle for minutes, defeating the 20-second cadence.
    $servicePids = [System.Collections.Generic.HashSet[int]]::new()
    Get-CimInstance Win32_Service | ForEach-Object {
      if ($_.ProcessId -gt 0) { [void] $servicePids.Add([int] $_.ProcessId) }
    }
    $bad = @(Get-Process svchost -ErrorAction SilentlyContinue |
      Where-Object { -not $servicePids.Contains([int] $_.Id) } |
      ForEach-Object Id)
    if ($bad.Count -gt 0) { Write-Output ($bad -join ",") }
  ' 2>/dev/null | tr -d '\r'
}

while true; do
  ts=$(date -Is)

  gpu_line=$("$NVSMI" --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader 2>/dev/null)
  apps=$("$NVSMI" --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>/dev/null)

  echo "[$ts] GPU: $gpu_line" >> "$LOG"
  [[ -z "$apps" ]] || echo "[$ts] APPS: $apps" >> "$LOG"

  # 1) 알려진 패턴이 아닌 GPU 사용 프로세스
  if [[ -n "$apps" ]]; then
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      pid=$(echo "$line" | cut -d, -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      pname=$(echo "$line" | cut -d, -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
      if [[ -n "$pname" && "$pname" != "[Insufficient Permissions]" ]] && ! echo "$pname" | grep -qiE "$KNOWN_RE"; then
        echo "[$ts] [ANOMALY] 알 수 없는 GPU 사용 프로세스 pid=$pid name=$pname -> 종료 시도"
        powershell.exe -NoProfile -Command "Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue" 2>/dev/null
        echo "[$ts] [KILLED] pid=$pid"
      fi
    done <<< "$apps"
  fi

  # 2) 서비스 없는 svchost(가짜 svchost) 재발 감시
  bad_svchost=$(check_fake_svchost)
  if [[ -n "$bad_svchost" ]]; then
    echo "[$ts] [ANOMALY] 서비스 없는 svchost 발견: PID $bad_svchost -> 자식 포함 종료 시도"
    for bpid in $(echo "$bad_svchost" | tr ',' ' '); do
      powershell.exe -NoProfile -Command "
        Get-CimInstance Win32_Process -Filter \"ParentProcessId=$bpid\" | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }
        Stop-Process -Id $bpid -Force -ErrorAction SilentlyContinue
      " 2>/dev/null
      echo "[$ts] [KILLED] svchost pid=$bpid (+children)"
    done
  fi

  # 3) 학습/평가 로그 정체 감시 (프로세스는 살아있는데 로그가 멈춘 경우만 신호)
  plog=$(latest_point_log)
  if [[ -n "$plog" ]]; then
    now_epoch=$(date +%s)
    mtime_epoch=$(stat -c %Y "$plog" 2>/dev/null || echo "$now_epoch")
    age=$(( now_epoch - mtime_epoch ))
    alive=$(pgrep -f 'train\.py|play\.py|go2_g_a060_pc2_run_chain' 2>/dev/null | head -1)
    if [[ "$age" -gt "$STALL_THRESHOLD_S" && -n "$alive" ]]; then
      echo "[$ts] [STALL] $plog 가 ${age}s 동안 갱신 안 됨 (프로세스는 살아있음, pid=$alive) — GPU util=$gpu_line"
    fi
  fi

  sleep "$INTERVAL_S"
done
