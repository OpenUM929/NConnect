"""Body height over the tread under the base, along the stairs (2026-10-01).

Purpose: define the body state of robots that climb 15/10 cm stairs without an
internal posture judgement, as a reference for reading later runs. height_rel
(root_z - scanner-area mean terrain) is biased near edges, so it is not used.

Geometry (Isaac Lab inverted_pyramid_stairs_terrain, A048 env.yaml; same as
tools/go2_a052_stairs_edge_trajectory.py): tile 8 m, border 1 m, tread 0.3 m,
6 steps, lowest centre platform half-width R0 = 1.2 m. Tread level under a
point = clamp(floor((cheb - R0) / 0.3) + 1, 0, 6), cheb = Chebyshev distance
from the tile centre. Tread height = z_c + level * h.
- Tile centre: evaluation tiles sit on the lattice x = 0, y = 4 + 8k and the
  start pose is centre +/- 0.5 m, so the centre is the nearest lattice point
  to the first row (checked: every start offset is within 0.5 m).
- z_c: median of first-row terrain_z over robots whose 1.6 x 1.0 m scanner
  footprint stays on the centre platform (cheb + 0.95 < R0). Checked against
  every such robot (spread reported in CHECKS.json).
- d = cheb - R0 of the base (negative: before the first edge; 0..0.3: first
  tread; 0.3..0.6: second tread ...). Base, not feet: front feet are ~0.19 m
  ahead of the base.
- body_over_tread = root_z - tread height under the base.
Groups (order from tools/go2_state_order_sink_check.py, internal judgements,
not video-confirmed falls): clean = >= 2 steps and no judgement;
ge2_then_judged; judged_before_ge2; lt2_judged; lt2_unjudged.
First episode rows only. Descriptive only.
"""
from __future__ import annotations

import csv
import json
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_state_outcome import ARMS, KEEP, SEEDS, first_episode, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_stairs_tread_height_20261001'
ORDER = ROOT / 'workspace/training/quadruped/reports/evidence/go2_state_order_sink_20261001/PER_ENV.csv'
R0, TREAD, NSTEP = 1.2, 0.3, 6
CASES = {'stairs_15_down': 0.15, 'stairs_10_down': 0.10}
ARMS_USED = ('A033', 'A038', 'A041', 'A042', 'A043', 'A044', 'A047', 'A048', 'A049', 'A050', 'A055', 'PC_A048')
D_BINS = [round(-0.6 + 0.1 * i, 1) for i in range(16)]  # -0.6 .. 0.9


def centre(x, y):
    return 0.0 + 8 * round(x / 8), 4.0 + 8 * round((y - 4) / 8)


def cheb(x, y, c):
    return max(abs(x - c[0]), abs(y - c[1]))


def level(dc):
    if dc < R0:
        return 0
    return min(NSTEP, math.floor((dc - R0) / TREAD) + 1)


def q(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def group_of(o):
    if o['order'] == 'ge2_no_fall':
        return 'clean'
    if o['order'] == 'ge2_then_fall':
        return 'ge2_then_judged'
    if o['order'] == 'fall_before_ge2':
        return 'judged_before_ge2'
    return 'lt2_judged' if o['fall'] == '1' else 'lt2_unjudged'


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    order = {(r['arm'], r['case'], int(r['seed']), int(r['env'])): r for r in csv.DictReader(ORDER.open(encoding='utf-8'))}
    per_env, prof_rows, zc_checks = [], {}, []
    for arm in ARMS_USED:
        folder = ARMS[arm][0]
        for case, h in CASES.items():
            for seed in SEEDS:
                f = KEEP / folder / 'evaluation/candidate/cases' / f'seed_{seed}' / case / 'steps.csv'
                if not f.exists():
                    continue
                envs = load(f)
                starts = {}
                for env, rows in envs.items():
                    c = centre(rows[0]['root_x'], rows[0]['root_y'])
                    off = (rows[0]['root_x'] - c[0], rows[0]['root_y'] - c[1])
                    assert max(abs(off[0]), abs(off[1])) <= 0.5 + 1e-6, (arm, case, seed, env, off)
                    starts[env] = (c, cheb(rows[0]['root_x'], rows[0]['root_y'], c), rows[0]['terrain_z'])
                inner = [tz for c, dc, tz in starts.values() if dc + 0.95 < R0]
                zc = st.median(inner)
                zc_checks.append(dict(arm=arm, case=case, seed=seed, n=len(inner), zc=zc,
                                      spread=max(inner) - min(inner)))
                for env, rows in sorted(envs.items()):
                    c = starts[env][0]
                    ep = first_episode(rows)
                    o = order[(arm, case, seed, env)]
                    g = group_of(o)
                    samples = []
                    for r in ep:
                        dc = cheb(r['root_x'], r['root_y'], c)
                        samples.append((dc - R0, r['root_z'] - (zc + level(dc) * h), r['time_s']))
                    def win(lo, hi):
                        v = [b for d, b, _ in samples if lo <= d < hi]
                        return st.median(v) if len(v) >= 5 else None
                    rec = dict(arm=arm, case=case, seed=seed, env=env, group=g, zc=zc,
                               max_d=max(d for d, _, _ in samples) if samples else None,
                               approach=win(-0.6, -0.2), edge_zone_min=min([b for d, b, _ in samples if -0.2 <= d < 0.3] or [None]) if any(-0.2 <= d < 0.3 for d, _, _ in samples) else None,
                               tread1=win(0.0, 0.3), tread2=win(0.3, 0.6), tread3=win(0.6, 0.9))
                    per_env.append(rec)
                    for lo in D_BINS:
                        v = [b for d, b, _ in samples if lo <= d < lo + 0.1]
                        if len(v) >= 3:
                            prof_rows.setdefault((arm, case, g, lo), []).append(st.median(v))
            print(arm, case, flush=True)
    profile = []
    for (arm, case, g, lo), v in sorted(prof_rows.items()):
        profile.append(dict(arm=arm, case=case, group=g, d_from=lo, d_to=round(lo + 0.1, 1), envs=len(v),
                            median=st.median(v), q25=q(v, .25), q75=q(v, .75)))
    summary = []
    for arm in ARMS_USED:
        for case in CASES:
            for g in ('clean', 'ge2_then_judged', 'judged_before_ge2', 'lt2_judged', 'lt2_unjudged'):
                rs = [r for r in per_env if r['arm'] == arm and r['case'] == case and r['group'] == g]
                if not rs:
                    continue
                row = dict(arm=arm, case=case, group=g, envs=len(rs))
                for k in ('max_d', 'approach', 'edge_zone_min', 'tread1', 'tread2', 'tread3'):
                    v = [r[k] for r in rs if r[k] is not None]
                    row[f'{k}_n'] = len(v)
                    row[f'{k}_med'] = st.median(v) if v else None
                    row[f'{k}_q25'] = q(v, .25) if v else None
                    row[f'{k}_q75'] = q(v, .75) if v else None
                summary.append(row)
    for name, data in (('PER_ENV.csv', per_env), ('PROFILE_BY_D.csv', profile), ('GROUP_SUMMARY.csv', summary)):
        keys = list(dict.fromkeys(k for d in data for k in d))
        with (OUT / name).open('w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
    (OUT / 'CHECKS.json').write_text(json.dumps(dict(zc=zc_checks, envs=len(per_env)), indent=1), encoding='utf-8')


if __name__ == '__main__':
    run()
