# 4강 · 코드 실습하기 Q4 — 심화 · 무중력 로봇
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 중력을 0으로 끄고 휴머노이드 로봇을 2.0m에 띄워요. 150스텝 뒤 높이 Z는? (떨어질까요?)

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
        position=np.array([0, 0, 2.0])))

    await world.reset_async()
    for _ in range(150):
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
    z = h1.get_world_pose()[0][2]
    print(f"무중력 150스텝 뒤 높이 Z = {z:.1f}")

asyncio.ensure_future(main())
