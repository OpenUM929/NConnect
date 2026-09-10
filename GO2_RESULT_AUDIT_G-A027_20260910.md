# G-A027 독립 결과 감사 및 H1 기반 보정 병기 — 2026-09-10

## 0. 예선 기준 현재 위치
- [예선 목표] Go2 시뮬레이션 70점 축의 정책 비교, H1 공식 결과로 내부 예측 오차를 드러내고 설계·리포트의 과장 방지.
- [현재 단계] 단계 3/6 — 환경 적응 게이트. G3~G7 내부 기준 미달(근거 C.scenarios, S.arms.a017.failed_scenarios).
- [확보] 기존 A017/Pilot 재평가 69 case씩, 원시 검증·승인 정책 대응, 후보 영상 7개. 새 학습 아님(V.arms, P, R.RUNNER_STATUS).
- [미확보] Go2 공식 결과, H1 공식 제출본 대응, G5 내려가기 영상, 독립 학습 seed 일반화.
- [이번 테스트] 기존/보정 점수를 둘 다 보존하며 A017의 상대 개선과 절대 안정성 미달을 구분한다.
- [흐름] 회수·정합성 검증 → **환경 적응 미달** → 보완 평가 후 단일변수 계획 → 계속 미달 시 정책 유지·승급 보류 → 최종 제출 판단.
- [지금 할 일] 추가 학습은 실행하지 않는다. H1 공식 제출본 대응 질문에 자료가 있으면 제공하고, 로컬 보고서를 확인한다.
- [보장하지 않음] 내부 점수·H1 이전 보정·단일 학습 seed로 공식 점수나 통과를 보장하지 않는다.

## 1. 입력 고정·검증 범위·증거 계층

아래 약칭은 모두 파일 경로이며 뒤의 점 표기는 JSON 필드다.

| 약칭 | 경로 |
|---|---|
| A | `workspace/server_returns/G-A027/audit_20260910/` |
| R | `workspace/server_returns/G-A027/received/go2_a017_full_suite/` |
| U | `workspace/server_returns/G-A027/approved/go2_a017_full_suite/` |
| I | A/`INPUT_INVENTORY.json` |
| M | A/`MANIFEST_VERIFICATION.json` |
| P | A/`POLICY_FILE_COMPARISON.json` |
| V | A/`HARVEST_VERIFICATION.json` |
| S | A/`INDEPENDENT_SCORE_RECOMPUTATION.json` |
| C | A/`COMPARISON.json` |
| B | A/`H1_RATIO_SENSITIVITY.json` |
| W | A/`video_review/video_observations.json` |
| H | `workspace/calibration/h1_official_20260910/H1_OFFICIAL_CALIBRATION.json` |

- **ARTIFACT_VERIFIED**: 반환 ZIP SHA `5108b047175c6fc0cb0982b1434c686e413bac5d75469ae9c71cb2d17d144ace`; 승인 ZIP SHA `e7749d0f6adc4abb2b32fca9393523b8059b8954cec068ba2c7c2930af0a7d15`. 승인값은 회수물의 주장이 아니라 사전 배포 `upload/G-A027/current/UPLOAD_MANIFEST.json:upload_files[0].sha256`에서 가져왔다(I.archives).
- ZIP CRC·중복/경로 탈출/링크 검사, 내부 manifest **882/882**, 승인 대비 model/env **4/4** 일치(M.checked, M.failed=[], P). `training` 병합·원장 덮어쓰기 없음.
- **INTERNAL_MEASUREMENT_OK**: 두 정책 각각 **69/69**, 32 env × 1,000 step, dt0.02, seed101/202/303. G7은 case명과 대응 seed만 사용한다(V.run_plan, V.arms[].cases[].csv; U.go2_self_eval_registry.json).
- 원시 행과 summary 재계산, 결측/비유한/중복/누락/시간축/자세 판정·도구 지문 검사에서 이름 붙은 결함 **0건**(V.arms[].faults, invalid_cases, instrument_mismatches). 도구의 `INTERNAL_GATE_PASS`는 **측정 유효성 통과**이며 성능 통과가 아니다.
- A017 model `0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4`; Pilot model `c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d`(V.run_plan.models, P). 본 감사는 SHA로 정확한 checkpoint를 고정하며, 학습 횟수나 사양 JSON의 max_iterations를 실제 checkpoint iter로 바꾸지 않는다.
- evaluator `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84`, schema6/posture_gate_v2/engine1.5.4, rc0, `TRAINING=none`(V.run_plan.evaluator_sha256; R/`RUNNER_STATUS.txt`). 이번은 재평가이지 새 튜닝 학습 완료가 아니다.
- VIDEO 계층은 아래 표와 W에 별도 기록. Go2 **OFFICIAL_RESULT 미측정**. 사용자가 준 57.45점은 H1 공식 결과이며 Go2로 전용하지 않는다(H.evidence).

