"""G-A036 — 회수된 체크포인트를 현 계측으로 일괄 재평가하는 패키지. 학습 0.

왜 이 회차인가. 70점 축의 전수 평가는 3건뿐이다(Pilot-01 · A017 · G-A033). 그래서
"커리큘럼 도달 → 70점" 고리를 검증할 수 없다(종합 §11-4). 그런데 학습된 정책 15개가
체크포인트로 `_keep`에 전부 남아 있다. **학습 시간 0으로 점을 3개에서 18개로 늘릴 수 있다.**

핀은 회차마다 다르다(700·800·900·999). 이 회차는 그걸 맞추려 하지 않는다 — 맞출 수 없다.
서버에 남아 있던 다른 체크포인트는 회수되지 않았다. 대신 **각 정책의 점수를 그 체크포인트와
같은 iteration의 `terrain`과 짝지어** 기록한다. 그러면 핀 차이는 교란이 아니라 x축의 폭이 된다.

러너는 새로 쓰지 않는다. 서버에서 이미 완주한 `server_run_go2_a017_full_suite.sh`의 본문을
그대로 쓰고, arm 목록만 매니페스트로 바꾼다. 바뀌는 곳은 아래 SUBSTITUTIONS 넷뿐이고
계약 테스트가 그 넷 말고는 한 글자도 다르지 않음을 검사한다.

    python tools/build_go2_reeval_package.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
KEEP = ROOT / "workspace" / "_keep"
sys.path.insert(0, str(ROOT / "tools"))

from go2_run_ledger import harvest, terrain_at  # noqa: E402

WORK = "G-A036"
SOURCE_RUNNER = GO2 / "server_run_go2_a017_full_suite.sh"
RUNNER = "server_run_go2_reeval.sh"
OUTPUT = GO2 / "go2_reeval.zip"
PREFIX = Path("go2_reeval")
FIXED_TIMESTAMP = (2026, 9, 16, 0, 0, 0)
SECONDS_PER_CASE = 23.7      # G-A033 캠페인 실측: 74 case 28.9분
CASES_PER_POLICY = 69

# 이미 현 계측(v2)에서 69 case 전수 평가를 받은 정책. 다시 재지 않는다.
ALREADY_MEASURED = {
    "c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d",  # Pilot-01
    "0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4",  # A017 iter900
    "ccd60e192bf4ec900a269cc264d7739a4962a4ce07a0c3607568346778646044",  # G-A033 iter900
}

# 검증된 러너 본문에서 바꾸는 곳. 이 넷 말고는 바꾸지 않는다.
SUBSTITUTIONS = (
    ('bash server_run_go2_a017_full_suite.sh --inner',
     f'bash {RUNNER} --inner'),
    ('[[ -d "$TRAIN_ROOT" && -d "$A017_ROOT" && -d "$PILOT_ROOT" && -s "$REGISTRY" ]] || {',
     '[[ -s "$MANIFEST" && -s "$REGISTRY" ]] || {'),
    ('echo "[DONE_MARKER] [DONE] GO2_A017_FULL_SUITE_RESULT_READY"',
     'echo "[DONE_MARKER] [DONE] GO2_REEVAL_RESULT_READY"'),
    ('sha256sum "$A017_ROOT/go2_eval_telemetry.py" >"$KEEP/meta/evaluator.sha256"',
     'sha256sum "$PACKAGE_ROOT/arm0/go2_eval_telemetry.py" >"$KEEP/meta/evaluator.sha256"'),
)

CORE_START = "package_result() {"
CORE_END = "\nSCENARIO_CASE=("


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files() -> list[Path]:
    files = [GO2 / name for name in
             ("train.py", "play.py", "pyproject.toml", "go2_eval_telemetry.py",
              "go2_policy_lineage.py", "quadruped_rewards.py")]
    files.extend(sorted((GO2 / "go2_task").glob("*.py")))
    return files


def candidates() -> list[dict[str, Any]]:
    """재평가 대상. 같은 정책이 두 디렉터리에 있으면 한 번만 싣는다."""
    picked: dict[str, dict[str, Any]] = {}
    for record in harvest():
        run_dir = ROOT / record["path"]
        models = [p for p in run_dir.rglob("model_*.pt")
                  if "by_reward" not in p.name and "baseline" not in p.name]
        if not models:
            continue
        # iter 900을 선호한다 — 이미 측정된 A017·G-A033이 그 핀이라 비교가 늘어난다.
        model = sorted(models, key=lambda p: (p.name != "model_900.pt", p.name))[0]
        digest = sha(model.read_bytes())
        if digest in ALREADY_MEASURED or digest in picked:
            continue
        found = re.search(r"model_(\d+)", model.name)
        iteration = int(found.group(1)) if found else None
        log = record.get("training", {}).get("log")
        env = run_dir.rglob("env.yaml")
        picked[digest] = {
            "run": record["run"],
            "checkpoint": model.relative_to(ROOT).as_posix(),
            "iteration": iteration,
            "model_sha256": digest,
            "terrain_at_pin": terrain_at(ROOT / log, iteration) if log and iteration else None,
            "env": next((p.relative_to(ROOT).as_posix() for p in env), None),
            "rewards": record.get("rewards", {}),
        }
    return list(picked.values())


def anchors() -> list[tuple[str, int, float]]:
    """이미 69 case v2로 잰 정책들의 (회차, 평가 iteration, 그 iteration의 terrain).

    예전에는 `[4.2503, 4.7087]`을 "A017·G-A033 iter900"이라는 주석과 함께 적어 넣었다.
    그 둘은 iter 999 값이었다(@900은 3.4268·4.4937).  짝짓기가 이 회차의 전제인데
    기준점만 짝이 어긋나 있었다.  그래서 체크포인트 SHA로 정책을 찾고, 그 파일 이름에서
    iteration을 읽고, 같은 iteration의 로그 값을 쓴다.  학습 로그가 없는 정책(Pilot-01)은
    기준점이 될 수 없으므로 빠진다.
    """
    found: dict[str, tuple[str, int, float]] = {}
    for record in harvest():
        log = record.get("training", {}).get("log")
        if not log:
            continue
        run_dir = ROOT / record["path"]
        for model in sorted(run_dir.rglob("model_*.pt")):
            hit = re.search(r"model_(?:iter)?(\d+)\.pt$", model.name)
            if not hit:
                continue
            digest = sha(model.read_bytes())
            if digest not in ALREADY_MEASURED or digest in found:
                continue
            value = terrain_at(ROOT / log, int(hit.group(1)))
            if value is not None:
                found[digest] = (record["run"], int(hit.group(1)), value)
    return sorted(found.values())


def order_by_information(arms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """예산이 중간에 끊겨도 가장 쓸모 있는 점이 남도록 고른다.

    다음 점의 가치는 '이미 가진 점들에서 가장 멀리 떨어져 있는가'다. 매번 가장 먼 것을
    하나씩 집는다.  이미 가진 점은 `anchors()`가 산출물에서 읽는다 — 손으로 적지 않는다.
    """
    have = [value for _run, _iteration, value in anchors()]
    remaining = [a for a in arms if a["terrain_at_pin"] is not None]
    tail = [a for a in arms if a["terrain_at_pin"] is None]
    ordered = []
    while remaining:
        best = max(remaining, key=lambda a: min(abs(a["terrain_at_pin"] - h) for h in have))
        remaining.remove(best)
        have.append(best["terrain_at_pin"])
        ordered.append(best)
    return ordered + tail


def build_runner(arms: list[dict[str, Any]]) -> str:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    core = text[text.index(CORE_START): text.index(CORE_END)]
    for old, new in SUBSTITUTIONS:
        if old not in core:
            raise RuntimeError(f"검증된 러너에 없는 치환 대상: {old[:60]}")
        core = core.replace(old, new)

    prelude = text[text.index("ISAACLAB_SH=${ISAACLAB_SH:-"): text.index("A017_EXPECTED_SHA=")]
    evaluator = re.search(r"^EVALUATOR_SHA=.*$", text, re.M).group(0)

    head = f"""#!/usr/bin/env bash
