"""Quadruped (Unitree Go2) training environment for NAVER Connect Robotics Cup 2026 예선.

기반: IsaacLab `UnitreeGo2RoughEnvCfg` (rough terrain + height_scanner).
Go2 는 사족로봇 - 계단/경사 가능, 큰 박스 (≥0.2m) 등반 어려움.

cfg 두 종류:
  - QuadrupedRoughEnvCfg  : 학생용, quadruped_rewards.py 로드
"""

from __future__ import annotations

import os

from isaaclab.utils import configclass
# IsaacLab 버전별 모듈 경로 차이 대응 (go2 vs unitree_go2)
try:
    from isaaclab_tasks.manager_based.locomotion.velocity.config.go2.rough_env_cfg import (
        UnitreeGo2RoughEnvCfg,
    )
except ImportError:
    try:
        from isaaclab_tasks.manager_based.locomotion.velocity.config.unitree_go2.rough_env_cfg import (
            UnitreeGo2RoughEnvCfg,
        )
    except ImportError:
        # Class 이름이 Go2RoughEnvCfg 인 경우도 대응
        from isaaclab_tasks.manager_based.locomotion.velocity.config.go2.rough_env_cfg import (
            Go2RoughEnvCfg as UnitreeGo2RoughEnvCfg,
        )

from quadruped_rewards import REWARD_WEIGHTS


def _apply_common_overrides(self, source_label: str, reward_weights: dict | None) -> None:
    """학생/운영진 공통 후처리 - reward override + terrain + command 범위."""
    if reward_weights:
        print(f"[Quadruped:{source_label}] {len(reward_weights)} reward 항목 로드")
        for name, weight in reward_weights.items():
            attr = getattr(self.rewards, name, None)
            if attr is None:
                # Windows CP949 콘솔 대응 - ASCII 만 사용.
                print(f"  [WARN] {name} - 비활성 또는 없음 (RewTerm 정의 X). skip")
                continue
            try:
                attr.weight = float(weight)
                print(f"  [OK] {name}.weight = {weight}")
            except AttributeError:
                print(f"  [WARN] {name} - weight 속성 없음 (잘못된 이름). skip")
    else:
        print(f"[Quadruped:{source_label}] reward 비어있음 - UnitreeGo2RoughEnvCfg default 사용")

    # 박스 obstacle 만 낮게 제한 (stairs/slope 는 stock 그대로 - Go2 climb 가능)
    try:
        sub = self.scene.terrain.terrain_generator.sub_terrains
        for key in ("boxes", "discrete_obstacles"):
            if key not in sub:
                continue
            cfg = sub[key]
            if hasattr(cfg, "grid_height_range"):
                cfg.grid_height_range = (0.02, 0.15)
            if hasattr(cfg, "obstacle_height_range"):
                cfg.obstacle_height_range = (0.02, 0.15)
        print(f"[Quadruped:{source_label}] terrain override - boxes ≤0.15m")
    except Exception as e:
        print(f"[Quadruped:{source_label}] terrain override 실패 (무시): {e}")

    # command 범위 — 게임 사용 범위(vx 캡 1.6, wz 캡 1.0) + 학습 가능성 기준.
    # ⚠️ 이전 (-1.5, 2.5) 는 과확장: 추종 보상이 exp(-err²/0.5²) 라 2 m/s+ 명령은
    #   보상 ≈ 0 → 학습 초기 gradient 없음 → "전진 포기 + 제자리 회전" 국소최적
    #   (실측: track_ang 만 0.55 학습, track_lin 0.13 · error_vel_xy 1.99 · terrain 0).
    #   검증된 IsaacLab Go2 기본은 (-1.0, 1.0). 게임 cap(1.6) 여유분만 남기고 축소.
    self.commands.base_velocity.ranges.lin_vel_x = (-1.0, 2.0)
    self.commands.base_velocity.ranges.lin_vel_y = (-0.6, 0.6)
    self.commands.base_velocity.ranges.ang_vel_z = (-1.0, 1.0)

    # 영상 녹화용 추적 카메라 (학습은 headless라 영향 없음, 표시 전용)
    # ⚠️ [2026-08-21] "영상에서 계단만 보이고 로봇이 안 보인다" 문의 → 앙각을 올렸다.
    #    예전 값(높이 2.5m / 수평 5.66m)은 앙각 **24°** 로 너무 낮아, 로봇이 계단·박스 위에
    #    있으면 카메라가 지형 측면에 파묻혔다. 높이를 올려 내려다보는 각도로 바꾼다.
    #    lookat 도 발밑(z=0)에서 **몸통 높이**로 올린다 — 발밑을 보면 화면이 바닥으로 찬다.
    # ⭐ 참가자가 바꾸고 싶으면 **Hydra CLI override** 를 쓴다 (재배포 불필요, 아무 cfg 필드나):
    #    play.py --task Quadruped-v0 ... env.viewer.eye="[-8.0,-8.0,7.0]"
    #    ⚠️ 거리만 늘리면 앙각이 *낮아져* 오히려 더 가린다 — 거리를 늘리면 높이도 같이.
    self.viewer.origin_type = "asset_root"   # 로봇을 계속 따라다님
    self.viewer.asset_name = "robot"
    self.viewer.eye = (-4.0, -4.0, 4.0)     # 수평 5.7m · 높이 4.0m → 앙각 약 33°
    self.viewer.lookat = (0.0, 0.0, 0.3)    # Go2 몸통 높이 (키 ~0.4m)
    self.viewer.resolution = (1920, 1080)


