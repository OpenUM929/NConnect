# 5강 · 코드 실습하기 Q1 — 기본 · 관절 개수 세기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# await world.reset_async() 뒤에 dof_names가 채워져요. Script Editor에 찍힌 전체 관절(DoF) 수는?

import asyncio
import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
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
        position=np.array([0, 0, 1.05])))
    await world.reset_async()

    print(f"H1의 관절 수 = {len(h1.dof_names)}")

asyncio.ensure_future(main())
