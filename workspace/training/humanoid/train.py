"""IsaacLab 의 공식 RSL-RL train.py 에 위임 + Humanoid task 등록.

자동:
  1. cwd 를 이 폴더로 변경 → logs/rsl_rl/humanoid/<날짜>/ 에 저장
  2. 학습 종료 후 best model 선별 → exported/ 폴더에 정리 (finalize)

구현 메모 (★ 부모/자식 구조):
  - IsaacLab(Isaac Sim) 는 학습 끝에 simulation_app.close() 로 **C레벨 강제종료**한다
    (Python os._exit 가 아니라 try/except·monkeypatch 로 못 잡음). 같은 프로세스면
    finalize() 가 실행되기 전에 죽음.
  - 또 이 학습을 *자식 프로세스*(python3 -c)로 띄우면 일부 환경(Linux 컨테이너+신형
    GPU)에서 Isaac Sim startup segfault(-11) 발생.
  - 해결: **부모(이 스크립트)가 학습을 `python.sh` 자식으로 실행** →
    ① 자식은 python.sh 의 정상 env 라 segfault 없음 (직접 실행 테스트와 동일),
    ② 자식이 강제종료돼도 *부모는 살아서* finalize() 실행.
  - python.sh 를 못 찾으면 in-process 폴백 (학습은 되나 finalize 는 _finalize.py 로
    수동 필요할 수 있음 — 현행 동작과 동일, 회귀 없음).
  - ⚠️ 부모는 Isaac Sim 을 안 띄우므로 torch/_finalize import 자유. 자식만 학습.

사용법은 README.md 참고.
"""

from __future__ import annotations

import os
import subprocess
import sys
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

# cwd 를 이 폴더로 — IsaacLab train.py 가 logs/ 를 cwd 기준으로 만들기 때문
os.chdir(PROJECT_DIR)

CHILD_FLAG = "--_run_isaaclab_child"   # 부모가 자식을 띄울 때 붙이는 내부 플래그


def _find_isaaclab_train() -> str:
    """IsaacLab rsl_rl train.py 경로 — OS/설치위치 무관 자동 탐지.
    우선순위: ISAACLAB_PATH 환경변수 → 흔한 절대경로 → __file__ 위로 IsaacLab 형제 탐색.
    """
    rel = Path("scripts") / "reinforcement_learning" / "rsl_rl" / "train.py"
    cands = []
    env = os.environ.get("ISAACLAB_PATH")
    if env:
        cands.append(Path(env) / rel)
    cands += [Path("/workspace/IsaacLab") / rel,
              Path.home() / "IsaacLab" / rel,
              Path(r"C:\IsaacLab") / rel]
    for up in Path(__file__).resolve().parents:   # 워크스페이스에서 IsaacLab 형제 자동 탐지
        cands.append(up / "IsaacLab" / rel)
    for c in cands:
        if c.is_file():
            return str(c)
    raise FileNotFoundError(
        "IsaacLab train.py 를 못 찾음. 환경변수로 지정하세요:\n"
        "  Linux  : export ISAACLAB_PATH=/workspace/IsaacLab\n"
        "  Windows: set ISAACLAB_PATH=C:\\IsaacLab")


def _isaac_python_launcher() -> str | None:
    """Isaac Sim 의 python.sh(Linux)/python.bat(Windows) — env 셋업 포함 런처. 없으면 None.
    이걸로 자식을 띄워야 (bare python3 와 달리) Isaac Sim 이 segfault 안 함.
    """
    name = "python.bat" if os.name == "nt" else "python.sh"
    cands = []
    try:
        cands.append(Path(sys.executable).resolve().parents[3] / name)  # <isaac_sim>/python.sh
    except Exception:
        pass
    try:
        ilab = Path(_find_isaaclab_train()).resolve().parents[3]        # <IsaacLab>
        cands.append(ilab / "_isaac_sim" / name)
    except Exception:
        pass
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def _runpy_isaaclab_train() -> None:
    """h1_task 등록 후 IsaacLab train.py 를 in-process runpy 로 실행.
    (IsaacLab 가 끝에 hard-exit 할 수 있음 — 자식 프로세스에서 호출되므로 OK.)
    """
    import runpy
    isaaclab_train = _find_isaaclab_train()
    sys.path.insert(0, str(PROJECT_DIR))
    sys.path.insert(0, os.path.dirname(isaaclab_train))
    import h1_task  # noqa: F401 — gym.register (가벼움: gymnasium + 문자열 등록만, torch X)
    args = [a for a in sys.argv[1:] if a not in (CHILD_FLAG, "--submit")]   # --submit 은 IsaacLab 에 안 넘김 (부모만 사용)
    sys.argv = [isaaclab_train, *args]
    runpy.run_path(isaaclab_train, run_name="__main__")   # 보통 여기서 IsaacLab 가 종료


