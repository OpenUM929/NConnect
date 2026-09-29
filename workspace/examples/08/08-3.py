# 8강 · 코앞 벽 앞에서 갈지 멈출지 정하기
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

    # 이번엔 앞벽이 코앞이에요 (앞면 1.2m)
    world.scene.add(FixedCuboid(prim_path="/World/wall_front", name="wall_front",
        position=np.array([1.3, 0.0, 1.0]), scale=np.array([0.2, 4.0, 2.0])))
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

    def is_safe_to_move_forward(summary, min_safe_distance=1.5):
        """앞으로 가도 안전한가?"""
        return summary["front"] > min_safe_distance

    def closest_direction(summary):
        """가장 막힌 방향 찾기."""
        return min(summary.items(), key=lambda x: x[1])

    if not is_safe_to_move_forward(summary):
        blocker = closest_direction(summary)
        print(f"전방 장애물! 가장 가까운 방향: {blocker[0]} ({blocker[1]:.2f}m)")
    else:
        print("전방 이동 안전")

asyncio.ensure_future(main())
