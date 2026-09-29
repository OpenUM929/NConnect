# 7강 · 코드 실습하기 Q5 — 탐구 · Depth 컬러맵 채널
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# cm.jet은 RGBA (H, W, 4)를 돌려줘요. 알파를 뺀 [:, :, :3]의 채널 수는?

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
import matplotlib.cm as cm

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
                    frequency=20, resolution=(640, 480),
                    orientation=np.array([1, 0, 0, 0]))
    await world.reset_async()
    camera.initialize()
    camera.add_distance_to_image_plane_to_frame()
    for _ in range(30):
        await omni.kit.app.get_app().next_update_async()

    depth = camera.get_depth()
    d = np.clip(depth, 0, 10) / 10.0
    colored = cm.jet(d)
    rgb_out = colored[:, :, :3]
    print(f"jet 컬러맵 출력 shape = {colored.shape}")
    print(f"저장용 RGB 채널 수 = {rgb_out.shape[2]}")

asyncio.ensure_future(main())
