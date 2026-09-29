# 7강 · 코드 실습하기 Q3 — 도전 · 1초에 흐르는 숫자
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# resolution=(1280, 720)이라 배열은 (720, 1280, 3)이고, frequency=20이라 1초에 20장이 와요. 1초에 흐르는 숫자 개수는?

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
                    resolution=(1280, 720),
                    orientation=np.array([1, 0, 0, 0]))
    await world.reset_async()
    camera.initialize()
    for _ in range(30):
        await omni.kit.app.get_app().next_update_async()

    rgb = camera.get_rgb()
    frames_per_sec = 20
    per_frame = rgb.shape[0] * rgb.shape[1] * rgb.shape[2]
    print(f"RGB shape = {rgb.shape}")
    print(f"한 장에 담긴 숫자 = {per_frame}")
    print(f"1초에 흐르는 숫자 = {per_frame * frames_per_sec}")

asyncio.ensure_future(main())
