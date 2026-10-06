"""go2_base_coherence 사전등록 판정 규칙 고정 (2026-10-01).  결과를 본 뒤 문턱을 바꾸면 이 테스트가 깨진다."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_base_coherence as bc  # noqa: E402


def test_thresholds_frozen():
    assert bc.MIN_DECIDED == 12
    assert abs(bc.WIN_SHARE - 2 / 3) < 1e-12
    assert set(bc.VARIABLES) == {"track_lin_vel_xy_exp", "ang_vel_xy_l2", "feet_air_time", "action_rate_l2"}
    assert len(bc.METRICS) == 9


def test_verdict_rule():
    assert bc.verdict(8, 3) == "INSUFFICIENT"
    assert bc.verdict(8, 4) == "LOCAL_BASE_MORE_COHERENT"
    assert bc.verdict(4, 8) == "SERVER_BASE_MORE_COHERENT"
    assert bc.verdict(7, 5) == "INCONCLUSIVE"


def test_residual_is_distance_to_neighbour_line():
    assert bc.residual(1.5, (1.4, 10.0), (1.6, 20.0), 15.0) == 0.0
    assert abs(bc.residual(-0.05, (-0.04, 0.0), (-0.08, 4.0), 3.0) - 2.0) < 1e-9


def test_stationary_neighbours_are_trend_points_not_dropped():
    """2026-10-01 사용자 정정: 정지 정책은 채택 후보 제외 표지일 뿐, 누적 추세 자료에서 빼지 않는다."""
    import inspect
    src = inspect.getsource(bc.main)
    assert "stationary(" not in src
    assert "trend_rows" in inspect.getsource(bc)
