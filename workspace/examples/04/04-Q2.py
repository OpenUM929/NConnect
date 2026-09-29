# 4강 · 코드 실습하기 Q2 — 보통 · 삼각형 대형
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 120° 간격으로 반경 1m 원 위에 세 대를 세웠어요. 이웃한 두 로봇 사이 거리는 몇 m일까요?

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
for i in range(3):
    theta = np.deg2rad(90 + i * 120)
    x, y = np.cos(theta), np.sin(theta)
    add_reference_to_stage(usd_path=go2_usd, prim_path=f"/World/Go2_{i}")
    dogs.append(world.scene.add(SingleArticulation(
        prim_path=f"/World/Go2_{i}", name=f"go2_dog_{i}",
        position=np.array([x, y, 0.5]))))

import asyncio
async def run():
    await world.reset_async()
    p0 = dogs[0].get_world_pose()[0]
    p1 = dogs[1].get_world_pose()[0]
    side = float(np.linalg.norm(p0[:2] - p1[:2]))
    print(f"이웃한 두 로봇 사이 거리 = {side:.2f} m")

asyncio.ensure_future(run())
