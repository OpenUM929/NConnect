"""The posture contract every case summary must satisfy before it is banked.

Plain JSON arithmetic: it does not import Isaac Sim and does not touch the GPU.
It still needs a Python interpreter, and the competition server has no system
``python3`` on PATH -- every other runner in this campaign only ever called
``/workspace/IsaacLab/isaaclab.sh -p``, and this runner was the first to add a
bare ``python3``, which stopped it at preflight on 260909.  Installing an
interpreter would be a change to the training environment, so the runner
resolves one from what is already on the machine and hands this file to it.
It is a file rather than a heredoc on stdin because ``isaaclab.sh -p`` does not
forward ``-`` as a script to read from stdin.

A substring test is not a value test.  measurement_contract carries the literal
string "posture_gate_v2" on every summary, including one whose survival number
is null because the posture channels were never read -- so the old
``grep -q posture_gate_v2`` passed on exactly the file it existed to reject.
Check the decided fields, check that the coverage behind them is real, check
that the rows that were not observed could not have changed who fell, and check
that the physics produced finite numbers at all: inf passes every threshold
test in the gate, so an exploded step read as a perfectly upright robot.

    <interpreter> posture_contract_check.py <summary.json>
"""

import json, math, sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
bad = []


def number(key):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        bad.append("%s=%r" % (key, value))
        return None
    return value


if data.get("schema_version") != 6:
    bad.append("schema_version=%r" % data.get("schema_version"))
if data.get("nonfinite_row_count") != 0:
    bad.append("nonfinite_row_count=%r" % data.get("nonfinite_row_count"))
if data.get("posture_fall_verdict_ambiguous") is not False:
    bad.append("posture_fall_verdict_ambiguous=%r"
               % data.get("posture_fall_verdict_ambiguous"))
if data.get("survival_proxy_source") != "posture_gate_v2":
    bad.append("survival_proxy_source=%r" % data.get("survival_proxy_source"))
if data.get("posture_measured") is not True:
    bad.append("posture_measured=%r" % data.get("posture_measured"))
if data.get("completed") is not True:
    bad.append("completed=%r" % data.get("completed"))
number("survival_proxy")
number("tracking_xy_rmse")
required = number("posture_min_coverage_required")
for key in ("posture_coverage", "posture_min_env_coverage"):
    seen = number(key)
    if seen is not None and required is not None and seen < required:
        bad.append("%s=%r<%r" % (key, seen, required))
if bad:
    sys.stderr.write("posture contract violated: " + ", ".join(bad) + "\n")
    sys.exit(1)
