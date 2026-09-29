# 6강 · 블록 200개로 지형 깔기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import omni.usd
import numpy as np
import random
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid
from pxr import UsdLux

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

stage = omni.usd.get_context().get_stage()
sun = UsdLux.DistantLight.Define(stage, "/World/Sun")
sun.CreateIntensityAttr(3000.0)

def build_terrain(start_x=1.5, forward=20, sides=10,
                  cell=0.5, min_h=0.02, max_h=0.20):
    for i in range(forward):
        for j in range(sides):
            h = random.uniform(min_h, max_h)
            x = start_x + (i * cell)
            y = (j - (sides - 1) / 2) * cell
            world.scene.add(
                FixedCuboid(
                    prim_path=f"/World/Terrain/block_{i}_{j}",
                    name=f"block_{i}_{j}",
                    position=np.array([x, y, h/2]),
                    scale=np.array([cell, cell, h])
                )
            )

build_terrain(start_x=1.5, forward=20, sides=10)

import asyncio
async def run():
    await world.reset_async()

asyncio.ensure_future(run())
