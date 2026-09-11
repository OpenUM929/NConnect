# Go2 1차 튜닝 기반 초기 작업계획

> **260901 대체됨:** 사용자가 실험 계보를 튜닝 전 기본값에서 다시 시작하기로 결정했다.
> 현재 실행 정본은 `workspace/training/quadruped/upload/plan/go2-default-baseline-experiment-plan.md`, 테스트 계약은
> `workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md`다.
> 이 문서는 이전 “Pilot fixed eval → 조건부 control” 계획의 이력으로만 보존한다.

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 proxy /70과 문서 자체감사 /30을 분리해 총 자체예상 최소 70점, 목표 75점 이상의 제출 후보를 만든다.
- [현재 단계] **단계 0/6 — 증거·artifact 정합성** (`GO2_PROJECT_STATE.md:6-15`).
- [확보] `train_260831-Go2_5var_1000`, iter 999, model SHA `c4d78adf…af8d`, env SHA `f5550641…975d`, tfevents·report·generic video (`GO2_PROJECT_STATE.md:17-28`).
- [미확보] 정확한 G1~G7 telemetry·영상, 평가 seed 101/202/303, policy actor tensor lineage, 공식 결과 (`GO2_PROJECT_STATE.md:56-66`).
- [이번 테스트] 새 학습 없이 Pilot-01의 G1~G7 약점과 survival/tracking 중 약한 인수를 찾는다.
- [흐름] Pilot-01 확보 → **G-A002 evaluator/package** → fixed eval → 조건부 control → 단일변수 screening → 장기 승급 → 제출.
- [지금 할 일] 로컬에서 evaluator와 package 계약을 구현·검증한다. 사용자는 로컬 검증 전 서버를 켜지 않는다.
- [보장하지 않음] 1,000 iter 단일 run, 평균 reward 18.02, generic video는 공식 점수·개별 reward 효과·통과 가능성을 보장하지 않는다 (`GO2_REWARD_EVIDENCE_MASTER.md:8-14`).

## 1. 요구사항 요약

1. Pilot-01은 네 reward를 동시에 바꾼 `MULTIVARIABLE_EXPLORATORY_BASELINE`으로만 사용한다 (`GO2_PROJECT_STATE.md:44-54`).
2. 다음 reward 값은 미리 고르지 않는다. G1~G7 최대 감점 시나리오와 약한 인수가 나온 뒤 하나만 선택한다 (`GO2_REWARD_EVIDENCE_MASTER.md:51-59`).
3. 공식 evaluator 상세는 미공개이므로 모든 점수는 `INTERNAL_PROXY`로 표기한다 (`workspace/training/quadruped/reports/GO2_EVALUATION_PROTOCOL.md:10-24`).
4. G1~G7의 ID·가중치·case·필수 metric은 canonical registry에서 직접 읽는다 (`workspace/training/quadruped/config/go2_self_eval_registry.json:36-99`).
5. `server_run_Go2_videos.sh`는 `LEGACY_INVALID_MAPPING`이므로 실행·import·재사용하지 않는다 (`workspace/training/quadruped/AGENTS.md:35-37`).
6. 최종 제출 계약은 Go2 선택 + `policy.pt` + 같은 run의 `env.yaml` + 30~200자 기술 개선 리포트다 (`workspace/training/quadruped/AGENTS.md:82-91`).

## 2. 기준선 해석

| 항목 | 현재 판정 | 계획에 미치는 영향 |
|---|---|---|
| reward 18.02@972, terrain 3.94, 학습지형 낙상 진단 13.8% | 학습 진단일 뿐 G1~G7 survival/tracking 아님 (`GO2_PROJECT_STATE.md:34-41`) | 승급·폐기 근거로 사용하지 않음 |
| `track_lin 1.2`, `feet_air 0.2`, `lin_z -2`, `ang_xy -0.05` | 네 항 동시 변경, 인과 귀속 불가 (`GO2_REWARD_EVIDENCE_MASTER.md:18-27`) | 다음 실험은 한 항만 변경 |
| generic video 1개 | checkpoint sidecar 없음 (`workspace/training/quadruped/reports/GO2_EVIDENCE_INDEX.md:12-16`) | `VIDEO_UNKNOWN`; evaluator 영상으로 교체 |
| `policy.pt` 없음 | 제출 파일·actor lineage 미완료 (`GO2_PROJECT_STATE.md:26-28`) | evaluator 실행에서 exact checkpoint로 export하고 tensor 대조 |
| timestamped 이전 model/env | `env_20260831154121.yaml`도 튜닝 reward를 보유 | 배포 기본 control로 사용 금지; provenance-valid control은 현재 없음 |

