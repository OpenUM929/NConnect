# Go2 Default-vs-Pilot video observation — 260901

- status: `VIDEO_OBSERVED`
- method: 14 MP4 각각에서 3%~97% 구간 12프레임을 균등 추출해 직접 관찰
- duration: 각 영상 약 9.98초, 500 frames, 50 fps
- scope: 정책별 G1~G7 정량 worst-case 1개
- limitation: 연속 gait timing, foot contact, jerk는 판독하지 않음; 정책 간 exact case가 다를 수 있음

| policy | G | 관찰 |
|---|---|---|
| Default | G1 | 자세는 유지하지만 빠른 전진 명령 대비 위치 변화가 매우 작음 |
| Default | G2 | 대각 이동 명령 대비 이동·회전량이 작음 |
| Default | G3 | rough 지형에서 전진량이 작고 불안정한 낮은 자세가 보임 |
| Default | G4 | 경사에서 자세는 유지하나 진행량이 작음 |
| Default | G5 | 계단 부근에서 뚜렷한 통과 없이 정체 |
| Default | G6 | 밀침 뒤 일부 개체의 낮은 자세·불안정이 보임 |
| Default | G7 | rough+DR에서 진행량이 작고 불안정 |
| Pilot | G1 | 평지에서 뚜렷한 전진 이동 |
| Pilot | G2 | 이동·회전 범위가 Default보다 큼 |
| Pilot | G3 | rough에서 이동은 늘지만 낮은 자세·불안정이 보임 |
| Pilot | G4 | 경사 진행량은 늘었으나 추종 부족 |
| Pilot | G5 | 계단 접근·이동은 늘지만 정체·불안정, 깨끗한 통과 미관찰 |
| Pilot | G6 | 밀침 뒤 대체로 자세 유지·회복 |
| Pilot | G7 | rough+DR 이동 개선, 안정·추종 미달 징후 |

Contact sheets are stored in `contact_sheets/`. Telemetry remains the source for exact survival, RMSE, completion, and recovery values.
