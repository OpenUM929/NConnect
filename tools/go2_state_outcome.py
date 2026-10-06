"""Read-only state -> outcome tables for Go2 (rough, stairs, yaw, push).

Extends tools/go2_height_crosscase.py (kept unchanged) to the plan
upload/plan/GO2_STATE_OPTIMUM_ANALYSIS_HANDOFF_20261001.md section 4.
Descriptive only: no causal claim, no reward value is produced here.

Definitions (fixed before reading results):
- height = height_rel = root_z - mean terrain_z under the 1.6 x 1.0 m scanner.
  On stairs the scanner area sees the next step before the body does, so the
  pre-edge height is lower than the body-to-tread distance. Same window, same
  bias for every arm; do not read it as clearance.
- first episode = rows before the first terminated/truncated row (alive_rows).
- fall = posture_gate_v2 union timer over all rows (classify() from
  go2_failure_events, same timer as the evaluator) OR any termination.
  Per-seed sums are checked against summary.json (CHECKS.json).
- early window = 1 <= t < 3 s of the first episode, cut at the first
  upright != 1 row, kept only with >= 25 rows. Envs with < 25 rows are the
  separate 'early_collapsed' stratum, not dropped from the denominators.
- tracking = RMS of error_xy (yaw cases: also error_yaw) over first-episode
  rows with t >= 1 s, before the fall start.
- stairs edge = first row from row 50 whose terrain_z exceeds the row-50
  terrain_z by half a step (crosscase definition). pre-edge = 25 rows before,
  all upright. post-edge = 0..1.5 s after the edge.
- push = config interval 4.0 s (velocity set 0.5 m/s), events at 4/8/12/16 s
  of the first episode. push_detected = a >= 0.3 m/s change of the body
  velocity vector within 0.1 s (body frame, so direction is not checked). Pre-push = [t-1, t), all
  upright. Fell-after = fall start in [t, t+4).
- height bins: width 0.02 m with origin 0 (main), origin 0.01 and width 0.04
  as the single sensitivity check. Bins are reported with their counts; sparse
  bins are not smoothed.
"""
from __future__ import annotations

import csv
import html
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from go2_climb_count import gained_steps  # noqa: E402
from go2_failure_events import classify  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / 'workspace/_keep'
OUT = ROOT / 'workspace/training/quadruped/reports/evidence/go2_state_outcome_20261001'
SEEDS = (101, 202, 303)
DT = 0.02
ARMS = {  # arm -> (keep dir, layer)
    'A033': ('go2_g_a033_a017_track_lin_vel_xy_150', 'server'),
    'A038': ('go2_g_a038_a033_ang_vel_xy_m008', 'server'),
    'A041': ('go2_g_a041_a033_ang_vel_xy_m004', 'server'),
    'A042': ('go2_g_a042_a033_track_lin_vel_xy_160', 'server'),
    'A043': ('go2_g_a043_a033_lin_vel_z_m15', 'server'),
    'A044': ('go2_g_a044_a033_lin_vel_z_m175', 'server'),
    'A047': ('go2_g_a047_a033_flat_orientation_m05', 'server'),
    'A048': ('go2_g_a048_a033_lin_vel_z_m125', 'server'),
    'A049': ('go2_g_a049_a033_lin_vel_z_m1', 'server'),
    'A050': ('go2_g_a050_a033_lin_vel_z_m1375', 'server'),
    'A055': ('go2_g_a055_a043_ang_vel_xy_m008', 'server'),
    'PC_A048': ('go2_g_a058_a048_seed42', 'pc'),
    'PC_track12': ('go2_g_a057_track_lin_vel_xy_exp_p1p2', 'pc'),
}
STATIONARY = {'PC_track12'}  # EXCLUDED_STATIONARY by the preregistered readout
CASES = ('rough_lateral', 'rough_forward', 'stairs_10_down', 'stairs_15_down',
         'combined_yaw_right', 'combined_yaw_left',
         'push_pos_x', 'push_neg_x', 'push_pos_y', 'push_neg_y')