def run_training() -> int:
    """부모: 학습을 python.sh 자식으로 실행 → 자식이 hard-exit/segfault 해도 부모 생존."""
    if "--task" not in sys.argv:
        print("[ERROR] --task 인자가 없습니다. 명령을 '한 줄' 로 실행했는지 확인하세요.")
        print("        예: isaaclab.sh -p train.py --task Humanoid-v0 --num_envs 4096 --max_iterations 15000 --headless")
        return 2

    launcher = _isaac_python_launcher()
    if launcher:
        cmd = [launcher, str(Path(__file__).resolve()), CHILD_FLAG, *sys.argv[1:]]
        print(f"[INFO] 학습 자식 실행 (env 셋업 python.sh): {launcher}")
        print(f"[INFO]   args: {sys.argv[1:]}")
        print("-" * 70)
        return subprocess.run(cmd, cwd=str(PROJECT_DIR), env=os.environ.copy()).returncode

    # python.sh 미발견 → in-process 폴백 (학습 O / finalize 는 hard-exit 로 생략될 수 있음)
    print("[WARN] python.sh 미발견 → in-process 실행 "
          "(끝나면 h1_task/_finalize.py 로 수동 finalize 필요할 수 있음)")
    _runpy_isaaclab_train()
    return 0


if __name__ == "__main__":
    # play.py 전용 밀침 스위치 — 학습에 새면 env 조건이 팀마다 달라진다.
    os.environ.pop("NCRC_PLAY_PUSH", None)
    # ── 자식 모드: python.sh 가 띄운 실제 학습 프로세스 ──
    if CHILD_FLAG in sys.argv:
        _runpy_isaaclab_train()
        os._exit(0)   # 보통 도달 안 함 (IsaacLab 가 먼저 종료)

    # ── 부모 모드 ──
    print(f"[INFO] Working dir : {PROJECT_DIR}")
    print(f"[INFO] Logs go to  : {PROJECT_DIR / 'logs' / 'rsl_rl' / 'humanoid'}")
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
        from h1_task._finalize import finalize   # 부모는 Isaac Sim 안 띄움 → torch import OK
        meta_result = finalize()
    except KeyboardInterrupt:
        # ⚠️ Ctrl+C 를 **두 번** 누른 경우. 첫 번째는 학습 중단으로 처리했고, 두 번째가
        #    여기(best 선별 = tfevents 읽기, 수십 초)에 떨어진다. KeyboardInterrupt 는
        #    Exception 이 아니라서 아래 except 로는 안 잡히고, 그대로 트레이스백과 함께
        #    끝나 **model_best.pt 가 안 생긴다**(22분 학습의 결과 선별을 잃는다).
        #    체크포인트는 logs/ 에 그대로 있으니 아래 명령으로 그 자리서 복구된다.
        print("\n[WARN] best 선별을 중단했습니다 — model_best.pt 가 만들어지지 않았습니다.")
        print("       체크포인트는 logs/ 에 그대로 있습니다. 아래로 이어서 만들 수 있습니다:")
        print(f"         {_isaac_python_launcher() or 'python3'} h1_task/_finalize.py")
        print("       (이번엔 Ctrl+C 누르지 말고 기다려 주세요 — 기록 읽기에 수십 초 걸립니다)")
    except Exception as e:
        print(f"[WARN] 선별 실패 (학습 결과는 logs/ 에 보존됨): {e}")
        print(f"       수동: {_isaac_python_launcher() or 'python3'} h1_task/_finalize.py")
        traceback.print_exc()

    # (리포트 report.html 생성 + 제출 zip 전송 모두 finalize() 가 자동 수행 — _finalize.py 내장.
    #  플래그 불필요. 자동 백업(제출 아님) 끄려면 env  NO_AUTO_SUBMIT=1)

    # ── 학습 종료 알림 (이메일/ntfy/discord, 설정 안 됐으면 silent skip) ──
    try:
        sys.path.insert(0, str(PROJECT_DIR.parent.parent / "scripts"))
        from notify import send_notification
        details = {"robot": "humanoid", "exit_code": exit_code, "args": " ".join(sys.argv[1:])}
        if meta_result:
            details.update({
                "run":         meta_result.get("run_name", "?"),
                "best_iter":   meta_result.get("best_iter", "?"),
                "best_reward": round(meta_result.get("best_reward") or 0, 2),
            })
        send_notification(
            title=f"[finals_game] Humanoid 학습 종료 (exit={exit_code})",
            body=f"학습 완료 — {PROJECT_DIR / 'exported' / 'model_best.pt'}",
            details=details,
        )
    except Exception as e:
        print(f"[notify] skip: {e}")

    sys.exit(exit_code if isinstance(exit_code, int) else 0)