## 2. 핵심 발견과 증거 강도

1. **높음·관찰/계산:** A017 기존 proxy **39.76495/70**, Pilot **33.67132/70**, **+6.09363**. 양쪽 동일 계측 계약에서 비교 가능하다(V, S, C.delta_points).
2. **높음·계산:** 총점 개선과 안전성은 다르다. A017은 **25/69**, Pilot은 **24/69** case가 생존0.95 또는 추종0.70 미달. A017은 같은 case 대비 생존이 0.10 넘게 감소한 case도 **6개**다(C.floor_failures, survival_regressions_over_0_1). 최저 곱 case 하나만 보고 안전하다고 결론 내리지 않는다.
3. **높음·계산:** A017 최대 손실은 **G5 10.50점**, 다음은 **G3 9.03점**. 계단 내려가기의 자세 생존이 가장 먼저 해결할 인수다. A017 `stairs_15_down` 세 seed 생존이 모두0, `stairs_10_down@202`도0(S.arms.a017.cases). 원인이 어떤 reward인지는 이 결과로 식별되지 않는다.
4. **높음·계산 / 원인 해석은 미확인:** G4는 tracking 개선에도 생존이 악화됐다. 같은 `slope_plus_20` seed101/202/303에서 생존 delta는 −0.21875/−0.25/−0.125다. 곱은 각각 +0.01587/−0.05361/+0.11374로 섞인다(C.case_deltas). “움직이기 시작했기 때문에 넘어졌다”는 인과관계는 확인되지 않았다.
5. **계산은 높음·예측 일반화는 미확인:** H1 Run06 자체65.73163과 공식57.45는 동일 제출본이라는 조건에서 **8.28163점 차이**다. 관측 비율0.8740084로 Go2에 별도 보정 참고열을 추가했지만 검증된 Go2 예측식은 아니다(H.comparison_eligibility, H.totals, B).

## 3. G1~G7 기존 점수 비교

점수는 `70 × weight × min_case(survival × tracking)`이다. S의 local scorer SHA와 path를 함께 보존했다. 기존 scorer를 수정하지 않고 재계산했다(S.scorer_path, scorer_sha256).

| 시나리오 | 배점 | Pilot 기존 | A017 기존 | 변화 | A017 손실 | 후보 영상 | 내부 정량 | 공식 결과 |
|---|---:|---:|---:|---:|---:|---|---|---|
| G1 전진 | 10.5 | 9.37 | 9.39 | +0.02 | 1.11 | VIDEO_OBSERVED | 양쪽 기준 충족 | 미측정 |
| G2 전방위 | 10.5 | 7.90 | 9.37 | +1.47 | 1.13 | VIDEO_OBSERVED | 양쪽 기준 충족 | 미측정 |
| G3 거친 지형 | 14 | 1.03 | 4.97 | +3.94 | 9.03 | VIDEO_OBSERVED | 양쪽 미달 | 미측정 |
| G4 ±20° 경사 | 10.5 | 5.55 | 5.36 | −0.19 | 5.14 | VIDEO_OBSERVED | 양쪽 미달 | 미측정 |
| G5 계단 | 10.5 | 0.00 | 0.00 | 0.00 | 10.50 | VIDEO_UNKNOWN | 양쪽 미달 | 미측정 |
| G6 밀침 | 7 | 6.55 | 6.10 | −0.45 | 0.90 | VIDEO_UNKNOWN | 후보 미달·기준 충족 | 미측정 |
| G7 DR | 7 | 3.27 | 4.57 | +1.30 | 2.43 | VIDEO_UNKNOWN | 양쪽 미달 | 미측정 |
| **합계** | **70** | **33.67** | **39.76** | **+6.09** | **30.24** | W 참조 | **양쪽 INTERNAL_GATE_FAIL(성능)** | 미측정 |

