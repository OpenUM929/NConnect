"""Go2 계단 오른 로봇 수 — 평가 `steps.csv`에서만 센다 (표준 라이브러리만, 서버 게이트에 실린다).

왜 따로 있는가.  G5 점수는 case·seed 최솟값이라 15cm 오르기가 모든 정책에서 0 근처다.
그래서 점수로는 10cm 오르기가 무너져도 움직이지 않는다(G-A038, `reports/GO2_G_A038_READOUT.md` §4).
분석 §8-4가 정한 계단 지표(오른 로봇 수)를 판정에도 쓰려면, 분석 도구
(`tools/go2_stairs_behavior.py`)와 서버 게이트·로컬 검증기가 **같은 함수**로 세야 한다.

방향은 이름이 아니라 출발 지형 높이다: 양수면 꼭대기 출발(내려가기), 음수면 구덩이 출발(오르기).
Isaac Lab v2.3.1 `mesh_terrains.py` 145행·245행과 같은 규칙이다(case 이름 `*_down`이 실제 오르기).
"""
from __future__ import annotations

import collections
import csv
from pathlib import Path

FULL_STEPS = 6          # 8 m 타일, 경계 1 m, 평지 3 m, 계단 폭 0.3 m → (8-2-3)//0.6+1
STEP_TOLERANCE = 0.3    # 계단 높이의 30% 안쪽이면 그 계단에 올라선 것으로 센다
SETTLE_ROW = 50         # 1초 뒤 몸 높이를 기준으로 한다 (착지 흔들림 제외)
MIN_TRAVEL_M = 1.0      # 출발점에서 이만큼 떨어진 행만 계단 판정에 쓴다
STAIR_HEIGHTS = {"stairs_10_up": 0.10, "stairs_10_down": 0.10,
                 "stairs_15_up": 0.15, "stairs_15_down": 0.15}


def alive_rows(steps: Path) -> dict[str, list[dict[str, str]]]:
    """env 별로 첫 종료·절단 직전까지의 행."""
    by: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    stopped: set[str] = set()
    with steps.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            env = row["env_id"]
            if env in stopped:
                continue
            if row.get("terminated") == "1" or row.get("truncated") == "1":
                stopped.add(env)
                continue
            by[env].append(row)
    return by


def travelled(row: dict[str, str], x0: float, y0: float) -> bool:
    return (float(row["root_x"]) - x0) ** 2 + (float(row["root_y"]) - y0) ** 2 >= MIN_TRAVEL_M ** 2


def gained_steps(env_rows: list[dict[str, str]], direction: str, height: float) -> int:
    base = env_rows[min(SETTLE_ROW, len(env_rows) - 1)]
    z0 = float(base["root_z"])
    x0, y0 = float(env_rows[0]["root_x"]), float(env_rows[0]["root_y"])
    # 평지 끝(중심에서 1.5 m, 출발 오프셋 ±0.5 m)에 닿은 행만 본다.  제자리에서
    # 엎드린 로봇의 몸통 하강을 '내려간 계단'으로 세지 않기 위해서다.
    away = [float(r["root_z"]) for r in env_rows if travelled(r, x0, y0)]
    if not away:
        rise = 0.0
    elif direction == "climb":
        rise = max(away) - z0
    else:
        rise = z0 - min(away)
    return int((rise + STEP_TOLERANCE * height) // height)


def count(steps: Path, height: float) -> dict | None:
    """한 case·seed의 계단 수 분포.  기록이 없으면 None."""
    by = alive_rows(steps)
    if not by:
        return None
    first = next(iter(by.values()))[0]
    key = "terrain_z" if "terrain_z" in first else "root_z"
    start = sum(float(r[0][key]) for r in by.values()) / len(by)
    if key == "root_z":
        start -= sum(float(r[0].get("height_rel") or 0) for r in by.values()) / len(by)
    direction = "descend" if start > 0 else "climb"
    ge1 = ge2 = full = 0
    for env_rows in by.values():
        gained = gained_steps(env_rows, direction, height)
        ge1 += gained >= 1
        ge2 += gained >= 2
        full += gained >= FULL_STEPS
    return {"height_key": key, "terrain_start_m": start, "direction": direction, "robots": len(by),
            "ge1": ge1, "ge2": ge2, "full": full}
