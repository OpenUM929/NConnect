"""robot_sim.py — 제어·시뮬 (제공 파일, 수정하지 않아요)

19-1.py 가 쓰는 World / Robot / Cube / parse_cube_order 를 제공해요:
  - waypoint_to_velocity()   목표 → 속도 벡터
  - compute_observation()    로봇 상태 → 정책 입력 (Flat 69 / Rough 256 자동)
  - Robot.walk_to()          관측 → 정책(policy.pt) → 관절
  - Robot.reached()          목표 큐브 도달 판정
  - parse_cube_order()       LLM 답 → 큐브 방문 순서

바닥 + 조명 + 3색 큐브(yellow·green·red) 가 있는 단순한 씬이에요.
정책이 Flat(69)인지 Rough(256, height_scan 포함)인지는 자동으로 감지해요.
평지라서 height_scan 187칸은 상수로 채워요 (레이캐스터 불필요).

준비물:
  assets/h1/h1.usd                     로봇 모델
  assets/h1/payloads/geometries.usd    메시 본체 (없으면 로봇이 바닥을 뚫고 떨어져요)
  my_test.pt                          내 정책 (H1, Flat 69 또는 Rough 256 · action 19)
"""
from __future__ import annotations

import base64
import math
import os
import re
import time
from pathlib import Path

import numpy as np
import torch

# ── 아이작심 부팅 (import 시 1회) — 도커 서버는 로컬 창이 없어서 스트리밍으로 봐요 ──
from isaacsim import SimulationApp
_APP = SimulationApp({
    "headless": True,                    # 컨테이너엔 화면이 없음 → 창 대신 스트리밍
    "width": 1920, "height": 1080,
    "renderer": "RaytracedLighting",
    # ★ RTX 렌더 모드 고정 (원본 practice_sim/engine 과 동일). 이게 없으면 서버 GPU(RTX 신형)
    #   에서 기본 모드가 rt(1.0)/pt(path tracing)로 잡혀 헤드리스 WebRTC 가 '흰 화면'으로 나옴.
    #   → rt2(RTX 2.0 실시간)만 켜고 rt/pt 끔.
    "extra_args": [
        "--/persistent/rtx/modes/rt/enabled=false",
        "--/persistent/rtx/modes/rt2/enabled=true",
        "--/persistent/rtx/modes/pt/enabled=false",
        "--/rtx/rendermode=RaytracedLighting",
    ],
})

# WebRTC 스트리밍 ON → 브라우저에서 관전 (원본 practice_sim 과 동일)
try:
    from isaacsim.core.utils.extensions import enable_extension
    _APP.set_setting("/app/window/drawMouse", True)
    _APP.set_setting("/app/livestream/allowResize", True)
    enable_extension("omni.kit.livestream.webrtc")
    print("[robot_sim] WebRTC 스트리밍 ON → 브라우저 http://<서버IP>:5173/ 에서 관전")
except Exception as e:
    print(f"[robot_sim] 스트리밍 활성 실패(무시): {e}")

from isaacsim.core.api import World as _World
from isaacsim.core.api.objects import VisualCuboid
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation as Articulation
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.core.utils.viewports import set_camera_view

_HERE = Path(__file__).resolve().parent
ROBOT_USD  = str(_HERE / "assets" / "h1" / "h1.usd")   # 로봇 모델
ROBOT_PRIM = "/World/Robot"                            # H1: default prim = articulation root
SPAWN_POS  = np.array([0.0, 0.0, 1.05], dtype=np.float32)
SPAWN_QUAT = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
ACTION_SCALE = 0.5    # target = default + 0.5 * action
PHYSICS_DT, RENDER_DT, DECIMATION = 1.0 / 200.0, 1.0 / 50.0, 4   # 학습과 동일 (원본 engine.py)

# Gemini 키 로드: ① 환경변수 GEMINI_API_KEY → ② practice_key.bin (운영진 배포 · 난독화 XOR+b64)
_KEY_SALT = b"NCRC2026-practice-v1"    # 운영진 practice_key.bin 과 동일해야 함


