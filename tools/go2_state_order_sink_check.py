"""Two local corrections to tools/go2_state_outcome.py (2026-10-01).

1. Stairs event order: time of reaching >= 2 steps (same rule as
   go2_climb_count.gained_steps) versus fall start (posture_gate_v2 union
   timer or termination). 'climbed then fell' needs t_ge2 < fall_t.
2. Low versus sinking: level = early-window height (1-3 s, as before);
   trend = change inside the same upright window.
   - rough: height_rel median 2.5-3.0 s minus 1.0-1.5 s (>= 10 rows each).
   - stairs: root_z on the flat approach (world z, scanner-free):
     median of the last 0.5 s before the scanner terrain rises 0.01 m above
     the row-50 terrain, minus median 1.0-1.5 s. Robots whose flat approach
     ends before 2.0 s get no trend.
   'low' = level below the policy's own median (same case, all seeds).
   'sank' = trend <= -0.01 m (fixed before reading results).
Descriptive only.
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_climb_count import MIN_TRAVEL_M, SETTLE_ROW, STEP_TOLERANCE  # noqa: E402
from go2_state_outcome import ARMS, KEEP, SEEDS, STATIONARY, early_window, env_record, first_episode, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_state_order_sink_20261001'
CASES = ('rough_lateral', 'stairs_10_down', 'stairs_15_down')
SINK = -0.01


def med(v):
    return st.median(v) if v else None


def t_ge2(ep, height):
    """First time the gained_steps rule reaches 2 steps, else None."""
    if not ep:
        return None
    z0 = ep[min(SETTLE_ROW, len(ep) - 1)]['root_z']
    x0, y0 = ep[0]['root_x'], ep[0]['root_y']
    for r in ep:
        if (r['root_x'] - x0) ** 2 + (r['root_y'] - y0) ** 2 < MIN_TRAVEL_M ** 2:
            continue
        if int((r['root_z'] - z0 + STEP_TOLERANCE * height) // height) >= 2:
            return r['time_s']
    return None


def trend(ep, case):
    win = early_window(ep)
    if not win:
        return None
    if case == 'rough_lateral':
        a = [r['height_rel'] for r in win if r['time_s'] < 1.5]
        b = [r['height_rel'] for r in win if r['time_s'] >= 2.5]
        return med(b) - med(a) if len(a) >= 10 and len(b) >= 10 else None
    base = ep[min(50, len(ep) - 1)]['terrain_z']
    flat_end = next((r['time_s'] for r in ep if r['time_s'] >= 1 and r['terrain_z'] - base > 0.01), None)
    if flat_end is None or flat_end < 2.0:
        return None
    a = [r['root_z'] for r in ep if 1.0 <= r['time_s'] < 1.5 and r['up']]
    b = [r['root_z'] for r in ep if flat_end - 0.5 <= r['time_s'] < flat_end and r['up']]
    return med(b) - med(a) if len(a) >= 10 and len(b) >= 10 else None


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for arm, (folder, layer) in ARMS.items():
        if arm in STATIONARY:
            continue
        for case in CASES:
            for seed in SEEDS:
                f = KEEP / folder / 'evaluation/candidate/cases' / f'seed_{seed}' / case / 'steps.csv'
                if not f.exists():
                    continue
                for env, rows in sorted(load(f).items()):
                    base = env_record(arm, case, seed, env, rows, [])
                    ep = first_episode(rows)
                    rec = dict(arm=arm, layer=layer, case=case, seed=seed, env=env, fall=base['fall'],
                               fall_t=base['fall_t'], early_h=base['early_h'], trend=trend(ep, case),
                               ge2=base['ge2'], t_ge2=None, order=None)
                    if case.startswith('stairs'):
                        t = t_ge2(ep, .10 if '_10_' in case else .15)
                        rec['t_ge2'] = t
                        assert (t is not None) == bool(base['ge2']), (arm, case, seed, env)
                        if t is not None:
                            rec['order'] = ('ge2_no_fall' if not base['fall'] else
                                            'ge2_then_fall' if base['fall_t'] > t else 'fall_before_ge2')
                    recs.append(rec)
            print(arm, flush=True)
    # level/trend classes relative to the policy's own median
    rows_out, order_out = [], []
    for arm in [a for a in ARMS if a not in STATIONARY]:
        for case in CASES:
            g = [r for r in recs if r['arm'] == arm and r['case'] == case]
            if not g:
                continue
            m = med([r['early_h'] for r in g if r['early_h'] is not None])
            for r in g:
                r['low'] = None if r['early_h'] is None else int(r['early_h'] < m)
                r['sank'] = None if r['trend'] is None else int(r['trend'] <= SINK)
            out = dict(arm=arm, layer=ARMS[arm][1], case=case, envs=len(g), level_median=m,
                       trend_n=sum(r['trend'] is not None for r in g),
                       trend_median=med([r['trend'] for r in g if r['trend'] is not None]))
            for lo in (0, 1):
                for sk in (0, 1):
                    cell = [r for r in g if r['low'] == lo and r['sank'] == sk]
                    key = f"{'low' if lo else 'high'}_{'sank' if sk else 'steady'}"
                    out[f'{key}_n'] = len(cell)
                    out[f'{key}_falls'] = sum(r['fall'] for r in cell)
                    if case.startswith('stairs'):
                        out[f'{key}_ge2'] = sum(r['ge2'] or 0 for r in cell)
            for lo in (0, 1):
                cell = [r for r in g if r['low'] == lo]
                out[f"{'low' if lo else 'high'}_trend_median"] = med([r['trend'] for r in cell if r['trend'] is not None])
            rows_out.append(out)
            if case.startswith('stairs'):
                o = [r for r in g if r['order']]
                gaps = [r['fall_t'] - r['t_ge2'] for r in o if r['order'] == 'ge2_then_fall']
                order_out.append(dict(arm=arm, case=case, ge2=len(o),
                                      ge2_no_fall=sum(r['order'] == 'ge2_no_fall' for r in o),
                                      ge2_then_fall=sum(r['order'] == 'ge2_then_fall' for r in o),
                                      fall_before_ge2=sum(r['order'] == 'fall_before_ge2' for r in o),
                                      t_ge2_median=med([r['t_ge2'] for r in o]),
                                      gap_median=med(gaps), gap_min=min(gaps) if gaps else None,
                                      gap_max=max(gaps) if gaps else None))
    for name, data in (('PER_ENV.csv', recs), ('LEVEL_TREND.csv', rows_out), ('STAIRS_ORDER.csv', order_out)):
        keys = list(dict.fromkeys(k for d in data for k in d))
        with (OUT / name).open('w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
    (OUT / 'CHECKS.json').write_text(json.dumps(dict(envs=len(recs), ge2_rule_consistent=True,
                                                     sink_threshold_m=SINK), indent=1), encoding='utf-8')


if __name__ == '__main__':
    run()
