# 5강 · 코드 실습하기 Q3 — 도전 · T-포즈
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 양 어깨를 각 90°씩 옆으로 들어 올려요(왼팔 +, 오른팔 -). 두 각도 크기의 합은 몇 rad일까요?

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
    left = np.deg2rad(90)
    right = np.deg2rad(90)
    q[h1.dof_names.index("left_shoulder_roll")]  = +left
    q[h1.dof_names.index("right_shoulder_roll")] = -right
    h1.set_joint_positions(q)
    for _ in range(30):
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()
    print(f"두 팔을 옆으로 들어 올린 각도 크기의 합 = {left + right:.2f} rad")

asyncio.ensure_future(main())