def load_gemini_key():
    k = os.getenv("GEMINI_API_KEY", "").strip()
    if k:
        return k
    kf = _HERE / "practice_key.bin"     # 이 폴더에 두세요 (운영진이 준 파일)
    if kf.exists():
        try:
            blob = base64.b64decode(kf.read_bytes())
            return bytes(b ^ _KEY_SALT[i % len(_KEY_SALT)]
                         for i, b in enumerate(blob)).decode("utf-8").strip()
        except Exception as e:
            print(f"[robot_sim] practice_key.bin 해독 실패: {e}")
    return ""

# H1 기본 관절 자세 (IsaacLab H1_CFG.init_state) — 원본 observation.py
H1_DEFAULT_JOINT_POS = [
    (r".*_hip_yaw$", 0.0), (r".*_hip_roll$", 0.0), (r".*_hip_pitch$", -0.28),
    (r".*_knee$", 0.79), (r".*_ankle$", -0.52), (r"^torso$", 0.0),
    (r".*_shoulder_pitch$", 0.28), (r".*_shoulder_roll$", 0.0),
    (r".*_shoulder_yaw$", 0.0), (r".*_elbow$", 0.52),
]


# ============================================================
# ③ 제어 — 목표(x, y) → 속도 벡터 (원본 waypoint_controller.py)
# ============================================================
MAX_VX, MAX_WZ = 1.0, 1.0
STOP_DIST, APPROACH_DIST, YAW_GAIN = 0.3, 1.0, 2.0


def _wrap_pi(a: float) -> float:
    a = math.fmod(a, 2 * math.pi)
    if a > math.pi:
        a -= 2 * math.pi
    elif a < -math.pi:
        a += 2 * math.pi
    return a


def waypoint_to_velocity(robot_pos, robot_yaw, goal):
    dx, dy = goal[0] - robot_pos[0], goal[1] - robot_pos[1]
    dist = math.hypot(dx, dy)
    if dist < STOP_DIST:
        return 0.0, 0.0
    yaw_err = _wrap_pi(math.atan2(dy, dx) - robot_yaw)
    wz = max(-MAX_WZ, min(MAX_WZ, YAW_GAIN * yaw_err))
    vx = MAX_VX * max(0.0, math.cos(yaw_err)) * min(1.0, dist / APPROACH_DIST)
    return vx, wz


# ============================================================
# 관측 — 로봇 상태 → 정책 입력 (원본 observation.py)
#   Flat  = 69  (아래 7개)
#   Rough = 256 = 69 + height_scan 187 (17×11 격자)
# ============================================================
HEIGHT_SCAN_OFFSET, HEIGHT_SCAN_CLIP, HEIGHT_SCAN_N = 0.5, 1.0, 187


def _quat_rotate_inverse(q, v):
    w, x, y, z = q[0], q[1], q[2], q[3]
    qv = np.array([x, y, z], dtype=np.float32)
    return v * (2 * w * w - 1) - np.cross(qv, v) * (2 * w) + qv * (2 * float(np.dot(qv, v)))


def _quat_to_yaw(q):
    w, x, y, z = q[0], q[1], q[2], q[3]
    return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def compute_observation(lin_w, ang_w, quat_w, base_z, jpos, jvel,
                        default_jpos, cmd, last_action, use_height_scan):
    gravity_w = np.array([0.0, 0.0, -1.0], dtype=np.float32)
    parts = [
        _quat_rotate_inverse(quat_w, lin_w),        # base_lin_vel_b     3
        _quat_rotate_inverse(quat_w, ang_w),        # base_ang_vel_b     3
        _quat_rotate_inverse(quat_w, gravity_w),    # projected_gravity  3
        cmd,                                        # velocity_command   3
        jpos - default_jpos,                        # joint_pos_rel      19
        jvel,                                       # joint_vel          19
        last_action,                                # last_action        19
    ]
    if use_height_scan:
        # 평지: 187개 ray 모두 z=0 바닥에 닿음 → height_rel = base_z - 0 - 0.5 (상수)
        h = float(np.clip(base_z - HEIGHT_SCAN_OFFSET, -HEIGHT_SCAN_CLIP, HEIGHT_SCAN_CLIP))
        parts.append(np.full(HEIGHT_SCAN_N, h, dtype=np.float32))    # 187
    return torch.from_numpy(np.concatenate(parts).astype(np.float32))


