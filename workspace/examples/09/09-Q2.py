# 9강 · 코드 실습하기 Q2 — 보통 · 100스텝 뒤의 각도
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 매 스텝 0.01 rad씩 올리고 상한은 1.4 rad예요. 100스텝 뒤 각도를 도로 바꾸면 몇 도일까요?

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path

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

    l_sh = h1.dof_names.index("left_shoulder_pitch")
    r_sh = h1.dof_names.index("right_shoulder_pitch")
    targets = h1.get_joint_positions().copy()
    angle = 0.0

    for step in range(100):
        angle = float(np.clip(angle + 0.01, -0.4, 1.4))
        targets[l_sh] = angle
        targets[r_sh] = angle
        h1.apply_action(ArticulationAction(joint_positions=targets))
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()

    print(f"100스텝 뒤 목표 어깨 각도(도) = {np.rad2deg(angle):.0f}")

asyncio.ensure_future(main())