## 3. 선택한 실행 전략

### 선택: 평가 우선, 조건부 control, 약점 기반 단일변수 ablation

이 전략은 현재 가장 큰 공백이 iteration 부족이 아니라 G1~G7 성능 미측정이라는 결정과 일치한다 (`GO2_PROJECT_STATE.md:48-54`).

| 대안 | 장점 | 기각·보류 이유 |
|---|---|---|
| 바로 5k~15k 장기학습 | 구현 없이 GPU를 즉시 사용 | 약점·성공 기준·부작용 게이트가 없어 iteration만 소비함 |
| 네 reward를 다시 조합 | 빠르게 다른 행동을 볼 수 있음 | Pilot-01의 인과 공백을 반복하고 어떤 변경이 유효했는지 알 수 없음 |
| 배포 기본 control을 먼저 새로 학습 | 상대 비교 기준 확보 | Pilot-01의 실제 약점도 모른 채 서버 비용을 사용함; fixed eval 뒤 정보가치가 있을 때만 수행 |
| **Pilot-01 fixed eval 후 분기** | 다음 실험의 시나리오·인수·reward를 직접 결정 | evaluator 구현이 선행되지만 이후 모든 run에 재사용 가능 |

## 4. 단계별 작업계획

### P0. G-A002 evaluator/package 완성 — 필수(제출요건)

**목표:** 학습 없이 exact Pilot-01 checkpoint를 canonical G1~G7 조건에서 재현하고, 정량·영상·lineage를 한 bundle로 회수한다.

구현 대상:

- `workspace/training/quadruped/go2_eval_telemetry.py`
- `workspace/training/quadruped/go2_fixed_eval_report.py`
- `workspace/training/quadruped/server_run_go2_eval_v1.sh`
- `tools/build_go2_eval_package.py`
- `tools/test_go2_eval_contract.py`

case 실행 계약:

- G1~G6의 22개 canonical case는 평가 seed 101/202/303으로 실행해 telemetry 66개를 만든다.
- G7은 registry의 `dr_seed_101/202/303`을 각 seed에 1:1로 실행해 telemetry 3개를 만든다.
- 총 telemetry 기대값은 **69 case**다. G7을 평가 seed와 다시 3×3으로 중복하지 않는다.
- 영상은 25개 canonical condition을 최소 한 번 촬영하고, scenario별 worst seed/case가 기존 영상과 다르면 최대 7개를 추가 재생한다.
- 모든 영상에 scenario, case, seed, command, terrain/push/DR 실현값, model SHA sidecar를 둔다 (`GO2_EVALUATION_PROTOCOL.md:59-64`).

완료 기준:

1. `python tools/validate_go2_campaign.py` 성공.
2. 신규 Python compile·unit/golden test 성공.
3. 신규 shell `bash -n`, CRLF 0.
4. ZIP CRC·안전 상대경로·manifest·embedded model/env SHA 성공.
5. registry weight 합 1.0, 69 telemetry execution plan, 필수 field 검증.
6. legacy runner import/call 0.
7. 예상시간·`[STARTED]/[MONITOR]/[RESULT]/[DONE]`·정확한 다운로드 경로 출력 검증 (`GO2_EVALUATION_PROTOCOL.md:66-98`).

**중단조건:** 하나라도 실패하면 `▲ 제출 불가 — G-A002 로컬 package 미완료`; 서버 명령을 제공하지 않는다.

### P1. Pilot-01 G1~G7 fixed eval — 필수(제출요건)

**최소 경로:** 검증된 ZIP 업로드 → 한 줄 실행 → FULL bundle과 `.sha256` 다운로드.

필수 회수물:

- 69개 case telemetry/summary/log 또는 명시적 실패 상태
- canonical 영상 25개 + 필요한 worst-case replay
- `SELF_EVAL_REPORT.json/md`, `VIDEO_STATUS.tsv`, `RUNNER_STATUS.txt`
- exact model/env/registry/source SHA, policy export, actor tensor 비교 결과
- package 내부 `SHA256SUMS.txt`

완료 기준:

- `ARTIFACT_VERIFIED`: 외부 SHA, ZIP/tar 안전성, manifest, model/env/source/registry 대응.
- `VIDEO_OBSERVED` 또는 case별 `VIDEO_UNKNOWN`: 행동 관찰과 판독 불가를 분리.
- G1~G7 각 scenario에 survival과 tracking이 모두 있어야 `SELF_ASSESSMENT_INCOMPLETE`를 해소.
- 내부 gate는 scenario별 survival ≥0.95, tracking ≥0.70, weighted simulation proxy ≥0.70 (`GO2_EVALUATION_PROTOCOL.md:26-36`).
- 공식 결과는 계속 `OFFICIAL_RESULT_UNMEASURED`다.