# One upload -> one command -> one result ZIP.  NO TRAINING, NO REWARD CHANGE.
#
# {WORK} "회수 체크포인트 일괄 재평가".
#
# 70점 축의 전수 평가가 3건뿐이라 "커리큘럼 도달 -> 점수" 고리를 검증할 수 없다.
# 학습된 정책 {len(arms)}개가 이미 체크포인트로 남아 있으므로, 학습 없이 재평가만으로
# 점을 3개에서 {len(arms) + 3}개로 늘린다.
#
# 각 정책의 핀은 회차마다 다르다(700/800/900/999).  맞추지 않는다 -- 서버에 있던 다른
# 체크포인트는 회수되지 않았다.  대신 매니페스트가 정책마다 그 체크포인트와 **같은
# iteration의 terrain**을 들고 다니므로, 핀 차이는 교란이 아니라 x축의 폭이 된다.
#
# 본문은 서버에서 이미 완주한 server_run_go2_a017_full_suite.sh 그대로다.  arm 목록만
# 매니페스트로 바뀌었고, 바뀐 곳은 {len(SUBSTITUTIONS)}군데이며 계약 테스트가 검사한다.
#
# 예산: GO2_REEVAL_BUDGET_MIN 분이 지나면 남은 arm을 건너뛰고 가진 것만 포장한다.
#       기본값 0 = 제한 없음.  arm 순서는 정보량 순이라 중간에 끊겨도 가장 먼 점이 남는다.
set -euo pipefail