# single reward difference pairs (base, arm, change)
PAIRS = [
    ('A033', 'A044', 'lin_vel_z -2.0->-1.75'), ('A033', 'A043', 'lin_vel_z -2.0->-1.5'),
    ('A033', 'A050', 'lin_vel_z -2.0->-1.375'), ('A033', 'A048', 'lin_vel_z -2.0->-1.25'),
    ('A033', 'A049', 'lin_vel_z -2.0->-1.0'), ('A033', 'A047', 'flat_orientation 0->-0.5'),
    ('A033', 'A038', 'ang_vel_xy -0.05->-0.08'), ('A033', 'A041', 'ang_vel_xy -0.05->-0.04'),
    ('A033', 'A042', 'track 1.5->1.6'), ('A043', 'A055', 'ang_vel_xy -0.05->-0.08 (A043 base)'),
    ('A048', 'PC_A048', 'none: same reward+seed, server->PC'),
]
REWARD_NAMES = ('track_lin_vel_xy_exp', 'feet_air_time', 'lin_vel_z_l2', 'ang_vel_xy_l2',
                'action_rate_l2', 'flat_orientation_l2')
COLS = ('time_s', 'cmd_vx', 'cmd_vy', 'cmd_wz', 'actual_vx', 'actual_vy', 'actual_wz', 'error_xy',
        'error_yaw', 'speed_xy', 'root_x', 'root_y', 'root_z', 'proj_grav_z', 'terrain_z', 'height_rel')


def med(v):
    return st.median(v) if v else None


