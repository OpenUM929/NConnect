# G-A044 회수 판독 — 2026-09-24

## 판정과 보존
- 등급: 조사. `INTERNAL_GATE_FAIL`; 기준선 G-A033 유지. 후보 승급·장기 학습 없음.
- 원본: `workspace/_keep/GO2_G_A044_RESULT.zip`(322,495,919 B), SHA256 `10824d2d3025769d101faf150248feccce169eed4a738b3b6439d0b68d5c20c0` 및 동명 `.sha256`. 원 ZIP/해제본은 변경하지 않는다.
- GO2_NOW의 긴 과거 A044 발행·미실행 행은 `workspace/server_returns/G-A044/GO2_NOW_PRIOR_A044_ENTRY.txt`에 그대로 보존하고 최신 회수 행으로 대체했다(진입점60줄 유지). 과거 발행 근거는 ARTIFACT_MANAGEMENT에도 남아 있다.
- 검증 기록: `workspace/server_returns/G-A044/INTEGRITY.json`, `LOCAL_VERIFY.json`, `SCREENING.json`, `VIDEO_INTEGRITY.json`, `LOCAL_SHA256SUMS.txt`. canonical training으로 병합하지 않았으며 MERGE_PLAN/RESULT에는 NO_CANONICAL_MERGE를 명시한다.
- 외부 SHA 일치, ZIP CRC 정상, 안전 경로, 내부 SHA 548항목 일치, 해제본 549파일 대조 불일치 0.
- `RUNNER_RC=0`, `COLLECTION_STATUS=FULL_69_COMPLETE`; 후보 telemetry69, 기준선 sentinel5. sentinel5 전부 저장 A033과 수치·계측 조건 일치. artifact_faults/ruler_mismatches/identity_faults 없음.
- 후보 identity: 평가 iter900 / model `1ccd7f7c156af70cb709a7740c619ffdaacdba99c436f680be0cb42f549d1cda`, env `a5aac74577bcf69dd33a76488fe26e298e13bc569652692a84c6f67ddcdee6a2`.
- evaluator `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84`; registry `8d8c34caf66813e2c18070fb9a85ed7c843c379cb3a5ffb3d0a73923b9349ba6`.

## 원 학습 report 직접 열람
`REPORT_READ_STATUS=READ_MATCHED`(학습 run 대응; 평가 checkpoint와는 구별).
세 run의 `exported/report.html` 본문을 직접 읽었다. A044는 `logs/candidate_training.log` 마지막 finalize 기록·training/env.yaml·CHECKPOINT_PIN 및 검증기의 가중치 대조와 일치한다.

| run | lin_vel_z | 학습 소요 | report 최고 reward | 마지막 terrain / 학습낙상 / std | report 모델 / 평가 모델 |
|---|---:|---|---|---|---|
| A033 | -2.0 | 58분56초 | 19.28 @651 | 4.71 /17.1% /0.613 | 700 /900 |
| A043 | -1.5 | 58분19초 | 20.41 @825 | 5.24 /18.1% /0.640 | 800 /900 |
| A044 | -1.75 | 58분21초 | 20.13 @758 | 4.92 /17.1% /0.576 | 800 /900 |

A044 학습 2026-09-23 22:55~23:53, 수집 종료 2026-09-24 00:29:23. 학습시각 분 단위 기준 전체 약94분; 접속·다운로드를 포함한 과금 시간과 잔여 팀예산은 미측정이다. report의 학습낙상은 평가 자세 생존이 아니며, reward 계수가 달라 최고 reward를 정책 성능 순위로 쓰지 않는다. report의 best800과 평가900이 다르므로 best800 성능을 이 결과로 단정하지 않는다.

## 내부 정량 — 공식 점수 아님
동일 posture_gate_v2 / 평가seed101·202·303, seed당32env. 학습seed는42 하나. 아래 시나리오 증감은 registry의 case/seed 집계 결과에 공식 가중치를 곱한 **내부 proxy**이며, 독립 학습 반복이 아니다.

| 시나리오 | A033 대비 가중 증감(/70) | 영상 행동 | 내부 정량 | 공식 결과 |
|---|---:|---|---|---|
| G1 | +0.445575 | VIDEO_UNKNOWN(신규 불필요) | 측정됨 | 미측정 |
| G2 | -0.412720 | VIDEO_UNKNOWN | 측정됨; left seed101 생존 하락0.125 | 미측정 |
| G3 | -2.821746 | VIDEO_UNKNOWN | 보호 한도 초과 | 미측정 |
| G4 | +0.534366 | VIDEO_UNKNOWN(신규 불필요) | 측정됨 | 미측정 |
| G5 | -0.044731 | VIDEO_UNKNOWN | 측정됨; 계단 screening 실패 | 미측정 |
| G6 | -1.168374 | VIDEO_UNKNOWN | 보호 한도 초과 | 미측정 |
| G7 | -0.167188 | VIDEO_UNKNOWN(신규 불필요) | 측정됨 | 미측정 |

