# 4강 · 두 로봇 소환
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

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
h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
go2_usd = assets_root + "/Isaac/Robots/Unitree/Go2/go2.usd"

add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
add_reference_to_stage(usd_path=go2_usd, prim_path="/World/Go2")

h1 = world.scene.add(
    SingleArticulation(
        prim_path="/World/H1",
        name="h1_humanoid",
        position=np.array([0.0, 0.0, 1.05])
    )
)
go2 = world.scene.add(
    SingleArticulation(
        prim_path="/World/Go2",
        name="go2_dog",
        position=np.array([1.5, 0.0, 0.5])
    )
)

import asyncio
async def run():
    await world.reset_async()

asyncio.ensure_future(run())
