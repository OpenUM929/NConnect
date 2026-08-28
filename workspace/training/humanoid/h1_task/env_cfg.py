"""Humanoid (H1) training environment for NAVER Connect Robotics Cup 2026 예선.

다양한 지형 (경사로, 계단, 박스언덕, 박스미로, 평지) 위에서 통합 학습.

기반: IsaacLab `H1RoughEnvCfg` + 박스 obstacle height 범위 확장 (0.45m 박스언덕 학습).

cfg 두 종류:
  - HumanoidRoughEnvCfg  : 학생용, humanoid_rewards.py 로드
"""

from __future__ import annotations

import os

from isaaclab.utils import configclass
from isaaclab_tasks.manager_based.locomotion.velocity.config.h1.rough_env_cfg import (
    H1RoughEnvCfg,
)

from humanoid_rewards import REWARD_WEIGHTS


def _apply_common_overrides(self, source_label: str, reward_weights: dict | None) -> None:
    """학생/운영진 공통 후처리 - reward override + terrain + command 범위."""
    # reward 가중치 적용
    if reward_weights:
        print(f"[Humanoid:{source_label}] {len(reward_weights)} reward 항목 로드")
        for name, weight in reward_weights.items():
            attr = getattr(self.rewards, name, None)
            if attr is None:
                # 항목 자체 없거나, H1RoughEnvCfg 에서 None 으로 disable 된 경우.
                # Windows CP949 콘솔 대응 - ASCII 만 사용.
                print(f"  [WARN] {name} - 비활성 또는 없음 (RewTerm 정의 X). skip")
                continue
            try:
                attr.weight = float(weight)
                print(f"  [OK] {name}.weight = {weight}")
            except AttributeError:
                print(f"  [WARN] {name} - weight 속성 없음 (잘못된 이름). skip")
    else:
        print(f"[Humanoid:{source_label}] reward 비어있음 - H1RoughEnvCfg default 사용")

    # ─── 지형 학습 (Option A: sub-terrain 분리 + proportion 조정) ──────
    # 실측 이력:
    #   (1) box width (0.5, 1.8) + num↑ → 박스 step-up 가능, 계단 자빠짐.
    #   (2) box height (0.05, 0.55) 만 확장 → 박스/계단 trade-off 여전.
    #   (3) step_height_range (0.10, 0.18) 좁힘 → 분포 끝점 robust 약화.
    #
    # 새 시도 (option A):
    #   · 박스 obstacle: height (0.15, 0.50) — finals 0.45m 중심, 작은 0.05m
    #     쓸데없는 학습 제거.
    #   · 계단 step_height: default (0.05, 0.23) wide 유지 — 분포 robust 우선.
    #   · 박스 sub_terrain proportion ↑ — 박스 step-up 노출 빈도 ↑.
    # 학습 iter 25000+ 권장.
    try:
        sub = self.scene.terrain.terrain_generator.sub_terrains
        print(f"[Humanoid:{source_label}] sub_terrains keys = {list(sub.keys())}")
        # 1) 박스류 obstacle height — finals 박스 0.45m 중심으로 좁힘
        box_overridden = []
        for key in ("boxes", "discrete_obstacles", "random_rough"):
            if key not in sub:
                continue
            cfg = sub[key]
            # box_long 단일 = 0.45m → 0.50 max 면 분포 안. 확장 안 함.
            # (이전 0.65 확장 → cube z 확인 결과 단일 박스 0.45m 라 불필요했음)
            if hasattr(cfg, "grid_height_range"):
                cfg.grid_height_range = (0.15, 0.50)
                box_overridden.append(f"{key}.grid_height")
            if hasattr(cfg, "obstacle_height_range"):
                cfg.obstacle_height_range = (0.15, 0.50)
                box_overridden.append(f"{key}.obstacle_height")
            # 박스 width 도 finals 박스 범위 (1m 정도) 고려
            if hasattr(cfg, "grid_width_range"):
                cfg.grid_width_range = (0.6, 1.5)
                box_overridden.append(f"{key}.grid_width")
            if hasattr(cfg, "obstacle_width_range"):
                cfg.obstacle_width_range = (0.6, 1.5)
                box_overridden.append(f"{key}.obstacle_width")
        if box_overridden:
            print(f"[Humanoid:{source_label}] 박스류 override: {box_overridden}")
        else:
            print(f"[Humanoid:{source_label}] 박스류 sub_terrain 없음")
        # 2) 계단 — default 유지 (wide 가 robust). step_width 만 결승 0.30 확인.
        stairs_overridden = []
        for key in ("pyramid_stairs", "pyramid_stairs_inv",
                    "stairs", "stairs_up", "stairs_down",
                    "hf_pyramid_stairs", "hf_pyramid_stairs_inv"):
            if key not in sub:
                continue
            cfg = sub[key]
            if hasattr(cfg, "step_width"):
                cfg.step_width = 0.30
                stairs_overridden.append(f"{key}.step_width=0.30")
        if stairs_overridden:
            print(f"[Humanoid:{source_label}] 계단 width override: {stairs_overridden}")
        # 3) Proportion — 박스 비중 ↑ (박스 step-up 노출 빈도 ↑)
        prop_changes = []
        for key, new_prop in (
            ("boxes", 0.30),
            ("discrete_obstacles", 0.25),
            ("random_rough", 0.10),
            ("pyramid_stairs", 0.15),
            ("pyramid_stairs_inv", 0.15),
        ):
            if key not in sub:
                continue
            cfg = sub[key]
            if hasattr(cfg, "proportion"):
                old = cfg.proportion
                cfg.proportion = new_prop
                prop_changes.append(f"{key}: {old:.2f}→{new_prop:.2f}")
        if prop_changes:
            print(f"[Humanoid:{source_label}] proportion: {prop_changes}")
    except Exception as e:
        print(f"[Humanoid:{source_label}] terrain override 실패 (무시): {e}")

    # cube 수집 task - 이동 속도 적정 범위
    self.commands.base_velocity.ranges.lin_vel_x = (-1.0, 1.5)
    self.commands.base_velocity.ranges.lin_vel_y = (-0.5, 0.5)
    self.commands.base_velocity.ranges.ang_vel_z = (-1.0, 1.0)

    # 영상 녹화용 추적 카메라 (학습은 headless라 영향 없음, 표시 전용)
    # ⚠️ [2026-08-21] "영상에서 계단만 보이고 로봇이 안 보인다" 문의 → 앙각을 올렸다.
    #    예전 값(높이 3m / 수평 7.07m)은 앙각 **23°** 로 너무 낮아, 로봇이 계단·박스 위에
    #    있으면 카메라가 지형 측면에 파묻혔다. 높이를 올려 내려다보는 각도로 바꾼다.
    #    lookat 도 발밑(z=0)에서 **골반 높이**로 올린다 — 발밑을 보면 화면이 바닥으로 찬다.
    # ⭐ 참가자가 바꾸고 싶으면 **Hydra CLI override** 를 쓴다 (재배포 불필요, 아무 cfg 필드나):
    #    play.py --task Humanoid-v0 ... env.viewer.eye="[-10.0,-10.0,10.0]"
    #    ⚠️ 거리만 늘리면 앙각이 *낮아져* 오히려 더 가린다 — 거리를 늘리면 높이도 같이.
    self.viewer.origin_type = "asset_root"   # 로봇을 계속 따라다님
    self.viewer.asset_name = "robot"
    self.viewer.eye = (-5.0, -5.0, 5.5)     # 수평 7.1m · 높이 5.5m → 앙각 약 33°
    self.viewer.lookat = (0.0, 0.0, 0.9)    # H1 골반 높이 (키 ~1.8m)
    self.viewer.resolution = (1920, 1080)


