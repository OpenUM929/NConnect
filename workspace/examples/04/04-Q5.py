# 4강 · 코드 실습하기 Q5 — 탐구 · 이름으로 다시 찾기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 세 대를 1.5m 간격으로 세우고, get_object("go2_dog_2")로 그중 한 대만 다시 찾아요. 그 로봇의 x 좌표는?

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.storage.native import get_assets_root_path

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

assets_root = get_assets_root_path()
go2_usd = assets_root + "/Isaac/Robots/Unitree/Go2/go2.usd"

for i in range(3):
    add_reference_to_stage(usd_path=go2_usd, prim_path=f"/World/Go2_{i}")
    world.scene.add(SingleArticulation(
        prim_path=f"/World/Go2_{i}", name=f"go2_dog_{i}",
        position=np.array([i * 1.5, 0, 0.5])))

import asyncio
async def run():
    await world.reset_async()
    third = world.scene.get_object("go2_dog_2")
    x = third.get_world_pose()[0][0]
    print(f"이름으로 찾은 로봇의 x = {x:.1f}")

asyncio.ensure_future(run())
