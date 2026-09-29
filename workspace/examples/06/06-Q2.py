# 6강 · 코드 실습하기 Q2 — 보통 · 자갈밭이 차지하는 길이
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# cell=0.2로 블록 하나를 작게 줄여 자갈처럼 빽빽하게 깔아요. 블록 수는 forward × sides로 450개인데, 이 자갈밭이 앞뒤로 차지하는 지형 길이는?

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
x_min = None
x_max = None
def build_terrain(start_x=1.5, forward=20, sides=10, cell=0.5, min_h=0.02, max_h=0.20):
    global count, x_min, x_max
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
            front = x - cell / 2
            back = x + cell / 2
            x_min = front if x_min is None else min(x_min, front)
            x_max = back if x_max is None else max(x_max, back)

build_terrain(forward=30, sides=15, cell=0.2, max_h=0.08)

import asyncio
async def run():
    await world.reset_async()
    print(f"자갈밭 블록 수 = {count}")
    print(f"지형 앞뒤 길이 = {x_max - x_min:.2f} m")

asyncio.ensure_future(run())
