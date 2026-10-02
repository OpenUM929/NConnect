"""추세 비교의 동일 조건 확인 — 비교한 정책 쌍이 정말 보상 한 항만 다른가 (2026-10-01, 읽기 전용).

쌍(기준 → 비교 정책)마다 회수물의 학습 기록을 직접 비교한다.
  보상     training/env.yaml 의 rewards: 블록 전체(모든 항의 weight 와 params). 다른 항과 값을 적는다.
  환경     env.yaml 의 rewards 블록 밖 전체(지형·명령·관측·이벤트·종료·seed 등). 경로·로그 위치·하늘 텍스처 행은 뺀다.
           다른 행 수와 앞의 몇 줄을 적는다.
  학습 코드 training/candidate_source.sha256 의 파일 해시(보상 파일 quadruped_rewards.py 제외).
  학습 설정 agent.yaml(PPO 설정) 전체 비교(run 이름·로그 경로 행 제외), run_config.env 의 TRAIN_SEED·MAX_ITERATIONS·NUM_ENVS,
           CHECKPOINT_PIN 의 평가 iter, 평가기·registry SHA.
판정 ONLY_ONE_REWARD = 보상 항 하나만 다르고 나머지가 모두 같다. 아니면 무엇이 다른지 적는다.
    python -B tools/go2_series_identity_check.py
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_state_outcome import ARMS, KEEP  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_series_identity_20261001"
PAIRS = [  # (series, value label, base, arm)
    ("lin_vel_z (A033 기준)", "-1.75", "A033", "A044"), ("lin_vel_z (A033 기준)", "-1.5", "A033", "A043"),
    ("lin_vel_z (A033 기준)", "-1.375", "A033", "A050"), ("lin_vel_z (A033 기준)", "-1.25", "A033", "A048"),
    ("lin_vel_z (A033 기준)", "-1.0", "A033", "A049"),
    ("ang_vel_xy (A033 기준)", "-0.04", "A033", "A041"), ("ang_vel_xy (A033 기준)", "-0.08", "A033", "A038"),
    ("ang_vel_xy (A043 기준)", "-0.08", "A043", "A055"),
    ("flat_orientation (A033 기준)", "-0.5", "A033", "A047"), ("track_lin_vel_xy (A033 기준)", "1.6", "A033", "A042"),
    ("참고: 보상 같음 서버→PC", "same", "A048", "PC_A048"),
]
SKIP = re.compile(r"(/workspace|[A-Z]:[/\\]|log_dir|texture_file|usd_path|asset_path|http|experiment_name|run_name|load_run|resume)", re.I)


def text(p):
    return p.read_bytes().replace(b"\r\n", b"\n").decode("utf-8", errors="replace").splitlines()


def split_env(lines):
    i = lines.index("rewards:")
    j = next(k for k in range(i + 1, len(lines)) if lines[k] and not lines[k].startswith(" "))
    return lines[:i] + lines[j:], lines[i + 1:j]


def reward_terms(block):
    terms, cur = {}, None
    for ln in block:
        m = re.match(r"^  ([a-z_0-9]+):(.*)$", ln)
        if m:
            cur = m.group(1)
            terms[cur] = [m.group(2).strip()]
        elif cur:
            terms[cur].append(ln.strip())
    return terms


def weight(lines):
    for ln in lines:
        if ln.startswith("weight:"):
            return ln.split(":", 1)[1].strip()
    return lines[0] if lines and lines[0] else "?"


def kv(p, keys):
    if not p.exists():
        return {}
    out = {}
    for ln in text(p):
        for k in keys:
            if ln.startswith(k + "="):
                out[k] = ln.split("=", 1)[1].strip()
    return out


def info(arm):
    d = KEEP / ARMS[arm][0]
    env = text(d / "training/env.yaml")
    rest, rew = split_env(env)
    agent = next((d / "training/logs").rglob("params/agent.yaml"), None)
    src = {}
    for ln in text(d / "training/candidate_source.sha256"):
        h, name = ln.split(None, 1)
        name = name.lstrip("*").strip()
        if not name.endswith("quadruped_rewards.py"):
            src[name.split("/candidate/")[-1]] = h
    cfg = kv(d / "meta/run_config.env", ("TRAIN_SEED", "MAX_ITERATIONS", "NUM_ENVS"))
    pin = kv(d / "training/CHECKPOINT_PIN.txt", ("EVAL_CHECKPOINT_ITER",))
    ev = (d / "meta/evaluator.sha256").read_text().split()[0][:12]
    rg = (d / "meta/registry.sha256").read_text().split()[0][:12]
    return {"rest": [l for l in rest if not SKIP.search(l)], "rewards": reward_terms(rew),
            "agent": [l for l in text(agent) if not SKIP.search(l)] if agent else None, "src": src,
            "cond": {**cfg, **pin, "evaluator": ev, "registry": rg, "layer": ARMS[arm][1]}}


def diff_lines(a, b):
    import difflib
    return [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = {}
    rows = []
    for series, val, base, arm in PAIRS:
        for a in (base, arm):
            if a not in cache:
                cache[a] = info(a)
        b, c = cache[base], cache[arm]
        rdiff = [f"{t}: {weight(b['rewards'].get(t, ['없음']))} → {weight(c['rewards'].get(t, ['없음']))}"
                 for t in sorted(set(b["rewards"]) | set(c["rewards"])) if b["rewards"].get(t) != c["rewards"].get(t)]
        ediff = diff_lines(b["rest"], c["rest"])
        adiff = diff_lines(b["agent"] or [], c["agent"] or []) if b["agent"] is not None and c["agent"] is not None else ["agent.yaml 없음"]
        sdiff = sorted(k for k in set(b["src"]) | set(c["src"]) if b["src"].get(k) != c["src"].get(k))
        cdiff = [f"{k}: {b['cond'].get(k)} → {c['cond'].get(k)}" for k in sorted(set(b["cond"]) | set(c["cond"]))
                 if b["cond"].get(k) != c["cond"].get(k)]
        only = len(rdiff) == 1 and not ediff and not adiff and not sdiff and not cdiff
        same = len(rdiff) == 0 and not ediff and not adiff and not sdiff
        verdict = "ONLY_ONE_REWARD" if only else ("SAME_REWARD_DIFFERENT_MACHINE" if same and cdiff == [f"layer: server → pc"] else "OTHER_DIFFERENCES")
        rows.append({"series": series, "value": val, "base": base, "arm": arm, "verdict": verdict,
                     "reward_diff": " ; ".join(rdiff) or "없음", "env_lines_diff": len(ediff), "env_diff_sample": " | ".join(ediff[:4]),
                     "agent_lines_diff": len(adiff), "agent_diff_sample": " | ".join(adiff[:4]),
                     "train_code_files_diff": " ; ".join(sdiff) or "없음", "condition_diff": " ; ".join(cdiff) or "없음",
                     "seed_iter_envs_ckpt": f"{c['cond'].get('TRAIN_SEED')}/{c['cond'].get('MAX_ITERATIONS')}/{c['cond'].get('NUM_ENVS')}/{c['cond'].get('EVAL_CHECKPOINT_ITER')}"})
    with (OUT / "SERIES_IDENTITY.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['series']} {r['value']} {r['base']}->{r['arm']}: {r['verdict']} | 보상 {r['reward_diff']} | env {r['env_lines_diff']} | agent {r['agent_lines_diff']} | code {r['train_code_files_diff']} | 조건 {r['condition_diff']} | {r['seed_iter_envs_ckpt']}")
        if r["env_lines_diff"]:
            print("   env:", r["env_diff_sample"][:300])
        if r["agent_lines_diff"]:
            print("   agent:", r["agent_diff_sample"][:300])


if __name__ == "__main__":
    main()
