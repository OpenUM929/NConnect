# 3강 · 코드 실습하기 Q3 — 도전 · 5단 폭포, 맨 위 상자
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 5개 상자가 같이 떨어져요. 가장 높은 5m 상자의 0.5초(30스텝) 뒤 높이 z(m)를 입력해보세요.

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
world.get_physics_context().set_gravity(-9.81)

boxes = []
for i, h in enumerate([1, 2, 3, 4, 5]):
    b = world.scene.add(DynamicCuboid(
        prim_path=f"/World/Box_{i}", name=f"box_{i}",
        position=np.array([i*0.3, 0, h]),
        scale=np.array([0.2, 0.2, 0.2]), mass=1.0))
    boxes.append(b)
import asyncio
async def run():
    await world.reset_async()
    top = boxes[-1]
    for _ in range(30):
        world.step(render=False)
    z = top.get_world_pose()[0][2]
    print(f"0.5초 뒤 맨 위 상자 높이 z = {z:.2f} m")

asyncio.ensure_future(run())
