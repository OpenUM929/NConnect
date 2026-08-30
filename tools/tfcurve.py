"""tfcurve.py — read RSL-RL tfevents locally, no tensorboard needed.

Why this exists: play.py emits zero performance numbers (F28), so every
quantitative claim about a run has to come from the training tfevents file.
Those files are ~6 MB each and are already on the PC, so this runs with
zero GPU minutes and zero server access.

Usage (from C:\\dev\\NConnect\\workspace\\training\\humanoid):
    python ../../../tools/tfcurve.py list                  # tags of every run
    python ../../../tools/tfcurve.py window Run04 Run05    # windowed means + slopes
    python ../../../tools/tfcurve.py dump Run05 Metrics/base_velocity/error_vel_yaw

TFRecord frame:  uint64 length | uint32 crc | payload | uint32 crc
Event proto:     1=wall_time(f64) 2=step(varint) 5=summary(msg)
Summary proto:   1=value(repeated msg)
Value proto:     1=tag(str) 2=simple_value(f32)
"""
from __future__ import annotations

import glob
import os
import struct
import sys

BASE = os.path.join("logs", "rsl_rl", "humanoid")

RUNS = {
    "Run01": "2026-08-28_08-15-40",
    "Run02": "2026-08-28_09-48-44",
    "Run03": "2026-08-28_20-36-33",
    "Run04": "2026-08-28_21-59-39",
    "Run05": "2026-08-29_16-22-32",
}

KEYS = [
    "Metrics/base_velocity/error_vel_xy",
    "Metrics/base_velocity/error_vel_yaw",
    "Episode_Termination/base_contact",
    "Curriculum/terrain_levels",
    "Policy/mean_std",
    "Train/mean_episode_length",
    "Train/mean_reward",
    "Episode_Reward/feet_air_time",
    "Loss/learning_rate",
]


def _varint(buf, i):
    r = s = 0
    while True:
        b = buf[i]
        i += 1
        r |= (b & 0x7F) << s
        if not b & 0x80:
            return r, i
        s += 7


def _fields(buf):
    i, n = 0, len(buf)
    while i < n:
        key, i = _varint(buf, i)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
            yield fn, wt, v
        elif wt == 1:
            yield fn, wt, buf[i:i + 8]; i += 8
        elif wt == 2:
            ln, i = _varint(buf, i)
            yield fn, wt, buf[i:i + ln]; i += ln
        elif wt == 5:
            yield fn, wt, buf[i:i + 4]; i += 4
        else:
            raise ValueError("wire %d" % wt)


def scalars(path):
    with open(path, "rb") as f:
        data = f.read()
    i, n = 0, len(data)
    while i + 12 <= n:
        (ln,) = struct.unpack_from("<Q", data, i)
        i += 12
        if i + ln + 4 > n:
            break
        rec = data[i:i + ln]
        i += ln + 4
        summary = None
        try:
            for fn, wt, val in _fields(rec):
                if fn == 5 and wt == 2:
                    summary = val
            if summary is None:
                continue
            for fn, wt, val in _fields(summary):
                if fn != 1 or wt != 2:
                    continue
                tag = sv = None
                for f2, w2, v2 in _fields(val):
                    if f2 == 1 and w2 == 2:
                        tag = v2.decode("utf-8", "replace")
                    elif f2 == 2 and w2 == 5:
                        (sv,) = struct.unpack("<f", v2)
                if tag is not None and sv is not None:
                    yield tag, sv
        except Exception:
            continue


def load(run):
    d = RUNS.get(run, run)
    hits = glob.glob(os.path.join(BASE, d, "events.out.tfevents.*"))
    if not hits:
        raise SystemExit("no tfevents under %s" % os.path.join(BASE, d))
    s = {}
    for tag, v in scalars(hits[0]):
        s.setdefault(tag, []).append(v)   # file order == iteration order
    return s


def slope_per_1k(xs):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = (n - 1) / 2.0, sum(xs) / n
    num = sum((i - mx) * (y - my) for i, y in enumerate(xs))
    den = sum((i - mx) ** 2 for i in range(n))
    return num / den * 1000.0


def cmd_list():
    for name in RUNS:
        s = load(name)
        k = next(iter(s))
        print("%s  tags=%d  iters=%d" % (name, len(s), len(s[k])))


def cmd_window(runs):
    S = {r: load(r) for r in runs}
    print("%-24s %10s %10s %10s %10s" % ("tag", "final", "mean(-500)", "slope/1k", "run"))
    for k in KEYS:
        for r in runs:
            xs = S[r].get(k)
            if not xs:
                continue
            print("%-24s %10.4f %10.4f %10.5f   %s" %
                  (k.split("/")[-1], xs[-1], sum(xs[-500:]) / len(xs[-500:]),
                   slope_per_1k(xs[-1000:]), r))
        print("-" * 68)


def cmd_dump(run, tag, every=100):
    xs = load(run)[tag]
    for i in range(0, len(xs), every):
        print("%6d %12.5f" % (i, xs[i]))
    print("%6d %12.5f" % (len(xs) - 1, xs[-1]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    op = sys.argv[1]
    if op == "list":
        cmd_list()
    elif op == "window":
        cmd_window(sys.argv[2:] or ["Run04", "Run05"])
    elif op == "dump":
        cmd_dump(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
