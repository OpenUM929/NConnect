# 8강 · 코드 실습하기 Q2 — 보통 · 가장 가까운 물체의 방향
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 왼쪽 앞으로 벽이 있고, 그중 튀어나온 한 곳이 가장 가까워요. argmin으로 찾은 그 빔은 몇 도 방향일까요? (양수가 왼쪽)

import numpy as np

azimuth = np.arange(-180, 180, 1)

linear_depth_data = np.full(len(azimuth), 5.0)
linear_depth_data[(azimuth >= 15) & (azimuth <= 35)] = 2.0
linear_depth_data[azimuth == 25] = 1.2

i = int(np.argmin(linear_depth_data))
print(f"가장 가까운 거리(m) = {linear_depth_data[i]:.1f}")
print(f"그 빔의 방향(도) = {azimuth[i]}")
