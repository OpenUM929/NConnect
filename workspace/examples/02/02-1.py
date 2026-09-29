# 2강 · 전체 코드와 실행 결과
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import omni.usd
import numpy as np
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicSphere

if World.instance() is not None:
    World.instance().clear_instance()

omni.usd.get_context().new_stage()

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

world.scene.add(
    DynamicSphere(
        prim_path="/World/MyBall",
        name="first_sphere",
        position=np.array([0, 0, 1.0]),
        radius=0.3,
        color=np.array([1.0, 0.5, 0.0])
    )
)

world.reset()
print("공 생성 완료: /World/MyBall")
