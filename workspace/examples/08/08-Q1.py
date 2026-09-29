# 8강 · 코드 실습하기 Q1 — 기본 · 한 바퀴 빔 수 세기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# -180°부터 1° 간격으로 한 바퀴를 도는 라이다예요. Script Editor에 찍힌 빔 수는?

import numpy as np

azimuth = np.arange(-180, 180, 1)

beam_count = len(azimuth)
print(f"한 바퀴 빔 수 = {beam_count}")
