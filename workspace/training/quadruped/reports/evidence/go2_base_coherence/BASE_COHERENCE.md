# 기준점 일관성 — 서버 A048 대 이 PC A048 (자동, 사전등록 규칙은 도구 머리말)

판정: **INSUFFICIENT** (이 PC 기준점 우세 0 / 서버 기준점 우세 0, 결정 0건, 최소 12)

| 변수 | 지표 | 상태 | 이웃 아래 | 이웃 위 | 직선 | 서버 A048 | 이 PC A048 | 잔차 서버 | 잔차 이 PC | 우세 | 같은 PC seed 흔들림 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| track_lin_vel_xy_exp | total_70 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | G3_score | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | rough_lateral_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | rough_forward_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | combined_yaw_right_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | push_falls_sum | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | stairs_10_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | stairs_15_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| track_lin_vel_xy_exp | rough_lateral_height_rel | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | total_70 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | G3_score | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | rough_lateral_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | rough_forward_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | combined_yaw_right_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | push_falls_sum | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | stairs_10_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | stairs_15_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| ang_vel_xy_l2 | rough_lateral_height_rel | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | total_70 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | G3_score | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | rough_lateral_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | rough_forward_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | combined_yaw_right_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | push_falls_sum | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | stairs_10_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | stairs_15_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| feet_air_time | rough_lateral_height_rel | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | total_70 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | G3_score | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | rough_lateral_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | rough_forward_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | combined_yaw_right_falls | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | push_falls_sum | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | stairs_10_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | stairs_15_down_ge2 | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |
| action_rate_l2 | rough_lateral_height_rel | NOT_YET |  |  |  |  |  |  |  |  | 미측정 |

- 이웃 점은 이 PC 학습이라 이 PC 기준점에 구조적 이점이 있다. 이 판정은 서버 A048 이 이 PC 자료와 한 줄에 놓이는지만 답한다.
- 미회수 이웃이 있는 변수는 비교하지 않는다. 정지 정책도 추세 점으로 쓴다(채택 후보 제외 표지일 뿐이다).

## 누적 추세표 (모든 값, 정지 결과 포함)

| 변수 | 값 | 출처 | PC | 정지 | total_70 | G3_score | rough_lateral_falls | rough_forward_falls | combined_yaw_right_falls | push_falls_sum | stairs_10_down_ge2 | stairs_15_down_ge2 | rough_lateral_height_rel |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| track_lin_vel_xy_exp | 1.2 | 재사용 | 이 PC | 정지 | 0.761 | 0.167 | 69 | 92 | 96 | 284 | 0 | 0 | 0.2484 |
| track_lin_vel_xy_exp | 1.4 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| track_lin_vel_xy_exp | 1.5 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| track_lin_vel_xy_exp | 1.5 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| track_lin_vel_xy_exp | 1.6 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| lin_vel_z_l2 | -2.0 | 재사용 | 서버 |  | 42.529 | 4.227 | 59 | 4 | 0 | 22 | 43 | 0 | 0.3661 |
| lin_vel_z_l2 | -1.75 | 재사용 | 서버 |  | 38.894 | 1.406 | 80 | 3 | 0 | 66 | 62 | 0 | 0.3511 |
| lin_vel_z_l2 | -1.5 | 재사용 | 서버 |  | 44.625 | 7.414 | 24 | 6 | 29 | 10 | 94 | 77 | 0.3441 |
| lin_vel_z_l2 | -1.375 | 재사용 | 서버 |  | 47.255 | 8.555 | 19 | 8 | 0 | 11 | 31 | 0 | 0.3279 |
| lin_vel_z_l2 | -1.25 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| lin_vel_z_l2 | -1.25 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| lin_vel_z_l2 | -1.0 | 재사용 | 서버 |  | 46.203 | 4.585 | 46 | 2 | 0 | 11 | 61 | 1 | 0.3374 |
| ang_vel_xy_l2 | -0.04 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| ang_vel_xy_l2 | -0.05 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| ang_vel_xy_l2 | -0.05 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| ang_vel_xy_l2 | -0.08 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| feet_air_time | 0.01 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| feet_air_time | 0.1 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| feet_air_time | 0.2 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| feet_air_time | 0.2 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| feet_air_time | 0.35 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| action_rate_l2 | -0.008 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| action_rate_l2 | -0.01 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| action_rate_l2 | -0.01 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| action_rate_l2 | -0.012 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| flat_orientation_l2 | 0.0 | 서버 A048 | 서버 |  | 50.157 | 8.977 | 16 | 3 | 0 | 1 | 90 | 24 | 0.242 |
| flat_orientation_l2 | 0.0 | 이 PC A048 | 이 PC |  | 43.397 | 2.178 | 68 | 6 | 0 | 10 | 76 | 6 | 0.3708 |
| flat_orientation_l2 | -0.25 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |
| flat_orientation_l2 | -0.5 | 새 학습 | 미회수 |  |  |  |  |  |  |  |  |  |  |

- PC 열이 다른 점끼리의 차이는 보상 효과와 PC·seed 차이가 섞여 있다.
