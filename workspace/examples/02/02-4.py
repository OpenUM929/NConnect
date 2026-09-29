# 2강 · 변형 3 : 빨강, 초록, 파랑 동시 소환하기
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

balls = [
    ("/World/RedBall",   "red_sphere",   [-1, 0, 1.0], [1, 0, 0]),
    ("/World/GreenBall", "green_sphere", [ 0, 0, 1.0], [0, 1, 0]),
    ("/World/BlueBall",  "blue_sphere",  [ 1, 0, 1.0], [0, 0, 1]),
]
for prim, name, pos, col in balls:
    world.scene.add(
        DynamicSphere(
            prim_path=prim,
            name=name,
            position=np.array(pos),
            radius=0.3,
            color=np.array(col),
        )
    )
world.reset()
