#!/usr/bin/env python3
"""PC2 트랙 고정 탐색트리 — 노드 하나의 실행 패키지 빌더 (G-A061 예정, 2026-10-04).

설계: workspace/training/quadruped/upload/plan/GO2_TRACK_FIXED_SEARCH_TREE_20261003.md §12·§13 (Codex §37 APPROVE).
  - 빌드할 노드는 트리 진행 규칙(tools/go2_pc2_tree_readout.next_step)이 RUN 으로 낸 노드뿐이다. 부모 보상(이전 변수의
    승자)도 그 규칙이 낸 값을 쓴다. 손으로 노드·부모를 고르지 않는다.
  - G-A060 PC2 단일 점 패키지와 같은 방식: G-A055 v2 의 per-arm 러너·배포 코드·평가기·registry·G-A033 sentinel 을
    바이트 그대로 쓰고, 보상 파일·run_config.env·설명 파일만 바꾼다(R-6). 러너 run_point.sh 도 G-A060 과 같은 바이트다.
  - 배포 목록 밖 항(dof_torques_l2·dof_acc_l2)은 REWARD_WEIGHTS 에 한 줄을 추가한다(사용자 U1 승인, G-A053 과 같은 함수).
    expected_rewards.json candidate 에 두 항을 모두 적어 서버 env-rewards 검사가 학습 env.yaml 값을 확인하게 한다.
  - 노드마다 따로 빌드한다(한 ZIP·한 명령·한 결과). 같은 항·같은 값 시험 이력이 있으면 빌드를 거부한다(§1-3).

    python -B tools/build_go2_pc2_tree_package.py --tree-state <json> --check
    python -B tools/build_go2_pc2_tree_package.py --tree-state <json> --publish --work-id G-A061
"""
from __future__ import annotations

import argparse
import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))
import build_go2_a033_reward_package as a033  # noqa: E402  (add_env_reward_line)
import build_go2_g_a057_sweep_package as a057  # noqa: E402
import build_go2_pc2_point_package as pkg  # noqa: E402
import go2_pc2_tree_readout as tree  # noqa: E402
from go2_tuning_config import REWARD_NAMES, reward_dict, render_reward_source  # noqa: E402

PROVISIONAL_WORK_ID = "G-A061"
DESIGN = "workspace/training/quadruped/upload/plan/GO2_TRACK_FIXED_SEARCH_TREE_20261003.md"
FIXED_TIME = (2026, 10, 4, 0, 0, 0)
HISTORY_FILES = ("workspace/training/quadruped/reports/GO2_REWARD_TRIAL_REFERENCE.md", "GO2_REWARD_EVIDENCE_MASTER.md")


NUM_RE = re.compile(r"(?<![\w.])[-−+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-−+]?\d+)?(?![\w.])")


def numbers(text: str) -> list[float]:
    """경계가 있는 수 토큰만 정확한 수로 읽는다(§39-R3). '-0.00015' 는 하나의 수이고 '-0.0001' 의 접두사로 보지 않는다."""
    out = []
    for m in NUM_RE.finditer(text.replace("→", " ").replace("->", " ")):
        try:
            out.append(float(m.group(0).replace("−", "-")))
        except ValueError:
            pass
    return out


def same_value(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=0.0)


def folder_token(value: float) -> str:
    """이 빌더의 노드 key 값 표기: -1e-4 → m1e_4, -1.25e-7 → m1p25e_7, -5e-5 → m5e_5."""
    mant, exp = f"{abs(value):e}".split("e")
    mant = mant.rstrip("0").rstrip(".").replace(".", "p")
    sign = "m" if value < 0 else "p"
    e = int(exp)
    return f"{sign}{mant}e_{-e}" if e < 0 else f"{sign}{mant}e{e}"


def history_conflicts(var: str, value: float) -> list[str]:
    """같은 항·같은 값의 실행 이력(§1-3). 원장 표에서 그 항 이름이 든 칸의 수만 정확히 비교하고('미실행' 행 제외),
    _keep 폴더명은 이 빌더의 값 표기를 '_' 경계로 비교한다. 같은 항의 다른 값(트리 앞 노드 등)은 막지 않는다."""
    hits = [f"{rel}: {line[:90]}" for rel in HISTORY_FILES
            for line in (ROOT / rel).read_text(encoding="utf-8").splitlines() if line_hit(line, var, value)]
    hits += [f"_keep/{p.name}" for p in (ROOT / "workspace/_keep").iterdir() if folder_hit(p.name, var, value)]
    return hits


