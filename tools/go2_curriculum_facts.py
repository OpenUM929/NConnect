"""지형 커리큘럼 사실표 — Isaac Lab v2.3.1 원문과 우리 학습 env.yaml 에서만 만든다.

왜 있는가.  2026-09-17~18 세션에서 "15 cm 계단은 커리큘럼 몇 번째 행인가", "평균 지형 레벨로 포화를
판정할 수 있는가", "IL 은 몇 iter 를 도는가"를 원문에서 읽고 계산했지만, 그 결과가 대화에만 있었다.
(메모리 규칙 analysis-is-an-asset: 생성 도구·증거·보고서·계약 테스트·포인터를 함께 남긴다.)

원문은 `reports/evidence/go2_curriculum_source_20260918/`에 SHA256 과 함께 보관돼 있고, 이 도구는
그 파일들을 **파싱해서** 값을 뽑는다. 숫자를 여기에 적어 두지 않는다.

    python -B tools/go2_curriculum_facts.py      # 증거 CSV 재생성
"""
from __future__ import annotations

import ast
import csv
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
SRC = QUAD / "reports/evidence/go2_curriculum_source_20260918"
OUT = SRC / "CURRICULUM_FACTS.csv"
# 우리 학습 설정의 원본: 동결 기준선 G-A033 이 실제로 학습한 env.yaml
TRAINED_ENV = ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/training/env.yaml"
OUR_ITERATIONS = 1000   # run_config 의 MAX_ITERATIONS (사양 training.max_iterations)


def source(name: str) -> tuple[str, list[str]]:
    text = (SRC / name).read_text(encoding="utf-8")
    return text, text.splitlines()


def find(lines: list[str], pattern: str) -> tuple[int, str]:
    """패턴이 처음 나오는 줄 번호(1-based)와 그 줄."""
    for number, line in enumerate(lines, 1):
        if re.search(pattern, line):
            return number, line.strip()
    raise RuntimeError(f"원문에서 {pattern!r} 를 찾지 못했다")


def literal(line: str, key: str) -> object:
    match = re.search(rf"{re.escape(key)}\s*=\s*(\([^)]*\)|[-\d.eE+]+)", line)
    if not match:
        raise RuntimeError(f"{key} 값을 읽지 못했다: {line!r}")
    return ast.literal_eval(match.group(1))


def env_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", text, re.M)
    if not match:
        raise RuntimeError(f"env.yaml 에서 {key} 를 찾지 못했다")
    return match.group(1).strip()


def env_tuple(text: str, key: str) -> str:
    """`key: !!python/tuple` 뒤에 `- 값` 으로 이어지는 YAML 튜플을 읽는다.

    계단 지형이 둘(pyramid_stairs, inverted)이라 같은 키가 여러 번 나온다 — 전부 같은지 확인하고
    하나로 돌려준다.  다르면 우리 지형이 원문과 다르다는 뜻이므로 실패시킨다.
    """
    found = set()
    for match in re.finditer(rf"^\s*{re.escape(key)}:\s*!!python/tuple\n((?:\s*- .+\n)+)", text, re.M):
        values = [line.split("- ", 1)[1].strip() for line in match.group(1).splitlines()]
        found.add("-".join(values))
    if not found:
        raise RuntimeError(f"env.yaml 에서 {key} 튜플을 찾지 못했다")
    if len(found) > 1:
        raise RuntimeError(f"env.yaml 의 {key} 가 지형마다 다르다: {sorted(found)}")
    return found.pop()


