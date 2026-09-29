# 3강 · 중력 실험
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

world.scene.add(
    DynamicCuboid(
        prim_path="/World/TestBox",
        position=np.array([0, 0, 2.0]),
        scale=np.array([0.3, 0.3, 0.3]),
        color=np.array([1.0, 0.5, 0.0]),
        mass=1.0
    )
)

import asyncio
async def run():
    await world.reset_async()

asyncio.ensure_future(run())
