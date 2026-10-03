#!/usr/bin/env bash
# Go2 학습 PC 감시 — 튜닝 진행상황과 GPU 이상(다른 프로그램의 GPU 점유, 속도 저하, VRAM 부족, 멈춤)을 기록한다.
# 보고만 한다. 어떤 프로세스도 끄지 않고, 학습·평가 파일을 바꾸지 않는다. 실행 시간에 상한이 있다.
#
# 사용:
#   bash tools/go2_gpu_watch.sh [--hours 10] [--interval 60] [--keep /workspace/_keep]
#        [--pattern 'go2_g_a060_pc2_*'] [--out DIR] [--allow REGEX] [--base-iter-s S] [--once]
#   --hours        최대 감시 시간(기본 10). 끝나면 스스로 종료한다.
#   --interval     확인 간격 초(기본 60).
#   --pattern      감시할 회수 폴더 이름 패턴(기본 go2_g_a060_pc2_*). 학습 로그 logs/candidate_training.log 를 읽는다.
#   --out          기록 폴더(기본 $KEEP/go2_gpu_watch).
#   --allow        GPU 를 써도 되는 프로세스 이름 정규식(기본 python|kit|isaac). 그 밖은 FOREIGN_GPU_PROCESS 경보.
#   --base-iter-s  정상 iteration 초. 생략하면 현재 학습의 iteration 6~25 중앙값을 기준으로 쓴다.
#   --once         한 번만 확인하고 끝낸다.
# 출력:
#   $OUT/WATCH.tsv   매 확인 한 줄(시간·GPU 사용률·VRAM·온도·전력·GPU 프로세스·학습 점·iteration·속도·ETA·경보)
#   $OUT/ALERTS.txt  경보만(같은 경보는 상태가 바뀔 때만 다시 적는다)
#   $OUT/GPU_PROCS.txt 마지막 확인의 GPU 프로세스 목록(PID·이름·VRAM·실행 파일 경로)
# 경보:
#   FOREIGN_GPU_PROCESS  허용 목록 밖 프로세스가 GPU 를 쓰고 있음(채굴기 등)
#   GPU_BUSY_NO_TRAINING 허용 프로세스가 없는데 GPU 사용률이 높음(목록에 안 잡히는 점유)
#   SLOWDOWN             최근 10 iteration 중앙값이 기준의 SLOW_RATIO(1.3)배 초과
#   VRAM_HIGH            VRAM 사용 95% 이상(4096 env 학습이 메모리 부족으로 죽을 수 있음)
#   STALL                학습·평가 로그가 STALL_MIN(20)분 동안 갱신되지 않음
#   NVIDIA_SMI_FAILED    nvidia-smi 실행 실패(query-gpu 또는 query-compute-apps — 실패를 빈 목록으로 보지 않는다)
#   MULTI_GPU_UNSUPPORTED GPU 가 여러 개 — 첫 장치만 보므로 전체 감시가 아니다(단일 GPU 전용)
# 종료 코드: 0 정상 종료(시간 상한 또는 --once), 64 인자 오류. 경보가 있어도 0 이다(감시 도구이므로).
# 테스트용: NVSMI 환경변수로 nvidia-smi 대신 다른 실행 파일을 쓸 수 있다.
set -uo pipefail

HOURS=10; INTERVAL=60; KEEP=/workspace/_keep; PATTERN='go2_g_a060_pc2_*'; OUT=""; ALLOW='python|kit|isaac'
BASE_ITER_S=""; ONCE=0
SLOW_RATIO=${GO2_WATCH_SLOW_RATIO:-1.3}; STALL_MIN=${GO2_WATCH_STALL_MIN:-20}; BUSY_UTIL=${GO2_WATCH_BUSY_UTIL:-30}
VRAM_FRAC=${GO2_WATCH_VRAM_FRAC:-0.95}; NVSMI=${NVSMI:-nvidia-smi}

usage() { sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'; }
need() { [[ $# -ge 2 ]] || { echo "$1 needs a value" >&2; exit 64; }; }  # 값 없는 옵션은 반복하지 않고 64(§27 R3)
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hours|--interval|--keep|--pattern|--out|--allow|--base-iter-s) need "$@" ;;
  esac
  case "$1" in
    --hours) HOURS=${2:-}; shift 2 ;;
    --interval) INTERVAL=${2:-}; shift 2 ;;
    --keep) KEEP=${2:-}; shift 2 ;;
    --pattern) PATTERN=${2:-}; shift 2 ;;
    --out) OUT=${2:-}; shift 2 ;;
    --allow) ALLOW=${2:-}; shift 2 ;;
    --base-iter-s) BASE_ITER_S=${2:-}; shift 2 ;;
    --once) ONCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 64 ;;
  esac
