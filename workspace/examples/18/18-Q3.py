# 18강 · 코드 실습하기 Q3 — 도전 · 잡담 속에서 JSON만 건지기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 건져낸 명령의 velocity_y 값을 입력해보세요.

import json, re

def extract_json(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m is None:
        raise ValueError("JSON 없음")
    return json.loads(m.group(0))

messy = '좋아요! {"velocity_x": 0.6, "velocity_y": -0.3, "velocity_yaw": 0.0} 이렇게 갈게요.'
cmd = extract_json(messy)
print(cmd["velocity_y"])