PACKAGE_ROOT=${{PACKAGE_ROOT:-/workspace/go2_reeval}}
MANIFEST="$PACKAGE_ROOT/arms.json"
REGISTRY="$PACKAGE_ROOT/go2_self_eval_registry.json"
KEEP=/workspace/_keep/go2_reeval
RESULT_ZIP=/workspace/_keep/GO2_REEVAL_RESULT.zip
TMUX_NAME=go2_reeval
SEEDS=(101 202 303)
EVAL_STEPS=${{GO2_EVAL_STEPS:-1000}}
VIDEO_STEPS=${{GO2_VIDEO_STEPS:-500}}
RESUME=${{GO2_RESUME:-0}}
BUDGET_MIN=${{GO2_REEVAL_BUDGET_MIN:-0}}
ARM_COUNT={len(arms)}

{prelude}{evaluator}

"""

    tail = f"""
START_EPOCH=$(date +%s)
DONE_ARMS=0
SKIPPED_ARMS=0

for ((i = 0; i < ARM_COUNT; i++)); do
  label=$("${{PY[@]}}" -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["label"])' "$MANIFEST" "$i")
  expected=$("${{PY[@]}}" -c 'import json,sys; print(json.load(open(sys.argv[1]))[int(sys.argv[2])]["model_sha256"])' "$MANIFEST" "$i")
  root="$PACKAGE_ROOT/arm$i"

  if (( BUDGET_MIN > 0 )); then
    elapsed_min=$(( ($(date +%s) - START_EPOCH) / 60 ))
    # 남은 예산이 한 arm(약 {int(CASES_PER_POLICY * SECONDS_PER_CASE / 60)}분)을 못 채우면 시작하지 않는다.
    # 반쯤 측정된 arm은 69 case가 아니라서 어차피 70점 축에 못 올린다.
    if (( elapsed_min + {int(CASES_PER_POLICY * SECONDS_PER_CASE / 60)} > BUDGET_MIN )); then
      echo "[BUDGET] stop before arm $i ($label): ${{elapsed_min}}min used of ${{BUDGET_MIN}}min"
      SKIPPED_ARMS=$(( ARM_COUNT - i ))
      break
    fi
  fi

  echo "[PHASE $((i + 1))/$ARM_COUNT] full {CASES_PER_POLICY}-case suite on $label (no training)"
  run_full_suite "$label" "$root" "$root/policy/model.pt" "$root/policy/env.yaml" "$expected"
  DONE_ARMS=$(( DONE_ARMS + 1 ))
done

echo '[PACKAGING] one-file result'
cp -a "$MANIFEST" "$KEEP/meta/arms.json"
printf 'RUNNER_RC=0\\nCOMPLETED_AT=%s\\nWORK_ID={WORK}\\nRUN_ID=eval_260916-Go2_reeval\\nTRAINING=none\\nARMS_PLANNED=%s\\nARMS_MEASURED=%s\\nARMS_SKIPPED=%s\\nBUDGET_MIN=%s\\nEVALUATOR=posture_gate_v2\\nEVALUATOR_SHA=%s\\nTELEMETRY_SCHEMA=6\\nVIDEO_STATUS=VIDEO_NOT_REQUESTED\\nOFFICIAL_RESULT=OFFICIAL_RESULT_UNMEASURED\\n' \\
  "$(date -Is)" "$ARM_COUNT" "$DONE_ARMS" "$SKIPPED_ARMS" "$BUDGET_MIN" "$EVALUATOR_SHA" >"$KEEP/RUNNER_STATUS.txt"
