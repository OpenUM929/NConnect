"""G-A052 진단 재생 회수 검증 (2026-09-28, v2 — Codex 검토 반영).  성능·원인을 판정하지 않는다.

두 판정을 따로 낸다.
  artifact  ARTIFACT_VERIFIED | ARTIFACT_NOT_VERIFIED
            필수 파일이 모두 있고 SHA256SUMS 에 올라 있으며 해시가 맞다 · 수집 완료 표시 · 정책·평가기 식별자 ·
            네 실행의 평가기 완료 · 재현 비교에 쓸 steps.csv 전부 · 진단 CSV 의 (step, env_id) 키가 1..1000 × 0..31 로
            중복·누락 없음
  channels  DIAG_CHANNELS_COMPLETE | DIAG_CHANNELS_INCOMPLETE
            필수 채널 묶음(body·feet·contact·terrain·action·reward)이 diag_meta 에서 UNAVAILABLE 이 아니고,
            판독기(tools/go2_diag_replay_readout.py)가 읽는 열 전부 — 네 발 각각의 접촉 시간·수평 속도·높이·주변 지형,
            몸통 roll·pitch 각속도, contact_fresh, action·prev_action 12개씩, diag_meta reward_weights 에 등록된
            보상 항마다 rew_<항> — 가 헤더에 있고,
            종료·시간초과 행이 아닌 모든 행에서 빈칸·NaN·Infinity 가 없으며(열마다 건수와 첫 위치를 기록),
            접촉 버퍼가 그 행들에서 그 step 에 갱신됐다(contact_fresh=1)
종료코드  0 = 둘 다 통과 → 서버 종료 가능(실행 안내 §5의 다른 줄과 함께)
          3 = artifact 통과 · 채널 미확보 → 서버를 켠 채 CHANNEL_PROBLEMS 를 읽고 복구 가능성을 판단한다
          1 = artifact 실패 → 끄지 않는다.  다시 회수한다
재현 비교(REPRO.csv)는 판정에 넣지 않는다.  steps.csv 가 같다는 것은 저장된 채널·정밀도에서 차이가 없었다는 뜻이지
모든 내부 상태에 개입이 없었다는 증명이 아니다.

    python -B tools/verify_go2_diag_replay_harvest.py <harvest_dir> [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORED = ROOT / "workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/evaluation/candidate/cases"
MODEL_SHA = "984e614933f3aae037df260cbf7ee72e7549337435a602ce116d6fc39e7f5ad7"
ENV_SHA = "a19077a984f829f23f1ca87405b9b4fa94ae6c618fedf95ea6bb640992f33a35"
EVALUATOR_SHA = "353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84"
RUNS = (("plain", 202, "rough_lateral"), ("diag", 202, "rough_lateral"),
        ("diag", 101, "stairs_10_down"), ("diag", 101, "stairs_15_down"))
STEPS, ENVS = 1000, 32
REQUIRED_GROUPS = ("body", "feet", "contact", "terrain", "action", "reward")
FEET = ("FL", "FR", "RL", "RR")
ACTION_DIM = 12
# 판독기가 읽는 열 전부(2026-09-28 Codex 검토: 앞왼발만 보던 목록이 RR_contact_time 전체 결측을 놓쳤다).
REQUIRED_COLUMNS = (("ang_vel_b_x", "ang_vel_b_y", "contact_fresh")
                    + tuple(f"{f}_{k}" for f in FEET
                            for k in ("contact_time", "vel_x", "vel_y", "pos_z", "terrain_zmax015_derived"))
                    + tuple(f"action_{i}" for i in range(ACTION_DIM))
                    + tuple(f"prev_action_{i}" for i in range(ACTION_DIM)))
LOCATIONS_KEPT = 5
TOP_FILES = ("RESULT_STATUS.txt", "RUNNER_STATUS.txt", "launcher.snapshot.log", "meta/identity.json",
             "meta/RUN_TIMES.txt", "meta/REPRO_STATUS.txt", "meta/run_config.env", "meta/experiment.json")
RUN_FILES = ("steps.csv", "summary.json", "STATUS.txt")
DIAG_FILES = ("diag.csv.gz", "diag_meta.json", "DIAG_STATUS.txt")
DEFAULT_OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_g_a052_diag_20260928"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def required_files() -> list[str]:
    out = list(TOP_FILES)
    for label, seed, case in RUNS:
        base = f"{label}/cases/seed_{seed}/{case}"
        out += [f"{base}/{f}" for f in RUN_FILES]
        out.append(f"logs/{label}_seed_{seed}_{case}.log")
        if label == "diag":
            out += [f"{base}/{f}" for f in DIAG_FILES]
    return out


def compare_steps(a: Path, b: Path) -> dict:
    with a.open(encoding="utf-8", newline="") as fa, b.open(encoding="utf-8", newline="") as fb:
        ra, rb = list(csv.reader(fa)), list(csv.reader(fb))
    if ra[:1] != rb[:1]:
        return {"status": "HEADER_DIFFERENT", "rows_a": len(ra), "rows_b": len(rb)}
    diff_envs: dict[str, int] = {}
    first = None
    for x, y in zip(ra[1:], rb[1:]):
        if x != y:
            diff_envs.setdefault(x[2], int(x[0]))
            first = int(x[0]) if first is None else min(first, int(x[0]))
    status = "NO_DIFFERENCE_IN_STORED_CHANNELS" if len(ra) == len(rb) and not diff_envs else "DIVERGED"
    return {"status": status, "rows_a": len(ra) - 1, "rows_b": len(rb) - 1, "first_diff_step": first,
            "envs_diverged": len(diff_envs), "envs_diverged_first_step": json.dumps(diff_envs, sort_keys=True)}


def reset_rows(steps_csv: Path) -> set[tuple[int, int]]:
    """종료·시간초과 행: 그 step 에 reset 된 env 는 센서가 스스로 낡음 표시를 한다."""
    out = set()
    with steps_csv.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["terminated"] == "1" or r["truncated"] == "1":
                out.add((int(r["step"]), int(r["env_id"])))
    return out


def check_diag(d: Path, case: str, problems: list[str], chan: list[str], channels: list[dict]) -> None:
    meta = json.loads((d / "diag_meta.json").read_text(encoding="utf-8"))
    unavailable = meta.get("unavailable", {})
    for g in REQUIRED_GROUPS:
        channels.append({"case": case, "item": f"group:{g}", "status": "UNAVAILABLE" if g in unavailable else "RECORDED",
                         "detail": unavailable.get(g, "")})
        if g in unavailable:
            chan.append(f"{case}: channel group {g} unavailable ({unavailable[g]})")
    resets = reset_rows(d / "steps.csv")
    keys: set[tuple[int, int]] = set()
    dup = 0
    with gzip.open(d / "diag.csv.gz", "rt", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        required = [c for c in REQUIRED_COLUMNS if c in header] + [c for c in header if c.startswith("rew_")]
        bad = {c: 0 for c in required}
        where: dict[str, list[str]] = {c: [] for c in required}
        stale = 0
        for r in reader:
            k = (int(r["step"]), int(r["env_id"]))
            dup += k in keys
            keys.add(k)
            if k in resets:  # reset 행은 센서·로봇 값이 다음 episode 첫 상태다 — 결측 검사 밖
                continue
            for c in required:
                v = r.get(c)
                try:
                    ok = v not in ("", None) and math.isfinite(float(v))
                except ValueError:
                    ok = False
                if not ok:
                    bad[c] += 1
                    if len(where[c]) < LOCATIONS_KEPT:
                        where[c].append(f"step={k[0]} env={k[1]} value={v!r}")
            if r.get("contact_fresh") != "1":
                stale += 1
    want = {(s, e) for s in range(1, STEPS + 1) for e in range(ENVS)}
    missing_keys, extra_keys = len(want - keys), len(keys - want)
    if dup or missing_keys or extra_keys:
        problems.append(f"diag {case}: keys duplicate={dup} missing={missing_keys} unexpected={extra_keys}")
    for c in REQUIRED_COLUMNS:
        if c not in header:
            chan.append(f"{case}: required column {c} absent")
    if not any(c.startswith("rew_") for c in header):
        chan.append(f"{case}: no reward-term column (rew_*)")
    # 보상 열은 CSV 에 있는 것만 보면 통째로 빠진 항을 놓친다: diag_meta 의 reward_weights 에 등록된 항마다 열을 요구한다.
    weights = meta.get("reward_weights") or {}
    if not weights:
        chan.append(f"{case}: diag_meta.json has no reward_weights (reward terms cannot be checked)")
    for name in weights:
        if f"rew_{name}" not in header:
            chan.append(f"{case}: reward column rew_{name} absent (registered in diag_meta reward_weights)")
    rows_checked = len(keys - resets)
    for c, n in bad.items():
        if n:
            chan.append(f"{case}: required column {c} missing or non-finite in {n}/{rows_checked} non-reset rows"
                        f" (first: {'; '.join(where[c])})")
        channels.append({"case": case, "item": f"column:{c}", "status": "COMPLETE" if not n else "MISSING_OR_NONFINITE",
                         "detail": f"bad_rows={n} first={' | '.join(where[c])}"})
    if stale:
        chan.append(f"{case}: {stale} non-reset rows with contact_fresh != 1 (contact buffer not proven current)")
    channels.append({"case": case, "item": "keys", "status": f"{len(keys)}/{len(want)}",
                     "detail": f"duplicate={dup} missing={missing_keys} unexpected={extra_keys}"})
    channels.append({"case": case, "item": "contact_fresh", "status": "ALL_NON_RESET_ROWS" if not stale else "STALE",
                     "detail": f"stale_non_reset_rows={stale} reset_rows={len(resets)}"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("harvest")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--stored", default=str(STORED))
    a = ap.parse_args(argv)
    h, out, stored = Path(a.harvest), Path(a.out), Path(a.stored)
    out.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    chan: list[str] = []
    listed: set[str] = set()
    sums = h / "SHA256SUMS.txt"
    if not sums.is_file():
        problems.append("SHA256SUMS.txt missing")
    else:
        for line in sums.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            name = name.lstrip("*").removeprefix("./")
            listed.add(name)
            p = h / name
            if not p.is_file() or sha(p) != digest:
                problems.append(f"sha mismatch or missing: {name}")
    for name in required_files():
        if not (h / name).is_file():
            problems.append(f"required file missing: {name}")
        elif name not in listed:
            problems.append(f"required file not in SHA256SUMS: {name}")
    status = (h / "RESULT_STATUS.txt").read_text(encoding="utf-8") if (h / "RESULT_STATUS.txt").is_file() else ""
    if "COLLECTION_STATUS=COMPLETE_4_OF_4" not in status:
        problems.append(f"collection not complete: {status.strip()!r}")
    ident_p = h / "meta/identity.json"
    ident = json.loads(ident_p.read_text(encoding="utf-8")) if ident_p.is_file() else {}
    for key, want in (("model_sha256", MODEL_SHA), ("env_sha256", ENV_SHA), ("evaluator_sha256", EVALUATOR_SHA)):
        if ident.get(key) != want:
            problems.append(f"identity {key}={ident.get(key)!r} != {want}")
    channels: list[dict] = []
    for label, seed, case in RUNS:
        d = h / label / "cases" / f"seed_{seed}" / case
        st = (d / "STATUS.txt").read_text(encoding="utf-8") if (d / "STATUS.txt").is_file() else ""
        if "EVAL_RC=0" not in st:
            problems.append(f"{label} {case}: evaluator STATUS {st.strip()!r}")
        if label == "diag" and all((d / f).is_file() for f in DIAG_FILES + ("steps.csv",)):
            check_diag(d, case, problems, chan, channels)
    repro = []
    pairs = [("plain_vs_stored", h / "plain/cases/seed_202/rough_lateral/steps.csv",
              stored / "seed_202/rough_lateral/steps.csv"),
             ("diag_vs_plain", h / "diag/cases/seed_202/rough_lateral/steps.csv",
              h / "plain/cases/seed_202/rough_lateral/steps.csv"),
             ("diag_vs_stored_stairs10", h / "diag/cases/seed_101/stairs_10_down/steps.csv",
              stored / "seed_101/stairs_10_down/steps.csv"),
             ("diag_vs_stored_stairs15", h / "diag/cases/seed_101/stairs_15_down/steps.csv",
              stored / "seed_101/stairs_15_down/steps.csv")]
    for name, x, y in pairs:
        if x.is_file() and y.is_file():
            repro.append({"pair": name, **compare_steps(x, y)})
        else:
            repro.append({"pair": name, "status": "MISSING"})
            problems.append(f"repro input missing: {name}")
    artifact = "ARTIFACT_VERIFIED" if not problems else "ARTIFACT_NOT_VERIFIED"
    channel_state = "DIAG_CHANNELS_COMPLETE" if not chan else "DIAG_CHANNELS_INCOMPLETE"
    verdict = {"artifact": artifact, "problems": problems, "channels": channel_state, "channel_problems": chan,
               "repro": {r["pair"]: r["status"] for r in repro},
               "repro_meaning": "no difference in stored channels at stored precision; not a proof of no interference"}
    for name, data in (("REPRO.csv", repro), ("CHANNELS_RECORDED.csv", channels)):
        cols: list[str] = []
        for r in data:
            cols += [k for k in r if k not in cols]
        with (out / name).open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols or ["empty"], lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    (out / "HARVEST_VERDICT.json").write_text(json.dumps(verdict, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(verdict, ensure_ascii=False))
    if problems:
        return 1
    return 3 if chan else 0


if __name__ == "__main__":
    raise SystemExit(main())
