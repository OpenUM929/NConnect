# 3강 · 코드 실습하기 Q4 — 심화 · 가벼운 상자와 무거운 상자
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 0.1kg과 100kg 상자가 반중력으로 솟아요. 3초 뒤 두 상자 높이의 차이를 예측해 입력해보세요.

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

world.get_physics_context().set_gravity(9.81)
light = world.scene.add(DynamicCuboid(
    prim_path="/World/LightBox", name="light",
    position=np.array([-1, 0, 0.5]), scale=np.array([0.3, 0.3, 0.3]), mass=0.1))
heavy = world.scene.add(DynamicCuboid(
    prim_path="/World/HeavyBox", name="heavy",
    position=np.array([1, 0, 0.5]), scale=np.array([0.3, 0.3, 0.3]), mass=100.0))
import asyncio
async def run():
    await world.reset_async()
    for _ in range(180):
        world.step(render=False)
    zl = light.get_world_pose()[0][2]
    zh = heavy.get_world_pose()[0][2]
    print(f"가벼운 z={zl:.2f}, 무거운 z={zh:.2f}, 차이={abs(zl - zh):.2f}")

asyncio.ensure_future(run())
