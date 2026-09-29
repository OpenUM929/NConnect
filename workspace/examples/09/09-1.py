# 9강 · 키보드로 어깨 관절 조종하기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import asyncio
import carb.input
import omni.appwindow
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path

class KeyboardTeleop:
    def __init__(self):
        self.pressed = set()
        app = omni.appwindow.get_default_app_window()
        self.kb = app.get_keyboard()
        self.ip = carb.input.acquire_input_interface()
        self.sub = self.ip.subscribe_to_keyboard_events(self.kb, self._on)

    def _on(self, e):
        if e.type == carb.input.KeyboardEventType.KEY_PRESS:
            self.pressed.add(e.input.name)
        elif e.type == carb.input.KeyboardEventType.KEY_RELEASE:
            self.pressed.discard(e.input.name)
        return True

    def is_pressed(self, k): return k in self.pressed

    def close(self): self.ip.unsubscribe_to_keyboard_events(self.kb, self.sub)

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0.0, 0.0, 1.05])))

    await world.reset_async()

    teleop = KeyboardTeleop()
    l_sh = h1.dof_names.index("left_shoulder_pitch")
    r_sh = h1.dof_names.index("right_shoulder_pitch")
    targets = h1.get_joint_positions().copy()
    angle = 0.0

    print(f"관절 {h1.num_dof}개 중 키로 움직이는 건 어깨 2개예요")
    print("W = 양팔 올리기 / S = 내리기 / R = 처음 자세 / Q = 종료")

    for step in range(3600):
        if teleop.is_pressed("Q"): break
        if teleop.is_pressed("W"): angle += 0.01
        if teleop.is_pressed("S"): angle -= 0.01
        if teleop.is_pressed("R"): angle = 0.0
        angle = float(np.clip(angle, -0.4, 1.4))
        targets[l_sh] = angle
        targets[r_sh] = angle
        h1.apply_action(ArticulationAction(joint_positions=targets))
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
        if step % 120 == 0:
            print(f"{step:5d}스텝 · 목표 어깨 각도 {angle:+.2f} rad")

    teleop.close()
    print("조종을 마쳤어요. 팔은 움직였지만 로봇이 걸어가진 않았죠")

asyncio.ensure_future(main())