def _build_default_joint_pos(dof_names):
    """USD dof 이름 순서대로 기본 관절 자세 (학습 default) 빌드."""
    out = np.zeros(len(dof_names), dtype=np.float32)
    for i, name in enumerate(dof_names):
        for pat, val in H1_DEFAULT_JOINT_POS:
            if re.fullmatch(pat, name):
                out[i] = val
                break
    return out


def _h1_pd_gains(dof_names):
    """관절별 PD gain (원본 engine.py). 0이면 모터가 안 움직여 로봇이 안 걸어요."""
    n = len(dof_names)
    kps, kds = np.zeros(n, dtype=np.float32), np.zeros(n, dtype=np.float32)
    for i, name in enumerate(dof_names):
        if name.endswith("_hip_yaw") or name.endswith("_hip_roll"):
            kps[i], kds[i] = 150.0, 5.0
        elif name.endswith("_hip_pitch") or name.endswith("_knee") or name == "torso":
            kps[i], kds[i] = 200.0, 5.0
        elif name.endswith("_ankle"):
            kps[i], kds[i] = 20.0, 4.0
        elif "_shoulder" in name or name.endswith("_elbow"):
            kps[i], kds[i] = 40.0, 10.0
        else:
            kps[i], kds[i] = 100.0, 5.0
    return kps, kds


# ============================================================
# 씬 — 바닥 + 조명 + 목표 큐브 하나
# ============================================================
def _add_lights():
    """기본 씬이 어두워서 돔+태양광 추가."""
    try:
        from pxr import UsdLux, Sdf
        import omni.usd
        stage = omni.usd.get_context().get_stage()
        dome = UsdLux.DomeLight.Define(stage, Sdf.Path("/World/DomeLight"))
        dome.CreateIntensityAttr(1500.0)
        sun = UsdLux.DistantLight.Define(stage, Sdf.Path("/World/SunLight"))
        sun.CreateIntensityAttr(3000.0)
    except Exception as e:
        print(f"[robot_sim] 조명 추가 실패(무시): {e}")


class World:
    def __init__(self):
        self.world = _World(physics_dt=PHYSICS_DT, rendering_dt=RENDER_DT,
                            stage_units_in_meters=1.0)
        # 바닥 마찰을 학습 지형과 동일하게 (μ=1.0, 반발 0). 기본값(0.5/반발0.8)이면
        # 발이 미끄러지고 튕겨서 다리는 도는데 앞으로 안 나가요 (IsaacLab H1 지형 미러).
        self.world.scene.add_default_ground_plane(
            static_friction=1.0, dynamic_friction=1.0, restitution=0.0)
        _add_lights()                    # 씬이 너무 어둡지 않게
        # ★ 카메라·스트림 초기화 순서 (원본 practice_sim 과 동일):
        #   reset() 를 *먼저* 해서 렌더/뷰포트 컨텍스트가 생긴 뒤에 set_camera_view 를 해야
        #   *스트리밍되는* 뷰포트에 카메라가 먹힘. reset 전에 카메라를 잡으면 뷰포트가 아직
        #   없어 기본 카메라(원점)로 남아 → 흰 화면. (RTX·render 고친 뒤에도 남던 잔여 원인.)
        self.world.reset()
        try:
            set_camera_view(eye=[-2.0, -18.0, 9.0], target=[8.0, 0.0, 0.6])
            print("[robot_sim] 카메라: 조망 시점 설정 완료")
        except Exception as e:
            print(f"[robot_sim] 카메라 설정 실패(무시): {e}")
        # 스트림 워밍업 — 렌더 몇 번 돌려 WebRTC 프레임 파이프라인·RTX 축적 확립
        #   (원본 practice_sim main() 의 워밍업 렌더 루프와 동일 역할)
        for _ in range(8):
            self.world.step(render=False)
            try:
                self.world.render()
            except Exception:
                pass
        self._next_t = None              # 실시간 페이싱 기준

    def is_running(self) -> bool:
        return _APP.is_running()

    def close(self):
        """아이작심 종료 — practice_sim.py 와 동일하게 sim_app.close() 하나.
        (scene.clear()·world.stop() 은 앱을 살려둔 채 viewport 만 비우는 '멀티매치 IDLE
         복귀'용 teardown 이라, 종료에 쓰면 씬이 비어 흰 화면이 돼요. 그래서 안 씀.)
        스트림·GPU·터미널이 준비 상태로 복귀해요."""
        try:
            _APP.close()
        except Exception:
            pass

    def step(self):
        # 제어 1틱(50Hz) = 물리 DECIMATION 스텝(200Hz) + 렌더 1회.
        # ★ 원본 practice_sim 헤드리스와 동일: 물리는 render=False, 스트림 렌더는 world.render()
        #   로 분리. (흰 화면의 진짜 원인은 렌더 호출 방식이 아니라 RTX 모드였음 — 위 SimulationApp
        #   extra_args 로 rt2 강제해 해결. 렌더 경로도 검증된 원본과 통일.)
        for _ in range(DECIMATION):
            self.world.step(render=False)
        try:
            self.world.render()
        except Exception:
            pass
        self._pace()

    def _pace(self):
        # 헤드리스 GPU는 물리를 벽시계보다 훨씬 빨리 돌려 '빨리감기'가 됨 → 실시간(1초=1초)으로 늦춤
        now = time.monotonic()
        if self._next_t is None:
            self._next_t = now
        self._next_t += RENDER_DT
        delay = self._next_t - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        elif delay < -0.5:
            self._next_t = time.monotonic()   # 너무 뒤처지면 기준 리셋


