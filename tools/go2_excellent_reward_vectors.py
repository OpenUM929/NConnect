"""Go2 우수 정책들의 전체 보상 벡터를 학습 env.yaml에서 직접 읽어 비교한다 (2026-10-01).

근거 대상: upload/plan/GO2_POST_A058_TWO_STRATEGIES_20261001.md 「Claude 검토 및 서버 첫 후보 제안」 §2-1
("우수 설정 조합 공간이 사실상 비어 있다").
입력: workspace/_keep/go2_g_aNNN_*/training/env.yaml 의 rewards.<항>.weight (서버 학습 시작 스냅샷).
출력: reports/evidence/go2_excellent_reward_vectors_20261001/REWARD_VECTORS.csv, DIFF_TERMS.txt
실행: python -B tools/go2_excellent_reward_vectors.py [--check]
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "workspace" / "_keep"
OUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_excellent_reward_vectors_20261001"

# 정책: (keep 폴더, 우수 사례로 거론된 이유)
POLICIES = {
    "A033": ("go2_g_a033_a017_track_lin_vel_xy_150", "기준선(대조군)"),
    "A038": ("go2_g_a038_a033_ang_vel_xy_m008", "험지 옆걸음 성공 78"),
    "A043": ("go2_g_a043_a033_lin_vel_z_m15", "15cm 계단 성공 46·≥2단 77"),
    "A048": ("go2_g_a048_a033_lin_vel_z_m125", "총점 50.16·험지·밀침"),
    "A049": ("go2_g_a049_a033_lin_vel_z_m1", "험지 전진 성공 94"),
    "A050": ("go2_g_a050_a033_lin_vel_z_m1375", "험지 옆걸음 성공 77"),
    "A055": ("go2_g_a055_a043_ang_vel_xy_m008", "우회전 판정 0·밀침 375"),
}


def read_weights(env_yaml: Path) -> dict:
    """rewards: 블록 안의 2칸 들여쓴 항 이름과 그 아래 첫 'weight:' 값을 읽는다."""
    weights, term, in_rewards = {}, None, False
    for line in env_yaml.read_text(encoding="utf-8").splitlines():
        if re.match(r"^rewards:", line):
            in_rewards = True
            continue
        if in_rewards and re.match(r"^\S", line):
            break
        if not in_rewards:
            continue
        m = re.match(r"^  ([a-z_0-9]+):\s*(null)?\s*$", line)
        if m:
            term = m.group(1)
            if m.group(2):
                weights[term] = None
            continue
        m = re.match(r"^    weight:\s*(\S+)", line)
        if m and term and term not in weights:
            weights[term] = float(m.group(1))
    return weights


def build():
    vectors = {}
    for pid, (folder, _) in POLICIES.items():
        vectors[pid] = read_weights(KEEP / folder / "training" / "env.yaml")
    terms = sorted({t for v in vectors.values() for t in v})
    diff = [t for t in terms if len({vectors[p].get(t) for p in vectors}) > 1]
    return vectors, terms, diff


def main():
    vectors, terms, diff = build()
    if "--check" in sys.argv:
        assert diff == ["ang_vel_xy_l2", "lin_vel_z_l2"], diff
        assert vectors["A043"]["lin_vel_z_l2"] == -1.5 and vectors["A048"]["lin_vel_z_l2"] == -1.25
        print("OK", diff)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "REWARD_VECTORS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["policy", "why_listed", "source_env_yaml"] + terms)
        for pid, (folder, why) in POLICIES.items():
            src = f"workspace/_keep/{folder}/training/env.yaml"
            w.writerow([pid, why, src] + ["null" if vectors[pid].get(t) is None else vectors[pid].get(t) for t in terms])
    (OUT / "DIFF_TERMS.txt").write_text(
        "값이 정책마다 다른 보상 항: " + ", ".join(diff) + "\n"
        + "나머지 항은 7개 정책에서 모두 같다: " + ", ".join(t for t in terms if t not in diff) + "\n",
        encoding="utf-8")
    print("diff terms:", diff)


if __name__ == "__main__":
    main()
