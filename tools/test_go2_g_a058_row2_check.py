"""G-A058 행 2 판독 수치 고정 (2026-10-02).

python -B tools/test_go2_g_a058_row2_check.py
보고서 GO2_G_A058_ROW2_A043_SEED43_READOUT_20261002.md 의 핵심 수치가 증거 CSV와 같은지 확인한다.
"""
import csv
from pathlib import Path

EV = Path(__file__).resolve().parents[1] / "workspace/training/quadruped/reports/evidence/go2_g_a058_row2_check_20261002"


def load():
    with open(EV / "ROW2_CHECK.csv", encoding="utf-8") as f:
        return {r["metric"]: r for r in csv.DictReader(f)}


def test_prereg_inputs():
    m = load()
    assert m["stairs_15_down_ge2"]["local_A043_s43"] == "0"
    assert m["combined_yaw_right_falls"]["local_A043_s43"] == "0"
    assert m["stairs_15_down_ge2"]["server_A043_s42"] == "77"
    assert m["combined_yaw_right_falls"]["server_A043_s42"] == "29"


def test_reported_axes():
    m = load()
    assert m["total_70"]["local_A043_s43"] == "41.892"
    assert m["push_falls_sum"]["local_A043_s43"] == "87"
    assert m["rough_lateral_falls"]["local_A043_s43"] == "5"


def test_edge_medians():
    with open(EV / "STAIRS_EDGE_MEDIANS.csv", encoding="utf-8") as f:
        rows = {(r["case"], r["group"], r["arm"]): r for r in csv.DictReader(f)}
    r = rows[("stairs_15_down", "ALL", "local_A043_s43")]
    assert r["reached_edge"] == "92" and abs(float(r["ed_rise"]) - 0.0159) < 1e-3
    assert rows[("stairs_15_down", "climb>=2", "local_A043_s43")]["n"] == "0"


if __name__ == "__main__":
    for t in (test_prereg_inputs, test_reported_axes, test_edge_medians):
        t()
    print("3 passed")
