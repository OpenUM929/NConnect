# 7강 · 코드 실습하기 Q2 — 보통 · 카메라를 기울여 찍은 장수
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 카메라를 0°에서 30°까지 10°씩 아래로 기울여가며 각 각도에서 한 장씩 받아요. Script Editor에 찍힌 장수는?

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
from isaacsim.core.utils.rotations import euler_angles_to_quat

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

    shots = 0
    for pitch_deg in [0, 10, 20, 30]:
        pitch = np.deg2rad(pitch_deg)
        camera.set_local_pose(orientation=euler_angles_to_quat([0, pitch, 0]))
        for _ in range(30):
            await omni.kit.app.get_app().next_update_async()
        rgb = camera.get_rgb()
        shots += 1
    print(f"받은 장수 = {shots}")

asyncio.ensure_future(main())
