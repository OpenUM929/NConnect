"""Apply the pre-existing G-A077 thresholds to its matched G-A074 comparison."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workspace/training/quadruped'))
import go2_fixed_eval_report as evaluator
from tools.go2_climb_count import count

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'workspace/training/quadruped/config/go2_self_eval_registry.json'
SEEDS = (101, 202, 303)


def read(root):
    identity = json.loads((root / 'identity.json').read_text(encoding='utf8'))
    result = evaluator.build_policy(root, REGISTRY, identity)
    if result['missing'] or result['observed_telemetry_count'] != 69:
        raise ValueError('Incomplete evaluation; no adoption decision')
    return result


def compare(candidate_root, baseline_root):
    candidate, baseline = read(candidate_root), read(baseline_root)
    assert candidate['identity']['model_sha256'] == '23c08ab15617b0001ee90d20c2682cf78041d80058bd83c1d090fdf94d756ca1'
    assert baseline['identity']['model_sha256'] == 'd39b88e9a6b06fd08498c90bbba334a3aaaca1cc8e540102c7d0e284bac72211'
    for key in ('registry_sha256', 'evaluator_sha256'):
        assert candidate['identity'][key] == baseline['identity'][key]
    assert set(candidate['cases']) == set(baseline['cases'])
    violations = []
    for case, row in candidate['cases'].items():
        for metric in ('survival_proxy', 'tracking_proxy'):
            old, new = baseline['cases'][case]['proxy'][metric], row['proxy'][metric]
            if new < old - 1e-9:
                violations.append({'case': case, 'metric': metric, 'baseline': old, 'candidate': new})
    stairs = {}
    for case in ('stairs_10_down', 'stairs_15_down'):
        stairs[case] = {}
        for seed in SEEDS:
            relative = Path('cases') / f'seed_{seed}' / case / 'steps.csv'
            height = 0.10 if case == 'stairs_10_down' else 0.15
            stairs[case][str(seed)] = {'baseline': count(baseline_root / relative, height), 'candidate': count(candidate_root / relative, height)}
    directional = all(stairs['stairs_15_down'][str(seed)]['candidate']['full'] > 0 and stairs['stairs_15_down'][str(seed)]['candidate']['ge2'] >= minimum for seed, minimum in zip(SEEDS, (17, 19, 14)))
    ten_cm = all(stairs['stairs_10_down'][str(seed)]['candidate']['ge2'] >= minimum for seed, minimum in zip(SEEDS, (32, 30, 28)))
    progress = all(candidate['cases'][f'G5/stairs_15_down/seed_{seed}']['raw']['projected_progress_m'] >= baseline['cases'][f'G5/stairs_15_down/seed_{seed}']['raw']['projected_progress_m'] - 1e-9 for seed in SEEDS)
    return {
        'official_result': False, 'candidate_status': candidate['status'],
        'candidate_proxy_70': candidate['simulation_points_70'], 'baseline_proxy_70': baseline['simulation_points_70'],
        'candidate_scenarios': candidate['scenarios'], 'baseline_scenarios': baseline['scenarios'],
        'stairs': stairs, 'directional_hypothesis_supported': directional,
        'all_69_case_protection': not violations, 'protection_violations': violations,
        'ten_cm_protection': ten_cm, 'fifteen_cm_progress_protection': progress,
        'preregistered_candidate_preservation': directional and not violations and ten_cm and progress,
        'next': 'H1 transition; retain G-A074; no automatic extra Go2 trial',
        'limitations': 'Full is six-step body-height/travel proxy, not video-verified completion. Protection failure alone does not refute the directional mechanism.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compare(Path('C:/workspace/_keep/go2_g_a077_flat_orientation_m0p225/evaluation/candidate'), Path('C:/workspace/_keep/go2_g_a074_report_policy/evaluation/candidate'))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf8', newline='\n') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({key: value for key, value in result.items() if key not in ('candidate_scenarios', 'baseline_scenarios', 'stairs', 'protection_violations')}, ensure_ascii=False))
    print(json.dumps(result['stairs'], ensure_ascii=False))
