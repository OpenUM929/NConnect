# 8강 · 코드 실습하기 Q4 — 심화 · 방향별 가장 가까운 거리
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 왼쪽 앞 20°~50°에만 물체를 뒀어요. summarize_lidar를 돌리면 front_left에 담기는 거리는 몇 m일까요?

import numpy as np

azimuth = np.arange(-180, 180, 1)
distances = np.full(len(azimuth), 5.0)
distances[(azimuth >= 20) & (azimuth <= 50)] = 2.5

def summarize_lidar(distances, azimuth):
    def nearest_in_range(min_deg, max_deg):
        mask = (azimuth >= min_deg) & (azimuth < max_deg) & (distances > 0)
        if not mask.any():
            return float('inf')
        return float(distances[mask].min())
    return {
        "front":       nearest_in_range(-15, 15),
        "front_left":  nearest_in_range(15, 60),
        "front_right": nearest_in_range(-60, -15),
        "left":        nearest_in_range(60, 120),
        "right":       nearest_in_range(-120, -60),
    }

summary = summarize_lidar(distances, azimuth)
for k, v in summary.items():
    print(f"{k} = {v:.1f} m")