근거: C.scenarios, S.arms.*.scenarios, W.records. 개별 반올림 합과 전체 합에는 반올림 차이가 있을 수 있다. VIDEO_OBSERVED는 표본 프레임에서 이동·자세를 관찰했다는 뜻이지 공식 시나리오 완수 판정이 아니다. 영상은 후보만 7개이며 Pilot 영상7개가 있는 것으로 쓰지 않는다. G5 영상은 `stairs_15_up` 한 개다. 내려가기 영상은 없다(W.records, I.archives.return.members).

### 두 인수와 모든 case 최저값

아래 `곱 인수`는 점수가 가장 낮은 **동일 case**의 생존/추종이다. `전체 최저` 두 값은 서로 다른 case일 수 있으며 둘을 곱해 점수를 만들지 않는다. 미달 case·seed 전량은 C.floor_failures, 최저값 위치는 S.arms.*.scenarios.*.{survival_floor_case,tracking_floor_case,worst_case}에 있다.

| G | Pilot 곱 인수 S/T | 후보 곱 인수 S/T | Pilot 전체 최저 S/T | 후보 전체 최저 S/T |
|---|---|---|---|---|
| G1 | 1.0000 / .8925 | 1.0000 / .8944 | 1.0000 / .8925 | 1.0000 / .8944 |
| G2 | 1.0000 / .7521 | 1.0000 / .8921 | 1.0000 / .7521 | 1.0000 / .8921 |
| G3 | .0938 / .7828 | .4688 / .7574 | .0938 / .5904 | .4688 / .6282 |
| G4 | 1.0000 / .5288 | .7500 / .6810 | .9688 / .5288 | .7500 / .6810 |
| G5 | .0000 / .1347 | .0000 / .1614 | .0000 / .1339 | .0000 / .1206 |
| G6 | .9688 / .9661 | .9063 / .9616 | .9688 / .9661 | .9063 / .9616 |
| G7 | .8438 / .5540 | .9063 / .7209 | .8438 / .5540 | .9063 / .6573 |

## 4. 기존·변경 점수 모두 보존

사용자 명시 결정: **기존 채점을 없애지 않는다. 두 채점 결과를 모두 제공한다.** 새 보고 계약은 `SCORING_CALIBRATION_POLICY_20260910.md`다. H1 시나리오별 기존/보정/공식 비교는 `H1_OFFICIAL_CALIBRATION_20260910.md`에 별도로 보존한다.

| 정책 | 기존 raw /70 | 변경: 보정 참고 /70 | 공식 /70 |
|---|---:|---:|---|
| Pilot | 33.67132 | 29.42901 | 미측정 |
| A017 | 39.76495 | 34.75490 | 미측정 |
| 후보−기준 | +6.09363 | +5.32588 | 미측정 |

변경 열은 **H1_RATIO_STRESS_SENSITIVITY = raw ×0.8740084014**. 기체 간 검증 없는 이전이므로 예상 공식 점수·신뢰구간·하한으로 사용하지 않는다. G1~G7 각각 기존/변경/변화량은 B.scenarios에 있다. 배점·기존 raw·안전 임계값은 불변이며 후보 승급에는 사용하지 않는다(B.validated_prediction=false, used_for_decisions=false, raw_gates_changed=false).

## 5. 과거 판단 유지·철회·미확인

- **유지:** 이전 코드 감사 종료 경계. 새 광범위 감사 라운드를 시작하지 않았다(`GO2_REAUDIT_ROUND8_RESPONSE_260909.md:§5`). 실제 회수 자료의 기존 검증만 실행했다.
- **유지:** 현재 회수의 총점 상대 개선, 양쪽 절대 성능 미달. 독립 점수 산출 저장 후 확인한 `_keep/go2_a017_full_suite/reports/TIER1_DECISION.json`의 두 총점·delta와 일치한다. 이 로컬 파생 보고서는 반환 ZIP 원본 구성원이 아니므로 원자료와 구분한다(I.archives.return.members).
- **제한:** 기존 Q1의 `INTERNAL_EARLY_KILL_PASS`를 모든 case 생존 비열등으로 확대하지 않는다. 별도 감사에서는 같은 case 생존 회귀 6개를 보고한다(C.survival_regressions_over_0_1). 기존 Q1 정의를 소급 변경하거나 삭제하지 않는다.
- **미확인으로 정정:** `GO2_PROJECT_STATE.md:G-F247`의 G4 생존 하락 원인 단정, G-F248의 “올라가는 것은 된다”라는 전범위 행동 단정. 수치상 계단 상승 일부 생존이 있어도 .95 기준에는 미달하며 영상에서 직접 등반을 확정하지 못했다(S, W).
- **정정:** 같은 원장 최신 NEXT의 “G5 영상7건”이 아니라 **전체 시나리오 영상7건 중 G5 상승1건**이다. 내려가기 원인 판독은 추가 영상이 필요하다(I, W).
- **재사용 금지:** 과거 무효 evaluator 비교에 의한 reward 최종 기각·인과결론은 이번 유효 결과 대신 사용하지 않는다. 단일 학습 seed 정책쌍 재평가이므로 reward 최적값·수렴을 확정하지 않는다.

