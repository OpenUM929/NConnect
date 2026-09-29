# 2강 · 코드 실습하기 Q5 — 탐구 · 여러 공을 리스트로 관리
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 공을 리스트에 모아 한꺼번에 위치를 출력해요. Script Editor에 뜬 리스트 공 개수를 입력해보세요.

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicSphere

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

balls = []
for i in range(3):
    b = world.scene.add(DynamicSphere(
        prim_path=f"/World/Ball_{i}", name=f"ball_{i}",
        position=np.array([i * 0.5 - 0.5, 0, 1.5]), radius=0.15))
    balls.append(b)
world.reset()

for b in balls:
    z = b.get_world_pose()[0][2]
    print(f"{b.name}: z = {z:.2f}")
print(f"리스트에 담긴 공 개수 = {len(balls)}")
