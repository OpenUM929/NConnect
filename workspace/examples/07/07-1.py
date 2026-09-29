# 7강 · 머리에 붙인 카메라로 첫 프레임 받기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.storage.native import get_assets_root_path
from isaacsim.sensors.camera import Camera
from pxr import UsdLux

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    stage = omni.usd.get_context().get_stage()
    UsdLux.DistantLight.Define(stage, "/World/Sun").CreateIntensityAttr(3000.0)

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0.0, 0.0, 1.05])))

    camera = Camera(
        prim_path="/World/H1/head_camera",
        position=np.array([0.15, 0.0, 1.75]),
        frequency=20,
        resolution=(640, 480),
        orientation=np.array([1, 0, 0, 0])
    )

    await world.reset_async()
    camera.initialize()
    camera.add_distance_to_image_plane_to_frame()

    for _ in range(30):
        await omni.kit.app.get_app().next_update_async()

    rgb = camera.get_rgb()
    depth = camera.get_depth()

    print("RGB shape:", rgb.shape)
    print("Depth shape:", depth.shape)

asyncio.ensure_future(main())
