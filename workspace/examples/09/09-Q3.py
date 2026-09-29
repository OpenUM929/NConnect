# 9강 · 코드 실습하기 Q3 — 도전 · 상한에 닿는 스텝 수
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 0.0에서 시작해 매 스텝 0.01씩 올려요. 상한 1.4에 닿기까지 걸리는 스텝 수는?

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
    targets = h1.get_joint_positions().copy()
    angle = 0.0
    steps = 0

    while angle < 1.4:
        angle = float(np.clip(angle + 0.01, -0.4, 1.4))
        steps += 1
        targets[l_sh] = angle
        h1.apply_action(ArticulationAction(joint_positions=targets))
        world.step(render=False)
        await omni.kit.app.get_app().next_update_async()

    print(f"상한 1.4 rad에 닿기까지 걸린 스텝 수 = {steps}")

asyncio.ensure_future(main())
