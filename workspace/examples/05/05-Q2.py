# 5강 · 코드 실습하기 Q2 — 보통 · 오른팔 들기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 오른쪽 어깨를 -90°로 들도록 명령해요. np.deg2rad(-90)으로 바꾼 라디안 값은?

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.storage.native import get_assets_root_path

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()
    world.get_physics_context().set_gravity(0.0)

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0, 0, 1.05])))
    await world.reset_async()

    q = np.zeros(len(h1.dof_names))
    target = np.deg2rad(-90)
    q[h1.dof_names.index("right_shoulder_pitch")] = target
    h1.set_joint_positions(q)
    for _ in range(30):
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
    print(f"오른팔에 명령한 각도 = {target:.2f} rad")

asyncio.ensure_future(main())
