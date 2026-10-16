#!/usr/bin/env bash
# PC2가 올린 결과 archive를 받아 _keep에 풀고, 받을 때마다 로컬 용량을 정리한다 (2026-10-05 사용자 지시).
#
#   bash tools/keep_fetch_result.sh GO2_G_A063_PC2_S08_FEET_AIR_TIME_P0P5_RESULT.zip [--verify-only]
#
# 1. parts(.000/.001 시작 모두)와 .sha256을 GitHub에서 직접 받는다. git을 거치지 않으므로 .git에 사본이 남지 않는다.
# 2. 이어 붙인 ZIP의 sha256을 manifest와 대조한다(대소문자 무시). 불일치면 아무것도 풀지 않고 멈춘다.
# 3. _keep에 압축을 푼다(백슬래시 경로 처리, 경로 탈출 거부).
# 4. ZIP·parts를 지운다(원본은 원격 parts에 있다, ARTIFACT_MANAGEMENT.md 6-a).
# 5. 압축 해제 폴더를 NTFS LZX로 압축한다(도구 입력이라 지우지 않는다).
# 6. 남은 임시 파일(*.tmp, 중단된 fetch의 tmp_pack_*)을 지우고 여유 공간 전후를 출력한다.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
KEEP="$ROOT/workspace/_keep"
REPO=OpenUM929/NConnect
BASE="${1:?archive name, e.g. GO2_G_A063_PC2_S08_..._RESULT.zip}"
MODE="${2:-}"
free_gb() { df -BM /c | awk 'NR==2{printf "%.1f", $4/1024}'; }
echo "[free before] $(free_gb) GB"

TOK=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
[ -n "$TOK" ] || { echo "no github credential" >&2; exit 2; }
# 2026-10-16: the local .git was removed (git is used for sharing only); ask the remote directly.
REF=$(git ls-remote "https://github.com/$REPO.git" refs/heads/master | cut -f1)
get() {  # get <repo path> <out file> -> http code
  curl -sS --retry 3 --max-time 1800 -o "$2" -w '%{http_code}' -H "Authorization: token $TOK" \
    "https://raw.githubusercontent.com/$REPO/$REF/$1"
}

WORK=$(mktemp -d "$KEEP/.fetch_XXXX")
trap 'rm -rf "$WORK"' EXIT
[ "$(get "workspace/_keep/$BASE.sha256" "$WORK/m")" = 200 ] || { echo "manifest not on remote: $BASE" >&2; exit 3; }
want=$(cut -d' ' -f1 "$WORK/m" | tr 'A-F' 'a-f')
: > "$WORK/z"
n=0; got=0
while :; do
  p=$(printf '%03d' "$n")
  code=$(get "workspace/_keep/$BASE.$p" "$WORK/part")
  if [ "$code" = 200 ]; then cat "$WORK/part" >> "$WORK/z"; got=$((got+1)); echo "  part .$p"
  elif [ "$n" = 0 ]; then :           # parts가 .001부터 시작
  else break; fi
  n=$((n+1)); [ "$n" -gt 60 ] && break
done
rm -f "$WORK/part"
[ "$got" -gt 0 ] || { echo "no parts on remote: $BASE" >&2; exit 3; }
have=$(sha256sum "$WORK/z" | cut -d' ' -f1)
[ "$have" = "$want" ] || { echo "SHA MISMATCH $BASE want=$want got=$have" >&2; exit 4; }
echo "[sha ok] $BASE ($got parts)"
[ "$MODE" = "--verify-only" ] && { echo "[verify-only] nothing extracted"; exit 0; }

cp "$WORK/m" "$KEEP/$BASE.sha256"
DIRS=$(cd "$KEEP" && python - "$WORK/z" <<'EOF'
import sys, zipfile, pathlib
z = zipfile.ZipFile(sys.argv[1]); tops = set()
for i in z.infolist():
    p = pathlib.Path(i.filename.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts:
        raise SystemExit(f"unsafe path {i.filename}")
    tops.add(p.parts[0])
    if i.filename.endswith(("/", "\\")):
        p.mkdir(parents=True, exist_ok=True); continue
    p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(z.read(i))
print("\n".join(sorted(tops)))
EOF
)
rm -f "$WORK/z"
echo "[extracted] $DIRS"
for d in $DIRS; do
  [ -d "$KEEP/$d" ] || continue
  head -2 "$KEEP/$d/RESULT_STATUS.txt" 2>/dev/null || true
  powershell -NoProfile -Command "compact /c /exe:lzx /s:'$(cygpath -w "$KEEP/$d")' /i /q | Out-Null"
done

# 정리: 남은 임시 파일, 중단된 fetch 임시 팩(git이 돌고 있지 않을 때만)
find "$KEEP" -maxdepth 1 \( -name '*.tmp' -o -name '*.rebuild.tmp' \) -delete
if ! tasklist 2>/dev/null | grep -qi '^git'; then
  for g in "$ROOT/.git"; do
    [ -d "$g/objects/pack" ] && find "$g/objects/pack" -maxdepth 1 -name 'tmp_pack_*' -delete
  done
fi
echo "[free after] $(free_gb) GB"
