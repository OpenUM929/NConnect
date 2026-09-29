# 3강 · 질량 다른 세 상자, 같은 높이 (전체 코드)
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

world.get_physics_context().set_gravity(-9.81)

for i, m in enumerate([1.0, 10.0, 100.0]):
    world.scene.add(
        DynamicCuboid(
            prim_path=f"/World/Cube_{i}",
            name=f"cube_{i}",
            position=np.array([i * 0.5, 0, 2.0]),
            scale=np.array([0.2, 0.2, 0.2]),
            mass=m,
        )
    )

import asyncio
async def run():
    await world.reset_async()

asyncio.ensure_future(run())
