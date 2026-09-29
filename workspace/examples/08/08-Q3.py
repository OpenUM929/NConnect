# 8강 · 코드 실습하기 Q3 — 도전 · 정면 빔 골라내기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 실습의 front 범위와 같은 -15° ~ 15° 마스크예요. 정면을 향하는 빔 수는?

import numpy as np

azimuth = np.arange(-180, 180, 1)

mask = (azimuth >= -15) & (azimuth < 15)

front_beams = int(mask.sum())
print(f"정면(±15°) 빔 수 = {front_beams}")
