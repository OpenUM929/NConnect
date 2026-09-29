# 17강 · 코드 실습하기 Q3 — 도전 · JSON 답에서 값 꺼내기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력된 vy(velocity_y) 값을 입력해보세요.

import json

reply = '{"velocity_x": 0.5, "velocity_y": -0.2, "velocity_yaw": 0.8, "reason": "왼쪽 벽을 피해서"}'

cmd = json.loads(reply)
print(f"vx={cmd['velocity_x']}  vy={cmd['velocity_y']}  yaw={cmd['velocity_yaw']}")
