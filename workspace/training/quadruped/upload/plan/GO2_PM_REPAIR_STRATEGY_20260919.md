# Go2 판단 오류 수정·튜닝 우선순위 검토

요청: 2026-09-19 사용자. STAY — 로컬 검사 수정과 사실 기반 전략 검토. 서버 실행·보상값 변경·패키지 발행은 이번 작업 범위가 아니다.

## 수정 계획
1. 회귀 테스트로 CSV의 다른 행 값을 섞는 오류, 반대 증거가 있으면 무조건 권고를 막는 오류를 재현한다.
2. CSV 키·값은 같은 행에서 확인한다. 탐색 권고와 성능 채택을 구분하며 반대 증거를 삭제하지 않는다. 탐색 권고는 반대 증거 대응·반증 조건을 요구한다.
3. 상황 시험의 알려진 오답 통과와 PM 열린 결정 누락을 고친다. 자동 시험은 의미 정확성의 완전한 증명이 아님을 명시한다.
4. 현재 상태의 마지막 실행과 기준선을 분리하고 포화 단정을 철회한다. 고정된 과거 판독 인계를 제거한다.
5. 원자료·원 학습 HTML·공식 수식으로 후보를 비교한다. 수학적 상한을 기대 이득으로 쓰지 않는다.

## 검증과 범위
- 수정 전 실패 재현 → 수정 후 표적 테스트 → 관련 회귀 검사.
- 기존 승인 ZIP·서버 배포 학습 코드·reward 파일·평가 수식과 성능 임계값은 수정하지 않는다.
- 결과 채택 기준을 낮추어 특정 후보를 통과시키지 않는다.
- 알려진 오답에 대한 회귀 방어와 누락 증거 전체 탐지는 다른 문제다. 독립 검토로 한계를 보고한다.

## 검토 결과
### 사실 → 우선순위

기준선 G-A033의 내부 proxy는 42.52861/70이다. `reports/runs/SCENARIO_SCORES.csv`의 G1~G7 점수는 각각 9.22452, 9.21294, 4.22726, 9.01774, 0.04473, 5.69295, 5.10847이다. 공식 결과가 아니다.

`reports/GO2_AXIS_BOTTLENECK.md`: G3 rough_lateral@202는 생존 .375, 추종 .80519가 병목이다. 모든 case의 생존만 1로 바꾼 반사실은 G3 4.22726→10.71746/14점이다. G5는 감점 10.45527점으로 더 크지만 같은 반사실에서도 0.04473→1.43139/10.5점에 그친다. 전진거리 부족이 남기 때문이다. **G3 생존을 개선하면서 추종을 지키는 실험을 먼저 검토한다. 반사실 상한은 기대 이득이나 쉬움의 실증이 아니다.**

| 순위 | 단일변수 후보 | 관측 근거·반대 증거 | PM 판단 |
|---|---|---|---|
| 1 | flat_orientation_l2 0→−0.5 | A033 rough_lateral tilt-only 낙상 9/8/13대. 낙상 전 tilt 식 .31123, 생존 .05106. 반대: Pilot에서는 부호 반대, 경사·계단에도 비용, Isaac rough 기본0 | 걷는 기준의 미탐색 정보 실험. 실제 개선 미측정 |
| 2 | ang_vel_xy_l2 −0.05→−0.06 | −0.08의 A038은 험지 옆걸음 표적 +.356, 밀침 +.049이나 계단 한단 도달 90→5. 중간값이 안전하다는 근거 없음 | 알려진 손실 방향 때문에 후순위. 보간으로 성공 주장 금지 |
| 후순위 | lin_vel_z_l2 −2→−1 | 기반 데이터 S5가 단조 원리를 반박하고 흔들림·밀침에 불리 | G3 우선 목표와 충돌 |
| 후순위 | dof_acc_l2 절반 | 최대 학습 벌점이라는 사실만 있고 시나리오 효과 미측정, 배포 목록 밖 R-6 해석 미해결 | 최대 벌점≠최대 점수 개선 |
| 유지 | track1.5, feet_air .2 | track 증가와 종료31→48→58 동행. feet_air 양방향 시도 기각이나 조건·iter 차이 한계 있음 | 기본값 복귀/추가 강화만으로 개선 주장하지 않음 |

**−0.5는 관측 최적값이 아니다.** 걷는 회차의 이 항 관측값은 0뿐이다(OUT_OF_RANGE). 기존 탐침 격자 −0.5/−1/−2.5 중 최소 크기를 고른 실험 설계값이며 −0.25보다 낫다는 증거도 없다. 원자료는 표적과 항 선택을 지지하고, 정확한 크기는 불확실성을 인정한 PM 선택이다. 부분 margin은 고정 궤적의 보상 산수이지 재학습 성능 예측이 아니다.

### 수식·출처

Isaac Lab v2.3.1의 flat_orientation은 `sum(projected_gravity_b[:2]²)`(자세 각도), ang_vel_xy는 `sum(root_ang_vel_b[:2]²)`(각속도)이다. 전자는 20도 기울기에서 약 .117이므로 −.5일 때 dt 곱 전 −.0585가 된다. 경사·계단에도 부과되므로 G4/G5를 보호한다. Go2 rough는 flat_orientation 0, flat 설정은 −2.5다. 상류값은 최적값의 증거가 아니다.

