# 4강 · 코드 실습하기 Q3 — 도전 · 5층 탑 쌓기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 로봇 다섯 대를 0.5m부터 0.5m씩 높여 쌓아요. ■ Stop 상태로 실행하면 5대가 높이대로 떠 있고, ▶ Play를 켜면 제어기가 없어 곧 무너져요. 맨 위(다섯째) 로봇의 높이 Z는?

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

tower = []
for i in range(5):
    z = 0.5 + i * 0.5
    add_reference_to_stage(usd_path=go2_usd, prim_path=f"/World/Go2_{i}")
    dog = world.scene.add(SingleArticulation(
        prim_path=f"/World/Go2_{i}", name=f"go2_dog_{i}",
        position=np.array([0, 0, z])))
    tower.append(dog)

import asyncio
async def run():
    await world.reset_async()
    top_z = tower[-1].get_world_pose()[0][2]
    print(f"맨 위 로봇의 높이 Z = {top_z:.1f}")

asyncio.ensure_future(run())
