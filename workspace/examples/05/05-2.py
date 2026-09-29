# 5강 · 중력을 끈 채 왼팔 들기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.storage.native import get_assets_root_path

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    world.get_physics_context().set_gravity(0.0)

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0, 0, 1.05])))
    await world.reset_async()

    idx = h1.dof_names.index("left_shoulder_pitch")
    targets = h1.get_joint_positions()
    targets[idx] = np.deg2rad(-90)
    h1.set_joint_positions(targets)
    for _ in range(30):
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
    print("왼팔을 앞으로 들었어요.")

asyncio.ensure_future(main())