## 6. 다음 행동과 사전등록

**선택: 후보·기준 모두 보존 + 조건부 추가 평가. 새 reward·장기학습은 실행하지 않는다.** 최대 손실 G5의 약한 인수는 생존이지만, 넘어지는 동작과 위치가 없어서 단일 reward 값을 고르는 단계까지는 근거가 부족하다(C, W).

| 항목 | 사전등록 |
|---|---|
| 등급 | 조사 — G5 내려가기·G4 생존 회귀 행동 원인 확인 |
| 기준 정책 | Pilot SHA c4d78a…af8d; 비교 후보 A017 SHA0563de…95a4(P에 전체값) |
| 변경값 | **reward 변경 없음**. 기존 후보1.4/기준1.2를 유지. 다음 단일변수 학습값은 원인 관찰 후 별도 등록하며 지금 임의값을 만들지 않는다 |
| 유지 조건 | 승인 evaluator·registry·정책·env·32env·1,000step·seed101/202/303, 공식 학습 경로는 변경하지 않음(V.run_plan) |
| 직접 측정 | G5 stairs_10_down, stairs_15_down 양쪽 정책 각3seed; G4 slope_plus_20 양쪽 각3seed. 총18 telemetry case. 이 보완만으로 G1/G2/G3/G6/G7 또는 전체 점수를 새로 확정하지 않음 |
| 영상 | 위 각 case/seed/정책 대응18개·20초, 정책/명령/지형 식별과 출발~종료 연속 관찰. 기존4env 영상이32env 정량과 다른 조건임을 분리 기록 |
| 성공 | 원시 유효성 확보, 하강 중 주저앉음/전도/정지 위치를 판독하고 두 정책 차이를 기술할 수 있음. 성능 개선 성공이라는 뜻이 아님 |
| 실패·불확정 | 원시 결함은 측정 불완전; 행동 미판독은 VIDEO_UNKNOWN. 정책 실패로 치환하지 않음 |
| 조기중단·회수 | 첫 paired case의 identity/자세/time축 불일치면 추가 실행 중단하고 로그·실패자료 회수. 회수물은 별도 작업ID로 등록·격리하고 SHA/manifest/telemetry/video 확보 |
| 시간·예산 | 현 GPU 잔량·확인 시각 미측정. 지금 GPU0, 로컬 분석만. 다음 접속 시 실측 잔량과 첫 paired case 벽시계 비용을 사용해 회수 여유 포함 예산 확정; 과거1h45 등을 현재 잔량으로 쓰지 않음 |
| 실패 시 대안 | 기존 정책·39.76/33.67 결과 유지, 영상 미확보 표시. 근거 없이 학습으로 우회하지 않음 |

위는 다음 평가의 조건부 사전등록이며 서버 명령/package 준비 완료 선언이 아니다. 사용자 역할은 서버 실행, 로컬 작업자는 실행 전 package·문법·다운로드 경로를 준비한다. 이번 감사의 실행 가능한 로컬 후속은 기존/보정 보고 도구 재실행이며, 서버를 자동 재가동하지 않는다.

## 7. 미확인 사항과 회수 방법

- H1 동일 제출본: 제출 라운드·업로드 policy 식별자/원본으로 Run06 대응. 이미 사용자에게 남은 외부 사실만 질문했다. 확인 전 계수는 조건부(H.comparison_eligibility).
- Go2 보정의 정확도: 같은 Go2 정책의 공식 결과가 있어야 raw와 보정 오차를 비교 가능. 그 전에는 두 점수를 표시하되 공식 예측으로 승격하지 않음(B.warning).
- 영상: G5 하강 원인, G6 충돌·회복 연속 장면, G7 DR 설정은 W의 미확인 범위를 유지. DR 설정 근거는 영상이 아니라 metadata 계약으로 확인한다.
- 원 학습 제출 무결성: 이번 재평가의 정책 파일 대응을 확인했을 뿐, 기존 정책을 만든 서버 학습 이력 전체를 다시 감사하지 않았다. 현 학습 경로를 수정하거나 재학습하지 않았다.
- 서버 현재 가동/잔량: 미확인. 회수파일만으로 서버 현재 상태를 추정하지 않으며, 이번 보고는 서버 종료 승인 요청에 대한 답변이 아니다.

