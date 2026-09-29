# 8강 · 벽 셋을 세우고 다섯 방향으로 요약
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

    world.scene.add(FixedCuboid(prim_path="/World/wall_front", name="wall_front",
        position=np.array([3.0, 0.0, 1.0]), scale=np.array([0.2, 4.0, 2.0])))
    world.scene.add(FixedCuboid(prim_path="/World/wall_left", name="wall_left",
        position=np.array([0.0, 2.0, 1.0]), scale=np.array([4.0, 0.2, 2.0])))
    world.scene.add(FixedCuboid(prim_path="/World/wall_right", name="wall_right",
        position=np.array([0.0, -1.5, 1.0]), scale=np.array([4.0, 0.2, 2.0])))

    lidar = LidarRtx(
        prim_path="/World/lidar",
        position=np.array([0.0, 0.0, 1.4]),
        config_file_name="Example_Rotary_2D",
    )
    lidar.attach_annotator("IsaacComputeRTXLidarFlatScan")

    writer = rep.writers.get("RtxLidarDebugDrawPointCloudBuffer")
    writer.attach([lidar.get_render_product_path()])

    await world.reset_async()
    set_camera_view(eye=[-4.0, -4.5, 4.0], target=[1.0, 0.0, 1.0])
    lidar.initialize()
    for _ in range(60):
        await omni.kit.app.get_app().next_update_async()

    data = lidar.get_current_frame()
    distances = np.asarray(data["linear_depth_data"])
    lo, hi = data["azimuth_range"]
    azimuth = np.linspace(lo, hi, len(distances))

    def nearest_in_range(min_deg, max_deg):
        """이 방향 부채꼴에서 가장 가까운 거리."""
        mask = (azimuth >= min_deg) & (azimuth < max_deg) & (distances > 0)
        if not mask.any():
            return float("inf")
        return float(distances[mask].min())

    summary = {
        "front":       nearest_in_range(-15, 15),
        "front_left":  nearest_in_range(15, 60),
        "front_right": nearest_in_range(-60, -15),
        "left":        nearest_in_range(60, 120),
        "right":       nearest_in_range(-120, -60),
    }
    for direction, dist in summary.items():
        print(f"  {direction}: {dist:.2f}m")

asyncio.ensure_future(main())
