# 2강 · 변형 1 : Z=5.0으로 더 높이 띄우기
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
        prim_path="/World/HighBall",
        name="high_sphere",
        position=np.array([0, 0, 5.0]),
        radius=0.3,
        color=np.array([1.0, 0.5, 0.0])
    )
)
world.reset()