@configclass
class HumanoidRoughEnvCfg(H1RoughEnvCfg):
    """Humanoid (H1) rough terrain velocity-tracking env - 학생용."""

    def __post_init__(self) -> None:
        super().__post_init__()
        _apply_common_overrides(self, "student", REWARD_WEIGHTS)
        # ── play.py --push 전용: 밀침 회복(채점표 H7) 확인 스위치 ─────────
        # ⚠️ 학습 조건을 바꾸는 문이 아니다 — train.py 가 이 변수를 지우므로
        #    학습에서는 절대 켜지지 않는다(전 팀 동일 조건 유지). 평가의 밀침은
        #    채점기가 별도로 구성하며 값도 여기와 다르다.
        #    이 설치본은 events.push_robot 이 None(비활성)이라 항을 새로 만든다.
        _push = os.environ.get("NCRC_PLAY_PUSH")
        if _push:
            try:
                from isaaclab.envs import mdp as _mdp
                from isaaclab.managers import EventTermCfg as _EvT
                _v = abs(float(_push)) or 0.5
                self.events.push_robot = _EvT(
                    func=_mdp.push_by_setting_velocity, mode="interval",
                    interval_range_s=(4.0, 4.0),
                    params={"velocity_range": {"x": (-_v, _v), "y": (-_v, _v)}})
                print(f"[Humanoid] 밀침 테스트 켜짐 — 4초마다 ±{_v} m/s (play 전용)")
            except Exception as e:                       # noqa: BLE001
                # 조용히 넘기지 않는다 — 켜 달라고 했는데 못 켰으면 말한다.
                print(f"[Humanoid] 🔴 --push 활성 실패 (밀침 없이 진행): {e}")


