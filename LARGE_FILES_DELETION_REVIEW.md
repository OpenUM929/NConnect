# 대용량 파일·영상 위치 정리 및 삭제 여부 검토 요청

- 작성일: 2026-09-04
- 작성자: Sisyphus (메인 루프)
- 수신: 상위 AI (삭제 최종 판정 요청)
- 저장 위치: root (`C:\dev\Nconnect\LARGE_FILES_DELETION_REVIEW.md`)
- 조사 명령 (재현용):
  - `Get-ChildItem -Recurse -File | Sort-Object Length -Descending | Select -First 100`
  - `Get-ChildItem -Recurse -File -Include *.mp4,*.avi,*.mov,*.mkv,*.webm`
  - `Where-Object { $_.Length -ge 50MB }`
  - `Where-Object { $_.Length -ge 5MB } | Group-Object Extension`
  - `git status --porcelain=v1 -uall`, `git ls-files -s`

## 0. 요약 (먼저 읽을 것)

- 50MB 이상 파일: 13개, 전부 `workspace/_keep/`, `workspace/server_returns/`, `workspace/*.tar.gz`에 있음. 전부 git untracked이므로 로컬 삭제는 git history에 영향 없음.
- 영상 전체: 약 123개·636MB. `workspace/training/humanoid/exported/` 21개, `workspace/training/humanoid/reports/S0*` 약 16개, `workspace/_keep/train_260831-06_run05cfg_10000_videos/` 10개, `server_returns/.../extracted_full|partial` 17개, Go2 평가 `videos/` 다수, `quadruped/exported/` 2개.
- 5MB 이상 확장자 요약: `.csv` 462개·3317.4MB (주로 `steps.csv` 약 9MB/개), `.mp4` 64개·459MB (5MB 이상만 집계, 전체 영상은 123개·636MB), `.pt` 60개·401MB, `.zip` 34개·1859.2MB, `.gz` 16개·688.4MB, `.log` 6개·79.4MB.
- 중복 구조가 명확함: `_keep` ↔ `server_returns/.../original` 동일 파일명·동일 바이트 다수 (예: 416,205,363B ZIP 2벌, 207,738,612B ZIP 2벌, 93,389,172B TAR 2벌). `extracted_full/partial` 영상은 원본 `VIDEOS_*.tar.gz` 해제본으로 보임.
- 주의: `workspace/training/humanoid/reports/S0*/**.mp4`와 `S0_260829/**.mp4`는 이미 git tracked임 (`git ls-files` 확인). 워킹카피에서 지워도 history에는 남으므로 리포 용량을 줄이려면 `git rm` 커밋 + history 정리 여부를 별도 판정해야 함.

## 1. 상위 AI에게 묻는 삭제 판정 (회신 형식 지정)

아래 Q1~Q5에 `승인 / 반려 / 조건부`로 답해 주세요. 조건부는 경로 패턴과 보관 조건을 함께 적어 주세요.

- Q1. 50MB 이상 13개 전체를 로컬에서 삭제해도 되는가? (git untracked, 재생성 가능 원본이 `server_returns/.../original`과 `_keep`에 이중 보관됨)
- Q2. 중복 2벌 중 1벌만 남긴다면 어느 쪽을 정본으로 하는가? (a) `workspace/_keep/` 유지 (b) `workspace/server_returns/` 유지 (c) 둘 다 삭제 후 필요시 서버 재수령
- Q3. 영상 123개를 전부 로컬 삭제해도 되는가? 아니라면 보관해야 할 최소 집합을 경로 패턴으로 지정해 달라. (예: `humanoid/reports/S0b/*`만 유지)
- Q4. git tracked 영상 (`humanoid/reports/S0*/**.mp4`, `S0_260829/**.mp4`, `humanoid/exported/play_video*.mp4` 중 tracked분)을 `git rm`으로 리포에서 제거해도 되는가? (history에는 남음, `git filter-repo`급 history 정리는 별도 작업)
- Q5. `.csv` steps 462개·3.3GB와 `.pt` 60개·401MB를 정리 대상에 포함해도 되는가? 포함한다면 임계값(예: 5MB 이상 전부 vs 50MB 이상만)과 예외 경로를 지정해 달라.

## 2. 50MB 이상 파일 전수 (13개, 크기 내림차순)

