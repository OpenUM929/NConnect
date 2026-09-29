# 3강 · 코드 실습하기 Q2 — 보통 · 달에서 1초 뒤
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 달 중력으로 2m 상자를 1초(60스텝) 떨어뜨려요. Script Editor에 찍힌 높이 z(m)를 입력해보세요.

import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

world.get_physics_context().set_gravity(-1.62)
box = world.scene.add(DynamicCuboid(
    prim_path="/World/MoonBox",
    position=np.array([0, 0, 2.0]),
    scale=np.array([0.3, 0.3, 0.3]), mass=1.0))
import asyncio
async def run():
    await world.reset_async()
    for _ in range(60):
        world.step(render=False)
    z = box.get_world_pose()[0][2]
    print(f"1초 뒤 높이 z = {z:.2f} m")

asyncio.ensure_future(run())