def line_hit(line: str, var: str, value: float) -> bool:
    """원장 표 한 행이 같은 항·같은 값의 실행 이력인가. '미실행' 행은 이력이 아니다."""
    stem = var.split("_l2")[0]
    if not line.startswith("| G-A") or "미실행" in line:
        return False
    return any(stem in cell and any(same_value(x, value) for x in numbers(cell.split(stem, 1)[1]))
               for cell in line.split("|"))


def folder_hit(name: str, var: str, value: float) -> bool:
    stem = var.split("_l2")[0]
    return bool(re.search(rf"{re.escape(stem)}(?:_l2)?_{re.escape(folder_token(value))}(?:_|$)", name))


def names(work_id: str, key: str) -> dict[str, str]:
    n = pkg.names(work_id)
    n["release"] = f"GO2_{n['up']}_PC2_TREE_{key}_v1"
    return n


def rewards(parent_changes: dict[str, float], var: str | None = None, value: float | None = None) -> dict[str, float]:
    """P0(A048 학습 보상 + 두 env 항 기본값) 위 부모 승자, 그 위 노드 변경."""
    w = {**pkg.base6(), "dof_torques_l2": tree.P0_REWARDS["dof_torques_l2"], "dof_acc_l2": tree.P0_REWARDS["dof_acc_l2"]}
    w.update(parent_changes)
    if var is not None:
        w[var] = float(value)
    return w


def render(template: str, w: dict[str, float]) -> str:
    src = render_reward_source(template, {k: w[k] for k in REWARD_NAMES})
    for k in tree.EXTRA_TERMS:
        if w[k] != tree.P0_REWARDS[k]:  # 기본값과 다른 env 항만 줄을 추가한다(부모 승자 포함)
            src = a033.add_env_reward_line(src, k, w[k])
    got = reward_dict(src)
    for k in REWARD_NAMES:
        if got.get(k) != w[k]:
            raise ValueError(f"rendered {k}={got.get(k)} != {w[k]}")
    for k in tree.EXTRA_TERMS:
        if got.get(k, tree.P0_REWARDS[k]) != w[k]:
            raise ValueError(f"rendered {k} does not read back as {w[k]}")
    return src


def run_config(template: str, n: dict, key: str, var: str, frm: float, to: float) -> str:
    keep = f"go2_{n['slug']}_pc2_{key}"
    repl = {
        "WORK_ID": n["work_id"], "RUN_ID": f"train_{n['work_id']}-Go2_pc2_{key}_1000", "EXPERIMENT_SLUG": keep,
        "KEEP_DIR_NAME": keep, "RESULT_ZIP_NAME": f"GO2_{n['up']}_PC2_{key.upper()}_RESULT.zip",
        "DONE_MARKER": f"'[DONE] GO2_{n['up']}_PC2_{key.upper()}_RESULT_READY'", "TMUX_NAME": keep, "TRAIN_SEED": "42",
        "SINGLE_CHANGE_NAME": var, "SINGLE_CHANGE_FROM": f"{frm:g}", "SINGLE_CHANGE_TO": f"{to:g}",
    }
    lines = []
    for line in template.splitlines():
        if line.startswith("# generated by"):
            lines.append("# generated by tools/build_go2_pc2_tree_package.py (PC2 search-tree node); do not edit")
            continue
        m = re.match(r"^([A-Z_]+)=", line)
        lines.append(f"{m.group(1)}={repl.pop(m.group(1))}" if m and m.group(1) in repl else line)
    if repl:
        raise ValueError(f"run_config template lacks {sorted(repl)}")
    return "\n".join(lines) + "\n"


P0_HARVEST = "workspace/server_returns/G-A060/extracted/go2_g_a060_pc2_a048_seed42"


