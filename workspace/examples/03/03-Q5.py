# 3강 · 코드 실습하기 Q5 — 탐구 · 중력을 서서히 0으로
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 중력을 -9.81에서 0까지 서서히 줄이며 1.5초(90스텝) 떨어뜨려요. 최종 높이 z(m)를 입력해보세요.

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

box = world.scene.add(DynamicCuboid(
    prim_path="/World/FadeBox",
    position=np.array([0, 0, 30.0]),
    scale=np.array([0.3, 0.3, 0.3]), mass=1.0))
import asyncio
async def run():
    await world.reset_async()
    for i in range(90):
        g = -9.81 * (1.0 - i / 90)
        world.get_physics_context().set_gravity(g)
        world.step(render=False)
    z = box.get_world_pose()[0][2]
    print(f"중력을 0으로 줄이며 1.5초 뒤 높이 z = {z:.1f} m")

asyncio.ensure_future(run())
