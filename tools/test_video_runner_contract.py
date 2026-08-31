#!/usr/bin/env python3
"""Static regression contract for the server video runner."""

from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "workspace/training/humanoid/server_run06_videos.sh"


def main() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    required = {
        "generator preflight": "preflight_config H5_rough",
        "up-slope preflight": "preflight_config H6_plus10_approx",
        "down-slope preflight": "preflight_config H6_minus10_approx",
        "preflight video check": "! -s exported/play_video.mp4",
        "preflight policy check": "! -s exported/policy.pt",
        "failure trap": "trap on_exit EXIT",
        "resume fingerprint": ".fingerprint.sha256",
        "artifact hash resume check": ".artifacts.sha256",
        "full exact validation": "validate_full",
        "atomic tar": 'local tmp="${tarball}.tmp"',
    }
    missing = [name for name, marker in required.items() if marker not in text]
    assert not missing, f"missing runner contracts: {missing}"
    assert "terrain_generator.seed=" not in text, "NoneType terrain seed override must not return"
    assert text.count("package_now FULL") == 1, "FULL package must be published exactly once"
    outer_start = text.index('if [[ "${1:-}" != "--inner" ]]')
    inner_start = text.index('cd "$ROOT"', outer_start)
    outer = text[outer_start:inner_start]
    assert "| tee" not in outer, "outer tmux pipeline must not hide inner exit status"
    print("video-runner-contract: PASS")


if __name__ == "__main__":
    main()