@configclass
class QuadrupedRoughEnvCfg(UnitreeGo2RoughEnvCfg):
    """Quadruped (Go2) rough terrain - 학생용."""

    def __post_init__(self) -> None:
        super().__post_init__()
        _apply_common_overrides(self, "student", REWARD_WEIGHTS)
        # ── play.py --push 전용: 밀침 회복(채점표 G6) 확인 스위치 ─────────
        # ⚠️ 학습 조건을 바꾸는 문이 아니다 — train.py 가 이 변수를 지우므로
        #    학습에서는 절대 켜지지 않는다(전 팀 동일 조건 유지). 평가의 밀침은
        #    채점기가 별도로 구성하며 값도 여기와 다르다.
        #    이 설치본은 events.push_robot 이 None(비활성)이라 항을 새로 만든다.
        _push = os.environ.get("NCRC_PLAY_PUSH")
        _push_x = os.environ.get("NCRC_PLAY_PUSH_X")
        _push_y = os.environ.get("NCRC_PLAY_PUSH_Y")
        if _push or _push_x is not None or _push_y is not None:
            try:
                from isaaclab.envs import mdp as _mdp
                from isaaclab.managers import EventTermCfg as _EvT
                if _push_x is not None or _push_y is not None:
                    _vx = float(_push_x or 0.0)
                    _vy = float(_push_y or 0.0)
                    _velocity_range = {"x": (_vx, _vx), "y": (_vy, _vy)}
                    _label = f"fixed ({_vx}, {_vy}) m/s"
                else:
                    _v = abs(float(_push)) or 0.5
                    _velocity_range = {"x": (-_v, _v), "y": (-_v, _v)}
                    _label = f"random ±{_v} m/s"
                self.events.push_robot = _EvT(
                    func=_mdp.push_by_setting_velocity, mode="interval",
                    interval_range_s=(4.0, 4.0),
                    params={"velocity_range": _velocity_range})
                print(f"[Quadruped] 밀침 테스트 켜짐 — 4초마다 {_label} (play 전용)")
            except Exception as e:                       # noqa: BLE001
                # 조용히 넘기지 않는다 — 켜 달라고 했는데 못 켰으면 말한다.
                print(f"[Quadruped] 🔴 --push 활성 실패 (밀침 없이 진행): {e}")

        # G7 internal stress test only.  Stock Go2 already randomizes base mass
        # but keeps contact material fixed; the old evaluator therefore ran G7
        # with the exact same configuration as G3.  Widen several existing
        # startup/reset ranges only when the runner explicitly requests G7.
        # These are internal proxy ranges, not disclosed official evaluator
        # parameters.
        if os.environ.get("NCRC_EVAL_DR") == "1":
            try:
                material = self.events.physics_material.params
                material["static_friction_range"] = (0.6, 1.0)
                material["dynamic_friction_range"] = (0.5, 0.9)
                material["restitution_range"] = (0.0, 0.1)
                self.events.add_base_mass.params["mass_distribution_params"] = (-2.0, 4.0)
                self.events.reset_robot_joints.params["position_range"] = (0.9, 1.1)
                print(
                    "[Quadruped] G7 internal DR enabled: friction, restitution, "
                    "base mass, joint reset"
                )
            except Exception as e:  # noqa: BLE001
                raise RuntimeError(f"G7 internal DR configuration failed: {e}") from e