def build(step: dict, work_id: str = PROVISIONAL_WORK_ID, parent_harvest: str | None = None) -> tuple[bytes, dict]:
    if step.get("action") != "RUN":
        raise ValueError(f"tree step is {step.get('action')}: {step.get('why')} — 빌드할 노드 없음")
    key, var, value, parent_changes = step["node"], step["variable"], float(step["value"]), step["parent_changes"]
    hits = history_conflicts(var, value)
    if hits:
        raise ValueError(f"{var}={value} 시험·실행 이력 있음 — §1-3 에 따라 EXCLUDED_HISTORY 로 기록하고 빌드하지 않는다: {hits}")
    n = names(work_id, key)
    src = a057.source_payload()
    sentinel6 = a057.six(json.loads(src["expected_rewards.json"])["baseline"])
    shared = a057.shared_files(src)
    parent_w, cand_w = rewards(parent_changes), rewards(parent_changes, var, value)
    diff = [k for k in tree.TREE_TERMS if cand_w[k] != parent_w[k]]
    if diff != [var]:
        raise ValueError(f"{key}: must change exactly {var}, changed {diff}")
    template = src["candidate/quadruped_rewards.py"].decode("utf-8")
    cand_src, parent_src = render(template, cand_w), render(template, parent_w)
    experiment = {
        "schema": "go2_pc2_tree_node_v1", "work_id": n["work_id"], "device": "PC2", "run_key": key,
        "design": DESIGN, "tree_step": step, "promotion": "forbidden_pc_exploration",
        "parent": {"label": "P0" if not parent_changes else "P0+" + ",".join(f"{k}={v:g}" for k, v in parent_changes.items()),
                   "harvest_for_readout": parent_harvest or (P0_HARVEST if not parent_changes else
                                                             "미지정 — 실제 부모(승자 노드) 수확물 경로가 필요하다. P0 아님"),
                   "rewards": parent_w},
        "single_change": {"name": var, "from": parent_w[var], "to": value}, "rewards": cand_w,
        "history_check": "같은 항·같은 값 시험 이력 없음(빌드 시 원장·_keep 검사)",
        "training": {"seed": 42, "num_envs": 4096, "max_iterations": 1000, "from_scratch": True},
        "evaluation": {"checkpoint_iter": 900, "seeds": [101, 202, 303], "case_count": 69},
        "readout": "tools/go2_pc2_tree_readout.py read --node {key} --point <harvest> --parent <parent harvest>",
        "lecture_prediction": "없음 — 강좌·배포 직접 예측이 없는 표 밖 항(계획 §12-1). 결과가 좋아도 강좌 예측 적중으로 쓰지 않는다.",
    }
    arm = {
        "candidate/quadruped_rewards.py": cand_src.encode("utf-8"),
        "reference/baseline_quadruped_rewards.py": parent_src.encode("utf-8"),
        "reference/reward_base_quadruped_rewards.py": parent_src.encode("utf-8"),
        "expected_rewards.json": (json.dumps({"baseline": sentinel6, "candidate": cand_w}, indent=2) + "\n").encode("utf-8"),
        "run_config.env": run_config(src["run_config.env"].decode("utf-8"), n, key, var, parent_w[var], value).encode("utf-8"),
        "experiment.json": (json.dumps(experiment, ensure_ascii=False, indent=1) + "\n").encode("utf-8"),
        "README.txt": (f"{n['work_id']} PC2 tree node {key}: 부모 {experiment['parent']['label']} 위 {var} "
                       f"{parent_w[var]:g} -> {value:g}. 학습 seed 42, 4096 env, 1000 iter, 평가 iter 900, 69 case.\n"
                       "이 폴더는 run_point.sh 가 펼쳐서 쓴다. PC 결과는 탐색용이며 제출 후보가 아니다.\n").encode("utf-8"),
    }
    arm["PACKAGE_SHA256SUMS.txt"] = a057.sums({**shared, **arm})
    files: dict[str, bytes] = {"shared/" + k: v for k, v in shared.items()}
    files.update({f"runs/{key}/{k}": v for k, v in arm.items()})
    cfg = arm["run_config.env"].decode("utf-8")
    keep = re.search(r"^KEEP_DIR_NAME=(.*)$", cfg, re.M).group(1)
    zipn = re.search(r"^RESULT_ZIP_NAME=(.*)$", cfg, re.M).group(1)
    files["points.txt"] = f"{key} {keep} {zipn}\n".encode("utf-8")
    files["point_config.env"] = (f"POINT_WORK_ID={n['work_id']}\nPOINT_STATUS_DIR_NAME={n['status_dir']}\n"
                                 f"POINT_WORK_DIR={n['work_dir']}\nPOINT_TMUX_NAME={n['tmux']}\n").encode("utf-8")
    files["run_point.sh"] = pkg.LAUNCHER.read_bytes().replace(b"\r\n", b"\n")
    files["README.txt"] = guide(n, key, var, parent_w[var], value, experiment["parent"]["label"], None).encode("utf-8")
    files["SHA256SUMS.txt"] = a057.sums(dict(files))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            info = zipfile.ZipInfo(n["prefix"] + name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            z.writestr(info, files[name])
    return buf.getvalue(), {"names": n, "files": files, "key": key, "rewards": cand_w, "parent": parent_w}


def guide(n: dict, key: str, var: str, frm: float, to: float, parent: str, zip_sha: str | None) -> str:
    return f"""GO2 {n['work_id']} PC2 탐색트리 노드 {key} — 실행 안내
==================================================
설계: {DESIGN} §12·§13 (Codex §37 APPROVE). 부모 {parent} 위 {var} {frm:g} -> {to:g} 한 항만 바꾼다.
학습 seed 42, 4096 env, 1000 iter, 평가 iter 900, 69 case, 영상 10편. 한 노드만 돌고 멈춘다.

1. 올리기: {n['release']}.zip  SHA256 {zip_sha or '(발행 시 기록)'}  → /workspace/{n['release']}.zip
2. 실행(한 줄): unzip -oq /workspace/{n['release']}.zip -d /workspace && bash /workspace/{n['prefix']}run_point.sh --only {key}
   진행: tmux attach -t {n['tmux']} / 상태: /workspace/_keep/{n['status_dir']}/POINT_STATUS.tsv
3. 실패 처리(§13-3):
   - 학습 시작 전 실패(rc 20~23): 환경을 고친 뒤 같은 명령. 고칠 수 없으면 보고하고 멈춘다.
   - 학습 완료 후 평가·회수 실패: 같은 명령으로 재개(완료 단계 SKIP, 재학습 없음).
   - 학습 도중 실패·복구 실패: 자동 재학습하지 말고 보고하고 멈춘다.
4. 회수: /workspace/_keep/go2_{n['slug']}_pc2_{key}/ 폴더 전체(report.html·69 case·영상 10편),
   GO2_{n['up']}_PC2_{key.upper()}_RESULT.zip + .sha256, /workspace/_keep/{n['status_dir']}/ → 저장소 workspace/_keep/
   (원본 유지, 100MB 초과는 95MB parts). GPU 감시: tools/go2_gpu_watch.sh (HANDOFF_G_A060_PC2.md §6).
5. 다음 노드는 판독(tools/go2_pc2_tree_readout.py) 뒤 트리 규칙이 정한다. 자동 연결 없음.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree-state", required=True, type=Path, help='{"nodes": {...}, "siblings": {...}}')
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--work-id")
    ap.add_argument("--parent-harvest", help="판독에 쓸 실제 부모 수확물 경로(부모가 P0 가 아닐 때 기록)")
    a = ap.parse_args(argv)
    if a.publish and not a.work_id:
        ap.error("--publish needs --work-id")
    try:
        step = tree.next_step(json.loads(a.tree_state.read_text(encoding="utf-8")))
    except tree.TreeStateError as err:
        print(f"[REFUSED] tree state: {err}", file=sys.stderr)
        return 2
    data, info = build(step, a.work_id or PROVISIONAL_WORK_ID, a.parent_harvest)
    zsha = a057.sha(data)
    n = info["names"]
    print(f"node {info['key']} work id {n['work_id']}{'' if a.work_id else ' (provisional)'} "
          f"files {len(info['files'])} zip {len(data)} bytes sha256 {zsha}")
    if not a.publish:
        return 0
    up = GO2 / "upload" / n["work_id"] / "current"
    if (up / f"{n['release']}.zip").exists():
        print(f"[REFUSED] {n['release']}.zip already published")
        return 2
    if pkg.id_in_use(n["work_id"]) and not up.exists():
        print("[REFUSED] work id already used: " + "; ".join(pkg.id_in_use(n["work_id"])))
        return 2
    up.mkdir(parents=True, exist_ok=True)
    (up / f"{n['release']}.zip").write_bytes(data)
    (up / f"{n['release']}.zip.sha256").write_text(f"{zsha}  {n['release']}.zip\n", encoding="utf-8", newline="\n")
    (up / f"{n['release']}_RUN_GUIDE.txt").write_text(
        guide(n, info["key"], step["variable"], info["parent"][step["variable"]], float(step["value"]),
              json.loads(info["files"][f"runs/{info['key']}/experiment.json"])["parent"]["label"], zsha),
        encoding="utf-8", newline="\n")
    print(f"published {up / (n['release'] + '.zip')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
