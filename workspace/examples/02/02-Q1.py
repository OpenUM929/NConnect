# 2강 · 코드 실습하기 Q1 — 기본 · Visual 상자 띄우기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# Script Editor에 뜬 상자 높이 Z를 입력해보세요. 떨어졌을까요?

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import VisualCuboid

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

box = world.scene.add(VisualCuboid(
    prim_path="/World/Box", name="floating_box",
    position=np.array([0, 0, 1.0]),
    scale=np.array([0.3, 0.3, 0.3]),
    color=np.array([0.2, 0.6, 1.0])))
world.reset()

for _ in range(120):
    world.step(render=False)
z = box.get_world_pose()[0][2]
print(f"120스텝 뒤 상자 높이 Z = {z:.1f}")
