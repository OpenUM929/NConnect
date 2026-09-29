# 6강 · 코드 실습하기 Q5 — 탐구 · 구간마다 달라지는 블록 밀도
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력에 네 구간이 한 줄씩 찍혀요. 자갈밭 구간의 블록 수는 평지 구간의 몇 배인가요?

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

sections = []
def build_terrain(label, start_x=1.5, forward=20, sides=10, cell=0.5, min_h=0.02, max_h=0.20):
    n = 0
    for i in range(forward):
        for j in range(sides):
            h = random.uniform(min_h, max_h)
            x = start_x + i * cell
            y = (j - (sides - 1) / 2) * cell
            world.scene.add(FixedCuboid(
                prim_path=f"/World/Terrain_{int(start_x)}/block_{i}_{j}",
                name=f"block_{int(start_x)}_{i}_{j}",
                position=np.array([x, y, h / 2]),
                scale=np.array([cell, cell, h])))
            n += 1
    sections.append((label, forward * cell, n))

build_terrain("평지", start_x=1.5, forward=10, min_h=0.02, max_h=0.02)
build_terrain("자갈밭", start_x=7.5, forward=20, cell=0.2, max_h=0.08)
build_terrain("높은 지형", start_x=12.5, forward=10, min_h=0.05, max_h=0.32)
build_terrain("험한 구간", start_x=17.5, forward=10, min_h=0.02, max_h=0.5)
import asyncio
async def run():
    await world.reset_async()
    for label, length, n in sections:
        print(f"{label}: 길이 {length:.1f} m, 블록 {n}개")

asyncio.ensure_future(run())
