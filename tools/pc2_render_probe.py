"""Isolated renderer startup probe; never loads a policy or changes task code."""
import argparse
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser()
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
print(f"PROBE_ARGS={args}", flush=True)
launcher = AppLauncher(args)
print("PROBE_STARTUP_OK", flush=True)
for _ in range(10):
    launcher.app.update()
print("PROBE_UPDATES_OK", flush=True)
launcher.app.close()
