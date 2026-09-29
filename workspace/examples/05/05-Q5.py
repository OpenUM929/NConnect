# 5강 · 코드 실습하기 Q5 — 탐구 · 라디안과 도 왕복
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 90°를 라디안으로 바꿨다가 다시 도로 되돌리면? np.rad2deg(np.deg2rad(90))의 결과는?

import numpy as np

deg = 90
rad = np.deg2rad(deg)
back = np.rad2deg(rad)
print(f"{deg}도 -> {rad:.2f}rad -> 다시 {back:.0f}도")
