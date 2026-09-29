# 5강 · 코드 실습하기 Q4 — 심화 · 동작 시퀀스
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 자세 3개를 각 60프레임씩 이어 재생해요. 전체 스텝 수는?

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

    poses = [np.zeros(len(h1.dof_names)) for _ in range(3)]
    poses[1][h1.dof_names.index("left_shoulder_pitch")]  = np.deg2rad(-90)
    poses[2][h1.dof_names.index("right_shoulder_pitch")] = np.deg2rad(-90)

    steps = 0
    for q in poses:
        h1.set_joint_positions(q)
        for _ in range(60):
            world.step(render=False)
            await omni.kit.app.get_app().next_update_async()
            steps += 1
    print(f"시퀀스 전체 스텝 수 = {steps}")

asyncio.ensure_future(main())
