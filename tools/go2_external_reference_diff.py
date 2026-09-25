"""Compare a Go2 env.yaml's reward weights with the external reference (MASTER §1-b, G-D-EXTREF-20260915).

Usage:
    python tools/go2_external_reference_diff.py <env.yaml> [<env.yaml> ...]

Prints one markdown table: Isaac Lab Go2 rough / flat, the deployed start value and each env,
and marks every term that departs from Isaac Lab Go2 rough. The reference is a comparison anchor,
not proof of an optimum.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace/training/quadruped"
REFERENCE = GO2 / "config/go2_external_reference.json"


def load_reference():
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def reward_weights(path):
    spec = importlib.util.spec_from_file_location("candidate_suite_checks", GO2 / "candidate_suite_checks.py")
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    return checks.reward_weights(Path(path).read_text(encoding="utf-8"))


def same(a, b):
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= 1e-12


def fmt(value):
    return "None" if value is None else f"{value:g}"


def deviations(weights, reference=None):
    rough = (reference or load_reference())["isaaclab"]["rewards"]["go2_rough"]
    return {term: (rough[term], weights.get(term)) for term in rough if not same(rough[term], weights.get(term))}


def table(envs):
    ref = load_reference()
    rough = ref["isaaclab"]["rewards"]["go2_rough"]
    flat = ref["isaaclab"]["rewards"]["go2_flat"]
    start = ref["deployed_start"]["rewards"]
    loaded = [(Path(p), reward_weights(p)) for p in envs]
    head = ["항", "IL Go2 rough", "IL Go2 flat", "배포 시작값"] + ["/".join(p.parts[-3:-1]) for p, _ in loaded]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for term in rough:
        cells = [f"`{term}`", fmt(rough[term]), fmt(flat[term]), fmt(start.get(term, rough[term]))]
        for _, weights in loaded:
            value = weights.get(term)
            cells.append(fmt(value) + ("" if same(value, rough[term]) else " **≠**"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 2
    print(f"Isaac Lab {load_reference()['isaaclab']['version']} 기준. **≠** = Go2 rough 값과 다름.")
    print(table(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
