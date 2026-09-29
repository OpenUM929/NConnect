# 18강 · 맛보기, JSON에서 값 꺼내기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import json

text = '{"vx": 0.4, "vy": 0.0, "yaw": 0.3}'
cmd  = json.loads(text)

print(cmd["vx"])
