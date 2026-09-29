# 9강 · 코드 실습하기 Q4 — 심화 · 상태 출력 횟수
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# range(3600)을 돌며 step % 120 == 0일 때만 한 줄씩 찍어요. 실습 본문과 같은 구조예요. 맨 아래 센 줄 수는?

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0.0, 0.0, 1.05])))

    await world.reset_async()

    targets = h1.get_joint_positions().copy()
    lines = 0

    for step in range(3600):
        h1.apply_action(ArticulationAction(joint_positions=targets))
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
        if step % 120 == 0:
            print(f"step {step} 진행 중")
            lines += 1

    print(f"센 줄 수 = {lines}")

asyncio.ensure_future(main())