_CUBE_RGB = {
    "yellow": (0.95, 0.85, 0.10),
    "green":  (0.10, 0.90, 0.30),
    "red":    (0.90, 0.15, 0.15),
}


class Cube:
    """목표 큐브 (색상 마커)."""

    def __init__(self, world, x, y, color="green"):
        self.pos = (float(x), float(y))
        self.color = color
        rgb = _CUBE_RGB.get(color, (0.8, 0.8, 0.8))
        VisualCuboid(
            f"/World/cube_{color}",
            position=np.array([x, y, 0.3]),
            scale=np.array([0.4, 0.4, 0.4]),
            color=np.array(rgb),
        )


def parse_cube_order(text, names):
    """LLM 답에서 큐브 방문 순서를 뽑아냄 (JSON 배열 우선, 없으면 색 등장 순서).
    빠진 색은 뒤에 채워서 항상 완전한 순서를 돌려줘요."""
    import json
    m = re.search(r"\[[^\]]*\]", text)
    if m:
        try:
            arr = [c for c in json.loads(m.group(0)) if c in names]
            if arr:
                for c in names:            # 빠진 색 보충
                    if c not in arr:
                        arr.append(c)
                return arr
        except Exception:
            pass
    ko = {"노랑": "yellow", "노란": "yellow", "초록": "green", "녹색": "green",
          "빨강": "red", "빨간": "red"}
    seen, low = [], text.lower()
    for w in re.findall("|".join(list(ko) + names), low):
        c = ko.get(w, w)
        if c in names and c not in seen:
            seen.append(c)
    for c in names:                        # 빠진 색 보충
        if c not in seen:
            seen.append(c)
    return seen


