# 8강 · 코드 실습하기 Q5 — 탐구 · 360°를 섹터로 나누기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 한 바퀴(360°)를 45°씩 섹터로 잘라 각 섹터의 최소 거리를 모아요. 만들어진 섹터 수는?

import numpy as np

angles_deg = np.arange(0, 360, 1)
distances = np.full(len(angles_deg), 5.0)

sector_size = 45
sector_mins = []
for start in range(0, 360, sector_size):
    mask = (angles_deg >= start) & (angles_deg < start + sector_size)
    sector_mins.append(distances[mask].min())

print(f"섹터 수 = {len(sector_mins)}")
