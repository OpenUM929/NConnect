"""학습 종료 후 best model 선별 + training/humanoid/exported/ 에 출력.

`train.py`, `train_and_submit.py` 등에서 import 해서 학습 끝난 후 호출.
독립 실행도 가능: `python _finalize.py [--run <run_dir>]`

출력 파일 (training/humanoid/exported/ 안 — 한 곳에 모음):
  - model_best.pt   : 예선 채점용 RSL-RL checkpoint
  - env.yaml        : 학습 환경 dump (reward 검증용)
  - policy.pt       : (play.py 실행 후) 본선 매치용 JIT exported

학생/운영자가 exported/ 한 폴더만 보면 됨 — 헷갈림 X.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent  # training/humanoid/
LOG_ROOT = PROJECT_DIR / "logs" / "rsl_rl" / "humanoid"
FINAL_DIR = PROJECT_DIR / "exported"  # ★ 결과물 한 폴더에 모음


def _model_iter(p: Path) -> int:
    # model_<iter>.pt → iter. 비숫자(model_best.pt 등 resume 용 사용자 파일)는
    # -1 반환 → 선별/정리 대상에서 제외. (int("best") ValueError 크래시 방지.)
    s = p.stem.split("_")[-1]
    return int(s) if s.isdigit() else -1


def find_latest_run() -> Path:
    if not LOG_ROOT.exists():
        raise FileNotFoundError(f"학습 log 없음: {LOG_ROOT}")
    runs = [p for p in LOG_ROOT.iterdir() if p.is_dir()]
    if not runs:
        raise FileNotFoundError(f"학습 run 없음: {LOG_ROOT}")
    return max(runs, key=lambda p: p.stat().st_mtime)


def find_best_model(run_dir: Path) -> tuple[Path, float | None, int | None]:
    """tfevents 의 mean_reward 최고 iter 모델 선택. 실패 시 마지막."""
    models = sorted([m for m in run_dir.glob("model_*.pt") if _model_iter(m) >= 0],
                    key=_model_iter)
    if not models:
        raise FileNotFoundError(f"model_*.pt (숫자 iter) 없음: {run_dir}")

    try:
        from tensorboard.backend.event_processing.event_accumulator import (
            EventAccumulator,
        )

        # 🔴 size_guidance 를 안 주면 scalar 를 태그당 10,000개만 남긴다 — 그것도
        #    잘림이 아니라 **무작위 표본**(reservoir, 시드 고정)이다. 10,000 iter 를
        #    넘는 학습은 최고점 step 이 표본에서 빠질 수 있어 엉뚱한 체크포인트가
        #    best 로 뽑히고, cleanup 이 진짜 best 를 지워 버린다(복구 불가).
        #    실측(참가자 제보, 25,000 iter): 표본 best 23101/6.749 → model_23100 선택,
        #    전체 best 24012/6.904 → model_24000 이 정답이었다.
        #    scalars=0 = 전부 보관. 다른 종류(images 등)는 기본값과 병합된다.
        ea = EventAccumulator(str(run_dir), size_guidance={"scalars": 0})
        # ⚠️ 이 읽기는 학습이 길면 수십 초 걸린다. 아무 출력이 없으면 멈춘 것처럼 보여
        #    사용자가 Ctrl+C 를 한 번 더 누르고, 그러면 best 선별을 통째로 잃는다.
        print("[INFO] 학습 기록(tfevents) 읽는 중... 수십 초 걸릴 수 있습니다 — Ctrl+C 누르지 마세요.")
        ea.Reload()
        tags = ea.Tags().get("scalars", [])
        for tag in (
            "Train/mean_reward",
            "Episode_Reward/mean",
            "Reward/mean",
            "Train/mean_episode_reward",
        ):
            if tag in tags:
                events = ea.Scalars(tag)
                if not events:
                    continue
                # ★ resume warmup 제외 — 리쥼 직후 초반은 보상이 비정상적으로 높을 수
                #   있어(이미 학습된 모델 + 커리큘럼/지형이 쉬운 초기) best 가 그 스파이크로
                #   잘못 잡힘. 앞 10%(최소 50 step) 워밍업을 빼고 '나중에 수렴한' 구간서 best.
                # ⚠️ resume 시 step 은 0 이 아니라 이어받은 iter(예: 13200)부터 시작 →
                #   warmup 임계는 절대값(0.1*max)이 아니라 이 run 의 step 범위(lo~hi) 기준.
                #   (절대값이면 lo > warmup 이라 리쥼 직후 스파이크가 안 걸러져
                #    best 가 resume iter 로 고정되는 버그 — 이후 학습분이 cleanup 으로 삭제됨.)
                steps_all = [e.step for e in events]
                lo, hi = min(steps_all), max(steps_all)
                warmup = lo + max(50, int((hi - lo) * 0.10))
                eligible = [e for e in events if e.step >= warmup] or events
                best = max(eligible, key=lambda e: e.value)
                best_model = min(models, key=lambda p: abs(_model_iter(p) - best.step))
                print(
                    f"[INFO] Best by '{tag}': step {best.step}, "
                    f"reward {best.value:.3f} → {best_model.name}"
                )
                return best_model, best.value, best.step
        print("[WARN] reward tag 못 찾음 → 마지막 model 사용.")
    except ImportError:
        print("[WARN] tensorboard 패키지 없음 → 마지막 model 사용.")
    except KeyboardInterrupt:
        # ⚠️ KeyboardInterrupt 는 Exception 이 **아니라서** 아래 except 에 안 걸린다.
        #    안 잡으면 여기서 트레이스백과 함께 finalize 가 죽고 model_best.pt 가 안 생긴다
        #    (학습 중단하려고 Ctrl+C 를 두 번 누르는 건 자연스러운 행동이다).
        print("[WARN] 기록 읽기를 중단했습니다 → 마지막 체크포인트를 사용합니다"
              " (보상 최고점 대신 마지막 시점).")
    except Exception as e:
        print(f"[WARN] tfevents 파싱 실패: {e} → 마지막 model 사용.")

    return models[-1], None, _model_iter(models[-1])


def _cleanup_intermediate_checkpoints(run_dir: Path, keep_iter: int | None = None) -> int:
    """run_dir 안의 model_*.pt 모두 삭제 — final/ 에 best 복사 후 호출.
    tfevents/params/exported 는 보존 (tensorboard, 분석, resume 용).

    keep_iter: 이 iter 의 model_<keep_iter>.pt 는 보존 → play.py 가 logs/ 에서
               찾을 수 있게. None 이면 모두 삭제 (이전 동작).
    """
    deleted_count = 0
    deleted_bytes = 0
    for p in run_dir.glob("model_*.pt"):
        # 비숫자 모델(model_best.pt 등 사용자 resume 파일) 은 삭제하지 않음
        if _model_iter(p) < 0:
            continue
        # play.py 호환용 best 모델은 보존
        if keep_iter is not None and _model_iter(p) == keep_iter:
            continue
        try:
            sz = p.stat().st_size
            p.unlink()
            deleted_count += 1
            deleted_bytes += sz
        except Exception as e:
            print(f"[WARN] {p.name} 삭제 실패: {e}")
    if deleted_count:
        mb = deleted_bytes / 1024 / 1024
        print(f"[CLEAN] logs/ 의 intermediate .pt {deleted_count}개 삭제 ({mb:.0f}MB 회수)")
    if keep_iter is not None:
        print(f"[KEEP] logs/<run>/model_{keep_iter}.pt 보존 (play.py 호환)")
    return deleted_count


def finalize(run_dir: Path | None = None, cleanup: bool = True) -> dict:
    """run_dir 에서 best 선별해 final/ 로 복사.

    cleanup=True (기본): final/ 복사 후 logs/<run>/ 의 model_*.pt 모두 삭제.
                        디스크 절약. tfevents 는 보존 (tensorboard 분석용).
    cleanup=False:        모든 체크포인트 그대로 보존 (resume / 다른 iter 선택용).
    """
    if run_dir is None:
        run_dir = find_latest_run()
    print(f"[INFO] Run: {run_dir}")

    best_model, best_reward, best_iter = find_best_model(run_dir)

    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    # 타임스탬프 (run 폴더 이름 기반 — 학습 시작 시각) — 실수 덮어쓰기 방지 백업용.
    # run_dir.name 예시: '2026-05-24_10-07-02' → ts = '20260524_100702'
    import re
    ts = re.sub(r"[-_]|:", "", run_dir.name)   # 숫자만 남김
    if not ts.isdigit() or len(ts) < 8:
        # fallback — 현재 시각
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─── 예선 제출용 2개 ────────────────────────────────
    # 1. model_best.pt — 예선 채점용 RSL-RL checkpoint
    #    latest (덮어씌어짐) + timestamp 백업 (보존)
    dest_model = FINAL_DIR / "model_best.pt"
    dest_model_ts = FINAL_DIR / f"model_best_{ts}.pt"
    shutil.copy(best_model, dest_model)
    shutil.copy(best_model, dest_model_ts)
    print(f"[OK] model_best.pt → {dest_model}  (iter={best_iter}, reward={best_reward})")
    print(f"[OK] 백업 → {dest_model_ts.name}")

    # 2. env.yaml — 학습 의도/reward 검증용
    env_yaml_src = run_dir / "params" / "env.yaml"
    if env_yaml_src.exists():
        shutil.copy(env_yaml_src, FINAL_DIR / "env.yaml")
        shutil.copy(env_yaml_src, FINAL_DIR / f"env_{ts}.yaml")
        print(f"[OK] env.yaml → {FINAL_DIR / 'env.yaml'}")
        print(f"[OK] 백업 → env_{ts}.yaml")
    else:
        print(f"[WARN] env.yaml 없음: {env_yaml_src}")

    # 나머지 (agent.yaml, exported/, meta.json) 는 logs/<run>/ 에 그대로 유지.
    # 필요하면 거기서 직접 가져갈 수 있음 — top-level 깔끔.

    # logs/ 정리 — best model 의 *실제* iter (저장 파일명 기준) 보존.
    # best_iter (tfevents step) 와 best_model 의 iter 는 다를 수 있음 —
    # save_interval=100 라 step 6718 의 best 는 model_6700.pt 로 저장됨.
    # 그래서 keep_iter=best_iter (6718) 면 cleanup 이 model_6700.pt 도 삭제 →
    # logs 안 model 0개 → play.py 가 model_0.pt 로 sync (이름 헷갈림).
    if cleanup:
        best_model_actual_iter = _model_iter(best_model)
        _cleanup_intermediate_checkpoints(run_dir, keep_iter=best_model_actual_iter)

    # 학습 결과 분석 리포트 (exported/report.html) — 자체 포함, 외부 파일 의존 X
    try:
        _generate_report(FINAL_DIR, run_dir.name, run_dir=run_dir,
                         best_reward=best_reward, best_iter=best_iter)
        print(f"[OK] report.html → {FINAL_DIR / 'report.html'}  (브라우저로 열어 보기)")
    except (Exception, KeyboardInterrupt) as _e_rep:
        # model_best.pt 는 위에서 이미 저장됐다 — 리포트 때문에 finalize 를 죽이지 않는다.
        print(f"[WARN] report.html 생성 skip: {type(_e_rep).__name__} {_e_rep}")

    # 학습 결과 자동 **백업** (zip → 운영 서버) — 예선 제출과 별개(편의 장치).
    #   학습이 길어 서버가 꺼져도 이력이 남도록. 끄려면 env  NO_AUTO_SUBMIT=1.
    try:
        _submit_zip(FINAL_DIR)
    except (Exception, KeyboardInterrupt) as _e_sub:
        print(f"[backup] 자동 백업 skip: {type(_e_sub).__name__} {_e_sub}")

    print("=" * 60)
    print(f"[DONE] 예선 제출 결과물 → {FINAL_DIR}/")
    print(f"  ★ model_best.pt    (예선 채점용 RSL-RL checkpoint)")
    print(f"  ★ env.yaml         (학습 의도/reward 검증)")
    print(f"")
    print(f"  본선 매치용 policy.pt 도 같은 폴더에 생길 거:")
    print(f"    > isaaclab.bat -p play.py --task Humanoid-v0 --num_envs 4")
    print(f"    → exported/policy.pt 자동 생성")
    print(f"    ⚠️ 시뮬 창을 '닫아야'(Esc/창 종료) exported/policy.pt 가 복사됨.")
    print(f"       (policy 는 시작 직후 logs/<run>/exported/ 에 만들어지고,")
    print(f"        창 종료 시 exported/ 직속으로 복사 — 창 떠 있으면 아직 안 옮겨짐.)")
    print(f"")
    print(f"  (학습 상세 자료는 logs/<run>/ 에 보존 — tfevents, params/)")
    print("=" * 60)
    return {
        "run_name": run_dir.name,
        "best_iter": best_iter,
        "best_reward": best_reward,
    }


# ════════════════════════════════════════════════════════════════════
#  학습 결과 분석 리포트 (exported/report.html) — 자체 포함 (외부 파일 import X)
#    env.yaml 의 reward 를 baseline 과 비교 → 게이지 + 표 + "보는 법".
#    finalize() 가 exported/ 를 만든 직후 _generate_report() 호출.
#    ⚠️ go2_task/_finalize.py 와 동일 — 한쪽 수정 시 미러.
# ════════════════════════════════════════════════════════════════════
_REP_BASELINE = {  # 기준값 = 배포 reward 파일의 첫 학습 시작값 (humanoid_rewards.py / quadruped_rewards.py)
    "humanoid": {"track_lin_vel_xy_exp": 0.5, "track_ang_vel_z_exp": 0.5, "feet_air_time": 0.2,
                 "flat_orientation_l2": -1.5, "joint_deviation_hip": -0.2,
                 "joint_deviation_torso": -0.1, "ang_vel_xy_l2": -0.05,
                 "action_rate_l2": -0.0005, "termination_penalty": -5.0},
    "quadruped": {"track_lin_vel_xy_exp": 1.0, "feet_air_time": 0.01, "lin_vel_z_l2": -3.0,
                  "action_rate_l2": -0.01, "ang_vel_xy_l2": -0.08},
}
_REP_RANGES = {
    # 배포 humanoid_rewards.py 의 ①~⑨ 순서 그대로 (리포트 게이지 순서 = 참가자가 보는 파일 순서)
    # ⚠️ 단일 진실 소스는 **배포 파일 주석의 `추천 a ~ b`** — 그걸 바꿨으면 여기도 같이 고친다.
    #    (여기는 (낮은쪽, 높은쪽) 로 담는다. 주석은 사람이 읽기 좋게 순서가 뒤집혀 있어도 된다.)
    #    대조: `python3 eval_suite/reward_baselines.py --check`
    "humanoid": {"track_lin_vel_xy_exp": (0.5, 2.5), "track_ang_vel_z_exp": (0.5, 2.0),
                 "feet_air_time": (0.1, 0.5), "termination_penalty": (-400.0, -50.0),
                 "flat_orientation_l2": (-3.0, -0.2), "ang_vel_xy_l2": (-0.3, -0.02),
                 "joint_deviation_hip": (-0.5, -0.1), "joint_deviation_torso": (-0.3, -0.02),
                 "action_rate_l2": (-0.008, -0.0005)},
    "quadruped": {"track_lin_vel_xy_exp": (0.5, 2.0), "feet_air_time": (0.01, 0.5),
                  "lin_vel_z_l2": (-5.0, -0.5), "ang_vel_xy_l2": (-0.3, -0.02),
                  "action_rate_l2": (-0.02, -0.005)},
}
_REP_ADV = {
    "humanoid": {},
    "quadruped": {"track_ang_vel_z_exp": (0.0, 1.5), "flat_orientation_l2": (-2.0, 0.0),
                  "undesired_contacts": (-1.5, 0.0), "termination_penalty": (-400.0, 0.0)},
}
# IsaacLab 이 **모든 제출본에 기본으로 넣는** reward 값 (참가자가 만진 게 아님).
# ⚠️ 이게 없으면 기본값 0.75 인 track_ang_vel_z_exp 가 "고급 옵션을 켰다"로 그려져
#    아무것도 안 바꾼 학생의 리포트에 변경한 것처럼 표시된다(실측).
# 출처: run_eval 의 Reward Manager 테이블(IsaacLab Go2 rough 기본값) 실측.
_REP_FRAMEWORK = {
    "humanoid": {},
    "quadruped": {"track_ang_vel_z_exp": 0.75, "flat_orientation_l2": 0.0,
                  "dof_pos_limits": 0.0},
}


def _rep_is_framework_default(robot, term, val) -> bool:
    """참가자가 안 건드린 프레임워크 기본값인가 (게이지·표에서 '변경'으로 오표기 방지)."""
    d = _REP_FRAMEWORK.get(robot, {})
    return term in d and abs(float(val) - float(d[term])) < 1e-9


_REP_INTENT = {
    "track_lin_vel_xy_exp": ("속도 추종", "속도 ↑ 빠릿·멀리(과속 시 넘어짐)", "속도 ↓ 천천·안정"),
    "track_ang_vel_z_exp": ("회전 추종", "선회 ↑ 빠른 방향전환", "선회 ↓ 둔한 방향전환"),
    "feet_air_time": ("발 들기", "발 높이 ↑ 등반 유리 (⚠️과하면 한발 깽깽이·바운딩 — 경계는 실행마다 다름)", "발 낮게 ↓ 평지안정·등반약"),
    "flat_orientation_l2": ("자세(수평)", "자세 자유 ↑ 과감·등반(평지안정 ↓)", "자세 ↑ 꼿꼿·안정·소극"),
    "joint_deviation_hip": ("골반 대칭", "한발 허용(균형 ↓)", "골반 대칭 ↑ 균형·한발억제"),
    "joint_deviation_torso": ("상체 정렬", "상체 비틀림 허용", "상체 정렬 ↑ 몸통 안정"),
    "ang_vel_xy_l2": ("좌우 흔들림", "흔들림 허용", "흔들림 억제 ↑ 안정"),
    "action_rate_l2": ("동작 부드러움", "민첩하나 떨림", "부드럽지만 굼뜸"),
    "termination_penalty": ("낙상 벌점", "위험 감수(속도 우선)", "안전제일(소극)"),
    "lin_vel_z_l2": ("지면 밀착", "통통 튐 허용(불안정)", "지면 밀착 ↑ 험지안정(굼뜸)"),
    "undesired_contacts": ("부적절 접촉 벌점", "접촉 허용", "배/무릎 접촉 억제 ↑ 깔끔보행"),
}


def _rep_yaml_load(text):
    """IsaacLab env.yaml 의 !!python/* 태그를 구조만 복원 (safe_load 거부 회피, RCE 없음)."""
    import yaml

    class _L(yaml.SafeLoader):
        pass

    def _g(loader, suf, node):
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node, deep=True)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node, deep=True)
        return loader.construct_scalar(node)

    _L.add_multi_constructor("tag:yaml.org,2002:python/", _g)
    return yaml.load(text, Loader=_L)


def _rep_rewards(env_path):
    data = _rep_yaml_load(env_path.read_text(encoding="utf-8")) or {}
    out = {}
    for term, cfg in (data.get("rewards") or {}).items():
        w = cfg.get("weight") if isinstance(cfg, dict) else cfg
        if isinstance(w, (int, float)) and not isinstance(w, bool):
            out[term] = float(w)
    return out


def _rep_pt(pt):
    import torch
    ck = torch.load(pt, map_location="cpu", weights_only=False)
    info = {"iter": ck.get("iter") if isinstance(ck, dict) else None}
    sd = None
    if isinstance(ck, dict):
        sd = ck.get("actor_state_dict") or ck.get("model_state_dict")
    if sd:
        info["params"] = sum(int(v.numel()) for v in sd.values() if hasattr(v, "numel"))
        w2 = [k for k in sd if k.endswith(".weight") and getattr(sd[k], "ndim", 0) == 2]
        if w2:
            last = sorted(w2, key=lambda k: int("".join(c for c in k if c.isdigit()) or 0))[-1]
            info["out_dim"] = int(sd[last].shape[0])
        info["nan"] = any(bool(v.isnan().any()) for v in sd.values() if hasattr(v, "isnan"))
    return info


def _rep_dur(sec):
    s = int(round(sec)); h, r = divmod(s, 3600); m, _ = divmod(r, 60)
    return f"{h}시간 {m}분" if h else (f"{m}분 {s % 60}초" if m else f"{s}초")


def _rep_classify(changed, extras):
    score = 0; ph = []; warn = []
    for term, b, cur in list(changed) + [(t, 0.0, c) for t, c in extras]:
        up = cur > b
        if term == "track_lin_vel_xy_exp":
            score += 1 if up else -1; ph.append("속도↑" if up else "속도↓")
        elif term == "feet_air_time":
            score += 1 if up else -1
            if cur > 0.3:
                ph.append("발들기↑(등반·⚠️깽깽이)")
                warn.append(f"feet_air_time {cur:g} > 0.3 → 한 발로 깡총거리는 보행(hop) 위험 (play.py 로 보행 확인)")
            elif cur < 0.05:
                ph.append("발들기≈0(⚠️STUCK)")
                warn.append(f"feet_air_time {cur:g} ≈ 0 → 발을 거의 안 들어 제자리서 못 걸을 위험 (STUCK) — play.py 로 보행 확인")
            else:
                ph.append("발들기↑(등반)" if up else "발들기↓(평지안정)")
        elif term == "flat_orientation_l2":
            score += 1 if up else -1; ph.append("자세자유↑(과감)" if up else "자세안정↑(꼿꼿)")
        elif term == "termination_penalty":
            score += 1 if up else -1; ph.append("위험감수↑" if up else "안전↑")
        elif term == "lin_vel_z_l2":
            score += 1 if up else -1; ph.append("튐허용↑(불안정)" if up else "지면밀착↑(안정)")
    bias = "공격/적극 지향" if score > 0 else "안정 지향" if score < 0 else "균형(혼합)"
    return bias, ph, warn


def _rep_diag(run_dir, best_reward=None, best_iter=None):
    """tfevents 에서 학습 '결과' 지표 추출 — 학생이 직접 정하는 값이 아니라 *실패 진단*용.
    best 보상/iter(인자) + 마지막 지형난이도·낙상률·탐색std. 부분 실패해도 가능한 만큼 dict.
    태그(rsl-rl/IsaacLab): Train/mean_reward · Policy/mean_std(구 mean_noise_std) ·
    Curriculum/terrain_levels(rough 전용) · Episode_Termination/*(낙상률 = 비-timeout 비율)."""
    d = {}
    if best_reward is not None:
        try: d["best_reward"] = float(best_reward)
        except Exception: pass
    if best_iter is not None:
        try: d["best_iter"] = int(best_iter)
        except Exception: pass
    if run_dir is None:
        return d
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
        # 🔴 scalars=0 필수 — 기본은 10,000개 무작위 표본이라(find_best_model 주석 참고)
        #    ① 발산 nan 이 표본에서 빠질 수 있고 ② resume 판정용 ev[0].step 이 진짜
        #    첫 이벤트가 아니게 된다(실측: 25,000 iter run 에서 첫 step 0 이 탈락).
        ea = EventAccumulator(str(run_dir), size_guidance={"scalars": 0}); ea.Reload()
        tags = set(ea.Tags().get("scalars", []))

        # ══ 발산 검사 — **가장 먼저** 한다 ═════════════════════════════════════
        # ⚠️ 발산(nan)은 **가중치가 아니라 손실에 먼저** 나타난다. best 체크포인트는 발산
        #    *이전* 시점이라 `_rep_pt` 의 NaN 검사를 늘 통과한다 → 손실 태그를 봐야 잡힌다.
        #    (콘솔의 "Mean value loss: nan" 이 `Loss/value_function` 으로 기록됨.)
        # 🔴 여기 있던 앞선 구현이 발산을 놓쳤다. 세 가지를 동시에 고친다:
        #    ① **태그 이름을 고정 목록으로 찍지 않는다** — rsl-rl 버전마다 이름이 달라
        #       목록에 없으면 검사가 *조용히 아무것도 안 하고* 통과한다.
        #    ② **마지막 값만 보지 않는다** — 크래시 시 flush 타이밍에 따라 nan 이 중간
        #       기록으로 남을 수 있다. 전 구간을 훑는다.
        #    ③ **다른 지표보다 먼저 읽는다** — 이 블록은 try 맨 끝에 있었고 그 아래가
        #       `except Exception: pass` 라, 앞 어딘가에서 예외가 나면 나머지 지표는
        #       남고 발산 판정만 사라졌다(정확히 이 리포트의 증상).
        #    + 검사 자체가 불가능했으면(`loss_tags`=0) '확인 불가' 로 남긴다 — 조용한 통과 금지.
        loss_tags = sorted(t for t in tags if t.startswith("Loss/"))
        d["loss_tags"] = len(loss_tags)
        for t in loss_tags:
            ev = ea.Scalars(t)
            hit = next((e for e in ev if not math.isfinite(e.value)), None)
            if hit is not None:
                d["diverged"] = t.rsplit("/", 1)[-1]
                d["diverged_at"] = int(hit.step) + 1        # step 은 0부터 → 사람이 읽는 회차
                break

        def _fin(*cands):   # 후보 태그들 중 존재하는 것의 마지막 (value, step)
            for t in cands:
                if t in tags:
                    ev = ea.Scalars(t)
                    if ev:
                        return ev[-1].value, ev[-1].step
            return None, None

        def _first(*cands):   # 이 run 이 시작한 step (resume 이면 0 이 아니다)
            for t in cands:
                if t in tags:
                    ev = ea.Scalars(t)
                    if ev:
                        return ev[0].step
            return None

        rew, step = _fin("Train/mean_reward", "Episode_Reward/mean", "Reward/mean")
        if rew is not None:
            d.setdefault("final_reward", float(rew))
            # ⚠️ tfevents step 은 **0부터**다. 5회 학습이면 마지막 step 이 4 →
            #    +1 해야 '실제로 돌린 횟수'. 안 하면 완주한 run 이 조기중단으로 잡힌다.
            d["total_iter"] = int(step) + 1
            s0 = _first("Train/mean_reward", "Episode_Reward/mean", "Reward/mean")
            if s0 is not None:
                d["start_iter"] = int(s0)
        std, _ = _fin("Policy/mean_std", "Policy/mean_noise_std")
        if std is not None:
            d["action_std"] = float(std)
        terr, _ = _fin("Curriculum/terrain_levels")
        if terr is not None:
            d["terrain_lv"] = float(terr)
        term_tags = [t for t in tags if "Episode_Termination/" in t]
        if term_tags:
            tot = fall = 0.0
            for t in term_tags:
                ev = ea.Scalars(t)
                if not ev:
                    continue
                v = ev[-1].value
                tot += v
                if "time_out" not in t.lower():   # time_out=생존, 그 외=낙상/실패
                    fall += v
            if tot > 1e-9:
                d["fall_rate"] = max(0.0, min(1.0, fall / tot))
    except Exception:
        pass
    # 요청한 총 iter. 이보다 일찍 끝났으면 학습이 끝까지 못 간 것(발산·크래시).
    try:
        import re as _re
        _m = _re.search(r"max_iterations:\s*(\d+)",
                        (Path(run_dir) / "params" / "agent.yaml").read_text(errors="ignore"))
        if _m:
            d["requested_iter"] = int(_m.group(1))
    except Exception:
        pass
    return d


def _diag_verdict(d):
    """진단 지표 → (severity, [메시지]). severity: 'bad' > 'warn' > 'ok'. 실패 원인 자동 해석."""
    msgs = []; order = {"ok": 0, "warn": 1, "bad": 2}; sev = "ok"

    def _bump(s, m):
        nonlocal sev
        msgs.append(m)
        if order[s] > order[sev]:
            sev = s

    # 이 run 에서 실제로 돈 횟수 (resume 이면 start_iter 가 0 이 아니다).
    _ri = d.get("requested_iter")
    _ti = d.get("total_iter")
    done = None if _ti is None else _ti - (d.get("start_iter") or 0)

    # ── ① 학습이 너무 짧으면 아래 지표 전부가 무의미하다 → 여기서 끝낸다 ──
    #    ⚠️ save_interval=100 이라 100 회 미만은 model_0.pt 만 저장 → 제출 파일이
    #    '학습이 반영되지 않은 초기 가중치' 다. 이때 terrain_lv·std 로 해석하면
    #    ("지형 3.4 니 학습은 됐다") 전부 오진 — terrain 은 시작값이 0 이 아니다.
    if done is not None and done < 100:
        _bump("bad", f"🔴 학습을 {done} 회만 돌렸습니다 — 체크포인트는 100 회마다 저장되므로 "
                     f"제출 파일이 사실상 '학습이 반영되지 않은 초기 가중치' 입니다.")
        _bump("bad", "→ 아래 지표(지형 난이도·낙상률·탐색 std)는 이 횟수에서는 판단 근거가 "
                     "못 됩니다. 동작 확인용 짧은 실행이었다면 정상입니다.")
        msgs.append("실제 보행 안정성은 숫자만으로 판단하지 말고 play.py 로 영상 확인하세요.")
        return sev, msgs

    # ── ② 발산·조기중단이 최우선 신호. 다른 지표가 좋아 보여도 그 뒤 학습은 버려졌다. ──
    if d.get("diverged"):
        _at = d.get("diverged_at")
        _bump("bad", f"🔴 학습이 발산했습니다 — 손실({d['diverged']})이"
                     + (f" {_at} 회째에" if _at else "") + " nan 이 되어 중단됐습니다. "
                     "제출 파일은 발산 *이전* 시점이라 위에 'NaN 없음(제출 파일)' 으로 "
                     "나오지만, 그 뒤 학습은 전부 버려졌습니다.")
        _bump("bad", "→ 안정 쪽 벌점을 너무 낮추지 않았는지 보세요 — 좌우 흔들림"
                     "(ang_vel_xy_l2)·수직 튐(lin_vel_z_l2)을 되돌리고 재학습.")
    if _ri and done and done < _ri * 0.95:
        _bump("bad", f"🔴 요청한 {_ri} 회 중 {done} 회에서 멈췄습니다 — 학습이 끝까지 못 갔습니다.")
        # ⚠️ 여기서 끝내면 안 된다 — 참가자가 알아야 하는 건 '멈췄다' 가 아니라 **왜** 다.
        #    그리고 nan 을 못 봤다고 '발산 아님' 으로 단정하면 안 된다: 손실 태그가 없거나
        #    크래시로 마지막 기록이 남지 않으면 못 본다. 확인할 곳을 알려준다.
        if not d.get("diverged"):
            if not d.get("loss_tags"):
                _bump("bad", "→ 손실 기록이 없어 **발산 여부를 확인할 수 없습니다**. 학습 콘솔 "
                             "마지막 줄에 'Mean value loss: nan' 이 있었는지 보세요.")
            else:
                _bump("bad", "→ 손실 기록에는 nan 이 없었습니다. 발산이 아니라 다른 이유"
                             "(메모리 부족·프로세스 종료·터미널 끊김)일 수 있습니다 — "
                             "학습 콘솔 마지막 줄을 확인하세요.")

    fr = d.get("fall_rate")
    if fr is not None:
        if fr > 0.5:
            _bump("bad", "🔴 절반 이상 넘어짐 — 거의 못 걷는 정책. 안정 쪽 보상을 재검토하세요.")
        elif fr > 0.2:
            _bump("warn", "⚠️ 자주 넘어짐 — 불안정. 안정 쪽 보상 검토.")
        elif fr < 0.05:
            _bump("ok", "✅ 거의 안 넘어짐 — 안정적.")
    tl = d.get("terrain_lv")
    if tl is not None and tl < 0.5:
        _bump("bad", "🔴 지형 난이도가 0 수준 — 평지조차 제대로 못 걸어 난이도가 안 올라감(주저앉기·STUCK 의심).")
    std = d.get("action_std")
    if std is not None:
        if std < 0.15:
            _bump("bad", "🔴 탐색 std 가 거의 0 — 한 동작에 갇힘(제자리·주저앉기 의심).")
        elif std > 0.9:
            # ⚠️ std 만 보고 '학습 부족' 이라 하면 오진하지만, 거꾸로 '학습은 됐다' 고
            #    단정해도 오진이다 — terrain_lv 는 **시작값이 0 이 아니라서** 짧은 run 에서도
            #    커 보인다. 그래서 **충분히 돌았을 때만** 엔트로피 과다로 읽는다.
            _enough = done is None or done >= 1000
            if _enough and ((d.get("terrain_lv") or 0) >= 1.0 or (fr is not None and fr < 0.2)):
                _bump("warn", "⚠️ 탐색 std 가 1.0 근처인데 지형·낙상 지표는 정상 — 학습은 됐지만 "
                              "무작위성이 안 줄었습니다(엔트로피 과다). 발산으로 이어질 수 있으니 "
                              "흔들림·튐 벌점을 너무 낮추지 않았는지 확인하세요.")
            else:
                _bump("warn", "⚠️ 탐색 std 가 초기값(1.0) 수준 — 거의 학습이 안 됨(iter 부족 의심).")
    if not msgs:
        msgs.append("✅ 수치상 큰 이상 신호 없음.")
    msgs.append("실제 보행 안정성은 숫자만으로 판단하지 말고 play.py 로 영상 확인하세요.")
    return sev, msgs


def _generate_report(final_dir, run_name=None, run_dir=None, best_reward=None, best_iter=None):
    """exported/{model_best.pt, env.yaml} → exported/report.html. 경로 반환(없으면 None).
    외부 모듈 import 없이 동작 (torch+PyYAML 만 필요). run_dir 주면 tfevents 진단 수치도 포함."""
    import html as _h
    from datetime import datetime
    env_path = final_dir / "env.yaml"
    pt_path = final_dir / "model_best.pt"
    if not env_path.exists():
        return None
    pt_info = {}; robot = None
    if pt_path.exists():
        try:
            pt_info = _rep_pt(pt_path)
            robot = {19: "humanoid", 12: "quadruped"}.get(pt_info.get("out_dim"))
        except Exception:
            pass
    rewards = _rep_rewards(env_path)
    if not robot:
        robot = "quadruped" if "lin_vel_z_l2" in rewards else "humanoid"
    diag = _rep_diag(run_dir, best_reward, best_iter)   # 학습 결과(진단) 수치 — tfevents

    started = None
    if run_name:
        import re
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})", str(run_name))
        if m:
            y, mo, d, h, mi, _s = m.groups()
            started = f"{y}-{mo}-{d} {h}:{mi}"
    ended = datetime.now()
    pt_info["ended"] = ended.strftime("%Y-%m-%d %H:%M")
    if started:
        pt_info["started"] = started
        try:
            pt_info["duration"] = _rep_dur((ended - datetime.strptime(started, "%Y-%m-%d %H:%M")).total_seconds())
        except Exception:
            pass

    base = _REP_BASELINE.get(robot, {})
    changed = [(t, base[t], rewards[t]) for t in base if t in rewards and abs(rewards[t] - base[t]) > 1e-9]
    # 프레임워크 기본값은 '참가자가 손댄 항목' 이 아니므로 제외 (표·판정 모두)
    extras = [(t, rewards[t]) for t in rewards
              if t not in base and t in _REP_INTENT and abs(rewards[t]) > 1e-9
              and not _rep_is_framework_default(robot, t, rewards[t])]
    # ⚠️ extras(REWARD_WEIGHTS 에 없는 항목)는 **판정에서 제외**한다. 기준값이 없어
    #    변경 여부를 알 수 없는데(참가자가 파일에 추가해 바꿀 수는 있다 —
    #    _apply_common_overrides 가 임의 키를 적용하므로), `_rep_classify` 가
    #    '0 → 현재값 으로 바꿨다'로 취급해 튜닝 의도 라벨이 왜곡된다
    #    (H1 무변경 제출본이 undesired_contacts 때문에 '변경함'으로 분류되던 문제).
    bias, phrases, warns = _rep_classify(changed, [])

    print("\n[report] 보상 변화 (기본값 대비):")
    for t, b, c in changed or []:
        print(f"  {t:<22}{b:+.4g} → {c:+.4g}  ({c - b:+.3g})  {_REP_INTENT.get(t, (t,))[0]}")
    if not changed:
        print("  (기본값과 동일)")
    print(f"[report] 튜닝 의도: {bias}" + (" — " + "·".join(phrases) if phrases else ""))
    for w in warns:
        print(f"  ⚠️ {w}")

    bcol = {"공격/적극 지향": ("#FAECE7", "#993C1D"), "안정 지향": ("#E6F1FB", "#0C447C")}.get(bias, ("#F1EFE8", "#444441"))

    def _over(lo, hi, cur):
        # ⚠️ 게이지와 표가 **같은 함수**로 판정해야 한다 (한 곳만 고치면 색과 설명이 어긋난다).
        span = (hi - lo) or 1.0
        raw = (cur - lo) / span
        return raw > 1.001 or raw < -0.001

    def _gauge(term, lo, hi, b, cur, suffix="", dtext=None):
        span = (hi - lo) or 1.0
        bp = max(0.0, min(1.0, (b - lo) / span)); raw = (cur - lo) / span
        over = _over(lo, hi, cur); sp = max(0.0, min(1.0, raw))
        same_ = abs(cur - b) < 1e-9
        # ⚠️ over(추천 범위 밖)를 same_(변화없음)보다 먼저 본다.
        #    배포 시작값이 일부러 추천 범위 밖인 다이얼이 있어(예: H1 termination_penalty -5.0,
        #    추천 -50~-400) same_ 우선이면 "안 건드린 참가자"에게 회색으로 그려져 함정이 안 보인다.
        color = "#E24B4A" if over else ("#888780" if same_ else ("#D85A30" if cur > b else "#378ADD"))
        name = _REP_INTENT.get(term, (term,))[0] + suffix
        if dtext is None:
            dtext = ("변화없음" if same_ else f"{cur - b:+.3g}") + (" · 범위 밖" if over else "")
        return (f'<div class=row><span class=lbl>{_h.escape(name)}</span>'
                f'<div class=track><span class=tick style="left:{bp*100:.1f}%"></span>'
                f'<span class=dot style="left:{sp*100:.1f}%;background:{color}"></span></div>'
                f'<span class=val>{cur:g} <em>({_h.escape(dtext)})</em></span></div>')

    rows = []; tbl = []   # tbl = 표에 넣을 목록 — 게이지와 **같은 항목**이어야 한다
    for term, (lo, hi) in _REP_RANGES.get(robot, {}).items():
        if term in rewards and term in base:
            rows.append(_gauge(term, lo, hi, base[term], rewards[term]))
            tbl.append((term, base[term], rewards[term], lo, hi, ""))
    # ⚠️ 고급 게이지는 **참가자가 실제로 바꾼 게 확실할 때만** 그린다.
    #    배포본(base)에 없는 항목은 IsaacLab 기본값일 수 있어 "켰다"고 단정 못 한다
    #    (기본값을 전부 검증해 _REP_FRAMEWORK 에 등록한 항목만 판별 가능).
    for term, (lo, hi) in _REP_ADV.get(robot, {}).items():
        known = term in _REP_FRAMEWORK.get(robot, {})
        if (term in rewards and abs(rewards[term]) > 1e-9
                and (term in base or (known and not _rep_is_framework_default(robot, term, rewards[term])))):
            rows.append(_gauge(term, lo, hi, 0.0, rewards[term], suffix=" (고급)", dtext="켬"))
            tbl.append((term, 0.0, rewards[term], lo, hi, " (고급)"))
    dials = "\n".join(rows) or "<p style=color:#999>게이지 대상 다이얼에 변화 없음</p>"

    warn_html = ("<div class=warn>" + "<br>".join("⚠ " + _h.escape(w) for w in warns) + "</div>") if warns else ""

    trows = ""
    # ⚠️ 표는 **게이지와 같은 목록(tbl)** 을 쓴다. '바뀐 것만' 넣으면 ① 게이지 5개 / 표 4개로
    #    개수가 어긋나 참가자가 누락으로 읽고, ② 무엇보다 **안 건드린 함정 다이얼**
    #    (배포 시작값이 추천 범위 밖 = 빨강, 예: H1 termination_penalty -5.0)이 표에서 빠져
    #    빨강의 이유를 설명하는 줄이 사라진다 — 설명이 가장 필요한 경우가 바로 그때다.
    for t, b, c, lo, hi, sfx in tbl:
        nm, up, dn = _REP_INTENT.get(t, (t, "↑", "↓"))
        over = _over(lo, hi, c)
        if sfx:                                   # 고급(off → 켬)
            dcol, eff = "켬", f"{nm}: 켬(기본은 꺼져 있음)"
        elif abs(c - b) < 1e-9:                   # 안 바꾼 다이얼도 반드시 한 줄
            dcol = "—"
            eff = f"{nm}: 바꾸지 않음" + (" — ⚠ 추천 범위 밖이니 조정해 보세요" if over else "")
        else:
            dcol = f"{c - b:+.3g}"
            eff = f"{nm}: {up if c > b else dn}" + (" ⚠ 추천 범위 밖" if over else "")
        trows += (f"<tr><td>{_h.escape(t + sfx)}</td><td>{b:g}</td><td>{c:g}</td>"
                  f"<td>{_h.escape(dcol)}</td><td>{_h.escape(eff)}</td></tr>")
    # extras 는 표에 넣지 않는다 — 참가자가 손댄 것처럼 읽힌다. 각주로만 안내.
    extra_note = ""
    if extras:
        extra_note = ("<p style='color:#888;font-size:13px;margin-top:6px'>그 외 env.yaml 에 들어 있는 "
                      "항목(배포 시작값에 원래 포함 — 기준값 미보유로 변경 여부 판단 불가): "
                      + ", ".join(f"{_h.escape(t)}={c:g}" for t, c in extras) + "</p>")
    if not trows:
        trows = "<tr><td colspan=5 style=color:#999>게이지 대상 다이얼이 env.yaml 에 없음</td></tr>"

    label = {"humanoid": "휴머노이드", "quadruped": "사족"}.get(robot, "?")
    meta = []
    if pt_info.get("out_dim"): meta.append(f"{pt_info['out_dim']}관절")
    if pt_info.get("iter") is not None:
        # ⚠️ 이 iter 는 '학습 반복 횟수' 가 아니라 **제출로 선택된 best 체크포인트의
        #    시점**이다. 초반에 정점을 찍은 run 은 15000 을 돌려도 여기가 작게 나와
        #    "학습이 안 됐나" 로 오해된다 → **총 반복 수를 함께** 보여준다.
        _tot = diag.get("total_iter"); _req = diag.get("requested_iter")
        _s = f"iter {pt_info['iter']}"
        if _tot:
            _s += f" / 총 {_tot}"
            # 요청보다 일찍 끝났으면 헤더에서 바로 보이게 (발산·크래시 신호).
            # ⚠️ 판정은 '이 run 에서 돈 횟수'로 — 진단 카드와 같은 기준이어야 한다.
            _dn = _tot - (diag.get("start_iter") or 0)
            if _req and _dn < _req * 0.95:
                _s += f" / ⚠ 요청 {_req}"
        meta.append(_s)
    if pt_info.get("params"): meta.append(f"{pt_info['params']/1e6:.2f}M params")
    # ⚠️ 그냥 "NaN 없음" 이면 '학습이 정상' 으로 읽힌다 — 이건 **제출 파일**에 대한 말이다
    #    (best 는 발산 *이전* 시점이라 발산한 학습도 늘 '없음' 이 된다).
    if pt_info.get("nan") is False: meta.append("NaN 없음(제출 파일)")
    elif pt_info.get("nan"): meta.append("⚠ NaN 발견")
    timing = []
    if pt_info.get("started"): timing.append(f"학습시작 {pt_info['started']}")
    if pt_info.get("ended"): timing.append(f"종료 {pt_info['ended']}")
    if pt_info.get("duration"): timing.append(f"소요 {pt_info['duration']}")
    timing_html = f"<div class=timing>{' · '.join(timing)}</div>" if timing else ""
    tail = (" — " + _h.escape("·".join(phrases))) if phrases else " — 기본값 그대로"

    # 학습 결과(진단) 카드 — 직접 정하는 값이 아니라 '결과' 지표(실패 원인 단서).
    diag_block = ""
    if diag and any(k in diag for k in ("best_reward", "terrain_lv", "fall_rate", "action_std")):
        _dc = []
        if "best_reward" in diag:
            _it = f" · iter {diag['best_iter']}" if diag.get("best_iter") is not None else ""
            _dc.append(f'<div class=stat><div class=sv>{diag["best_reward"]:.2f}</div><div class=sk>최고 보상{_h.escape(_it)}</div></div>')
        if "terrain_lv" in diag:
            _dc.append(f'<div class=stat><div class=sv>{diag["terrain_lv"]:.2f}</div><div class=sk>지형 난이도 (마지막)</div></div>')
        if "fall_rate" in diag:
            _dc.append(f'<div class=stat><div class=sv>{diag["fall_rate"]*100:.1f}%</div><div class=sk>낙상률 (마지막)</div></div>')
        if "action_std" in diag:
            _dc.append(f'<div class=stat><div class=sv>{diag["action_std"]:.3f}</div><div class=sk>탐색 std (마지막)</div></div>')
        _sev, _msgs = _diag_verdict(diag)
        _mh = "<br>".join(_h.escape(m) for m in _msgs)
        diag_block = (
            '<div class="card diag"><div class=head>학습 결과 (수치)'
            ' <span class=meta>실패 진단용 · 직접 정하는 값 아님</span></div>'
            '<p class=note>아래는 <b>학습이 어떻게 끝났는지</b> 보여주는 결과예요. '
            '보상·전략을 바꾼 게 어떤 결과로 이어졌는지, 특히 <b>실패 원인</b>을 여기서 읽습니다.</p>'
            f'<div class=stats>{"".join(_dc)}</div>'
            f'<div class="diagmsg {_sev}">{_mh}</div></div>\n')
        print("[report] 학습 결과(진단): " + " · ".join(
            x for x in [
                f"최고보상 {diag['best_reward']:.2f}(iter {diag.get('best_iter')})" if "best_reward" in diag else "",
                f"지형 {diag['terrain_lv']:.2f}" if "terrain_lv" in diag else "",
                f"낙상률 {diag['fall_rate']*100:.1f}%" if "fall_rate" in diag else "",
                f"std {diag['action_std']:.3f}" if "action_std" in diag else "",
            ] if x))

    doc = f"""<!DOCTYPE html><html lang=ko><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>제출 분석 — {label}</title><style>
body{{font-family:system-ui,'Apple SD Gothic Neo',sans-serif;background:#faf9f7;color:#222;margin:0;padding:24px;}}
.card{{max-width:720px;margin:0 auto;background:#fff;border:1px solid #e1e0d9;border-radius:12px;padding:24px 28px;}}
.head{{font-size:18px;font-weight:600;border-bottom:1px solid #eee;padding-bottom:12px;overflow:hidden;}}
.head .meta{{font-size:13px;color:#777;font-weight:400;float:right;font-family:ui-monospace,monospace;}}
.timing{{clear:both;font-size:12px;color:#888;font-family:ui-monospace,monospace;padding-top:8px;}}
.banner{{background:{bcol[0]};color:{bcol[1]};border-radius:8px;padding:12px 16px;margin:16px 0 22px;font-size:15px;font-weight:600;}}
.banner small{{display:block;font-size:11px;font-weight:400;text-transform:uppercase;opacity:.7;letter-spacing:.04em;}}
.axis{{display:flex;justify-content:space-between;font-size:11px;color:#999;margin:0 132px 8px 152px;}}
.row{{display:flex;align-items:center;gap:10px;margin-bottom:14px;}}
.lbl{{width:140px;font-size:12.5px;color:#555;text-align:right;flex:none;}}
.track{{position:relative;flex:1;height:8px;background:#f0efec;border:1px solid #ddd;border-radius:6px;}}
.tick{{position:absolute;top:-3px;width:2px;height:14px;background:#999;transform:translateX(-1px);}}
.dot{{position:absolute;top:50%;width:14px;height:14px;border-radius:50%;border:2px solid #fff;transform:translate(-50%,-50%);}}
.val{{width:132px;font-size:12px;font-family:ui-monospace,monospace;text-align:right;flex:none;white-space:nowrap;}}
.val em{{color:#999;font-style:normal;}}
.warn{{background:#FCEBEB;color:#A32D2D;border-radius:8px;padding:10px 14px;margin-top:18px;font-size:13px;}}
table{{width:100%;border-collapse:collapse;margin-top:22px;font-size:13px;}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid #eee;}}
th{{color:#777;font-weight:500;}}
.guide{{margin-top:18px;}}
.guide h2{{font-size:16px;font-weight:600;margin:0;}}
.guide h3{{font-size:13.5px;font-weight:600;color:#333;margin:18px 0 6px;border-top:1px solid #f0f0f0;padding-top:14px;}}
.guide dt{{font-family:ui-monospace,monospace;font-weight:600;font-size:12.5px;color:#222;margin-top:10px;}}
.guide dd{{margin:2px 0 0;font-size:13px;color:#555;line-height:1.65;}}
.guide ul{{margin:6px 0 0;padding-left:18px;}} .guide li{{font-size:13px;color:#555;line-height:1.85;}}
.guide p{{font-size:13px;color:#555;line-height:1.65;margin:6px 0 0;}}
.guide .hint{{color:#7a6a3a;font-size:12px;background:#f6f1e3;border-radius:6px;padding:9px 12px;margin-top:12px;line-height:1.6;}}
.guide code{{background:#eee;padding:1px 5px;border-radius:4px;font-family:ui-monospace,monospace;font-size:12px;}}
.guide .keep{{background:#FFF7E6;border:1px solid #f0e0b8;border-radius:8px;padding:11px 14px;color:#7a5b00;margin-top:8px;line-height:1.65;}}
.swatch{{display:inline-block;width:11px;height:11px;border-radius:50%;border:1px solid #0002;margin:0 3px -1px 0;}}
.diag .note{{font-size:13px;color:#555;line-height:1.6;margin:0 0 16px;}}
.stats{{display:flex;flex-wrap:wrap;gap:12px;}}
.stat{{flex:1;min-width:118px;background:#f7f6f3;border:1px solid #eceae3;border-radius:8px;padding:13px 14px;text-align:center;}}
.sv{{font-size:20px;font-weight:600;font-family:ui-monospace,monospace;color:#222;}}
.sk{{font-size:11.5px;color:#888;margin-top:4px;}}
.diagmsg{{margin-top:16px;border-radius:8px;padding:11px 14px;font-size:13px;line-height:1.7;}}
.diagmsg.ok{{background:#EAF4EC;color:#1F6B33;}}
.diagmsg.warn{{background:#FBF3E2;color:#8A5A00;}}
.diagmsg.bad{{background:#FCEBEB;color:#A32D2D;}}
</style></head><body><div class=card>
<div class=head>{label} <span class=meta>{' · '.join(meta)}</span>{timing_html}</div>
<div class=banner><small>튜닝 의도</small>{_h.escape(bias)}{tail}</div>
<div class=axis><span>← 안정</span><span>공격 →</span></div>
{dials}
{warn_html}
<table><tr><th>항목</th><th>기본</th><th>제출</th><th>Δ</th><th>의도/효과</th></tr>{trows}</table>{extra_note}
</div>
{diag_block}<div class="card guide">
<h2>리포트 보는 법</h2>
<h3>① 맨 윗줄 — 모델 정보</h3>
<dl>
<dt>관절 수 (예: 12)</dt><dd>로봇이 움직이는 관절(다리 모터) 수. 사족(Go2)=12, 휴머노이드(H1)=19 → <b>로봇 종류 확인용</b>.</dd>
<dt>iter A / 총 B (예: 11800 / 총 15000)</dt><dd><b>A</b> = 제출용으로 선택된 <b>best 체크포인트의 시점</b>(보상이 가장 높았던 반복), <b>B</b> = 실제로 돌린 <b>총 반복 횟수</b>. 둘은 다릅니다 — <b>A 가 B 보다 많이 작으면</b> 초반에 정점을 찍고 이후 나빠졌다는 뜻(보상 설정 의심). 아주 짧게 돌리면(예: 10회) 학습이 되기 전이라 A 가 0 으로 나올 수 있어요.</dd>
<dt>params (예: 0.29M)</dt><dd>정책 신경망 가중치 개수 = <b>모델 크기</b>. 로봇 종류 같으면 보통 비슷.</dd>
<dt>NaN 없음(제출 파일) / NaN 발견</dt><dd>가중치에 '깨진 값'(계산 불가)이 있나 검사. <b>없음 = 제출 파일이 멀쩡하다</b>는 뜻입니다. ⚠️ <b>학습 도중 발산했는지는 이것으로 알 수 없습니다</b> — 제출은 보상이 가장 높았던 시점(발산 *이전*)을 고르므로 발산한 학습도 여기는 '없음' 으로 나옵니다. <b>발산 여부는 아래 '학습 결과' 카드</b>에서 확인하세요. <i>(NaN 없음이 '잘 걷는다'는 뜻도 아님.)</i></dd>
<dt>학습시작 · 종료 · 소요</dt><dd>학습 시작/종료 시각과 걸린 시간. 학습 종료 시 자동 기록.</dd>
</dl>
<p class=hint>※ <code>iter</code> 는 '<b>반복 횟수</b>', <b>소요</b> 는 실제 걸린 '<b>시간</b>' — 둘은 다릅니다(같은 iter라도 GPU·설정에 따라 시간이 달라요).</p>
<h3>② 게이지 — 안정 ↔ 공격</h3>
<ul>
<li><b>회색 세로 눈금</b> = 기본값, <b>색 점</b> = 제출값.</li>
<li><b>왼쪽=안정 / 오른쪽=공격</b> — 오른쪽일수록 빠르고 과감.</li>
<li><span class=swatch style="background:#D85A30"></span><b>주황</b> 공격 쪽 이동 · <span class=swatch style="background:#378ADD"></span><b>파랑</b> 안정 쪽 이동 · <span class=swatch style="background:#888780"></span><b>회색</b> 안 바꿈.</li>
<li><span class=swatch style="background:#E24B4A"></span><b>빨강</b> = 추천 범위 <b>벗어남</b>(보행 망가질 수 있어 꼭 확인).
<b>처음 받은 값 그대로여도 빨강일 수 있어요</b> — 그 항목은 직접 조정해 보라는 뜻입니다.</li>
<li><b>(고급)</b> = 기본은 꺼져 있는(off) 옵션을 켰다는 뜻.</li>
</ul>
<h3>③ 학습 결과 수치 — 실패 진단</h3>
<dl>
<dt>최고 보상 (iter N)</dt><dd>학습 중 보상이 가장 높았던 시점과 그 반복 횟수 — 이 시점 모델을 제출용으로 자동 선택해요. <b>iter 가 너무 초반</b>이면 초반에 정점 찍고 이후 나빠졌다는 뜻(보상 설정 의심).</dd>
<dt>지형 난이도 (terrain level)</dt><dd>로봇이 견딘 지형의 어려움 단계(평지에서 시작해 험지로 <b>자동 상승</b>). 높을수록 거친 지형까지 정복. <b>0 근처에 머물면</b> 평지조차 제대로 못 걸어 난이도가 안 올라간 것(걷기 실패). <i>(평지 전용 학습이면 표시 안 됨.)</i></dd>
<dt>낙상률</dt><dd>에피소드가 <b>넘어져서</b> 끝난 비율(시간이 다 차서 끝나면 '생존'). 낮을수록 안정. <b>높으면</b> 불안정 → 안전 쪽 보상(낙상 벌점↑·속도↓) 검토.</dd>
<dt>탐색 std</dt><dd>정책이 동작을 얼마나 <b>무작위로 시도</b>하는지(처음 1.0 → 학습되며 보통 0.3~0.6 으로 감소). <b>너무 낮으면(≈0)</b> 한 동작에 갇힘(제자리·주저앉기), <b>1.0 근처면</b> 거의 학습이 안 된 것.</dd>
</dl>
<p class=hint>※ 이 수치들은 학습이 끝난 '결과'예요. 보상·전략을 바꾼 게 좋은 결과로 이어졌는지, 특히 <b>왜 실패했는지</b> 단서를 줍니다. 위 색 박스가 🔴(빨강)면 그 항목부터 확인하세요.</p>
<h3>꼭 기억하세요</h3>
<p class=keep>이 리포트는 보상을 <b>어떻게 바꿨나(의도)</b>만 보여줍니다. <b>실제로 잘 걷는지</b>는 숫자로 안 보여요 — 반드시 <code>play.py</code> 로 <b>영상을 직접 확인</b>하세요.</p>
</div></body></html>"""
    out = final_dir / "report.html"
    out.write_text(doc, encoding="utf-8")
    return out


def _submit_config():
    """제출 서버 host/token — env(SUBMIT_HOST / SUBMIT_TOKEN) > <repo>/submit_config.txt.
    ⚠️ training/ 은 참가자에게 배포되는 영역이라 코드·주석에 자격증명을 두지 않는다.
       운영 서버에만 env 또는 submit_config.txt(gitignored) 를 배치해 사용."""
    import os
    host = (os.environ.get("SUBMIT_HOST") or "").strip()
    token = (os.environ.get("SUBMIT_TOKEN") or "").strip()
    if not (host and token):
        try:
            cfg = PROJECT_DIR.parent.parent / "submit_config.txt"
            if cfg.exists():
                for ln in cfg.read_text(encoding="utf-8").splitlines():
                    ln = ln.strip()
                    if not ln or ln.startswith("#") or "=" not in ln:
                        continue
                    k, v = (x.strip() for x in ln.split("=", 1))
                    if k.lower() == "host" and not host:
                        host = v
                    elif k.lower() == "token" and not token:
                        token = v
        except Exception:
            pass
    return host.rstrip("/"), token


def _submit_zip(final_dir):
    """exported/ 결과물을 zip 으로 묶어 운영 서버에 **자동 백업** (학습 종료 시).

    ⚠️ **예선 제출이 아니다.** 공식 제출은 참가자가 대회 웹사이트에서 policy.pt·env.yaml·
       코멘트를 직접 업로드하는 것. 이 기능은 학습이 몇 시간 걸리므로 **서버가 꺼지거나
       컨테이너가 재생성돼도 학습 이력이 남도록** 제공하는 편의 장치다.
    zip = model_best.pt + env.yaml + report.html. (코멘트/의도는 참가자가 별도 제출 — zip 에 X.)
    stdlib(urllib)만. 서버 설정은 _submit_config() 참조 — 코드에 자격증명 없음.
    설정이 없으면 제출을 건너뛴다. 자동 제출 끄기: env  NO_AUTO_SUBMIT=1.
    ⚠️ h1_task/go2_task 미러."""
    import io
    import os
    import time
    import uuid
    import zipfile
    from urllib import request as _rq
    from urllib.error import HTTPError, URLError

    if os.environ.get("NO_AUTO_SUBMIT"):
        print("[backup] NO_AUTO_SUBMIT 설정됨 — 자동 백업 건너뜀")
        return
    pt = final_dir / "model_best.pt"
    yml = final_dir / "env.yaml"
    if not (pt.exists() and yml.exists()):
        print("[backup] model_best.pt/env.yaml 없음 — 자동 백업 skip")
        return
    host, token = _submit_config()
    if not (host and token):
        print("[backup] 백업 서버 설정 없음 — 자동 백업 skip. "
              "(운영 서버: env SUBMIT_HOST/SUBMIT_TOKEN 또는 submit_config.txt)")
        return

    buf = io.BytesIO()
    names = ["model_best.pt", "env.yaml"]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(pt, "model_best.pt")
        z.write(yml, "env.yaml")
        report = final_dir / "report.html"
        if report.exists():
            z.write(report, "report.html"); names.append("report.html")
    data = buf.getvalue()
    fname = f"submission_{int(time.time())}.zip"
    boundary = "----finalsgame" + uuid.uuid4().hex
    body = ((f"--{boundary}\r\nContent-Disposition: form-data; name=\"upfile\"; "
             f"filename=\"{fname}\"\r\nContent-Type: application/zip\r\n\r\n").encode("utf-8")
            + data + f"\r\n--{boundary}--\r\n".encode("utf-8"))
    req = _rq.Request(host + "/api/front/v1/studyFile", data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
    })
    # ⚠️ 이 로그는 **참가자 화면에 그대로 보인다.** 백업 서버 주소·응답 본문(팀/유저/파일 ID,
    #    내부 API 구조)을 찍지 않는다 — 호스트·토큰을 코드에서 뺀 것과 같은 이유다.
    #    운영자가 원인을 봐야 할 때만 env  SUBMIT_DEBUG=1 로 상세를 켠다.
    _dbg = bool(os.environ.get("SUBMIT_DEBUG"))
    print(f"[backup] 학습 결과 자동 백업 중... ({len(data)/1024:.0f}KB, {' + '.join(names)})"
          + (f"  → {host}" if _dbg else "")
          + "\n          ⚠️ 이것은 **예선 제출이 아닙니다** — 제출은 대회 웹사이트에서 policy.pt 를 직접 업로드하세요.")
    try:
        with _rq.urlopen(req, timeout=120) as resp:
            _body = resp.read().decode("utf-8", "replace")
            print("[backup] ✅ 백업 완료" + (f" (HTTP {resp.status}) — {_body[:200]}" if _dbg else ""))
    except HTTPError as e:
        reason = {413: "업로드 용량 초과 — 서버 nginx client_max_body_size 상향 필요",
                  404: "미등록 서버 — 개발사에 서버 IP 등록 요청",
                  401: "인증 토큰 오류", 403: "권한 거부"}.get(e.code)
        body = e.read().decode('utf-8', 'replace')[:200]
        # 실패는 참가자도 알아야 하지만, 응답 본문은 운영자(SUBMIT_DEBUG)만 본다.
        print(f"[backup] ❌ 백업 실패 (HTTP {e.code})"
              + (f" — {reason}" if reason else "")
              + (f"  응답: {body}" if _dbg else "")
              + "\n          (학습 결과는 exported/ 에 그대로 있습니다 — 백업만 실패한 것입니다)")
    except URLError as e:
        print(f"[backup] ⚠️ 연결 실패: {e.reason}  (오프라인/미등록 서버면 무시)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="학습 결과 best 선별 + 정리")
    parser.add_argument("--run", type=str, default=None, help="run 폴더 경로 (생략시 최신)")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="logs/ 의 intermediate .pt 삭제 안 함 (기본은 삭제)")
    args = parser.parse_args()
    run = Path(args.run) if args.run else None
    finalize(run, cleanup=not args.no_cleanup)