추종은 body-frame `exp(-sum((command_xy-root_lin_vel_b_xy)²)/std²)`이다. feet_air_time은 첫 접지 때 체공시간−threshold를 합하고 명령 xy 크기>.1일 때만 적용한다. 발 높이 보상이 아니다. 강의 14강의 단일변수·영상/report 확인은 실험 설계 근거이며 공식 채점 출처가 아니다.

공식 원문: [reward 수식](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/source/isaaclab/isaaclab/envs/mdp/rewards.py), [체공](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/mdp/rewards.py), [rough](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/rough_env_cfg.py), [flat](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/go2/flat_env_cfg.py).

### 학습 report 대응·한계

PM과 분석 담당은 두 원본 HTML 본문을 직접 읽었다.
- `workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/exported/report.html`: 2026-09-15 21:29~22:27, 선택 checkpoint iter700, 최고 reward19.28(iter651), 마지막 terrain4.71·학습낙상17.1%·std .613. 평가 기준은 iter900/model SHA `ccd60e192bf4ec900a269cc264d7739a4962a4ce07a0c3607568346778646044`다.
- `workspace/_keep/go2_g_a038_a033_ang_vel_xy_m008/exported/report.html`: 2026-09-17 14:11~15:11, 선택 checkpoint iter999, 최고 reward20.11(iter984), 마지막 terrain3.03·학습낙상12.4%·std .525. 부분 평가 기준은 iter900이다.
- `REPORT_READ_STATUS=READ_MATCHED`는 같은 학습 run의 report/env/log 대응에 한정한다. best checkpoint와 평가 checkpoint는 다르다. A017 원 학습 report는 MISSING(과거 회수 공백), 기존 로그/SELF_EVAL만 대체 근거다.
- 이번 작업은 영상을 새로 재관찰하지 않았다. G1~G7 영상은 이번 검토 VIDEO_UNKNOWN, 내부 정량은 위 원자료 범위, 공식 결과는 모두 미측정이다.

### 검증·다음 분기

| 등급 | 작업 | 완료 기준 |
|---|---|---|
| 개선 | G3 단일변수 정보 실험 | 같은 evaluator·iter900·rough_forward/rough_lateral 3평가 seed, 생존과 추종 동시 측정 |
| 개선 | G4/G5 부작용 | 경사 양방향·10/15cm 전진거리·tilt/height·오른 로봇 수를 검사. G5 최솟값만으로 붕괴를 숨기지 않음 |
| 조사 | 기전 | tilt 감소·정지 증가·추종 손실 분리. tilt-only 감소가 없다고 모든 인과효과 부재를 단정하지 않음 |
| 필수(제출요건) | 최종 후보 평가·제출물 | G1~G7 전수, 영상, report/env/policy 정합. 이번 작업에서 완료한 단계 아님 |

1000iter 학습 선례는 A033 약59분/A038 약60분이다. 전체 평가·회수 비용은 별도이고 잔여 TTL은 미측정이다. G-A040의 15cm guard는 `4−5.523≤0`으로 감소 검출 불가다. 보호 축 key 정합성도 발행 전에 검사해야 한다. **임계값을 낮추지 않고 현 사양을 실행 준비 완료로 취급하지 않는다.** INFORMATION_RUN은 미실행 검토 후보이며 패키지 발행/승급이 아니다. G3가 좋아도 계단·경사 붕괴면 채택하지 않는다. 불완전 결과는 INCONCLUSIVE, seed42 한 번은 exploratory다.

### 수정 검증 범위

CSV 다른 행 값 혼합은 수정 전 실패 재현 후 수정했다. 반대 증거를 남긴 탐색 권고는 대응·반증 조건을 요구한다. 상황 시험은 알려진 오답 방어이며 자연어 의미의 완전 검증이 아니다. 누락된 반대 증거 전체 탐지는 여전히 독립 검토 대상이다. 서버 배포 코드·reward·기존 ZIP·성능 임계값은 바꾸지 않았다.

추가 수식 한계: 중력 xy 제곱은 정규화 중력에서 1−gz²와 같아 똑바로 선 상태와 완전히 뒤집힌 상태 모두 0이다. 따라서 signed gz·높이를 쓰는 생존 gate와 같은 함수가 아니며, 자세 벌점만으로 낙상 방지를 보장하지 않는다. A040 원문에 남은 “same quantity”는 기울기 관련 채널이라는 뜻 이상으로 해석하면 안 된다.

### 최종 검증 기록
- 관련 74개 실행: 73개 성공, GO2_NOW 60줄 제한 1개 실패. 빈 줄만 줄여 제한을 유지하고 canonical/PM/상황 시험 31개 재실행 모두 성공. 마지막 사양 문구 수정 뒤 inference 19개도 성공. 74개 전체의 최종 일괄 재실행은 하지 않았다.
- Python AST 7파일 정상, git diff --check 정상(기존 파일의 LF/CRLF 경고만).
- 연계 claim-check 13개 중 12개 성공, 기존 NOTICE 문서 미분류 1개 실패는 별도 결함으로 남김. 검사 범위나 임계값을 늘려 숨기지 않았다.
- 독립 감사는 핵심 반대 근거와 guard 검출불가를 보고했으나 사용량 제한으로 최종 승인 보고를 완료하지 못했다. 독립 감사 완료로 주장하지 않는다.
- 수정 범위: inference 관문/신규 회귀, 상황 시험/회귀, PM brief/회귀·생성 보고서, claim-check 표본 처리, 현재 상태·결정 기록·역할 인계·upload 안내, A040 미실행 사양의 정보 실험 분류. 학습·서버·제출 성능은 검증하지 않았다.
