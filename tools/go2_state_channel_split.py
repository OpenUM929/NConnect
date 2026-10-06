"""Height level x fall-judgement channel (interpretation table, 2026-10-01).

The internal posture gate (posture_gate_v2) judges a fall when tilt OR
height_rel < 0.18 m persists 0.5 s, or the episode terminates. Using height
as the explanatory variable while the gate also uses a height threshold can
create part of the association by construction. This tool splits every
judgement into channels and re-reads the within-policy level association
with judgements that do not use the 0.18 m height threshold.

Channels per env (whole run, same timer as the evaluator):
  terminated  - any termination (base contact)
  height_only - no termination, height timer only
  tilt_or_both- no termination, tilt timer alone satisfied (with or without height)
  union_only  - no termination, only the combined timer (tilt and height
                violations alternating) - uses the height threshold
  none        - no judgement
Non-height judgement = terminated or tilt_or_both (union_only excluded).
Height sensitivity = height_rel < 0.12 m for 0.5 s (no termination needed),
reported as an extra column only, not as a fall definition.
Level groups: early_h (1-3 s, as go2_state_outcome) vs the policy's own
median over envs with an early_h; envs without early_h are 'collapsed'.
Preregistered judgements are not changed. Descriptive only.
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_failure_events import DT, GRACE_S, HOLD_S, TILT_COS, classify  # noqa: E402
from go2_state_outcome import ARMS, KEEP, SEEDS, STATIONARY, env_record, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_state_channel_split_20261001'
CASES = ('rough_lateral', 'rough_forward', 'stairs_10_down', 'stairs_15_down', 'combined_yaw_right')
CHANNELS = ('terminated', 'height_only', 'tilt_or_both', 'union_only', 'none')


def channel(rows):
    if any(r['term'] for r in rows):
        return 'terminated'
    c = classify(rows)['channel']
    if c in ('height_only', 'union_only'):
        return c
    return 'tilt_or_both' if c in ('tilt_only', 'both') else 'none'


def timer_hit(rows, bad):
    run = 0.0
    for r in rows:
        if r['time_s'] < GRACE_S:
            continue
        run = run + DT if bad(r) else 0.0
        if run >= HOLD_S - 1e-9:
            return True
    return False


def med(v):
    return st.median(v) if v else None


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
                    b = env_record(arm, case, seed, env, rows, [])
                    ch = channel(rows)
                    assert (ch != 'none') == bool(b['fall']), (arm, case, seed, env)
                    recs.append(dict(arm=arm, layer=layer, case=case, seed=seed, env=env, channel=ch,
                                     fall=b['fall'], early_h=b['early_h'], ge2=b['ge2'],
                                     trk_xy_rms=b['trk_xy_rms'],
                                     tilt_timer=int(timer_hit(rows, lambda r: not r['proj_grav_z'] <= -TILT_COS)),
                                     h012_timer=int(timer_hit(rows, lambda r: r['height_rel'] is None or r['height_rel'] < 0.12))))
            print(arm, flush=True)
    table = []
    for arm in [a for a in ARMS if a not in STATIONARY]:
        for case in CASES:
            g = [r for r in recs if r['arm'] == arm and r['case'] == case]
            if not g:
                continue
            m = med([r['early_h'] for r in g if r['early_h'] is not None])
            groups = {'all': g,
                      'high': [r for r in g if r['early_h'] is not None and r['early_h'] >= m],
                      'low': [r for r in g if r['early_h'] is not None and r['early_h'] < m],
                      'collapsed': [r for r in g if r['early_h'] is None]}
            for name, gg in groups.items():
                row = dict(arm=arm, layer=ARMS[arm][1], case=case, group=name, level_median=m, n=len(gg),
                           judged=sum(r['fall'] for r in gg))
                for c in CHANNELS:
                    row[c] = sum(r['channel'] == c for r in gg)
                row['non_height'] = row['terminated'] + row['tilt_or_both']
                row['tilt_timer_any'] = sum(r['tilt_timer'] for r in gg)
                row['h012_timer_any'] = sum(r['h012_timer'] for r in gg)
                row['trk_unjudged_med'] = med([r['trk_xy_rms'] for r in gg if not r['fall'] and r['trk_xy_rms'] is not None])
                if case.startswith('stairs'):
                    row['ge2'] = sum(r['ge2'] or 0 for r in gg)
                    for c in CHANNELS:
                        row[f'ge2_{c}'] = sum(1 for r in gg if r['ge2'] and r['channel'] == c)
                table.append(row)
    for name, data in (('PER_ENV.csv', recs), ('LEVEL_BY_CHANNEL.csv', table)):
        keys = list(dict.fromkeys(k for d in data for k in d))
        with (OUT / name).open('w', encoding='utf-8', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(data)
    (OUT / 'CHECKS.json').write_text(json.dumps(dict(envs=len(recs), channel_matches_fall=True), indent=1),
                                     encoding='utf-8')


if __name__ == '__main__':
    run()