done
num() { [[ "$1" =~ ^[0-9]+([.][0-9]+)?$ ]]; }
for v in "$HOURS" "$INTERVAL"; do num "$v" || { echo "--hours/--interval must be numbers" >&2; exit 64; }; done
[[ -z "$BASE_ITER_S" ]] || num "$BASE_ITER_S" || { echo "--base-iter-s must be a number" >&2; exit 64; }
[[ -d "$KEEP" ]] || { echo "keep dir not found: $KEEP" >&2; exit 64; }
OUT=${OUT:-$KEEP/go2_gpu_watch}
mkdir -p "$OUT"
TSV="$OUT/WATCH.tsv"; ALERTS="$OUT/ALERTS.txt"
[[ -s "$TSV" ]] || printf 'time\tgpu_util\tvram_used_mb\tvram_total_mb\ttemp_c\tpower_w\tgpu_procs\tforeign\tpoint\titer\titer_total\titer_s_recent\titer_s_base\teta\tlog_age_min\talerts\n' >"$TSV"

exe_path() {  # PID -> 실행 파일 경로(가능하면)
  local pid=$1
  if [[ -e "/proc/$pid/exe" ]] && readlink "/proc/$pid/exe" >/dev/null 2>&1; then readlink "/proc/$pid/exe"; return; fi
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "(Get-Process -Id $pid -ErrorAction SilentlyContinue).Path" 2>/dev/null | tr -d '\r'
  fi
}

median() { sort -g | awk '{a[NR]=$1} END{if(NR==0){print ""; exit} m=(NR%2)?a[(NR+1)/2]:(a[NR/2]+a[NR/2+1])/2; printf "%.2f", m}'; }