| 크기 | 위치 (root 상대) |
|---|---|
| 396.9 MB | `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip` |
| 396.9 MB | `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` |
| 249.4 MB | `workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip` |
| 198.1 MB | `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` |
| 198.1 MB | `workspace/server_returns/go2_feet_air_time_020_v1_full_260901/original/GO2_FEET_AIR_TIME_020_RESULT.zip` |
| 89.1 MB | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz` |
| 89.1 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/original/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz` |
| 66.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/original/train_260831-06_run05cfg_10000_VIDEOS_PARTIAL.tar.gz` |
| 66.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_PARTIAL.tar.gz` |
| 66.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_CORE.tar.gz` |
| 55.9 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/original/training_train_260831-06_run05cfg_10000_snapshot.tar.gz` |
| 55.9 MB | `workspace/training_train_260831-06_run05cfg_10000_snapshot.tar.gz` |
| 52.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_INDEPENDENT_EVAL_FULL.tar.gz` |

## 3. 영상 전수 위치 (약 123개, 크기 내림차순, root 상대 표기)

대표 중복 구조: `H4_complex_right.mp4 (8.6MB)`, `H4_complex.mp4 (8.6MB)`, `H2_forward.mp4 (8.5MB)` 등은 `_keep/.../videos/` + `server_returns/.../extracted_full/.../videos/` + `extracted_partial/.../videos/` 3벌로 존재.

| 크기 | 위치 |
|---|---|
| 9.1 MB | `workspace/training/humanoid/reports/S0d/H5_rough.mp4` |
| 9.1 MB | `workspace/training/humanoid/exported/play_video_20260829_230924.mp4` |
| 8.9 MB | `workspace/training/humanoid/exported/play_video_20260829_224233.mp4` |
| 8.9 MB | `workspace/training/humanoid/reports/S0c/H5_rough.mp4` |
| 8.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H4_complex_right.mp4` |
| 8.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H4_complex_right.mp4` |
| 8.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H4_complex_right.mp4` |
| 8.6 MB | `workspace/training/humanoid/exported/play_video_20260829_212532.mp4` |
| 8.6 MB | `workspace/training/humanoid/reports/S0b/H2_forward.mp4` |
| 8.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H4_complex.mp4` |
| 8.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H4_complex.mp4` |
| 8.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H4_complex.mp4` |
| 8.5 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H2_forward.mp4` |
| 8.5 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H2_forward.mp4` |
| 8.5 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H2_forward.mp4` |
| 8.5 MB | `workspace/training/humanoid/reports/S0d/H2_forward.mp4` |
| 8.5 MB | `workspace/training/humanoid/exported/play_video_20260829_231248.mp4` |
| 8.4 MB | `workspace/training/humanoid/reports/S0b/H4_turn.mp4` |
| 8.4 MB | `workspace/training/humanoid/exported/play_video_20260829_213148.mp4` |
| 8.1 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H5_rough.mp4` |
| 8.1 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H5_rough.mp4` |
| 7.9 MB | `workspace/training/humanoid/exported/play_video_20260829_223713.mp4` |
| 7.9 MB | `workspace/training/humanoid/reports/S0c/H5_rough_r1.mp4` |
| 7.6 MB | `workspace/training/humanoid/reports/S0b/H3_right.mp4` |
| 7.6 MB | `workspace/training/humanoid/exported/play_video_20260829_213030.mp4` |
| 7.4 MB | `workspace/training/humanoid/reports/S0b/H3_left.mp4` |
| 7.4 MB | `workspace/training/humanoid/exported/play_video_20260829_212846.mp4` |
| 7.2 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H3_right.mp4` |
| 7.2 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H3_right.mp4` |
| 7.2 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H3_right.mp4` |
| 7.1 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H3_left.mp4` |
| 7.1 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H3_left.mp4` |
| 7.1 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H3_left.mp4` |
| 6.6 MB | `workspace/training/humanoid/reports/S0b/H7_push.mp4` |
| 6.6 MB | `workspace/training/humanoid/exported/play_video_20260829_213300.mp4` |
| 6.6 MB | `workspace/training/humanoid/exported/play_video_20260828_211821.mp4` |
| 6.5 MB | `workspace/training/humanoid/exported/play_video_20260829_162108.mp4` |
| 6.5 MB | `workspace/training/humanoid/reports/S0_260829/S0_00_baseline.mp4` |
| 6.5 MB | `workspace/training/humanoid/exported/play_video_20260828_225108.mp4` |
| 6.5 MB | `workspace/training/humanoid/exported/play_video.mp4` |
| 6.5 MB | `workspace/training/humanoid/reports/S0_260829/00_baseline.mp4` |
| 6.5 MB | `workspace/training/humanoid/exported/play_video_20260829_171725.mp4` |
| 6.4 MB | `workspace/training/humanoid/reports/S0b/H1_stand.mp4` |
| 6.4 MB | `workspace/training/humanoid/exported/play_video_20260829_212336.mp4` |
| 6.4 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H7_push.mp4` |
| 6.4 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H7_push.mp4` |
| 6.4 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H7_push.mp4` |
| 6.4 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H1_stand.mp4` |
| 6.4 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_partial/train_260831-06_run05cfg_10000_videos/videos/H1_stand.mp4` |
| 6.4 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H1_stand.mp4` |
| 6.1 MB | `workspace/training/humanoid/reports/S0c/H6_down.mp4` |
| 6.1 MB | `workspace/training/humanoid/exported/play_video_20260829_224454.mp4` |
| 5.8 MB | `workspace/training/humanoid/exported/play_video_20260829_224343.mp4` |
| 5.8 MB | `workspace/training/humanoid/reports/S0c/H6_up.mp4` |
| 5.8 MB | `workspace/training/humanoid/exported/play_video_20260829_231140.mp4` |
| 5.8 MB | `workspace/training/humanoid/reports/S0d/H6_down.mp4` |
| 5.7 MB | `workspace/training/humanoid/exported/play_video_20260829_231032.mp4` |
| 5.7 MB | `workspace/training/humanoid/reports/S0d/H6_up.mp4` |
| 5.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H6_plus10_approx.mp4` |
| 5.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H6_plus10_approx.mp4` |
| 5.6 MB | `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/H6_minus10_approx.mp4` |
| 5.6 MB | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/train_260831-06_run05cfg_10000_videos/videos/H6_minus10_approx.mp4` |
| 5.5 MB | `workspace/training/humanoid/exported/play_video_20260828_212708.mp4` |
| 5.1 MB | `workspace/training/humanoid/exported/play_video_20260828_085939.mp4` |
| 4.3 MB 이하 | `workspace/_keep/go2_pilot_v2_baseline/evaluation/pilot_v2/videos/` 7개, `workspace/_keep/go2_default_vs_pilot_v1/evaluation/{default,pilot}/videos/` 14개, `server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/{default,pilot}/` 14개, `workspace/_keep/go2_feet_air_time_020_v1/evaluation/candidate/videos/` 7개 + 대응 `server_returns/.../extracted/...` 7개, `workspace/training/quadruped/exported/play_video*.mp4` 2개, `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/videos/` 1개 + 대응 extracted 1개 + `_keep` 1개 등 (개별 1~4MB대, 전수 60여개, 위 디렉토리별 집계 참조) |

영상 디렉토리별 개수:

| 디렉토리 | 개수 |
|---|---:|
| `workspace/training/humanoid/exported/` | 21 |
| `workspace/server_returns/train_260831-06_run05cfg_10000/videos/extracted_full/.../videos/` | 10 |
| `workspace/_keep/train_260831-06_run05cfg_10000_videos/videos/` | 10 |
| `workspace/_keep/go2_default_vs_pilot_v1/evaluation/default/videos/` | 7 |
| `server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/default/` | 7 |
| `workspace/_keep/go2_feet_air_time_020_v1/evaluation/candidate/videos/` | 7 |
| `workspace/_keep/go2_pilot_v2_baseline/evaluation/pilot_v2/videos/` | 7 |
| `workspace/_keep/go2_default_vs_pilot_v1/evaluation/pilot/videos/` | 7 |
| `server_returns/go2_feet_air_time_020_v1_full_260901/extracted/.../evaluation/candidate/videos/` | 7 |
| `server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/pilot/` | 7 |
| `server_returns/.../extracted_partial/.../videos/` | 7 |
| `workspace/training/humanoid/reports/S0b/` | 6 |
| `workspace/training/humanoid/reports/S0c/` | 4 |
| `workspace/training/humanoid/reports/S0d/` | 4 |
| `workspace/training/humanoid/reports/S0_260829/` | 2 |
| `workspace/training/quadruped/exported/` | 2 |

## 4. 대용량 상위 파일 TOP 40 (영상 제외분 포함, 바이트 실측)

| 바이트 | 위치 |
|---|---|
| 416,205,363 | `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip` |
| 416,205,363 | `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` |
| 261,566,874 | `workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip` |
| 207,738,612 | `workspace/server_returns/go2_feet_air_time_020_v1_full_260901/original/GO2_FEET_AIR_TIME_020_RESULT.zip` |
| 207,738,612 | `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` |
| 93,389,172 | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/original/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz` |
| 93,389,172 | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz` |
| 69,792,876 | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/original/train_260831-06_run05cfg_10000_VIDEOS_PARTIAL.tar.gz` |
| 69,792,876 | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_PARTIAL.tar.gz` |
| 69,785,808 | `workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_CORE.tar.gz` |
| 58,568,563 | `workspace/server_returns/train_260831-06_run05cfg_10000/original/training_train_260831-06_run05cfg_10000_snapshot.tar.gz` |
| 58,568,563 | `workspace/training_train_260831-06_run05cfg_10000_snapshot.tar.gz` |
| 55,154,271 | `workspace/_keep/train_260831-06_run05cfg_10000_INDEPENDENT_EVAL_FULL.tar.gz` |
| 43,938,195 | `workspace/_keep/GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip` |
| 43,226,568 | `workspace/_keep/GO2_FLAT_ORIENTATION_M1_RESULT.zip` |
| 42,420,526 | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/original/train_260831-06_run05cfg_10000_VIDEOS_CORE.tar.gz` |
| 37,227,124 | `workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` |
| 37,224,891 | `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` |
| 37,224,891 | `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/original/GO2_TRACK_LIN_VEL_120_RESULT.zip` |
| 34,415,796 | `workspace/server_returns/go2_feet_air_time_020_v1_partial_260901/original/GO2_FEET_AIR_TIME_020_RESULT.zip` |
| 34,290,616 | `workspace/training/quadruped/go2_feet_air_time_020_v2.zip` |
| 22,799,896 | `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz` |
| 20,588,779 | `workspace/server_returns/train_260831-06_run05cfg_10000/original/train_260831-06_run05cfg_10000_DOWNLOAD.tar.gz` |
| 20,588,779 | `workspace/_keep/train_260831-06_run05cfg_10000_DOWNLOAD.tar.gz` |
| 20,125,962 | `workspace/server_returns/train_260831-06_run05cfg_10000/extracted/train_260831-06_run05cfg_10000/run/events.out.tfevents.1788139618.da-perfect32.1199.0` |
| 20,125,962 | `workspace/_keep/train_260831-06_run05cfg_10000/run/events.out.tfevents.1788139618.da-perfect32.1199.0` |
| 18,102,753 | `workspace/_keep/train_260831-06_run05cfg_10000/launcher.log` |
| 18,102,543 | `workspace/server_returns/train_260831-06_run05cfg_10000/extracted/train_260831-06_run05cfg_10000/launcher.log` |
| 18,102,318 | `workspace/_keep/train_260831-06_run05cfg_10000/train.log` |
| 18,102,318 | `workspace/server_returns/train_260831-06_run05cfg_10000/extracted/train_260831-06_run05cfg_10000/train.log` |
| 13,408,419 | `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_PARTIAL.tar.gz` |
| 13,408,419 | `workspace/train_260831-06_run05cfg_10000_FIXED_EVAL_PARTIAL.tar.gz` |
| 13,408,419 | `workspace/server_returns/train_260831-06_run05cfg_10000/fixed_eval/original/train_260831-06_run05cfg_10000_FIXED_EVAL_PARTIAL.tar.gz` |
| 12,781,997 | `workspace/training/quadruped/upload/G-A015/history/20260903_engine-v1.3/go2_tuning_engine_v1_3.zip` |
| 12,781,997 | `workspace/training/quadruped/upload/G-A015/current/go2_tuning_engine_v1_3.zip` |
| 12,781,997 | `workspace/training/quadruped/go2_tuning_engine_v1_3.zip` |
| 12,781,997 | `workspace/training/quadruped/upload/G-A015/history/20260903_engine-v1.3-r2/go2_tuning_engine_v1_3.zip` |
| 11,187,240 | `test.zip` (root) |
| 9,561,681 | `workspace/training/humanoid/exported/play_video_20260829_230924.mp4` |
| 9,561,681 | `workspace/training/humanoid/reports/S0d/H5_rough.mp4` |

## 5. 삭제 시 주의 (git 추적 여부)

- 50MB 이상 13개는 모두 untracked. 삭제해도 git에 영향 없음. 단 `server_returns/.../original/*`은 서버 재수령 근거이므로 Q2 정본 판정 전까지 삭제 금지.
- 영상 중 `humanoid/reports/S0*/**.mp4`, `S0_260829/**.mp4`는 tracked. 로컬 `rm`만으로는 리포 용량이 줄지 않음. 리포 축소가 목적이면 Q4 승인 후 `git rm` + 커밋이 필요하고, history 자체를 줄이려면 별도 history 정리 작업이 필요함.
- `.zip`, `.tar.gz`, untracked `.pt`는 이전 커밋에서 의도적으로 제외됨. 삭제해도 push 상태와 무관.
- `git status` untracked 총 4423개 중 대부분은 `server_returns`, `_keep`, `_go2_tuning_runtime` 하위 소규모 evidence (`steps.csv`, `summary.json`, 로그). 이번 문서는 대용량(50MB+)과 영상 전수에 집중했고, 소규모 evidence 일괄 삭제는 Q5 후속으로 다룬다.
