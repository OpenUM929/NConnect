"""Read-only matched H-A002 comparison; reuse preregistered P0 metrics."""
import argparse
import json
from pathlib import Path

from tools.h1_ha001_p0_readout import SEEDS, case_metrics, judge


def compare(root):
    metrics = {}
    for arm in ('control', 'candidate'):
        for seed in SEEDS:
            files = sorted((root / arm / 'evaluation' / f'seed_{seed}').glob('*/steps.csv'))
            if len(files) != 19:
                raise ValueError(f'{arm} seed{seed}: expected19 cases, got{len(files)}')
            for csv in files:
                summary = json.loads(csv.with_name('summary.json').read_text(encoding='utf8'))
                if summary.get('completed') is not True or summary.get('rows') != 32000:
                    raise ValueError(f'Incomplete {csv}')
                metrics[(arm, seed, csv.parent.name)] = case_metrics(csv)
    judgements = {arm: judge(metrics, arm) for arm in ('control', 'candidate')}
    rows = []
    for (arm, seed, case), candidate in sorted(metrics.items()):
        if arm != 'candidate':
            continue
        control = metrics[('control', seed, case)]
        rows.append({'seed': seed, 'case': case, 'control': control, 'candidate': candidate,
                     'falls_noninferior': candidate['falls'] <= control['falls'],
                     'xy_noninferior': candidate['xy_rmse'] <= control['xy_rmse'] * 1.05,
                     'yaw_noninferior': candidate['yaw_rmse'] <= control['yaw_rmse'] * 1.05})
    highest = {arm: {family: value['verified_highest_vx'] for family, value in j['families'].items()}
               for arm, j in judgements.items()}
    improvements = [family for family in highest['control']
                    if highest['candidate'][family] is not None and
                    (highest['control'][family] is None or highest['candidate'][family] > highest['control'][family])]
    violations = [row for row in rows if not all(row[key] for key in ('falls_noninferior', 'xy_noninferior', 'yaw_noninferior'))]
    return {'work_id': 'H-A002', 'official_result': None, 'video_status': 'VIDEO_UNKNOWN',
            'classification': 'exploratory_one_training_seed', 'highest': highest,
            'improved_families': improvements, 'protection_violations': violations,
            'matched_cases': rows, 'within_policy_judgements': judgements,
            'direction_gate': 'INTERNAL_GATE_PASS' if improvements and not violations else 'INTERNAL_GATE_FAIL',
            'next': 'Independent matched seed only if direction and protection succeed; otherwise retain Run06; no automatic retraining.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf8', newline='\n') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({key: result[key] for key in ('highest', 'improved_families', 'direction_gate')}, ensure_ascii=False))
    print('protection_case_violations', len(result['protection_violations']))