LAST_ALERTS=$(cat "$OUT/.last_alerts" 2>/dev/null || true)  # 재시작해도 같은 경보를 다시 적지 않는다
check() {
  local now alerts=() gpu util vu vt temp pw procs n_procs=0 foreign=0 allowed=0 n_gpu=0 procs_failed=0
  now=$(date -Is)
  # --- GPU ---
  if gpu=$("$NVSMI" --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw \
             --format=csv,noheader,nounits 2>/dev/null | tr -d '\r ') && [[ -n "$gpu" ]]; then
    n_gpu=$(grep -c . <<<"$gpu")
    IFS=, read -r util vu vt temp pw <<<"$(head -1 <<<"$gpu")"
    # 단일 GPU 전용이다. 여러 장치면 첫 장치만 보므로 전체 감시로 기록하지 않는다(§27 R2).
    (( n_gpu > 1 )) && alerts+=("MULTI_GPU_UNSUPPORTED gpus=$n_gpu (first device only)")
  else
    util=NA; vu=NA; vt=NA; temp=NA; pw=NA; alerts+=("NVIDIA_SMI_FAILED query-gpu")
  fi
  # 프로세스 조회 실패를 '빈 목록'과 구분한다(§27 R1).
  if ! procs=$("$NVSMI" --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits 2>/dev/null | tr -d '\r'); then
    procs=""; procs_failed=1; alerts+=("NVIDIA_SMI_FAILED query-compute-apps")
  fi
  : >"$OUT/GPU_PROCS.txt"
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    local pid name mem base
    pid=$(awk -F', *' '{print $1}' <<<"$line"); mem=$(awk -F', *' '{print $NF}' <<<"$line")
    name=$(sed -E 's/^[^,]*, *//; s/, *[^,]*$//' <<<"$line")
    base=$(basename "${name//\\//}")
    n_procs=$((n_procs + 1))
    if grep -Eiq "$ALLOW" <<<"$base"; then
      allowed=$((allowed + 1)); printf 'OK\t%s\t%s\t%s\t%s\n' "$pid" "$name" "$mem" "$(exe_path "$pid")" >>"$OUT/GPU_PROCS.txt"
    else
      foreign=$((foreign + 1)); printf 'FOREIGN\t%s\t%s\t%s\t%s\n' "$pid" "$name" "$mem" "$(exe_path "$pid")" >>"$OUT/GPU_PROCS.txt"
      alerts+=("FOREIGN_GPU_PROCESS pid=$pid name=$base vram_mb=$mem")
    fi
  done <<<"$procs"
  if num "$util" && (( ${util%.*} >= BUSY_UTIL )) && (( allowed == 0 )) && (( procs_failed == 0 )); then
    alerts+=("GPU_BUSY_NO_TRAINING util=${util}%")
  fi
  if num "$vu" && num "$vt" && awk -v u="$vu" -v t="$vt" -v f="$VRAM_FRAC" 'BEGIN{exit !(t>0 && u/t>=f)}'; then
    alerts+=("VRAM_HIGH ${vu}/${vt}MB")
  fi
  # --- 학습 진행 ---
  local log="" point=- it=- tot=- recent=- base=- eta=- age=-
  log=$(ls -t "$KEEP"/$PATTERN/logs/candidate_training.log 2>/dev/null | head -1)
  if [[ -n "$log" ]]; then
    point=$(basename "$(dirname "$(dirname "$log")")")
    local last times
    last=$(grep -aoE 'Learning iteration [0-9]+/[0-9]+' "$log" | tail -1)
    if [[ -n "$last" ]]; then it=${last#Learning iteration }; tot=${it#*/}; it=${it%/*}; fi
    times=$(grep -aoE 'Iteration time: [0-9.]+s' "$log" | grep -oE '[0-9.]+' )
    eta=$(grep -aoE 'ETA: [0-9:]+' "$log" | tail -1 | awk '{print $2}'); eta=${eta:--}
    recent=$(tail -n 10 <<<"$times" | median); recent=${recent:--}
    if [[ -n "$BASE_ITER_S" ]]; then base=$BASE_ITER_S
    elif (( $(grep -c . <<<"$times") >= 25 )); then base=$(sed -n '6,25p' <<<"$times" | median)
    fi
    base=${base:--}
    if num "$recent" && num "$base" && (( $(grep -c . <<<"$times") >= 35 || ${#BASE_ITER_S} > 0 )) \
       && awk -v r="$recent" -v b="$base" -v k="$SLOW_RATIO" 'BEGIN{exit !(r>b*k)}'; then
      alerts+=("SLOWDOWN point=$point iter_s=${recent} base=${base}")
    fi
  fi
  # 멈춤: 학습 로그·러너 로그 중 가장 최근 갱신
  local newest
  newest=$(ls -t "$KEEP"/$PATTERN/logs/*.log "$KEEP"/go2_g_a060_pc2_points/logs/*.log "$KEEP"/go2_g_a060_pc2_points/point.log 2>/dev/null | head -1)
  if [[ -n "$newest" ]]; then
    age=$(( ( $(date +%s) - $(date -r "$newest" +%s) ) / 60 ))
    if (( age >= STALL_MIN )); then
      local done_note=""
      [[ -f "$KEEP/go2_g_a060_pc2_points/POINT_STATUS.tsv" ]] && done_note=$(tail -1 "$KEEP/go2_g_a060_pc2_points/POINT_STATUS.tsv" | cut -f1,2 | tr '\t' ':')
      alerts+=("STALL no log update ${age}min (last status ${done_note:-none})")
    fi
  fi
  local joined; joined=$(IFS='|'; echo "${alerts[*]:-}")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$now" "$util" "$vu" "$vt" "$temp" "$pw" \
    "$n_procs" "$foreign" "$point" "$it" "$tot" "$recent" "$base" "$eta" "$age" "${joined:--}" >>"$TSV"
  # 경보 이름만 비교해 상태가 바뀔 때 적는다(값이 매번 조금씩 달라도 같은 경보를 반복하지 않는다)
  local kinds; kinds=$(for a in "${alerts[@]:-}"; do echo "${a%% *}"; done | sort -u | tr '\n' ' ')
  if [[ "$kinds" != "$LAST_ALERTS" ]]; then
    if [[ -n "${kinds// /}" ]]; then printf '%s\tALERT\t%s\n' "$now" "$joined" >>"$ALERTS"
    elif [[ -n "${LAST_ALERTS// /}" ]]; then printf '%s\tCLEARED\t%s\n' "$now" "$LAST_ALERTS" >>"$ALERTS"; fi
    LAST_ALERTS=$kinds; printf '%s' "$kinds" >"$OUT/.last_alerts"
  fi
  echo "[$now] gpu=${util}% vram=${vu}/${vt}MB procs=$n_procs foreign=$foreign point=$point iter=$it/$tot iter_s=$recent base=$base eta=$eta alerts=${joined:-none}"
}

end=$(( $(date +%s) + $(awk -v h="$HOURS" 'BEGIN{printf "%d", h*3600}') ))
while :; do
  check
  (( ONCE )) && break
  (( $(date +%s) + ${INTERVAL%.*} > end )) && break
  sleep "${INTERVAL%.*}"
done
exit 0