# ============================================================
# 로봇 — 느린 대뇌(전략) + 빠른 소뇌(정책 policy.pt)
# ============================================================
class Robot:
    def __init__(self, world, policy_file):
        self.sim = world                                         # 스텝/페이싱용 World 참조
        # 정책 파일 찾기: 준 경로 → 없으면 스크립트 폴더(examples/19) 기준 → 친절한 안내
        pf = Path(policy_file)
        if not pf.exists() and (_HERE / policy_file).exists():
            pf = _HERE / policy_file
        if not pf.exists():
            pts = sorted(p.name for p in _HERE.glob("*.pt"))
            raise FileNotFoundError(
                f"정책 파일 '{policy_file}' 을 못 찾았어요. "
                f"이 폴더의 .pt: {pts or '(없음)'} — "
                f".pt 를 {_HERE} 에 두고 19-1.py 의 POLICY 를 그 이름으로 맞추세요.")
        self.policy = torch.jit.load(str(pf)).eval()             # ④ 소뇌(policy.pt) 로드
        self.obs_dim = self._infer_obs_dim()                     # 69(Flat) or 256(Rough)
        self.use_height_scan = self.obs_dim >= 256
        print(f"[robot_sim] 정책 관측 {self.obs_dim}차원 "
              f"({'Rough·height_scan' if self.use_height_scan else 'Flat'}) 감지")

        # 로드 순서 (원본 practice_sim): 참조 추가 → reset → articulation → 씬 등록 → reset
        add_reference_to_stage(ROBOT_USD, ROBOT_PRIM)
        world.world.reset()
        self.robot = Articulation(ROBOT_PRIM, name="h1",
                                  position=SPAWN_POS, orientation=SPAWN_QUAT)
        world.world.scene.add(self.robot)
        world.world.reset()

        # setup_after_reset (원본 engine.py): 기본 자세 + PD gain
        dof = list(self.robot.dof_names)
        self.default_jpos = _build_default_joint_pos(dof)
        self.robot.set_world_pose(SPAWN_POS, SPAWN_QUAT)
        self.robot.set_joint_positions(self.default_jpos)
        self.robot.set_joint_velocities(np.zeros(len(dof), dtype=np.float32))
        kps, kds = _h1_pd_gains(dof)
        self.robot.get_articulation_controller().set_gains(kps=kps, kds=kds)
        self.last_action = np.zeros(len(dof), dtype=np.float32)

    def _infer_obs_dim(self):
        """정책이 기대하는 관측 차원 자동 감지 (Flat 69 / Rough 256)."""
        for dim in (69, 256):
            try:
                with torch.no_grad():
                    self.policy(torch.zeros(1, dim))
                return dim
            except Exception:
                continue
        return 69

    @property
    def pos(self):
        return np.asarray(self.robot.get_world_pose()[0], dtype=np.float32)[:2]

    @property
    def yaw(self):
        return _quat_to_yaw(np.asarray(self.robot.get_world_pose()[1], dtype=np.float32))

    def hold(self):
        """정책으로 제자리 균형 (속도 벡터 0). 걷는 정책은 명령이 0이면 가만히 균형을 잡아요.
        기본 자세만 PD로 고정하면 균형 제어가 없어 넘어져요 — 그래서 정책을 계속 돌려요."""
        self.walk_to(self.pos)          # 목표 = 현재 위치 → 속도 0 → 제자리 균형

    def stand(self, seconds=3.0):
        """몇 초간 정책으로 제자리 균형 (로딩·LLM 대기 동안 안 넘어지게)."""
        for _ in range(int(seconds / RENDER_DT)):
            self.hold()
            self.sim.step()

    def reached(self, goal, tol=0.6):
        """현재 위치가 목표 큐브에 도달했는지 (평면 거리)."""
        return float(np.hypot(self.pos[0] - goal[0], self.pos[1] - goal[1])) < tol

    def walk_to(self, goal):
        """🦿 빠른 소뇌: 목표 → 속도 벡터 → 정책 → 관절 (원본 engine.py policy_step)."""
        vx, wz = waypoint_to_velocity(self.pos, self.yaw, goal)   # ③ 제어
        cmd = np.array([vx, 0.0, wz], dtype=np.float32)

        pos, quat = self.robot.get_world_pose()
        obs = compute_observation(
            np.asarray(self.robot.get_linear_velocity(), dtype=np.float32),
            np.asarray(self.robot.get_angular_velocity(), dtype=np.float32),
            np.asarray(quat, dtype=np.float32),
            float(np.asarray(pos, dtype=np.float32)[2]),         # base_z
            np.asarray(self.robot.get_joint_positions(), dtype=np.float32),
            np.asarray(self.robot.get_joint_velocities(), dtype=np.float32),
            self.default_jpos, cmd, self.last_action, self.use_height_scan,
        )
        with torch.no_grad():
            action = self.policy(obs.unsqueeze(0)).squeeze(0)     # ④ 정책 → 관절 토크
        self.last_action = action.cpu().numpy().astype(np.float32)

        target = self.default_jpos + ACTION_SCALE * self.last_action
        self.robot.apply_action(ArticulationAction(joint_positions=target))
