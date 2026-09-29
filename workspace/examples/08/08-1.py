# 8강 · Script Editor에서 라이다 설치
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
import omni.replicator.core as rep
from isaacsim.core.api import World
from isaacsim.core.api.objects import FixedCuboid
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.sensors.rtx import LidarRtx

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    world.scene.add(FixedCuboid(
        prim_path="/World/wall", name="wall",
        position=np.array([3.0, 0.0, 1.0]),
        scale=np.array([0.2, 4.0, 2.0])))

    lidar = LidarRtx(
        prim_path="/World/lidar",
        position=np.array([0.0, 0.0, 1.4]),
        config_file_name="Example_Rotary_2D",
    )
    lidar.attach_annotator("IsaacComputeRTXLidarFlatScan")

    writer = rep.writers.get("RtxLidarDebugDrawPointCloudBuffer")
    writer.attach([lidar.get_render_product_path()])

    await world.reset_async()
    set_camera_view(eye=[-3.0, -3.0, 3.0], target=[2.0, 0.0, 1.2])
    lidar.initialize()
    for _ in range(60):
        await omni.kit.app.get_app().next_update_async()

    data = lidar.get_current_frame()
    distances = np.asarray(data["linear_depth_data"])
    lo, hi = data["azimuth_range"]
    azimuth = np.linspace(lo, hi, len(distances))

    hit = distances > 0
    print("빔 개수 =", len(distances), "| 무언가에 맞은 빔 =", int(hit.sum()))
    print("가장 가까운 거리 =", round(float(distances[hit].min()), 2), "m")

asyncio.ensure_future(main())
