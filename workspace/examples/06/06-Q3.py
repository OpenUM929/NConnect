# 6강 · 코드 실습하기 Q3 — 도전 · 지형에 입힌 마찰 확인하기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 블록마다 까끌한 재질을 입히고, 그 재질이 가진 마찰 값을 출력해요. 마찰이 두 줄로 찍히는데 운동 마찰 값은 얼마인가요?

import omni.usd
import numpy as np
import random
from pxr import UsdLux
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid
from isaacsim.core.api.materials import PhysicsMaterial

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

stage = omni.usd.get_context().get_stage()
sun = UsdLux.DistantLight.Define(stage, "/World/Sun")
sun.CreateIntensityAttr(3000.0)

rough = PhysicsMaterial(prim_path="/World/rough_material",
                        static_friction=1.10, dynamic_friction=0.80, restitution=0.0)

count = 0
for i in range(18):
    for j in range(10):
        h = random.uniform(0.05, 0.25)
        x = 1.5 + i * 0.5
        y = (j - 4.5) * 0.5
        world.scene.add(FixedCuboid(
            prim_path=f"/World/Terrain/block_{i}_{j}",
            name=f"block_{i}_{j}",
            position=np.array([x, y, h / 2]),
            scale=np.array([0.5, 0.5, h]),
            physics_material=rough))
        count += 1
import asyncio
async def run():
    await world.reset_async()
    print(f"마찰을 입힌 지형 블록 수 = {count}")
    print(f"정지 마찰 = {rough.get_static_friction():.2f}")
    print(f"운동 마찰 = {rough.get_dynamic_friction():.2f}")

asyncio.ensure_future(run())
