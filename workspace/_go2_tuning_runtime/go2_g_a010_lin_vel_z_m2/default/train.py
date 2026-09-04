"""IsaacLab 공식 RSL-RL train.py 위임 + quadruped task 등록.

자동:
  1. cwd 를 이 폴더로 변경 → logs/rsl_rl/quadruped/<날짜>/ 에 저장
  2. 학습 종료 후 best model 선별 → exported/ 폴더에 정리 (finalize)

구현 (★ 부모/자식 — humanoid/train.py 와 동일):
  - Isaac Sim 은 끝에 C레벨 강제종료 → 같은 프로세스면 finalize 못 돎.
  - 자식 프로세스(python3 -c)로 띄우면 일부 환경서 startup segfault(-11).
  - 해결: 부모가 학습을 `python.sh` 자식으로 실행 → 자식은 정상 env(segfault X),
    부모는 살아서 finalize 실행. python.sh 없으면 in-process 폴백.

사용:
    isaaclab.sh -p train.py --task Quadruped-v0 --num_envs 4096 --max_iterations 15000 --headless
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

os.chdir(PROJECT_DIR)

CHILD_FLAG = "--_run_isaaclab_child"


def _find_isaaclab_train() -> str:
    """IsaacLab rsl_rl train.py 경로 — OS/설치위치 무관 자동 탐지."""
    rel = Path("scripts") / "reinforcement_learning" / "rsl_rl" / "train.py"
    cands = []
    env = os.environ.get("ISAACLAB_PATH")
    if env:
        cands.append(Path(env) / rel)
    cands += [Path("/workspace/IsaacLab") / rel,
              Path.home() / "IsaacLab" / rel,
              Path(r"C:\IsaacLab") / rel]
    for up in Path(__file__).resolve().parents:
        cands.append(up / "IsaacLab" / rel)
    for c in cands:
        if c.is_file():
            return str(c)
    raise FileNotFoundError(
        "IsaacLab train.py 를 못 찾음. 환경변수로 지정하세요:\n"
        "  Linux  : export ISAACLAB_PATH=/workspace/IsaacLab\n"
        "  Windows: set ISAACLAB_PATH=C:\\IsaacLab")


def _isaac_python_launcher() -> str | None:
    """Isaac Sim python.sh(Linux)/python.bat(Windows) — env 셋업 런처. 없으면 None."""
    name = "python.bat" if os.name == "nt" else "python.sh"
    cands = []
    try:
        cands.append(Path(sys.executable).resolve().parents[3] / name)
    except Exception:
        pass
    try:
        ilab = Path(_find_isaaclab_train()).resolve().parents[3]
        cands.append(ilab / "_isaac_sim" / name)
    except Exception:
        pass
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def _runpy_isaaclab_train() -> None:
    """go2_task 등록 후 IsaacLab train.py 를 in-process runpy (자식에서 호출)."""
    import runpy
    isaaclab_train = _find_isaaclab_train()
    sys.path.insert(0, str(PROJECT_DIR))
    sys.path.insert(0, os.path.dirname(isaaclab_train))
    import go2_task  # noqa: F401 — gym.register (가벼움)
    args = [a for a in sys.argv[1:] if a not in (CHILD_FLAG, "--submit")]   # --submit 은 IsaacLab 에 안 넘김 (부모만 사용)
    sys.argv = [isaaclab_train, *args]
    runpy.run_path(isaaclab_train, run_name="__main__")


def run_training() -> int:
    """부모: 학습을 python.sh 자식으로 실행 → 자식 종료해도 부모 생존 → finalize."""
    if "--task" not in sys.argv:
        print("[ERROR] --task 인자가 없습니다. 명령을 '한 줄' 로 실행했는지 확인하세요.")
        print("        예: isaaclab.sh -p train.py --task Quadruped-v0 --num_envs 4096 --max_iterations 15000 --headless")
        return 2

    launcher = _isaac_python_launcher()
    if launcher:
        cmd = [launcher, str(Path(__file__).resolve()), CHILD_FLAG, *sys.argv[1:]]
        print(f"[INFO] 학습 자식 실행 (env 셋업 python.sh): {launcher}")
        print(f"[INFO]   args: {sys.argv[1:]}")
        print("-" * 70)
        return subprocess.run(cmd, cwd=str(PROJECT_DIR), env=os.environ.copy()).returncode

    print("[WARN] python.sh 미발견 → in-process 실행 "
          "(끝나면 go2_task/_finalize.py 로 수동 finalize 필요할 수 있음)")
    _runpy_isaaclab_train()
    return 0


if __name__ == "__main__":
    # play.py 전용 밀침 스위치 — 학습에 새면 env 조건이 팀마다 달라진다.
    os.environ.pop("NCRC_PLAY_PUSH", None)
    os.environ.pop("NCRC_PLAY_PUSH_X", None)
    os.environ.pop("NCRC_PLAY_PUSH_Y", None)
    if CHILD_FLAG in sys.argv:
        _runpy_isaaclab_train()
        os._exit(0)

    print(f"[INFO] Working dir : {PROJECT_DIR}")
    print(f"[INFO] Logs go to  : {PROJECT_DIR / 'logs' / 'rsl_rl' / 'quadruped'}")
    print(f"[INFO] Final output: {PROJECT_DIR / 'exported' / 'model_best.pt'}  (+ env.yaml)")

    try:
        exit_code = run_training()
    except KeyboardInterrupt:
        # Ctrl+C — 자식(학습)은 subprocess 가 정리함. 트레이스백 없이 지금까지
        # 저장된 체크포인트로 best 선별(model_best.pt 생성) 까지 진행.
        print("\n[INFO] Ctrl+C 감지 — 학습 중단. 지금까지 체크포인트로 best 선별합니다...")
        exit_code = 130

    print("\n" + "=" * 70)
    print(f"[POST] 학습 종료 (exit={exit_code}) → best model 선별 → {PROJECT_DIR}")
    print("=" * 70)
    meta_result = None
    try:
        from go2_task._finalize import finalize
        meta_result = finalize()
    except KeyboardInterrupt:
        # ⚠️ Ctrl+C 를 **두 번** 누른 경우. 첫 번째는 학습 중단으로 처리했고, 두 번째가
        #    여기(best 선별 = tfevents 읽기, 수십 초)에 떨어진다. KeyboardInterrupt 는
        #    Exception 이 아니라서 아래 except 로는 안 잡히고, 그대로 트레이스백과 함께
        #    끝나 **model_best.pt 가 안 생긴다**(22분 학습의 결과 선별을 잃는다).
        #    체크포인트는 logs/ 에 그대로 있으니 아래 명령으로 그 자리서 복구된다.
        print("\n[WARN] best 선별을 중단했습니다 — model_best.pt 가 만들어지지 않았습니다.")
        print("       체크포인트는 logs/ 에 그대로 있습니다. 아래로 이어서 만들 수 있습니다:")
        print(f"         {_isaac_python_launcher() or 'python3'} go2_task/_finalize.py")
        print("       (이번엔 Ctrl+C 누르지 말고 기다려 주세요 — 기록 읽기에 수십 초 걸립니다)")
    except Exception as e:
        print(f"[WARN] 선별 실패 (학습 결과는 logs/ 에 보존됨): {e}")
        print(f"       수동: {_isaac_python_launcher() or 'python3'} go2_task/_finalize.py")
        traceback.print_exc()

    # (리포트 report.html 생성 + 제출 zip 전송 모두 finalize() 가 자동 수행 — _finalize.py 내장.
    #  플래그 불필요. 자동 백업(제출 아님) 끄려면 env  NO_AUTO_SUBMIT=1)

    try:
        sys.path.insert(0, str(PROJECT_DIR.parent.parent / "scripts"))
        from notify import send_notification
        details = {"robot": "quadruped", "exit_code": exit_code, "args": " ".join(sys.argv[1:])}
        if meta_result:
            details.update({
                "run":         meta_result.get("run_name", "?"),
                "best_iter":   meta_result.get("best_iter", "?"),
                "best_reward": round(meta_result.get("best_reward") or 0, 2),
            })
        send_notification(
            title=f"[finals_game] Quadruped 학습 종료 (exit={exit_code})",
            body=f"학습 완료 — {PROJECT_DIR / 'exported' / 'model_best.pt'}",
            details=details,
        )
    except Exception as e:
        print(f"[notify] skip: {e}")

    sys.exit(exit_code if isinstance(exit_code, int) else 0)
