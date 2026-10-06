"""Contract tests for tools/go2_success_discrimination.py (synthetic records + produced evidence).

Codex 검토(2026-10-01) 요청 3·4·5: 전체 대수는 지표별 유효 표본이 아니라 로봇 레코드로 세고,
추세 비교는 정책들이 공통으로 가진 평가 칸(case × 평가 seed)만 쓰며, 모서리 값은 끝까지 지난 로봇만 쓴다.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_success_discrimination as sd  # noqa: E402

PROFILE = sd.EV / "go2_robot_state_profile_20261001/PER_ENV.csv"


def rec(arm, case, cell, success, **kw):
    return {"arm": arm, "case": case, "cell": cell, "success": success, **kw}


def test_case_counts_use_all_records_not_metric_n():
    recs = [rec("A", "stairs_15_down", ("stairs_15_down", "101"), 1, edge_tilt_max=20.0),
            rec("A", "stairs_15_down", ("stairs_15_down", "101"), 0),            # no metric at all
            rec("A", "stairs_15_down", ("stairs_15_down", "101"), 0, w_h=0.3),
            rec("A_diag", "stairs_15_down", None, 0, thigh=0.8)]                 # diag replay is not a robot record
    assert sd.case_counts(recs, "stairs_15_down") == (1, 2)


def test_common_cells_is_intersection():
    g = [rec("A033", "push", (c, s), 1) for c in ("push_pos_x", "push_neg_x") for s in ("101", "202")]
    g += [rec("A038", "push", ("push_pos_x", s), 1) for s in ("101", "202")]
    assert sd.common_cells(g, ["A033", "A038"]) == {("push_pos_x", "101"), ("push_pos_x", "202")}


def test_trend_counts_only_common_cells_and_labels_config():
    recs = [rec("A033", "push", (c, s), 1) for c in ("push_pos_x", "push_neg_x") for s in ("101", "202") for _ in range(2)]
    recs += [rec("A041", "push", ("push_pos_x", s), 0) for s in ("101", "202") for _ in range(2)]
    recs += [rec("A038", "push", ("push_pos_x", s), 1) for s in ("101", "202") for _ in range(2)]
    ident = {("A033", "A041"): {"verdict": "ONLY_ONE_REWARD"}, ("A033", "A038"): {"verdict": "ONLY_ONE_REWARD"}}
    out = "\n".join(sd.trend_rows(recs, "push", [], ident))
    assert "공통 2칸만 사용" in out
    assert "| 성공 / 전체 (로봇) | 0/4 | 4/4 | 4/4 |" in out  # A033 8 robots -> only its 4 common-cell robots


def test_trend_series_do_not_leak_filtering_between_series():
    # a narrower series must not shrink the next series' cells
    recs = [rec(a, "push", (c, "101"), 1) for a in ("A033", "A044", "A043", "A050", "A048", "A049", "A047")
            for c in ("push_pos_x", "push_neg_x")]
    recs += [rec("A041", "push", ("push_pos_x", "101"), 1)]
    ident = {}
    out = "\n".join(sd.trend_rows(recs, "push", [], ident))
    assert "| flat_orientation (A033 기준) | 0 (A033) | -0.5 (A047) |\n|---|---|---|\n| 성공 / 전체 (로봇) | 2/2 | 2/2 |" in out


def test_edge_metrics_only_from_full_edge_robots():
    recs = sd.records()
    body = {(r["arm"], r["case"], r["seed"], r["env"]): r for r in sd.rd(PROFILE)}
    assert all(r.get("edge_status") == "full" for r in recs if "edge_tilt_max" in r)
    assert any(b.get("edge_full") == "0" and b.get("edge_tilt_max") for b in body.values())  # truncated values exist in source


def test_produced_counts_match_codex_recount():
    recs = sd.records()
    assert sd.case_counts(recs, "stairs_15_down") == (53, 907)
    assert sd.case_counts(recs, "rough_lateral")[1] == 545
    assert sd.case_counts(recs, "rough_forward")[1] == 77


def test_edge_status_partition_stairs15():
    rows = [r for r in sd.rd(PROFILE) if r["case"] == "stairs_15_down" and r["arm"] not in sd.EXCLUDE and r["success"] == "0"]
    from collections import Counter
    c = Counter(r.get("edge_status") or "no_data" for r in rows)
    assert c == Counter({"judged_in_edge": 736, "unjudged_not_crossed": 109, "full": 55, "no_data": 7})


def test_report_has_separate_config_label():
    text = sd.REPORT.read_text(encoding="utf-8")
    assert "공통 3칸만 사용(push_pos_x seed 101·202·303)" in text
    assert "전체 로봇 성공 53대 / 실패 907대" in text
    assert "| 성공 / 전체 (로봇) | 178/192 | 170/192 |" in text
