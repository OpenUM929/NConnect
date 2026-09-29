# 4강 · 코드 실습하기 Q1 — 기본 · 로봇 여러 대
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 같은 go2_usd를 주소와 이름만 바꿔 여러 번 등록해요. Script Editor에 찍힌 로봇 수를 입력해보세요.

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

dogs = []
for i in range(2):
    add_reference_to_stage(usd_path=go2_usd, prim_path=f"/World/Go2_{i}")
    dog = world.scene.add(SingleArticulation(
        prim_path=f"/World/Go2_{i}", name=f"go2_dog_{i}",
        position=np.array([i * 1.5, 0, 0.5])))
    dogs.append(dog)

import asyncio
async def run():
    await world.reset_async()
    print(f"스테이지에 올린 로봇 수 = {len(dogs)}")

asyncio.ensure_future(run())
