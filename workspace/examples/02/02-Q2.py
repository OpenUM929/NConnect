# 2강 · 코드 실습하기 Q2 — 보통 · color 값으로 색 바꾸기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 이 코드는 빨간 공(color=[1.0, 0.0, 0.0])을 만들어요. 가운데 초록 값을 얼마로 올리면 노란 공이 될까요? (0~1 사이 값)

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicSphere

if World.instance() is not None:
    World.instance().clear_instance()
omni.usd.get_context().new_stage()
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

world.scene.add(DynamicSphere(
    prim_path="/World/Ball", name="my_sphere",
    position=np.array([0, 0, 1.5]),
    radius=0.2, color=np.array([1.0, 0.0, 0.0])))
world.reset()
