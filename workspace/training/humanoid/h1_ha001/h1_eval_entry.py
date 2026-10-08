"""H-A001 read-only evaluation entry. The distributed play.py is not modified.

The distributed ``play.py`` runs Isaac Lab's play script in a ``python.sh`` child.
This entry follows the same path: it loads the original ``play.py`` as a module
(its ``__main__`` block does not run), re-executes itself through the same
``python.sh`` launcher, installs ``eval_telemetry`` (shipped next to this file),
and then calls the original ``play._runpy_isaaclab_play()``.

It does not stage ``exported/model_best.pt``, does not copy ``policy.pt`` into
``exported/``, and does not write to ``logs/``. The checkpoint comes from the
explicit ``--checkpoint`` argument.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("H1_PROJECT_DIR", str(HERE.parent))).resolve()
CHILD_ENV = "H1_HA001_EVAL_CHILD"


def _load_play():
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("ncrc_h1_play_original", ROOT / "play.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    if not any(a.startswith("--checkpoint") for a in sys.argv[1:]):
        raise SystemExit("[h1-eval] --checkpoint <absolute path> is required")
    play = _load_play()
    play._extract_push_flag()
    if os.environ.get(CHILD_ENV) != "1":
        launcher = play._isaac_python_launcher()
        if launcher:
            env = os.environ.copy()
            env[CHILD_ENV] = "1"
            cmd = [launcher, str(Path(__file__).resolve()), *sys.argv[1:]]
            print(f"[h1-eval] child via {launcher}")
            os._exit(subprocess.run(cmd, cwd=str(ROOT), env=env).returncode)
        print("[h1-eval] [WARN] python.sh not found; running in-process")
    sys.path.insert(0, str(HERE))
    if os.environ.get("NCRC_EVAL_OUT"):
        import eval_telemetry

        eval_telemetry.install()
    sys.argv = [str(ROOT / "play.py"), play.CHILD_FLAG, *sys.argv[1:]]
    play._runpy_isaaclab_play()
    os._exit(0)


if __name__ == "__main__":
    main()
