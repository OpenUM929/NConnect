# 19강 · 코드 실습하기 Q1 — 기본 · 도착했는지 거리로 판정
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력된 거리 값을 입력해보세요.

import math

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

robot = (3.0, 1.0)
cube  = (3.2, 1.4)
d = distance(robot, cube)
print(round(d, 2), "→ 도착" if d < 0.6 else "→ 아직 멀어요")
