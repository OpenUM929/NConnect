# 2강 · 코드 실습하기 Q3 — 도전 · 바둑판 격자 채우기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 이중 for 루프가 격자를 채워요. Script Editor에 뜬 총 공 개수를 입력해보세요.

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicSphere

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

count = 0
for ix in range(3):
    for iy in range(3):
        world.scene.add(DynamicSphere(
            prim_path=f"/World/Ball_{ix}_{iy}", name=f"ball_{ix}_{iy}",
            position=np.array([ix * 0.5, iy * 0.5, 2.0]), radius=0.15))
        count += 1
world.reset()
print(f"격자에 만든 공 개수 = {count}")