## 8. 실행 검증·종료 코드·한계

| 실행 | 결과 |
|---|---|
| Python zipfile SHA/CRC·안전 경로·중복·링크 검사 후 별도 디렉터리 추출 | exit0; I |
| SHA256SUMS 내부 파일 전량 hashlib 대조 | exit0; M 882/882 |
| 승인 model/env와 반환 파일 hashlib 대조 | exit0; P 4/4 |
| `python tools/verify_go2_a027_harvest.py --harvest .../received/go2_a017_full_suite --registry .../approved/go2_a017_full_suite/go2_self_eval_registry.json --runner .../approved/go2_a017_full_suite/server_run_go2_a017_full_suite.sh --evaluator .../approved/go2_a017_full_suite/a017/go2_eval_telemetry.py --expect-env-sha a017=41050c084cd05e7646ce2cb4ac34e06a6870fb7a65b4f767c5714611b9a801ff --expect-env-sha pilot=f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d --out .../audit_20260910/HARVEST_VERIFICATION.json` | exit0; V. `...`는 workspace/server_returns/G-A027 |
| 기존 `go2_fixed_eval_report.build_policy`로 양쪽 재계산 | exit0; S. 업로드 ZIP에는 scorer가 없어 로컬 scorer를 사용하고 SHA 보존 |
| `python -m unittest tools/test_go2_calibration_sensitivity.py` | exit0; 3 tests |
| `python tools/build_go2_calibration_sensitivity.py --comparison workspace/server_returns/G-A027/audit_20260910/COMPARISON.json --calibration workspace/calibration/h1_official_20260910/H1_OFFICIAL_CALIBRATION.json --out workspace/server_returns/G-A027/audit_20260910/H1_RATIO_SENSITIVITY.json` | exit0; B |

초기 경로 탐색에서 ZIP에 없는 scorer/report 경로 읽기는 exit1이었다. 해당 경로를 근거로 사용하지 않았고 실제 로컬 scorer와 분리된 파생 보고서 경로를 확인했다. 첫 policy glob은0건이어서 인증에 사용하지 않았고 정확한 파일명으로4건 대조를 재실행했다. 광범위 코드 재감사·공식 evaluator 역공학·새 서버 실험·새 학습·공식 보정 일반화 검증은 수행하지 않았다.

**종료:** 이번 결과의 측정 유효성·상대 개선·절대 미달·최대 손실·구체적 다음 공백을 확인했다. 기존/보정 두 점수 모두 저장했다. 예측 정밀도가 개선됐다는 주장은 추가 동일 정책 대응과 외부 표본 검증 전까지 보류한다.

## 9. 사용자 요청 확정 — 시나리오별 기존/보정 동시 표시 (2026-09-11 마감)

| 시나리오 | Pilot 기존 | Pilot 보정참고 | A017 기존 | A017 보정참고 | 기존 delta | 보정 delta |
|---|---:|---:|---:|---:|---:|---:|
| G1 | 9.371 | 8.191 | 9.391 | 8.208 | +0.019 | +0.017 |
| G2 | 7.897 | 6.902 | 9.367 | 8.187 | +1.471 | +1.285 |
| G3 | 1.027 | 0.898 | 4.970 | 4.344 | +3.943 | +3.446 |
| G4 | 5.552 | 4.853 | 5.363 | 4.687 | -0.189 | -0.165 |
| G5 | 0.000 | 0.000 | 0.000 | 0.000 | +0.000 | +0.000 |
| G6 | 6.552 | 5.726 | 6.100 | 5.332 | -0.451 | -0.394 |
| G7 | 3.272 | 2.860 | 4.573 | 3.997 | +1.301 | +1.137 |

근거: B.scenarios. 이 보정열은 공식점수가 아니며 기존채점을 대체하지 않는다.

최종 검증: H14건+Go2보정3건 총7개 단위테스트 exit0; 신규4개 Python 파일 py_compile exit0; 관련 tracked 원장 git diff --check exit0. LF/CRLF 정규화 경고만 있으며 검증오류는 없었다. 프레임 표본관찰 한계와 공식예측 일반화 공백은 유지한다.
