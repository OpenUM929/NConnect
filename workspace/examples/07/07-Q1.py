# 7강 · 코드 실습하기 Q1 — 기본 · 첫 프레임 픽셀 수
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# resolution=(640, 480)이면 RGB 배열은 (480, 640, 3)이에요. 한 프레임의 픽셀 수(H×W)는?

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from pxr import UsdLux
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.storage.native import get_assets_root_path
from isaacsim.sensors.camera import Camera

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    stage = omni.usd.get_context().get_stage()
    UsdLux.DistantLight.Define(stage, "/World/Sun").CreateIntensityAttr(3000.0)

    assets_root = get_assets_root_path()
    add_reference_to_stage(usd_path=assets_root + "/Isaac/Robots/Unitree/H1/h1.usd", prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(prim_path="/World/H1", name="h1", position=np.array([0, 0, 1.05])))

    camera = Camera(prim_path="/World/H1/head_camera",
                    position=np.array([0.15, 0.0, 1.75]),
                    frequency=20,
                    resolution=(640, 480),
                    orientation=np.array([1, 0, 0, 0]))

    await world.reset_async()
    camera.initialize()
    for _ in range(30):
        await omni.kit.app.get_app().next_update_async()

    rgb = camera.get_rgb()
    h, w = rgb.shape[0], rgb.shape[1]
    print(f"RGB shape = {rgb.shape}")
    print(f"한 프레임의 픽셀 수 H*W = {h * w}")

asyncio.ensure_future(main())