### P2. 약점 지도와 첫 재평가 — 필수(제출요건)

각 G별로 `영상 / 내부 정량 / 공식 결과`를 분리해 다음을 계산한다.

```text
scenario_loss = weight × (1 - survival_proxy × tracking_proxy)
```

분기:

| 결과 | 다음 행동 |
|---|---|
| telemetry·실현값·영상 누락 | evaluator/package 수리 후 같은 checkpoint 재평가; 새 학습 금지 |
| 특정 G의 survival <0.95 | 최대 감점 G의 낙상·회복 원인과 직접 연결되는 안정성 reward/환경 축 하나 선정 |
| survival은 통과, tracking <0.70 | 해당 G의 명령 추종 reward 축 하나 선정 |
| G7만 INCONCLUSIVE | reward 변경보다 DR 적용·실현값 로깅을 먼저 수리 |
| 전 G gate 통과, 총 자체예상 ≥75 | 추가 튜닝을 기본 중단하고 최종 문서·policy lineage 단계로 이동 |
| 전 G gate 통과, 총 자체예상 70~75 | 문서 /30 자체감사를 먼저 닫고, 개선 기대값이 큰 경우에만 screening |
| 총 자체예상 <70 또는 어떤 G라도 fail | P3/P4로 진행 |

### P3. 배포 기본 control — 조건부 조사

현재 provenance-valid 기본 checkpoint가 없다. timestamped backup은 tuned env와 연결돼 control로 사용할 수 없다.

아래 두 조건을 모두 만족할 때만 새 1,000 iter control을 만든다.

1. Pilot-01 fixed eval 결과만으로 네 변경 중 무엇을 유지할지 결정할 수 없다.
2. control 비교가 다음 screening 후보 또는 제출문 인과 설명을 실제로 바꾼다.

control은 강좌 배포값 `1.0 / 0.01 / -3.0 / -0.08 / -0.01`, 학습 seed 42, 4096 env, 1,000 iter를 사용하고 Pilot-01과 동일 evaluator로 비교한다. control 결과도 단일 seed exploratory이며 공식 결과가 아니다.

### P4. 최대 감점 축 단일변수 screening — 개선

**1차 계획 예산:** 한 번에 후보 하나, 1,000 iter. 1k에서 정보가 부족한 승자만 3k→5k로 확장한다.

첫 실험은 임의 신값보다 Pilot-01에서 한 항만 강좌 배포값으로 되돌리는 ablation을 우선한다.

| 약점 | 1차 후보 ablation | 직접 측정 | 직접 측정하지 않음 |
|---|---|---|---|
| G1/G2 선속도 tracking | `track_lin_vel_xy_exp: 1.2 → 1.0` | vx/xy tracking, 전방위 worst case | 계단·push 인과효과 |
| G2 yaw tracking | `track_ang_vel_z_exp` 단일 후보를 별도 사전등록 | yaw tracking | 선속도·험지 안정성 |
| G3/G5 발 걸림·completion | `feet_air_time: 0.2 → 0.01` | rough/stairs completion과 gait | 흔들림 penalty 단독효과 |
| G3/G4/G5 수직 튐·낙상 | `lin_vel_z_l2: -2.0 → -3.0` | vertical stability와 survival | yaw tracking |
| G4/G6 roll/pitch 붕괴 | `ang_vel_xy_l2: -0.05 → -0.08` | slope/push stability | 발 들기 인과효과 |
| 떨림·급격한 관절 명령 | `action_rate_l2` 단일 후보 | jerk/action delta와 영상 | terrain 적응 전체 |
| G7 DR 취약 | reward를 바로 바꾸지 않음 | realized DR별 survival/tracking | 공식 DR 범위 |

screening 고정값:

- 첫 비교 학습 seed 42, num_envs 4096, evaluator seed 101/202/303.
- primary: 최대 감점 scenario의 `scenario_proxy` 개선.
- side-effect: 나머지 G worst-case 비열등, 정상 네발 gait, bounding·배 끌기·정지 편법 없음.
- 한 seed 성공은 `exploratory`; 장기 승급 전 독립 학습 seed를 사전등록해 재검증한다.
- 5k 초과 전 `GO2_REWARD_EVIDENCE_MASTER.md`에 변경값·유지값·근거·G 범위·성공/실패/INCONCLUSIVE·조기중단·회수물을 기록한다.

### P5. 장기 승급 — 개선

