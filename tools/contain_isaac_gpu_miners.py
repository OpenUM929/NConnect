"""One-shot reversible containment of the positively identified PC2 miners.

Run elevated with the Isaac venv Python. Never delete signed Windows executables.
Identity checks prevent touching unrelated processes after PID reuse.
"""
import argparse
import json
from pathlib import Path
import re
import time

import psutil


def verified_processes(evidence):
    rows = {row['Id']: row for row in evidence['Processes']}
    ids = [2588, 5780, 21840]
    processes = []
    for pid in ids:
        row = rows[pid]
        p = psutil.Process(pid)
        expected_time = int(re.fullmatch(r'/Date\((\d+)\)/', row['Created'])[1]) / 1000
        if abs(p.create_time() - expected_time) > 0.01:
            raise RuntimeError(f'PID {pid}: creation time mismatch')
        if p.exe().lower() != row['Path'].lower() or p.ppid() != row['ParentId']:
            raise RuntimeError(f'PID {pid}: path/parent mismatch')
        cmd = ' '.join(p.cmdline())
        if pid == 5780 and not ('rx/0' in cmd and 'ssl-maimai.com:27039' in cmd):
            raise RuntimeError('CPU miner command mismatch')
        if pid == 21840 and not ('progpowz' in cmd and 'pool.zh.woolypooly.com:3146' in cmd):
            raise RuntimeError('GPU miner command mismatch')
        if pid == 2588:
            if p.name().lower() != 'svchost.exe':
                raise RuntimeError('Parent process mismatch')
            if any(s.pid() == pid for s in psutil.win_service_iter()):
                raise RuntimeError('Refusing to suspend a registered Windows service')
        processes.append(p)
    return processes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check', 'suspend', 'resume'])
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    processes = verified_processes(json.loads(args.evidence.read_text(encoding='utf-8-sig')))
    before = {p.pid: p.status() for p in processes}
    changed = []
    try:
        # Freeze the launcher before its children; resume it last.
        for p in reversed(processes) if args.action == 'resume' else processes:
            if args.action == 'suspend' and before[p.pid] != psutil.STATUS_STOPPED:
                p.suspend()
                changed.append(p)
            elif args.action == 'resume' and before[p.pid] == psutil.STATUS_STOPPED:
                p.resume()
                changed.append(p)
        result = {
            'time': time.time(), 'action': args.action, 'changed': [p.pid for p in changed],
            'before': before, 'after': {p.pid: p.status() for p in processes},
            'training_pid_untouched': 22380,
        }
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result))
    except BaseException:
        for p in reversed(changed):
            if args.action == 'suspend':
                p.resume()
            elif args.action == 'resume':
                p.suspend()
        raise


if __name__ == '__main__':
    main()
