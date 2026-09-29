# 2강 · 코드 실습하기 Q4 — 심화 · 떨어지며 회전하는 큐브
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 큐브가 돌면서 떨어져요. Script Editor에 뜬 최종 높이 Z를 입력해보세요.

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

cube = world.scene.add(DynamicCuboid(
    prim_path="/World/Cube", name="cube",
    position=np.array([0, 0, 2.0]),
    scale=np.array([0.3, 0.3, 0.3]),
    color=np.array([0.2, 0.8, 0.2])))
world.reset()
cube.set_angular_velocity(np.array([0, 0, 5.0]))

for _ in range(120):
    world.step(render=False)
z = cube.get_world_pose()[0][2]
print(f"회전하며 떨어진 큐브 높이 Z = {z:.2f}")