최소 경로는 `screening 승자 5k → 10k → 15k`이며 각 지점이 독립적인 재평가점이다.

승급 조건:

1. primary scenario 개선.
2. survival과 tracking 중 반대 인수 비열등.
3. 다른 G scenario worst-case 비열등.
4. evaluator 영상 부작용 없음.
5. checkpoint·env·source·policy lineage와 bundle 검증 완료.
6. 독립 학습 seed 또는 예산상 못 한 한계를 명시.

조건 미달이면 직전 verified checkpoint로 되돌리고 다음 iter를 승인하지 않는다.

### P6. 최종 평가·제출 — 필수(제출요건)

- G1~G7 전부 seed 101/202/303으로 재평가.
- `simulation proxy /70`, `설계 의도 자체감사 /20`, `리포트 자체감사 /10`, `총 자체예상 /100` 분리.
- `policy.pt`와 선택 checkpoint actor tensor 비교, 같은 run `env.yaml`, manifest 생성.
- 기술 개선 리포트는 검증된 문제·단일 변경·결과·한계를 30~200자로 작성하고 글자수 검사.
- 대시보드 Go2 선택, 2파일·리포트 업로드, 접수 화면 증거 회수 후에만 제출 완료로 기록.

## 5. G1~G7 측정 매트릭스

| 시나리오 | 영상 | 내부 정량 | 공식 결과 | 이번 fixed eval이 직접 보장하지 않는 것 |
|---|---|---|---|---|
| G1 전진 | canonical 속도별 gait | survival, vx RMSE, tracking proxy | `OFFICIAL_RESULT_UNMEASURED` | 공식 command grid·tracking 변환 |
| G2 전방위 | 후진·좌우·대각·yaw 방향 편향 | survival, xy/yaw RMSE, worst tracking | 동일 | 공식 방향·속도 조합 |
| G3 rough | 걸림·미끄러짐·발 들기 | terrain 실현값, survival, xy RMSE | 동일 | 공식 rough generator 세기 |
| G4 ±20° | 상승·하강 자세 | 실제 경사각, survival, xy RMSE | 동일 | 공식 경사 길이·마찰 |
| G5 10/15cm 계단 | 발 걸림·배 접촉·점프 편법 | step 실현값, completion, survival, tracking | 동일 | 공식 계단 형상·상하행 구성 |
| G6 push | 충격과 회복의 인과 영상 | 힘·시각·방향, recovery, post-push tracking | 동일 | 공식 push 조건 |
| G7 DR | 조건별 gait 붕괴 | realized mass/friction/기타 DR, survival, tracking | 동일 | 공식 DR 항목·범위 |

## 6. 검증 명령

계획 반영 검증:

```powershell
python tools/validate_go2_campaign.py
git diff --check
```

G-A002 구현 후 추가 검증:

```powershell
python -m py_compile workspace/training/quadruped/go2_eval_telemetry.py workspace/training/quadruped/go2_fixed_eval_report.py tools/build_go2_eval_package.py tools/test_go2_eval_contract.py
python tools/test_go2_eval_contract.py
bash -n workspace/training/quadruped/server_run_go2_eval_v1.sh
python tools/build_go2_eval_package.py
```

## 7. 위험과 완화

| 위험 | 완화 |
|---|---|
| 내부 proxy를 공식 점수로 오인 | 모든 보고에 `INTERNAL_PROXY`, 공식 결과 별도 열 유지 |
| 69 case·영상 비용 증가 | telemetry 전수 + canonical condition 영상 + worst-case replay로 증거와 비용 분리 |
| G7 DR가 실제로 적용되지 않음 | 실현값 없으면 `INTERNAL_GATE_INCONCLUSIVE`, reward tuning 금지 |
| Pilot-01 네 변경의 인과 귀속 | 조건부 control과 one-at-a-time rollback ablation 사용 |
| policy export 직렬화 해시 변동 | 파일 해시가 아니라 actor tensor 대조로 의미 동일성 판정 |
| 휘발성 서버에서 결과 유실 | FULL bundle·SHA 로컬 도착 전 서버 종료 판정 금지 |

## 8. 계획 완료 조건

이 초기 계획은 다음 상태에서 실행계획으로서 완료된다.

1. G-A002의 입력·case 수·산출물·로컬 stop condition이 문서화됨.
2. Pilot-01 평가 결과별 다음 분기가 하나로 결정됨.
3. 다음 reward 값이 사전 측정 없이 고정되지 않음.
4. 최소 경로, 1차 계획 예산, 재평가 지점이 구분됨.
5. Go2 일정·상태·reward 원장과 모순이 없음.
