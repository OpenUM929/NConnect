"""계약: 우수 정책 7개의 보상 벡터는 lin_vel_z_l2·ang_vel_xy_l2만 다르다 (2026-10-01 서버 첫 후보 검토 §2-1의 근거)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "vec", Path(__file__).with_name("go2_excellent_reward_vectors.py"))
vec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vec)


def test_only_two_terms_differ():
    _, _, diff = vec.build()
    assert diff == ["ang_vel_xy_l2", "lin_vel_z_l2"]


def test_a043_a048_differ_only_in_lin_vel_z():
    v, terms, _ = vec.build()
    assert [t for t in terms if v["A043"].get(t) != v["A048"].get(t)] == ["lin_vel_z_l2"]


def test_untested_combination_is_a048_with_ang_vel_m008():
    v, _, _ = vec.build()
    pairs = {(p["lin_vel_z_l2"], p["ang_vel_xy_l2"]) for p in v.values()}
    assert (-1.25, -0.08) not in pairs
    assert (-1.5, -0.08) in pairs and (-2.0, -0.08) in pairs
