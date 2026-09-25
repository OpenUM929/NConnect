"""Plain checks the candidate-suite runner needs on the server.

Standard library only: no Isaac Sim import and no GPU.  The server has no
system ``python3`` on PATH, so the runner hands this file to whatever
interpreter it resolved, as it does posture_contract_check.py.

    <interpreter> candidate_suite_checks.py env-rewards <env.yaml> <expected_rewards.json> <role>
        exit 0 when the trained env.yaml carries exactly the role's reward weights
    <interpreter> candidate_suite_checks.py moving <summary.json>
        exit 0 when the case is not stationary, 1 when it is, 2 when unreadable

The reward file ignores an unknown name with only a warning, so the trained
env.yaml is the evidence of which weights were in force, not the source file.

"Stationary" is the locomotion floor go2_fixed_eval_report.build_policy
applies to every case: mean planar speed under 0.10 m/s while the case's own
tracking RMSE is at least 0.30.  The same numbers, so the gate cannot call a
policy stationary that the scorer would call walking, or the reverse.
"""

import json
import math
import re
import sys

TOLERANCE = 1e-9
STATIONARY_SPEED = 0.10
STATIONARY_RMSE = 0.30


def reward_weights(text):
    """Return {term: weight} from the top-level ``rewards:`` block of an env.yaml.

    A term written as ``name: null`` is undefined in the env and maps to None.
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip() == "rewards:")
    except StopIteration:
        return {}
    weights = {}
    term = None
    term_indent = None
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            break
        if term_indent is None:
            term_indent = indent
        if indent == term_indent:
            match = re.match(r"^\s*([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
            term = match.group(1) if match else None
            if term and match.group(2) == "null":
                weights[term] = None
                term = None
            continue
        match = re.match(r"^\s*weight:\s*(\S+)\s*$", line)
        if match and term and term not in weights:
            weights[term] = float(match.group(1))
    return weights


def env_rewards(env_path, expected_path, role):
    expected = json.load(open(expected_path, encoding="utf-8"))[role]
    found = reward_weights(open(env_path, encoding="utf-8").read())
    bad = []
    for name, value in expected.items():
        seen = found.get(name)
        if seen is None or abs(seen - float(value)) > TOLERANCE:
            bad.append("%s=%r expected %r" % (name, seen, value))
    if bad:
        sys.stderr.write("ENV_REWARDS_MISMATCH role=%s: %s\n" % (role, ", ".join(bad)))
        return 1
    print("ENV_REWARDS_OK role=%s %s" % (role, " ".join("%s=%r" % (k, found[k]) for k in expected)))
    return 0


def moving(summary_path):
    try:
        data = json.load(open(summary_path, encoding="utf-8"))
    except (OSError, ValueError) as error:
        sys.stderr.write("summary unreadable: %s\n" % error)
        return 2
    speed = data.get("speed_xy_mean")
    rmse = data.get("tracking_xy_rmse")
    for key, value in (("speed_xy_mean", speed), ("tracking_xy_rmse", rmse)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            sys.stderr.write("summary %s=%r is not a finite number\n" % (key, value))
            return 2
    stationary = speed < STATIONARY_SPEED and rmse >= STATIONARY_RMSE
    print("LOCOMOTION %s speed_xy_mean=%.4f tracking_xy_rmse=%.4f"
          % ("STATIONARY" if stationary else "MOVING", speed, rmse))
    return 1 if stationary else 0


def main(argv):
    if len(argv) == 5 and argv[1] == "env-rewards":
        return env_rewards(argv[2], argv[3], argv[4])
    if len(argv) == 3 and argv[1] == "moving":
        return moving(argv[2])
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
