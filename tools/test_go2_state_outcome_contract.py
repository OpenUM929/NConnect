"""Contract tests for tools/go2_state_outcome.py (synthetic rows + produced evidence)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import go2_state_outcome as so  # noqa: E402


def row(t, z=0.40, ground=0.05, up=True, term=False, vx=0.0, vy=0.0, cmd=(0.0, 0.0), pgz=-1.0):
    return dict(time_s=t, cmd_vx=cmd[0], cmd_vy=cmd[1], cmd_wz=0.0, actual_vx=vx, actual_vy=vy, actual_wz=0.0,
                error_xy=0.1, error_yaw=0.05, speed_xy=abs(vx) + abs(vy), root_x=0.0, root_y=0.0, root_z=z,
                proj_grav_z=pgz, terrain_z=ground, height_rel=z - ground, term=term, trunc=False, up=up)


def rows_for(seconds, **kw):
    return [row(round((i + 1) * so.DT, 4), **kw) for i in range(int(seconds / so.DT))]


def test_bin_boundaries():
    assert so.bin_label(0.24, .02, 0.0) == '0.240-0.260'
    assert so.bin_label(0.2399999, .02, 0.0) == '0.220-0.240'
    assert so.bin_label(0.24, .02, .01) == '0.230-0.250'
    assert so.bin_label(None, .02, 0.0) is None


def test_early_window_censor_and_min_rows():
    rows = rows_for(4)
    assert len(so.early_window(rows)) == 100  # 1 <= t < 3 s
    # non-upright at 1.4 s leaves < 25 rows -> collapsed stratum
    bad = [dict(r, up=r['time_s'] < 1.4) for r in rows]
    assert so.early_window(bad) is None
    ok = [dict(r, up=r['time_s'] < 1.6) for r in rows]
    assert len(so.early_window(ok)) >= 25


def test_first_episode_cuts_at_termination():
    rows = rows_for(4)
    rows[60]['term'] = True
    assert len(so.first_episode(rows)) == 60


def test_fall_from_termination_and_posture_timer():
    rows = rows_for(6)
    rows[150]['term'] = True
    rec = so.env_record('A048', 'rough_lateral', 101, 0, rows, [])
    assert rec['fall'] == 1 and abs(rec['fall_t'] - rows[150]['time_s']) < 1e-9
    low = [dict(r, root_z=0.10, height_rel=0.05) if r['time_s'] >= 2 else r for r in rows_for(6)]
    rec = so.env_record('A048', 'rough_lateral', 101, 0, low, [])
    assert rec['fall'] == 1 and 1.99 <= rec['fall_t'] <= 2.01
    rec = so.env_record('A048', 'rough_lateral', 101, 0, rows_for(6), [])
    assert rec['fall'] == 0 and rec['early_collapsed'] == 0


def test_push_event_detection_and_episode_limit():
    rows = rows_for(10)
    for r in rows:
        if 4.0 <= r['time_s'] < 4.1 or 8.0 <= r['time_s'] < 8.1:
            r['actual_vx'] = 0.5
    out = []
    so.env_record('A048', 'push_pos_x', 101, 0, rows, out)
    assert [e['event'] for e in out] == [1, 2]  # 12 s and 16 s are beyond the 10 s episode
    assert all(e['push_detected'] == 1 for e in out)
    out = []
    so.env_record('A048', 'push_neg_x', 101, 0, rows_for(10), out)
    assert [e['push_detected'] for e in out] == [0, 0]  # no velocity change, no push


def test_stairs_preedge_requires_upright_window():
    rows = rows_for(6)
    for r in rows:
        if r['time_s'] >= 3:
            r['terrain_z'] = 0.20
            r['height_rel'] = r['root_z'] - 0.20
    rec = so.env_record('A043', 'stairs_15_down', 101, 0, rows, [])
    assert rec['reached_edge'] == 1 and rec['preedge_h'] is not None
    rows[140]['up'] = False  # inside the 25 rows before the edge at 3.0 s
    rec = so.env_record('A043', 'stairs_15_down', 101, 0, rows, [])
    assert rec['preedge_h'] is None


def test_produced_evidence_reproduces_counts():
    checks = json.loads((so.OUT / 'CHECKS.json').read_text(encoding='utf-8'))
    assert checks['max_height_arithmetic_error'] < 1e-9
    assert checks['fall_check_mismatch'] == []
    assert checks['crosscase_compared'] > 4000
    assert checks['crosscase_early_h_diff'] == 0 and checks['crosscase_ge2_diff'] == 0
    # 20/16533 undetected (2026-10-01): mostly robots already down before the push
    assert checks['push_not_detected'] / checks['push_events'] < 0.005



def test_t_ge2_matches_climb_rule():
    import go2_state_order_sink_check as osc
    rows = rows_for(8)
    for r in rows:
        r['root_x'] = r['time_s'] * 0.5
        if r['time_s'] >= 5:
            r['root_z'] = 0.40 + 0.21  # rise 0.21: 2 steps of 10 cm (needs >= 0.17), 1 step of 15 cm
    assert abs(osc.t_ge2(rows, .10) - 5.0) < 1e-6
    assert osc.t_ge2(rows, .15) is None
    flat = rows_for(8)
    assert osc.t_ge2(flat, .10) is None



def test_channel_split():
    import go2_state_channel_split as cs
    ok = rows_for(6)
    assert cs.channel(ok) == 'none'
    low = [dict(r, root_z=0.20, height_rel=0.15) if r['time_s'] >= 2 else r for r in rows_for(6)]
    assert cs.channel(low) == 'height_only'
    tilt = [dict(r, proj_grav_z=-0.3) if r['time_s'] >= 2 else r for r in rows_for(6)]
    assert cs.channel(tilt) == 'tilt_or_both'
    term = rows_for(6)
    term[200]['term'] = True
    assert cs.channel(term) == 'terminated'


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