총 내부 proxy A033 **42.528610** → A044 **38.893793/70**, **-3.634817**. A043는44.624542였다. 설계 의도/20·문서/10은 이번에 감사하지 않았으며 총 자체예상/100을 산출하지 않는다.

### 원자료에서 확인한 동작 지표
각 수는 평가3seed×32env를 합한96개체다. 계단 ≥n단은 몸통 상승 궤적 기반 계단 도달 진단이며 생존 완주/발 접촉 성공과 같은 뜻이 아니다.

| 항목 | A033 | A044 |
|---|---:|---:|
| 10cm ≥1단 | 90/96 | 87/96 |
| 10cm ≥2단 | 43/96 | 62/96 |
| 15cm ≥1단 | 4/96 | 39/96 |
| 15cm ≥2단 | 0/96 | 0/96 |
| 10cm 자세 낙상 | 34/96 | 65/96 |
| 15cm 자세 낙상 | 90/96 | 95/96 |
| 험지 전진 자세 낙상 | 4/96 | 3/96 |
| 험지 옆걸음 자세 낙상 | 59/96 | 80/96 |
| 밀침 +x/-x/+y/-y 자세 낙상 | 8/6/4/4 (각96) | 14/15/21/16 (각96) |

screening `post_a043_push4_v1` 31조건 중21조건 미달. 단순 여유0 추종 차이만 남은 경우가 아니다. 계단10cm +31낙상, 험지 옆걸음 +21낙상, 밀침 네 방향 생존 악화가 동시에 있다. 성능 미달을 노이즈로 확정하거나 사후 문턱을 완화하지 않는다.

## 사전등록 가설 대조
- G2 손실 L=0.412720은 시나리오 한도0.567 안으로 줄었다. 그러나 G2 left seed101 생존 하락0.125가 case 한도0.0625를 넘으므로 **c3 전체 충족은 아니다**.
- 비G2 순이득 B는 **-3.222098**이다. 필요했던 B≥3.097과 반대다. G2를 고치면 총점도 따라온다는 해석은 성립하지 않는다.
- -1.75에서 관측된 총점38.893793은 양 끝 -2.0(42.528610), -1.5(44.624542)보다 낮다. 이번 표본에서 '중간값→중간 성능'은 반박됐다. 모든 seed에서 비단조이거나 -1.5가 최적이라는 일반화는 불가하다.
- `lin_vel_z_l2`의 원 역할은 몸통 좌표 vz² 벌점(보관 Isaac Lab v2.3.1 mdp_rewards.py:76~80)이다. 위/아래를 가리지 않는다. 완화하면 같은 동작의 벌점은 줄지만 재학습 정책의 계단·생존 개선은 보장하지 않는다.

## 다음 튜닝 정책 분석
정본 분석: `workspace/training/quadruped/upload/plan/GO2_POST_A044_POLICY_ANALYSIS_20260924.md`.
기준선 유지, -1.875 자동 이분 탐색 금지, A044 연장/승급하지 않음. 우선순위는 A043의 큰 계단 이득이 다른 학습seed에서도 재현되는지 A033과 대칭 비교하는 정보 실험이다. 새 보상 다이얼은 대안이며 자동 실행하지 않는다.

## 한계·검토 상태
- 필수 영상 파일 회수·해시·지문·디코딩은 VIDEO_INTEGRITY.json으로 별도 확인한다. 전체 행동 영상 관찰은 아직 VIDEO_UNKNOWN이며 정량 실패 판정을 영상 성공으로 바꾸지 않는다.
- 증거 관리자/독립 검증자에게 명시 호출했으나 두 호출 모두 사용량 한도로 실패했다. 리더가 직접 원문·해시·판독기를 확인했다. 별도 INPUT_REVIEW/OUTPUT_REVIEW/PM_REVIEW는 **UNREVIEWED**이며 독립 감사 완료라고 쓰지 않는다.
- 생성 기반 데이터의 과거 표를 최신으로 가정하지 않는다. 이번 분석은 위 raw A044와 LOCAL_VERIFY/SCREENING을 우선한다. 신규 실행 패키지나 학습은 만들지 않았다.
