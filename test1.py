import asyncio
from datetime import datetime
from pathlib import Path

import numpy as np
import omni.kit.app
import omni.usd

from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path


async def main():
    # Isaac Sim 서버의 student_workspace에 저장될 일반 텍스트 로그입니다.
    log_path = Path("/workspace/student_workspace/h1_stand.log")
    log_file = log_path.open("w", encoding="utf-8")

    def write_log(message):
        print(message)
        log_file.write(message + "\n")
        log_file.flush()

    try:
        if World.instance() is not None:
            World.instance().clear_instance()

        omni.usd.get_context().new_stage()
        world = World(stage_units_in_meters=1.0)
        world.scene.add_default_ground_plane()
        world.get_physics_context().set_gravity(-9.81)

        assets_root = get_assets_root_path()
        add_reference_to_stage(
            usd_path=assets_root + "/Isaac/Robots/Unitree/H1/h1.usd",
            prim_path="/World/H1",
        )

        h1 = world.scene.add(
            SingleArticulation(
                prim_path="/World/H1",
                name="h1_humanoid",
                position=np.array([0.0, 0.0, 1.05]),
            )
        )

        await world.reset_async()

        write_log(f"RUN_TIME: {datetime.now().isoformat(timespec='seconds')}")
        write_log("TEST: H1 stand with gravity")
        write_log("EXPECTED: H1 remains upright for 600 frames")
        write_log(f"DOF_COUNT: {len(h1.dof_names)}")

        heights = []
        for step in range(600):
            world.step(render=False)
            await omni.kit.app.get_app().next_update_async()

            position, orientation = h1.get_world_pose()
            height = float(position[2])
            heights.append(height)

            if step % 60 == 0:
                write_log(
                    f"STEP: {step}, ROOT_Z_M: {height:.3f}, "
                    f"ORIENTATION_XYZW: {orientation.tolist()}"
                )

        min_height = min(heights)
        final_height = heights[-1]
        result = "PASS" if min_height >= 0.80 else "FAIL"

        write_log(f"RESULT: {result}")
        write_log(f"MIN_ROOT_Z_M: {min_height:.3f}")
        write_log(f"FINAL_ROOT_Z_M: {final_height:.3f}")
        write_log(f"LOG_FILE: {log_path}")

    except Exception as error:
        write_log(f"ERROR: {type(error).__name__}: {error}")
        raise
    finally:
        log_file.close()


asyncio.ensure_future(main())
