# 6강 · 코드 실습하기 Q1 — 기본 · 두 배로 길게
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# forward를 20에서 40으로 늘려요. Script Editor에 찍힌 지형 블록 수는?

import omni.usd
import numpy as np
import random
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

count = 0
def build_terrain(start_x=1.5, forward=20, sides=10, cell=0.5, min_h=0.02, max_h=0.20):
    global count
    for i in range(forward):
        for j in range(sides):
            h = random.uniform(min_h, max_h)
            x = start_x + i * cell
            y = (j - (sides - 1) / 2) * cell
            world.scene.add(FixedCuboid(
                prim_path=f"/World/Terrain/block_{i}_{j}",
                name=f"block_{i}_{j}",
                position=np.array([x, y, h / 2]),
                scale=np.array([cell, cell, h])))
            count += 1

build_terrain(start_x=1.5, forward=40, sides=10)

import asyncio
async def run():
    await world.reset_async()
    print(f"깔린 지형 블록 수 = {count}")

asyncio.ensure_future(run())