def rows() -> list[list[str]]:
    ppo_text, ppo = source("isaaclab_tasks_go2_agents_rsl_rl_ppo_cfg.py")
    rough_text, rough = source("isaaclab_terrains_config_rough.py")
    gen_text, gen = source("isaaclab_terrains_terrain_generator.py")
    imp_text, imp = source("isaaclab_terrains_terrain_importer.py")
    cur_text, cur = source("isaaclab_tasks_locomotion_velocity_mdp_curriculums.py")
    env = TRAINED_ENV.read_text(encoding="utf-8")

    it_line, it_text = find(ppo, r"^\s*max_iterations\s*=\s*\d+")
    rows_line, rows_text = find(rough, r"num_rows\s*=")
    cols_line, cols_text = find(rough, r"num_cols\s*=")
    step_line, step_text = find(rough, r"step_height_range\s*=")
    diff_line, diff_text = find(gen, r"difficulty = \(sub_row")
    resend_line, _ = find(imp, r"randint_like")
    up_line, up_text = find(cur, r"distance >")
    mean_line, mean_text = find(cur, r"return torch\.mean")

    il_iterations = int(literal(it_text, "max_iterations"))
    num_rows = int(literal(rows_text, "num_rows"))
    num_cols = int(literal(cols_text, "num_cols"))
    low, high = (float(v) for v in literal(step_text, "step_height_range"))

    out = [["fact", "value", "source", "line", "quote"]]

    def add(fact: str, value: object, name: str, line: int, quote: str) -> None:
        out.append([fact, str(value), name, str(line), quote])

    add("isaaclab_go2_rough_max_iterations", il_iterations,
        "isaaclab_tasks_go2_agents_rsl_rl_ppo_cfg.py", it_line, it_text)
    add("our_max_iterations", OUR_ITERATIONS, "config/experiments/*.json training.max_iterations", 0,
        "우리 전 회차 공통")
    add("terrain_num_rows", num_rows, "isaaclab_terrains_config_rough.py", rows_line, rows_text)
    add("terrain_num_cols", num_cols, "isaaclab_terrains_config_rough.py", cols_line, cols_text)
    add("stairs_step_height_range_m", f"{low}-{high}", "isaaclab_terrains_config_rough.py", step_line, step_text)
    add("difficulty_formula", "(sub_row + uniform()) / num_rows",
        "isaaclab_terrains_terrain_generator.py", diff_line, diff_text)
    add("mean_level_is_capped_by_random_resend", "True",
        "isaaclab_terrains_terrain_importer.py", resend_line, imp[resend_line - 1].strip())
    add("mean_level_saturation_unreadable", "True", "판독 규칙", 0,
        "마지막 레벨에 닿은 로봇을 0~max 무작위 행으로 되돌리므로 평균 레벨로는 포화를 판정할 수 없다")
    add("promotion_rule", "distance > terrain size[0] / 2",
        "isaaclab_tasks_locomotion_velocity_mdp_curriculums.py", up_line, up_text)
    add("logged_level_is_a_mean", "robots x 5 sub-terrain types",
        "isaaclab_tasks_locomotion_velocity_mdp_curriculums.py", mean_line, mean_text)

    # 행 → 계단 높이 (난이도 = (행 + 0~1 난수)/행수, 높이 = low + 난이도*(high-low))
    for row in range(num_rows):
        lo = low + (high - low) * (row / num_rows)
        hi = low + (high - low) * ((row + 1) / num_rows)
        add(f"stairs_height_row_{row}_m", f"{lo:.4f}-{hi:.4f}",
            "계산: terrain_generator.py + trimesh/mesh_terrains.py", 0,
            f"행 {row} 의 계단 높이 구간")

    # 우리가 평가하는 두 계단 높이가 어느 행인가
    for label, height in (("stairs_10", 0.10), ("stairs_15", 0.15)):
        row = int((height - low) / (high - low) * num_rows)
        add(f"{label}_curriculum_row", row, "계산", 0,
            f"{height} m 는 행 {row} 구간에서 학습된다(0-based, 행 {num_rows - 1} 이 최고)")

    # 우리 학습 지형이 원문과 같은 설정인가 (다르면 위 표를 우리 회차에 적용할 수 없다)
    for key, expected in (("num_rows", num_rows), ("num_cols", num_cols)):
        add(f"our_env_{key}", env_value(env, key), str(TRAINED_ENV.relative_to(ROOT)).replace("\\", "/"), 0,
            f"원문 {expected} 와 같아야 한다")
    add("our_env_step_height_range", env_tuple(env, "step_height_range"),
        str(TRAINED_ENV.relative_to(ROOT)).replace("\\", "/"), 0, f"원문 ({low}, {high}) 와 같아야 한다")
    add("our_env_max_init_terrain_level", env_value(env, "max_init_terrain_level"),
        str(TRAINED_ENV.relative_to(ROOT)).replace("\\", "/"), 0, "학습 시작 레벨 상한")
    return out


def sources_match() -> list[str]:
    """SOURCES.csv 의 SHA256 과 보관 파일이 같은지 — 원문이 바뀌면 위 표는 무효다."""
    faults = []
    with (SRC / "SOURCES.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            path = SRC / row["file"]
            if not path.is_file():
                faults.append(f"{row['file']} 없음")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                faults.append(f"{row['file']} SHA256 불일치")
    return faults


def main() -> int:
    faults = sources_match()
    if faults:
        raise SystemExit("원문 무결성 실패: " + ", ".join(faults))
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows())
    print(OUT.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