package_result FULL
trap - EXIT
echo '[DONE] GO2_REEVAL_RESULT_READY'
"""
    return head + core + tail


def manifest(arms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "label": f"arm{i}_{a['run'].replace('go2_', '')[:40]}",
        "run": a["run"],
        "checkpoint": a["checkpoint"],
        "iteration": a["iteration"],
        "model_sha256": a["model_sha256"],
        "terrain_at_pin": a["terrain_at_pin"],
        "rewards": a["rewards"],
    } for i, a in enumerate(arms)]


def readme(arms: list[dict[str, Any]], entries: list[dict[str, Any]]) -> str:
    minutes = CASES_PER_POLICY * SECONDS_PER_CASE / 60
    lines = [
        f"{WORK} 회수 체크포인트 일괄 재평가 — 학습 0",
        "",
        "  cd /workspace && unzip -o GO2_REEVAL.zip && cd go2_reeval && bash " + RUNNER,
        "",
        f"정책 {len(arms)}개 x {CASES_PER_POLICY} case x {SECONDS_PER_CASE}s "
        f"= 약 {len(arms) * minutes / 60:.1f}시간. arm 하나당 약 {minutes:.0f}분.",
        "예산을 걸려면 GO2_REEVAL_BUDGET_MIN=<분>. arm 순서가 정보량 순이라 중간에",
        "끊겨도 이미 가진 점(terrain " + "·".join(f"{v:.4f}@{i}" for _r, i, v in anchors())
        + ")에서 가장 먼 점부터 채워진다.",
        "",
        "arm 순서와 짝지은 커리큘럼 도달:",
        "",
    ]
    for i, entry in enumerate(entries):
        pin = "—" if entry["terrain_at_pin"] is None else f"{entry['terrain_at_pin']:.4f}"
        lines.append(f"  {i:2d}  {entry['run'].replace('go2_', '')[:42]:42s} "
                     f"iter {entry['iteration']:<4} terrain {pin}")
    lines += [
        "",
        "결과는 정책마다 69 case의 summary.json이다. 로컬에서",
        "  python tools/go2_run_ledger.py  로 재채점하고",
        "  python tools/build_go2_run_reports.py  로 보고서를 다시 생성한다.",
        "",
        "이 회차는 reward를 바꾸지 않고 학습도 하지 않는다. 전부 회수된 체크포인트의 재생이다.",
        "",
    ]
    return "\n".join(lines)


def build_payload() -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    arms = order_by_information(candidates())
    entries = manifest(arms)
    payload: dict[str, bytes] = {}

    for i, arm in enumerate(arms):
        for path in source_files():
            payload[f"arm{i}/{path.relative_to(GO2).as_posix()}"] = path.read_bytes()
        # `stage_policy`가 arm 루트의 `exported/`를 통째로 지우고 다시 만든다.
        # 그래서 원본은 반드시 `exported/` 밖에 둔다 — 안에 두면 복사 전에 사라진다.
        payload[f"arm{i}/policy/model.pt"] = (ROOT / arm["checkpoint"]).read_bytes()
        if not arm["env"]:
            raise RuntimeError(f"{arm['run']}: env.yaml이 회수되지 않아 평가할 수 없다")
        payload[f"arm{i}/policy/env.yaml"] = (ROOT / arm["env"]).read_bytes()

    payload["arms.json"] = json.dumps(entries, indent=1, ensure_ascii=False).encode("utf-8")
    payload["go2_self_eval_registry.json"] = (GO2 / "config/go2_self_eval_registry.json").read_bytes()
    for name in ("package_go2_result.py", "posture_contract_check.py"):
        payload[name] = (GO2 / name).read_bytes()
    payload[RUNNER] = build_runner(arms).encode("utf-8")
    payload["README.txt"] = readme(arms, entries).encode("utf-8")

    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PACKAGE_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload, entries


def build() -> tuple[Path, list[dict[str, Any]]]:
    payload, entries = build_payload()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo((PREFIX / name).as_posix(), FIXED_TIMESTAMP)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            archive.writestr(info, payload[name])
    return OUTPUT, entries


def main() -> int:
    path, entries = build()
    data = path.read_bytes()
    minutes = CASES_PER_POLICY * SECONDS_PER_CASE / 60
    print(f"{path.relative_to(ROOT)}  {len(data) / 1e6:.1f} MB  sha256 {sha(data)[:16]}…")
    print(f"정책 {len(entries)}개 · 학습 0 · 견적 {len(entries) * minutes / 60:.1f}시간 "
          f"(arm당 약 {minutes:.0f}분)")
    have = "·".join(f"{v:.4f}@{i}" for _r, i, v in anchors())
    print(f"\narm 순서 (정보량 순 — 이미 가진 terrain {have}에서 먼 것부터):")
    for i, entry in enumerate(entries):
        pin = "—" if entry["terrain_at_pin"] is None else f"{entry['terrain_at_pin']:7.4f}"
        print(f"  {i:2d}  terrain {pin}  iter {str(entry['iteration']):<4} "
              f"{entry['run'].replace('go2_', '')[:44]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
