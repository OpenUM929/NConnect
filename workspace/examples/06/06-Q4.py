# 6강 · 코드 실습하기 Q4 — 심화 · 10단 계단
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# random.uniform을 h = 0.05 + i*0.03으로 바꾸면 같은 줄은 높이가 같아 계단이 돼요. range(10)으로 열 줄을 깔았을 때 맨 윗단(i=9)의 높이 h는?

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

top_h = 0.0
for i in range(10):
    h = 0.05 + i * 0.03
    for j in range(10):
        x = 1.5 + i * 0.5
        y = (j - 4.5) * 0.5
        world.scene.add(FixedCuboid(
            prim_path=f"/World/Stairs/block_{i}_{j}",
            name=f"block_{i}_{j}",
            position=np.array([x, y, h / 2]),
            scale=np.array([0.5, 0.5, h])))
    top_h = h
import asyncio
async def run():
    await world.reset_async()
    print(f"맨 윗단(i=9) 계단 높이 = {top_h:.2f}")

asyncio.ensure_future(run())
