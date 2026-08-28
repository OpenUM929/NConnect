"""IsaacLab 의 공식 RSL-RL play.py 에 위임 + Humanoid task 등록.

══════════════════════════════════════════════════════════════════════
결과물 폴더: training/humanoid/exported/  (한 곳에 모두)
  ★ model_best.pt  : 예선 채점용 (train.py 가 만듦)
  ★ env.yaml       : 학습 환경 dump
  ★ policy.pt      : 본선 매치용 (play.py 가 export)
══════════════════════════════════════════════════════════════════════

구현 메모:
  IsaacLab play.py 는 sim_app.close() + os._exit() 로 process 강제 종료.
  같은 process 에서 runpy 로 실행하면 finally 블록 실행 안 됨 →
  _export_policy_to_exported() 가 작동 X.

  해결: subprocess 분리 (train.py 와 동일 패턴). 자식 process 가 죽어도
  메인 wrapper 는 살아서 export 후처리 가능.

자동 처리:
  실행 전:  exported/model_best.pt → logs/<latest>/ sync (IsaacLab 호환)
  실행 중:  IsaacLab 가 logs/<run>/exported/policy.pt 생성 (JIT export)
  실행 후:  logs/<run>/exported/policy.pt → exported/policy.pt 복사

사용:
  isaaclab.bat -p play.py --task Humanoid-v0 --num_envs 4
  isaaclab.sh -p play.py --task Humanoid-v0 --num_envs 1 --headless --video --push   # 밀침 테스트
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import h1_task  # noqa: F401 — gym.register (가벼움: gymnasium + 문자열 등록만)

PROJECT_DIR   = Path(__file__).resolve().parent
EXPORT_DIR    = PROJECT_DIR / "exported"
LOGS_ROOT     = PROJECT_DIR / "logs" / "rsl_rl" / "humanoid"


def _find_isaaclab_play() -> str:
    """IsaacLab rsl_rl play.py 경로 — OS/설치위치 무관 자동 탐지 (train.py 와 동일 규칙)."""
    rel = Path("scripts") / "reinforcement_learning" / "rsl_rl" / "play.py"
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
        "IsaacLab play.py 를 못 찾음. 환경변수: export ISAACLAB_PATH=/workspace/IsaacLab")


_RUN_START_TS = __import__("time").time()

CHILD_FLAG = "--_run_isaaclab_child"


def _isaac_python_launcher() -> str | None:
    """Isaac Sim python.sh/python.bat — env 셋업 런처 (자식 segfault 방지). 없으면 None."""
    name = "python.bat" if os.name == "nt" else "python.sh"
    cands = []
    try:
        cands.append(Path(sys.executable).resolve().parents[3] / name)
    except Exception:
        pass
    try:
        ilab = Path(_find_isaaclab_play()).resolve().parents[3]
        cands.append(ilab / "_isaac_sim" / name)
    except Exception:
        pass
    for c in cands:
        if c.is_file():
            return str(c)
    return None


def _runpy_isaaclab_play() -> None:
    """h1_task 등록 후 IsaacLab play.py 를 in-process runpy (자식에서 호출)."""
    import runpy
    isaaclab_play = _find_isaaclab_play()
    sys.path.insert(0, str(PROJECT_DIR))
    sys.path.insert(0, os.path.dirname(isaaclab_play))
    args = [a for a in sys.argv[1:] if a != CHILD_FLAG]
    # 부모가 이미 --checkpoint 를 붙여 넘겼다 (여기선 그대로 전달)
    sys.argv = [isaaclab_play, *args]
    runpy.run_path(isaaclab_play, run_name="__main__")


# ⭐ 재생 대상은 **오직 `exported/model_best.pt`** 하나다.
#    IsaacLab play.py 는 `--checkpoint <절대경로>` 를 그대로 로드하고(125~126행,
#    `retrieve_file_path`), JIT export 를 **그 파일 옆 `exported/`** 에 만든다(171행).
#    → 그래서 `exported/model_best.pt` 를 직접 가리키면
#         · policy.pt  → exported/exported/policy.pt
#         · 영상        → exported/videos/play/*.mp4
#      로 생기고, wrapper 가 `exported/` 직속으로 올려 복사한다. logs/ 를 거치지 않는다.
#
# ⚠️ 왜 이렇게 바꿨나 (2026-08-24 실측 사고):
#    예전엔 체크포인트 선택을 IsaacLab 의 **알파벳순 자동 탐색**에 맡겼다. 그런데
#     ① `logs/` 에 `model_best` 라는 폴더가 있으면(예전 구현이 만들었다) `2026-…` 보다
#        뒤라 **모든 play 가 거기서 로드**했고,
#     ② 한 run 안에서도 `model_900.pt` 가 `model_4500.pt` 를 이겨(`9 > 4`) **best 가
#        아닌 중간 체크포인트**를 재생했다(30번 서버 실측).
#    결과: 서로 다른 두 학습의 제출 `policy.pt` 가 **비트 단위로 동일**하고 각 run 의
#    `model_best.pt` 와도 일치하지 않았다(가중치 298,259개 중 같은 값 0개).


def _stage_best() -> Path | None:
    """재생할 체크포인트(`exported/model_best.pt`) 경로. 없으면 None.

    ⭐ 이 자리에 파일을 **올려놓기만 하면** 그대로 재생된다 — 본인 PC 에서 받아 둔
       pt 를 올리거나 타임스탬프 백업을 `model_best.pt` 로 덮어써도 된다.
       (별도 옵션 없이 규칙이 하나: 최신 학습 결과가 이 이름으로 남는다.)
    """
    best_pt = EXPORT_DIR / "model_best.pt"
    if not best_pt.exists():
        legacy = PROJECT_DIR / "model_best.pt"
        if legacy.exists():
            best_pt = legacy
            print(f"[play] legacy 위치 사용: {legacy}")
        else:
            print("[play] [WARN] exported/model_best.pt 없음 — 학습(train.py)을 먼저 하세요")
            print(f"       기대 위치: {EXPORT_DIR}/model_best.pt")
            return None

    # IsaacLab 이 이번 실행에서 새로 쓸 자리 — 옛 파일이 남아 있으면 지운다.
    stale = best_pt.parent / "exported"
    if stale.is_dir():
        shutil.rmtree(stale, ignore_errors=True)

    # 예전 구현이 logs/ 에 만든 `model_best` 폴더는 알파벳순 마지막이라
    # **학습 resume** 의 자동 선택을 가로챈다 → 이름만 앞으로 바꿔 무력화(내용 보존).
    poison = LOGS_ROOT / "model_best"
    if poison.is_dir():
        safe = LOGS_ROOT / "0000_legacy_model_best"
        try:
            if safe.exists():
                shutil.rmtree(poison)
            else:
                poison.rename(safe)
            print(f"[play] 옛 logs/model_best 폴더 무력화 → {safe.name}")
        except OSError as e:
            print(f"[play] [WARN] 옛 model_best 폴더 정리 실패: {e}")

    print(f"[play] 재생 대상: {best_pt}")
    return best_pt


def _inject_load_args(argv: list[str], ckpt: Path | None) -> list[str]:
    """IsaacLab 에 **어느 파일인지 절대 경로로** 넘긴다 (자동 탐색에 맡기지 않는다).

    사용자가 직접 `--checkpoint` 를 준 경우는 존중하고 건드리지 않는다.
    """
    if ckpt is None or any(a.startswith("--checkpoint") for a in argv):
        return list(argv)
    return list(argv) + ["--checkpoint", str(ckpt)]


def _export_policy_to_exported(ckpt: Path | None = None) -> bool:
    """이번 play 가 만든 `policy.pt` 만 `exported/` 로 복사한다.

    ⚠️ **예전 구현의 사고** (2026-08-24): `logs/` 와 `exported/` 를 통째로 뒤져
       *가장 최근 mtime* 을 복사했다. IsaacLab 이 export 를 못 한 경우(창을 닫지
       않거나 비정상 종료) **`exported/` 에 있던 이전 policy.pt·백업이 후보로 잡혀
       자기 자신을 다시 복사**하고 "export 완료" 를 찍었다. 그래서 서로 다른 학습의
       제출 `policy.pt` 가 **비트 단위로 동일**해졌다. 제출물이 policy.pt 이므로
       참가자가 자기 학습 결과가 아닌 파일을 내게 된다.
       → 이제 **이번 run 폴더 안**만 보고, 없으면 **조용히 넘기지 않고 실패를 알린다.**
    """
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if ckpt is None:
        print("[play] [WARN] 재생 대상이 없어 export 를 건너뜁니다"
              " (exported/model_best.pt 가 없었습니다).")
        return False
    run = Path(ckpt).parent / "exported"      # IsaacLab 이 여기에 JIT 을 쓴다

    started = _RUN_START_TS
    found_any = False
    for filename in ("policy.pt", "policy.onnx"):
        # ★ 이번 run 폴더 안에서만 찾는다 (exported/ 를 뒤지지 않는다 — 자기 복사 방지)
        cands = [c for c in run.rglob(filename) if c.is_file()] if run.is_dir() else []
        # 이번 실행 중에 새로 쓰인 것만 (옛 파일이 폴더에 남아 있을 여지 차단)
        fresh = [c for c in cands if c.stat().st_mtime >= started - 5]
        if not fresh:
            if cands:
                print(f"[play] [WARN] {filename} 이 이번 실행에서 새로 만들어지지 않았습니다"
                      " — 옛 파일은 쓰지 않습니다.")
            continue
        cand = max(fresh, key=lambda p: p.stat().st_mtime)
        dest = EXPORT_DIR / filename
        shutil.copy(cand, dest)
        stem, suffix = Path(filename).stem, Path(filename).suffix
        dest_ts = EXPORT_DIR / f"{stem}_{ts}{suffix}"
        shutil.copy(cand, dest_ts)
        print("=" * 70)
        print(f"[play] ★ {filename} export 완료")
        print(f"       원본: {cand}")
        print(f"       복사: {dest}   (백업 {dest_ts.name})")
        print("=" * 70)
        found_any = True

    if not found_any:
        print("=" * 70)
        print("[play] 🔴 policy.pt 가 만들어지지 않았습니다 — exported/policy.pt 는"
              " **갱신되지 않았습니다.**")
        print("       IsaacLab 은 시뮬 창을 정상적으로 닫을 때 export 합니다.")
        print("       창을 닫고(또는 --headless 로) 다시 실행하세요.")
        print(f"       확인: ls -l {run}")
        print("       ⚠️ 지금 exported/policy.pt 는 **이전 실행의 파일**입니다 —"
              " 그대로 제출하면 이번 학습 결과가 아닙니다.")
        print("=" * 70)
    return found_any


def _export_video_to_exported() -> bool:
    """logs 안 가장 최근 play 영상(.mp4)을 exported/ 로 복사. latest + timestamp 백업.

    --video 로 녹화한 경우에만 호출 (finally 에서 guard). policy.pt 와 동일 패턴:
    자식(IsaacLab play.py)이 logs/<run>/videos/play/ 에 mp4 저장 후 종료 →
    부모(이 wrapper)가 exported/ 직속으로 복사.
    """
    # IsaacLab 은 영상을 `<체크포인트 폴더>/videos/play/` 에 쓴다 → exported/ 아래.
    roots = [r for r in (EXPORT_DIR, LOGS_ROOT) if r.exists()]
    if not roots:
        print(f"[play] [WARN] 찾을 폴더 없음: {EXPORT_DIR}, {LOGS_ROOT}")
        return False

    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    vids = [v for r in roots for v in r.rglob("*.mp4")
            if v.parent.name != EXPORT_DIR.name]        # exported/ 직속 복사본은 제외
    if not vids:
        print("[play] [WARN] 영상(.mp4) 못 찾음 — --video 녹화가 끝까지 됐는지 확인")
        return False

    cand = max(vids, key=lambda p: p.stat().st_mtime)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    dest = EXPORT_DIR / "play_video.mp4"
    dest_ts = EXPORT_DIR / f"play_video_{ts}.mp4"
    shutil.copy(cand, dest)
    shutil.copy(cand, dest_ts)
    print("=" * 70)
    print("[play] ★ 영상 export 완료")
    print(f"       원본: {cand}")
    print(f"       복사: {dest}")
    print(f"       백업: {dest_ts.name}")
    print("=" * 70)
    return True


def _extract_push_flag() -> None:
    """`--push [세기 m/s]` 를 argv 에서 떼어 환경변수로 전달.

    IsaacLab play 의 argparse 가 모르는 인자라 argv 에 남기면 죽는다 → 여기서
    소비하고, env_cfg 가 NCRC_PLAY_PUSH 를 읽어 밀침 이벤트를 켠다(4초 간격).
    세기 생략 시 0.5 m/s. ⚠️ play 전용 — train.py 는 이 변수를 지운다.
    """
    if "--push" not in sys.argv:
        return
    i = sys.argv.index("--push")
    strength = "0.5"
    if i + 1 < len(sys.argv):
        try:
            float(sys.argv[i + 1])
            strength = sys.argv.pop(i + 1)
        except ValueError:
            pass
    sys.argv.remove("--push")
    os.environ["NCRC_PLAY_PUSH"] = strength
    print(f"[play] 밀침 테스트 — 4초마다 무작위 방향 ±{strength} m/s 충격을 가합니다")


def run_play() -> int:
    """부모: play 를 python.sh 자식으로 실행 → 자식이 강제종료해도 부모 생존 →
    __main__ 의 finally(policy.pt export 복사)가 실행됨. (train.py 와 동일 구조.)
    python.sh 없으면 in-process 폴백 (export 가 생략될 수 있음).
    """
    launcher = _isaac_python_launcher()
    if launcher:
        cmd = [launcher, str(Path(__file__).resolve()), CHILD_FLAG,
               *_inject_load_args(sys.argv[1:], play_ckpt)]
        print(f"[play] play 자식 실행 (env 셋업 python.sh): {launcher}")
        print(f"[play]   args: {sys.argv[1:]}")
        print("-" * 70)
        return subprocess.run(cmd, cwd=str(PROJECT_DIR), env=os.environ.copy()).returncode

    print("[play] [WARN] python.sh 미발견 → in-process (policy.pt export 가 생략될 수 있음)")
    _runpy_isaaclab_play()
    return 0


def _tidy_after_play(ckpt: Path | None, policy_ok: bool, video_ok: bool) -> None:
    """play 가 남긴 중간 산출물 정리 — exported/ 안에 폴더가 또 생겨 헷갈리지 않게.

    IsaacLab 은 출력 자리를 체크포인트 경로에서 파생시켜서
      · JIT   → exported/exported/          · 영상 → exported/videos/play/
      · hydra 로그 → outputs/<날짜>/<시각>/
    에 만들고, 래퍼가 최종본만 exported/ 직속으로 복사한다. 복사가 끝난 중간
    산출물은 참가자에게 혼란만 준다("익스포티드 안에 또 생겨") → 여기서 지운다.

    ⚠️ **복사가 성공한 것만 지운다** — 실패했으면 그 폴더가 유일본이라 남겨 둔다
       (어차피 다음 play 시작 때 _stage_best 가 치운다).
    """
    try:
        if policy_ok and ckpt is not None:
            inner = Path(ckpt).parent / "exported"
            if inner.is_dir():
                shutil.rmtree(inner, ignore_errors=True)
        if video_ok or "--video" not in sys.argv:
            vids = EXPORT_DIR / "videos"
            if vids.is_dir():
                shutil.rmtree(vids, ignore_errors=True)
        # hydra 로그 — 이번 실행이 만든 것만 (mtime 기준). 과거 학습 로그는 안 건드린다.
        outs = PROJECT_DIR / "outputs"
        if outs.is_dir():
            for d in sorted(outs.glob("*/*")):
                if d.is_dir() and d.stat().st_mtime >= _RUN_START_TS - 5:
                    shutil.rmtree(d, ignore_errors=True)
            for d in sorted(outs.glob("*")):          # 빈 날짜 폴더 → outputs 까지
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
            if not any(outs.iterdir()):
                outs.rmdir()
    except OSError as e:
        print(f"[play] [WARN] 중간 산출물 정리 실패(무해): {e}")


def _guard_gpu_free(need_mb: int = 4000) -> None:
    """GPU 여유가 부족하면 실행을 거부한다.

    ⚠️ [2026-08-22] 참가자가 tmux 로 `play.py` **21개**를 동시에 띄워 서버가 마비된
    사고(38번/.105). 실제로 뜬 것은 **5개**(GPU 16GB ÷ Isaac Sim 3~4GB)이고 나머지는
    메모리 부족으로 실패했으며, 그 5개가 자원을 다 써 **code-server(같은 컨테이너)까지
    응답 불가**가 됐다. 안내만으로는 막히지 않으니 여기서 거부한다.

    ⭐ 프로세스 개수를 세지 않고 **GPU 여유를 직접 본다** — play.py 는 부모/자식 구조라
    `pgrep` 으로 세면 자기 자신이 잡혀 과다 계산된다. 학습(train.py)이 GPU 를 쓰는 중에도
    같은 이유로 막히는 게 맞다(둘 다 느려지거나 OOM).
    ⚠️ `nvidia-smi` 가 없거나 실패하면 **조용히 통과** — 가드가 실행을 막아선 안 된다.
    """
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip().splitlines()[0]
        free_mb, total_mb = (int(x.strip()) for x in out.split(","))
    except Exception:                                    # noqa: BLE001
        return
    if free_mb >= need_mb:
        return
    print("=" * 70)
    print(f"🔴 GPU 여유 메모리 부족 — {free_mb} MB / 전체 {total_mb} MB (필요 약 {need_mb} MB)")
    print("")
    print("   Isaac Sim 은 하나당 GPU 3~4 GB 를 씁니다.")
    print("   이미 실행 중인 학습이나 play.py 가 있으면 끝난 뒤에 다시 실행하세요.")
    print("   실행 중인 것 확인:  nvidia-smi")
    print("")
    print("   💡 여러 로봇·여러 지형을 한 번에 보려면 play.py 를 여러 개 띄우지 말고")
    print("      한 프로세스에서 --num_envs 를 늘리세요 (로봇 16대를 한 화면에):")
    print("        play.py --task Humanoid-v0 --num_envs 16 --headless --video \\")
    print("            --enable_cameras env.viewer.origin_type=world \\")
    print('            env.viewer.eye="[35.0,35.0,22.0]" env.viewer.lookat="[8.0,8.0,0.0]"')
    print("")
    print("   (가드 무시: PLAY_SKIP_GPU_CHECK=1)")
    print("=" * 70)
    sys.exit(1)


if __name__ == "__main__":
    _extract_push_flag()
    # ── 자식 모드: python.sh 가 띄운 실제 play 프로세스 ──
    if CHILD_FLAG in sys.argv:
        _runpy_isaaclab_play()
        os._exit(0)

    if os.environ.get("PLAY_SKIP_GPU_CHECK") != "1":
        _guard_gpu_free()

    print("=" * 70)
    print("[play] ⚠️ exported/policy.pt 는 '시뮬 창을 닫은 뒤' 생성됩니다.")
    print("        (창이 떠 있는 동안엔 logs/<run>/exported/ 에만 있음 → 창 종료")
    print("         시 exported/ 직속으로 자동 복사. 창 안 닫으면 policy.pt 안 보임.)")
    print("=" * 70)
    # 1. 실행 전 — model_best.pt → logs 자동 sync
    play_ckpt = _stage_best()
    if play_ckpt is None:
        # ⚠️ 억지로 옛 파일을 쓰지 않는다 — 없으면 아예 시작하지 않는다.
        #    (예전엔 그대로 진행해 IsaacLab 이 logs 의 아무 체크포인트나 집었다)
        print("=" * 70)
        print("[play] 🔴 재생할 정책이 없어 실행하지 않습니다.")
        print("       exported/model_best.pt 가 있어야 합니다 — 학습(train.py)을 먼저 끝내세요.")
        print("=" * 70)
        sys.exit(1)      # ⚠️ 모듈 최상위(`if __name__`)라 return 을 쓸 수 없다

    # 2. IsaacLab play.py 실행 (subprocess 분리)
    exit_code = 1
    try:
        exit_code = run_play()
        print(f"\n[play] subprocess 종료 (exit={exit_code})")
    except KeyboardInterrupt:
        print("\n[play] ⚠️ Ctrl+C 받음 — 그래도 policy.pt 동기화 시도")
    except Exception as e:
        print(f"\n[play] ⚠️ subprocess 에러: {e} — 그래도 policy.pt 동기화 시도")
    finally:
        # 3. 어떤 상황에서도 — exported/policy.pt 자동 복사 (본선용).
        # Ctrl+C 든 에러든 IsaacLab 가 logs 에 export 했으면 root 로 옮김.
        print("[play] 동기화 시작 (finally)...")
        _ok_p = _export_policy_to_exported(play_ckpt)
        _ok_v = _export_video_to_exported() if "--video" in sys.argv else False
        _tidy_after_play(play_ckpt, _ok_p, _ok_v)

    # Isaac Sim 잔여 스레드 hang 방지 — export 후처리까지 끝낸 뒤 강제 종료
    os._exit(exit_code if isinstance(exit_code, int) else 0)
