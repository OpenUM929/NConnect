# 9강 · 코드 실습하기 Q5 — 탐구 · 조종이 닿는 관절 수
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 목표 배열을 복사해두고, 어깨 관절에만 새 값을 넣었어요. targets != before로 센 바뀐 칸 수는?

import asyncio
import omni.usd
import omni.kit.app
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.storage.native import get_assets_root_path

async def main():
    if World.instance() is not None:
        World.instance().clear_instance()
    omni.usd.get_context().new_stage()
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    assets_root = get_assets_root_path()
    h1_usd = assets_root + "/Isaac/Robots/Unitree/H1/h1.usd"
    add_reference_to_stage(usd_path=h1_usd, prim_path="/World/H1")
    h1 = world.scene.add(SingleArticulation(
        prim_path="/World/H1", name="h1_humanoid",
        position=np.array([0.0, 0.0, 1.05])))

    await world.reset_async()

    l_sh = h1.dof_names.index("left_shoulder_pitch")
    r_sh = h1.dof_names.index("right_shoulder_pitch")
    before = h1.get_joint_positions().copy()
    targets = before.copy()

    targets[l_sh] = 0.9
    targets[r_sh] = 0.9
    h1.apply_action(ArticulationAction(joint_positions=targets))
    world.step(render=False)
    await omni.kit.app.get_app().next_update_async()

    changed = int(np.sum(targets != before))
    print(f"전체 관절 수 = {len(targets)}")
    print(f"키로 값을 바꾼 관절 수 = {changed}")

asyncio.ensure_future(main())
