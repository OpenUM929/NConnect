# 3강 · 코드 실습하기 Q1 — 기본 · 1초 뒤 떨어지는 속도
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 먼저 예측해봐요. 중력은 높이가 아니라 속도를 바꿔요. 10m에서 떨어지는 상자의 속도는 1초(60스텝) 동안 몇 m/s 늘어날까요?

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

box = world.scene.add(DynamicCuboid(
    prim_path="/World/FallBox",
    position=np.array([0, 0, 10.0]),
    scale=np.array([0.3, 0.3, 0.3]), mass=1.0))
import asyncio
async def run():
    await world.reset_async()
    v_before = box.get_linear_velocity()[2]
    for _ in range(60):
        world.step(render=False)
    v_after = box.get_linear_velocity()[2]
    print(f"1초 동안 늘어난 속도 = {abs(v_after - v_before):.1f} m/s")

asyncio.ensure_future(run())