def q(v, p):
    if not v:
        return None
    s = sorted(v)
    k = (len(s) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def rms(v):
    return math.sqrt(sum(x * x for x in v) / len(v)) if v else None


def tilt_deg(pgz):
    return math.degrees(math.acos(max(-1.0, min(1.0, -pgz))))


def load(path: Path):
    """env -> list of rows (all rows, whole run). Floats for COLS, flags kept."""
    envs = {}
    with path.open(encoding='utf-8', newline='') as fh:
        rd = csv.reader(fh)
        head = next(rd)
        ix = {c: head.index(c) for c in COLS}
        it, itr, iu, ie = head.index('terminated'), head.index('truncated'), head.index('upright'), head.index('env_id')
        for row in rd:
            r = {c: (float(row[i]) if row[i] != '' else None) for c, i in ix.items()}
            r['term'] = row[it] == '1'
            r['trunc'] = row[itr] == '1'
            r['up'] = row[iu] == '1'
            envs.setdefault(int(row[ie]), []).append(r)
    return envs


def first_episode(rows):
    out = []
    for r in rows:
        if r['term'] or r['trunc']:
            break
        out.append(r)
    return out


def bin_label(h, width, origin):
    if h is None:
        return None
    k = math.floor((h - origin) / width + 1e-12)
    lo = origin + k * width
    return f'{lo:.3f}-{lo + width:.3f}'


def early_window(ep):
    win = []
    for r in ep:
        t = r['time_s']
        if t < 1:
            continue
        if t >= 3 or not r['up']:
            break
        win.append(r)
    return win if len(win) >= 25 else None


def window_stats(win, prefix):
    if not win:
        return {f'{prefix}_{k}': None for k in ('h', 'z', 'ground', 'speed', 'tilt', 'err_xy', 'wz', 'along')}
    def along(r):
        n = math.hypot(r['cmd_vx'], r['cmd_vy'])
        return None if n == 0 else (r['actual_vx'] * r['cmd_vx'] + r['actual_vy'] * r['cmd_vy']) / n
    al = [a for a in (along(r) for r in win) if a is not None]
    return {f'{prefix}_h': med([r['height_rel'] for r in win]),
            f'{prefix}_z': med([r['root_z'] for r in win]),
            f'{prefix}_ground': med([r['terrain_z'] for r in win]),
            f'{prefix}_speed': med([r['speed_xy'] for r in win]),
            f'{prefix}_tilt': med([tilt_deg(r['proj_grav_z']) for r in win]),
            f'{prefix}_err_xy': med([r['error_xy'] for r in win]),
            f'{prefix}_wz': med([r['actual_wz'] for r in win]),
            f'{prefix}_along': med(al)}


def env_record(arm, case, seed, env, rows, push_out):
    c = classify(rows)
    term_idx = next((i for i, r in enumerate(rows) if r['term']), None)
    starts = [i for i in (c['union_fall_start'], term_idx) if i is not None]
    fall = bool(c['fu'] or term_idx is not None)
    fall_t = rows[min(starts)]['time_s'] if starts else None
    ep = first_episode(rows)
    ew = early_window(ep)
    rec = dict(arm=arm, layer=ARMS[arm][1], case=case, seed=seed, env=env, fall=int(fall), fall_t=fall_t,
               ep_rows=len(ep), early_collapsed=int(ew is None))
    rec.update(window_stats(ew, 'early'))
    z0 = ep[min(25, len(ep) - 1)] if ep else None
    rec['early_dz_from_0p5s'] = (rec['early_z'] - z0['root_z']) if (ew and z0) else None
    rec['early_dground_from_0p5s'] = (rec['early_ground'] - z0['terrain_z']) if (ew and z0) else None
    trk = [r for r in ep if r['time_s'] >= 1 and (fall_t is None or r['time_s'] < fall_t)]
    rec['trk_rows'] = len(trk)
    rec['trk_xy_rms'] = rms([r['error_xy'] for r in trk])
    rec['trk_yaw_rms'] = rms([r['error_yaw'] for r in trk])
    rec['trk_xy_rms_1to3'] = rms([r['error_xy'] for r in trk if r['time_s'] < 3])
    for k in ('ge2', 'gained', 'reached_edge', 'edge_t', 'preedge_h', 'preedge_speed', 'post_min_h',
              'post_max_rise', 'post_max_tilt'):
        rec[k] = None
    if case.startswith('stairs') and ep:
        height = .10 if '_10_' in case else .15
        g = gained_steps([{'root_z': str(r['root_z']), 'root_x': str(r['root_x']), 'root_y': str(r['root_y'])} for r in ep],
                         'climb', height)
        rec['gained'], rec['ge2'] = g, int(g >= 2)
        base = ep[min(50, len(ep) - 1)]['terrain_z']
        edge = next((i for i in range(50, len(ep)) if ep[i]['terrain_z'] - base > .5 * height), None)
        rec['reached_edge'] = int(edge is not None)
        if edge is not None:
            rec['edge_t'] = ep[edge]['time_s']
            pre = ep[max(0, edge - 25):edge]
            if len(pre) == 25 and all(r['up'] for r in pre):
                rec['preedge_h'] = med([r['height_rel'] for r in pre])
                rec['preedge_speed'] = med([r['speed_xy'] for r in pre])
            post = ep[edge:edge + 75]
            if post:
                rec['post_min_h'] = min(r['height_rel'] for r in post)
                rec['post_max_rise'] = max(r['root_z'] for r in post) - ep[edge]['root_z']
                rec['post_max_tilt'] = max(tilt_deg(r['proj_grav_z']) for r in post)
    if case.startswith('push') and ep:
        for k, t0 in enumerate((4.0, 8.0, 12.0, 16.0)):
            pre = [r for r in ep if t0 - 1 <= r['time_s'] < t0]
            after = [r for r in ep if t0 <= r['time_s'] < t0 + 0.1]
            if len(pre) < 45 or not after:
                continue  # first episode ended before this event
            # world-frame push, body-frame channels, random yaw: use the vector change
            vx0, vy0 = med([r['actual_vx'] for r in pre[-5:]]), med([r['actual_vy'] for r in pre[-5:]])
            jump = max(math.hypot(r['actual_vx'] - vx0, r['actual_vy'] - vy0) for r in after)
            ev = dict(arm=arm, layer=ARMS[arm][1], case=case, seed=seed, env=env, event=k + 1, t=t0,
                      push_detected=int(jump >= 0.3), jump=jump,
                      pre_upright=int(all(r['up'] for r in pre)),
                      pre_h=med([r['height_rel'] for r in pre]),
                      pre_tilt=med([tilt_deg(r['proj_grav_z']) for r in pre]),
                      pre_speed=med([r['speed_xy'] for r in pre]),
                      fell_after=int(fall_t is not None and t0 <= fall_t < t0 + 4),
                      peak_tilt_1p5=max([tilt_deg(r['proj_grav_z']) for r in ep if t0 <= r['time_s'] < t0 + 1.5] or [0]),
                      min_h_1p5=min([r['height_rel'] for r in ep if t0 <= r['time_s'] < t0 + 1.5] or [0]))
            push_out.append(ev)
    return rec


def identity(arm):
    d = KEEP / ARMS[arm][0]
    out = dict(arm=arm, layer=ARMS[arm][1], keep_dir=ARMS[arm][0])
    txt = (d / 'training/ENV_REWARD_CHECK.txt').read_text(encoding='utf-8', errors='replace')
    m = re.search(r'ENV_REWARDS_OK.*', txt)
    env_rw = dict(re.findall(r'(\w+)=(-?[\d.e-]+)', m.group(0))) if m else {}
    for k in REWARD_NAMES:
        out[k] = env_rw.get(k)
    cfg = (d / 'meta/run_config.env').read_text(encoding='utf-8', errors='replace')
    out['train_seed'] = (re.search(r'TRAIN_SEED=(\d+)', cfg) or [None, None])[1]
    out['max_iter'] = (re.search(r'MAX_ITERATIONS=(\d+)', cfg) or [None, None])[1]
    pin = (d / 'training/CHECKPOINT_PIN.txt').read_text(encoding='utf-8', errors='replace')
    out['eval_ckpt_iter'] = (re.search(r'EVAL_CHECKPOINT_ITER=(\d+)', pin) or [None, None])[1]
    out['eval_ckpt_sha12'] = (re.search(r'EVAL_CHECKPOINT_SHA=(\w{12})', pin) or [None, None])[1]
    for f, k in (('meta/evaluator.sha256', 'evaluator_sha12'), ('meta/registry.sha256', 'registry_sha12')):
        p = d / f
        out[k] = p.read_text().split()[0][:12] if p.exists() else None
    rep = d / 'exported/report.html'
    status = 'MISSING'
    if rep.exists():
        t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', rep.read_text(encoding='utf-8'))))
        rep_rw = {k: (re.search(rf'{k} (-?[\d.]+) (-?[\d.]+)', t) or [None, None, None])[2] for k in REWARD_NAMES}
        same = all(rep_rw[k] is None or env_rw.get(k) is None or abs(float(rep_rw[k]) - float(env_rw[k])) < 1e-9
                   for k in REWARD_NAMES if k != 'flat_orientation_l2')
        out['report_rewards'] = ';'.join(f'{k}={rep_rw[k]}' for k in REWARD_NAMES if rep_rw[k] is not None)
        for k, pat in (('report_train_start', r'학습시작 ([\d-]+ [\d:]+)'), ('report_best_reward', r'([\d.]+) 최고 보상'),
                       ('report_terrain_last', r'([\d.]+) 지형 난이도'), ('report_fall_last', r'([\d.]+)% 낙상률'),
                       ('report_std_last', r'([\d.]+) 탐색 std')):
            mm = re.search(pat, t)
            out[k] = mm.group(1) if mm else None
        status = 'READ_MATCHED' if same and out['report_rewards'] else 'READ_UNMATCHED'
    out['REPORT_READ_STATUS'] = status
    return out


def iqr(v):
    return (q(v, .25), q(v, .75)) if v else (None, None)


def write(name, data):
    if not data:
        return
    keys = list(dict.fromkeys(k for d in data for k in d))
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(data)


def summarize(records, pushes):
    a_rows, b_rows, c_rows = [], [], []
    for arm in ARMS:
        for case in CASES:
            g_all = [r for r in records if r['arm'] == arm and r['case'] == case]
            if not g_all:
                continue
            for seed in SEEDS + ('all',):
                g = g_all if seed == 'all' else [r for r in g_all if r['seed'] == seed]
                if not g:
                    continue
                eh = [r['early_h'] for r in g if r['early_h'] is not None]
                lo, hi = iqr(eh)
                surv = [r for r in g if not r['fall']]
                row = dict(arm=arm, layer=ARMS[arm][1], case=case, seed=seed, envs=len(g),
                           early_n=len(eh), early_collapsed=sum(r['early_collapsed'] for r in g),
                           early_h_med=med(eh), early_h_q25=lo, early_h_q75=hi,
                           early_speed=med([r['early_speed'] for r in g if r['early_speed'] is not None]),
                           early_along=med([r['early_along'] for r in g if r['early_along'] is not None]),
                           early_tilt=med([r['early_tilt'] for r in g if r['early_tilt'] is not None]),
                           early_wz=med([r['early_wz'] for r in g if r['early_wz'] is not None]),
                           early_dz=med([r['early_dz_from_0p5s'] for r in g if r['early_dz_from_0p5s'] is not None]),
                           falls=sum(r['fall'] for r in g),
                           trk_xy_surv=med([r['trk_xy_rms'] for r in surv if r['trk_xy_rms'] is not None]),
                           trk_yaw_surv=med([r['trk_yaw_rms'] for r in surv if r['trk_yaw_rms'] is not None]),
                           stationary=int(arm in STATIONARY))
                if case.startswith('stairs'):
                    row.update(ge2=sum(r['ge2'] or 0 for r in g), reached_edge=sum(r['reached_edge'] or 0 for r in g),
                               ge2_then_fell=sum(1 for r in g if r['ge2'] and r['fall']),
                               ge2_and_survived=sum(1 for r in g if r['ge2'] and not r['fall']),
                               preedge_n=sum(r['preedge_h'] is not None for r in g),
                               preedge_h_med=med([r['preedge_h'] for r in g if r['preedge_h'] is not None]))
                if case.startswith('push'):
                    ev = [e for e in pushes if e['arm'] == arm and e['case'] == case and (seed == 'all' or e['seed'] == seed)]
                    row.update(push_events=len(ev), push_detected=sum(e['push_detected'] for e in ev),
                               push_fell_after=sum(e['fell_after'] for e in ev),
                               pre_push_h_med=med([e['pre_h'] for e in ev if e['pre_upright']]))
                a_rows.append(row)
            # Table B: within-policy outcome groups (all seeds)
            groups = {'survived': [r for r in g_all if not r['fall']], 'fell': [r for r in g_all if r['fall']]}
            if case.startswith('stairs'):
                groups.update({'ge2_survived': [r for r in g_all if r['ge2'] and not r['fall']],
                               'ge2_fell': [r for r in g_all if r['ge2'] and r['fall']],
                               'lt2_survived': [r for r in g_all if not r['ge2'] and not r['fall']],
                               'lt2_fell': [r for r in g_all if not r['ge2'] and r['fall']],
                               'ge2': [r for r in g_all if r['ge2']], 'lt2': [r for r in g_all if not r['ge2']],
                               'no_edge': [r for r in g_all if not r['reached_edge']]})
            surv = groups['survived']
            tv = [r['trk_xy_rms'] for r in surv if r['trk_xy_rms'] is not None]
            if tv:
                cut = med(tv)
                groups['survived_trk_better_half'] = [r for r in surv if r['trk_xy_rms'] is not None and r['trk_xy_rms'] <= cut]
                groups['survived_trk_worse_half'] = [r for r in surv if r['trk_xy_rms'] is not None and r['trk_xy_rms'] > cut]
            for name, g in groups.items():
                out = dict(arm=arm, layer=ARMS[arm][1], case=case, group=name, n=len(g))
                for key in ('early_h', 'preedge_h', 'early_tilt', 'early_speed', 'post_max_rise', 'post_max_tilt'):
                    v = [r[key] for r in g if r.get(key) is not None]
                    lo, hi = iqr(v)
                    out.update({f'{key}_n': len(v), f'{key}_med': med(v), f'{key}_q25': lo, f'{key}_q75': hi})
                b_rows.append(out)
            # Table C: height bins on early_h (and preedge_h for stairs)
            for key in ('early_h', 'preedge_h') if case.startswith('stairs') else ('early_h',):
                for width, origin, label in ((.02, 0.0, 'w02_o00'), (.02, .01, 'w02_o01'), (.04, 0.0, 'w04_o00')):
                    bins = {}
                    for r in g_all:
                        b = bin_label(r[key], width, origin)
                        if b is not None:
                            bins.setdefault(b, []).append(r)
                    for b, g in sorted(bins.items()):
                        sv = [r for r in g if not r['fall']]
                        c_rows.append(dict(arm=arm, layer=ARMS[arm][1], case=case, height=key, binning=label, bin=b,
                                           n=len(g), seeds=len({r['seed'] for r in g}), falls=sum(r['fall'] for r in g),
                                           fall_rate=sum(r['fall'] for r in g) / len(g),
                                           ge2=(sum(r['ge2'] or 0 for r in g) if case.startswith('stairs') else None),
                                           trk_xy_surv_med=med([r['trk_xy_rms'] for r in sv if r['trk_xy_rms'] is not None]),
                                           trk_yaw_surv_med=med([r['trk_yaw_rms'] for r in sv if r['trk_yaw_rms'] is not None])))
        # push bins on pre-push height
        for case in [c for c in CASES if c.startswith('push')]:
            ev = [e for e in pushes if e['arm'] == arm and e['case'] == case and e['pre_upright']]
            bins = {}
            for e in ev:
                bins.setdefault(bin_label(e['pre_h'], .02, 0.0), []).append(e)
            for b, g in sorted(bins.items()):
                c_rows.append(dict(arm=arm, layer=ARMS[arm][1], case=case, height='pre_push_h', binning='w02_o00', bin=b,
                                   n=len(g), seeds=len({e['seed'] for e in g}), falls=sum(e['fell_after'] for e in g),
                                   fall_rate=sum(e['fell_after'] for e in g) / len(g)))
    return a_rows, b_rows, c_rows


def pairs_table(a_rows):
    idx = {(r['arm'], r['case']): r for r in a_rows if r['seed'] == 'all'}
    out = []
    for base, arm, change in PAIRS:
        for case in CASES:
            b, a = idx.get((base, case)), idx.get((arm, case))
            if not b or not a:
                continue
            def d(k):
                return None if a.get(k) is None or b.get(k) is None else a[k] - b[k]
            out.append(dict(base=base, arm=arm, change=change, case=case, envs_base=b['envs'], envs_arm=a['envs'],
                            early_h_base=b['early_h_med'], early_h_arm=a['early_h_med'], d_early_h=d('early_h_med'),
                            d_early_tilt=d('early_tilt'), d_early_speed=d('early_speed'), d_early_along=d('early_along'),
                            falls_base=b['falls'], falls_arm=a['falls'], d_falls=d('falls'),
                            d_trk_xy_surv=d('trk_xy_surv'), d_trk_yaw_surv=d('trk_yaw_surv'),
                            ge2_base=b.get('ge2'), ge2_arm=a.get('ge2'), d_ge2=d('ge2'),
                            d_preedge_h=d('preedge_h_med'), push_fell_base=b.get('push_fell_after'),
                            push_fell_arm=a.get('push_fell_after')))
    return out


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    records, pushes, checks = [], [], []
    max_err = 0.0
    for arm, (folder, _) in ARMS.items():
        for case in CASES:
            for seed in SEEDS:
                cdir = KEEP / folder / 'evaluation/candidate/cases' / f'seed_{seed}' / case
                if not (cdir / 'steps.csv').exists() or not (cdir / 'summary.json').exists():
                    continue
                info = json.loads((cdir / 'summary.json').read_text(encoding='utf-8'))
                envs = load(cdir / 'steps.csv')
                recs = []
                for env, rows in sorted(envs.items()):
                    for r in rows:
                        if r['height_rel'] is not None and r['terrain_z'] is not None:
                            max_err = max(max_err, abs(r['height_rel'] - r['root_z'] + r['terrain_z']))
                    recs.append(env_record(arm, case, seed, env, rows, pushes))
                records.extend(recs)
                opt = info.get('posture_fall_env_count_optimistic')
                pes = info.get('posture_fall_env_count_pessimistic')
                mine = sum(r['fall'] for r in recs)
                checks.append(dict(arm=arm, case=case, seed=seed, envs=len(recs), my_falls=mine,
                                   summary_falls_opt=opt, summary_falls_pes=pes,
                                   match=(opt == pes == mine) if opt is not None else None))
            print(arm, case, flush=True)
    a_rows, b_rows, c_rows = summarize(records, pushes)
    write('IDENTITY.csv', [identity(a) for a in ARMS])
    write('PER_ENV.csv', records)
    write('PER_PUSH_EVENT.csv', pushes)
    write('TABLE_A_ARM_CASE_SEED.csv', a_rows)
    write('TABLE_B_WITHIN_POLICY.csv', b_rows)
    write('TABLE_C_HEIGHT_BINS.csv', c_rows)
    write('TABLE_D_REWARD_PAIRS.csv', pairs_table(a_rows))
    write('FALL_COUNT_CHECK.csv', checks)
    # crosscase reproduction: early_h and ge2 per env must equal the earlier tool
    cc = ROOT / 'workspace/training/quadruped/reports/evidence/go2_height_crosscase_20261001/PER_ENV.csv'
    old = {}
    with cc.open(encoding='utf-8') as f:
        for r in csv.DictReader(f):
            old[(r['arm'], r['case'], int(r['seed']), int(r['env']))] = r
    diff_h = diff_ge2 = compared = 0
    for r in records:
        o = old.get((r['arm'], r['case'], r['seed'], r['env']))
        if not o:
            continue
        compared += 1
        oh = float(o['early_h']) if o['early_h'] else None
        if (oh is None) != (r['early_h'] is None) or (oh is not None and abs(oh - r['early_h']) > 1e-9):
            diff_h += 1
        if o['ge2'] != '' and int(o['ge2']) != r['ge2']:
            diff_ge2 += 1
    summary = dict(max_height_arithmetic_error=max_err, fall_check_rows=len(checks),
                   fall_check_mismatch=[c for c in checks if c['match'] is False],
                   crosscase_compared=compared, crosscase_early_h_diff=diff_h, crosscase_ge2_diff=diff_ge2,
                   push_events=len(pushes), push_not_detected=sum(1 for e in pushes if not e['push_detected']))
    (OUT / 'CHECKS.json').write_text(json.dumps(summary, indent=1, default=str), encoding='utf-8')
    print(json.dumps({k: (v if not isinstance(v, list) else len(v)) for k, v in summary.items()}))
    assert max_err < 1e-9


if __name__ == '__main__':
    run()
