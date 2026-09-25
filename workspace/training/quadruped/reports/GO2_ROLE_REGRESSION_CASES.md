# Go2 역할 회귀 사례 — 실제로 저지른 실수를 시험 자료로 보존한다

> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_role_regression.py` 가 만든다.
> 증거 `reports/evidence/go2_role_regression_20260918/CASES.csv`, 시험지 `reports/evidence/go2_role_regression_20260918/fixtures/`,
> 관문 `tools/test_go2_role_regression_contract.py`.

쓰는 법:
1. **관문 회귀** — 기계로 잡히는 사례는 고장난 사양(fixture)으로 보존한다. 관문이 그것을 *실패*시키지 못하면 관문이 썩은 것이다.
2. **역할 시험** — 감사자·분석가·기획자에게 사례를 주고, `correct_verdict` 를 스스로 찾아내는지 본다. 정답을 미리 보여주지 않는다.
3. **새 실수는 지우지 않고 여기에 추가한다.** 사례를 지우는 것은 규칙 위반이다.

## 기계로 잡는 사례

| 사례 | 역할 | 무엇을 했나 | 왜 틀렸나 | 반증 원본 | 옳은 판정 | 관문 |
|---|---|---|---|---|---|---|
| C01 | 기획자 | 실행된 최신 회차(G-A038)보다 앞 번호인 미실행 초안 G-A035를 1순위로 추천했다 | 원장 시간순이 깨지고, 근거가 아니라 '이미 빌드돼 있어 편한 것'이 순서를 정했다 | `reports/runs/LEDGER.csv` | 번호가 원장 최신 실행 회차보다 크지 않으면 추천 불가 | `tools/test_go2_detectability_gate.py::test_10_a_recommendation_is_newer_than_every_executed_run` |
| C02 | 기획자 | 학습 길이(1500 iter)와 학습 seed 반복을 1·2순위 추천으로 올렸다 | 둘 다 R-6(보상 가중치만) 밖이다. 사용자에게 우리 규칙의 예외 승인을 요구한 꼴이 됐다 | `GO2_NOW.md` | R-6 밖 변경은 RECOMMENDED 불가 | `tools/test_go2_detectability_gate.py::test_11_only_a_reward_weight_change_can_be_recommended` |
| C03 | 분석가 | 커리큘럼 지연 수치를 텐서보드에서 다시 뽑아 '새로 찾았다'고 보고했다 | 같은 값이 이미 원장 TERRAIN_AT_PIN.csv 에 있었다. 원장을 읽지 않은 것이 원인이다 | `reports/runs/TERRAIN_AT_PIN.csv` | 추천 사슬은 reports/runs/ 원장을 최소 한 행 인용해야 한다 | `tools/test_go2_detectability_gate.py::test_12_a_recommendation_cites_the_run_ledger` |
| C04 | 기획자 | 반증 조건을 '평균 지형 레벨이 기준선보다 높지 않으면'으로 적었다 | 커리큘럼은 마지막 레벨에 닿은 로봇을 무작위 행으로 되돌려 평균에 상한이 걸린다 — 포화를 볼 수 없다 | `reports/evidence/go2_curriculum_source_20260918/CURRICULUM_FACTS.csv` | 평균 지형 레벨은 반증 조건으로 쓸 수 없다 | `tools/test_go2_curriculum_facts_contract.py::test_6_the_mean_level_may_not_be_used_as_a_saturation_metric` |
| C05 | 분석가 | 계산된 예측(PROBE_SITUATIONS.csv)을 측정값처럼 인용해 방향을 주장했다 | 그 칸은 비어 있다 — 빈 칸은 0이 아니라 '측정 없음'이다. 예측과 측정을 섞으면 근거가 무너진다 | `reports/evidence/go2_reward_mechanism_20260917/PROBE_SITUATIONS.csv` | 빈 칸을 근거로 방향을 주장하면 결함 | `tools/test_go2_detectability_gate.py::test_13_an_unmeasured_situation_may_not_be_quoted_as_measured` |
| C06 | 기획자 | 잡음 구간 안의 차이를 이득으로 적었다(총점 sd 1.264, 검출 한계 2.528 미만 값) | 이득 구간 밖이어야 이득이다. 안쪽 값은 seed 운과 구별되지 않는다 | `reports/runs/BASELINE_MARGIN.csv` | 검출 한계 미만의 이득 수치는 근거로 쓸 수 없다 | `tools/test_go2_detectability_gate.py::test_6_a_stated_point_gain_must_clear_the_limit` |
| C07 | 기획자 | 우리가 스스로 넓힌 규칙(R6_CHANGE_CLASSES 에 env_reward_weight 추가)으로 추천을 통과시키고, 그 해석이 승인 전이라는 사실을 사양에 적지 않았다 | 관문 통과는 규칙 준수의 증거가 아니다 — 경계를 검증한 것이 아니라 경계를 넓힌 것이다. 사양만 읽는 역할은 이 사실을 알 수 없어 우리 해석을 기성 사실로 읽는다 | `reports/GO2_OPEN_DECISIONS.md` | 권한을 넓히는 열린 결정에 기대는 추천은 그 번호를 open_decisions 에 적어야 한다 | `tools/test_go2_detectability_gate.py::test_15_a_recommendation_that_leans_on_an_open_decision_must_name_it` |
| C08 | 기획자 | 분석가 판독문 없이 원자료를 혼자 읽고 회차를 기획했다(사양에 inference.readout 이 없다) | 순서는 분석가(판독) → 기획자(값) → 감사자(결함)다. 기획자가 혼자 읽으면 R-6 같은 판단을 자기 역할 문서의 문장 하나에 기대게 되고(상황 인지 시험 Q12 실패), 사후 검증은 이미 감사자 몫이라 분석가가 감사자와 겹친다 | `reports/GO2_G_A038_READOUT.md` | 추천 사양은 기준선 회차를 판독한 문서를 지목하고, 그 판독문에 기준선 이름이 실제로 있어야 한다 | `tools/test_go2_detectability_gate.py::test_16_a_recommendation_stands_on_an_analyst_readout` |

## 사람·역할 에이전트 시험지 (기계 관문 없음)

| 사례 | 역할 | 무엇을 했나 | 왜 틀렸나 | 반증 원본 | 찾아내야 하는 것 |
|---|---|---|---|---|---|
| M01 | 분석가 | G-A038의 10cm 오르기 붕괴를 레버 효과로 단정했다 | 평가 고정 iter 900 에서 두 팔의 지형 레벨이 4.4937 대 1.9499 였다 — 커리큘럼 지연과 구별되지 않는다 | `reports/evidence/go2_g_a038_readout_20260917/CURRICULUM_LAG.csv` | 레버 효과와 학습 진도 차이를 가를 수 없다고 적어야 한다 |
| M02 | 감사자 | 받아 온 Isaac Lab 원문을 scratchpad 에만 두고 결론을 보고했다 | 저장소에 없는 파일은 아무도 재검증할 수 없다. 증거가 아니라 주장이 된다 | `reports/evidence/go2_curriculum_source_20260918/SOURCES.csv` | 원문은 URL·SHA256과 함께 저장소에 등록돼야 인용 가능하다 |
| M03 | 기획자 | 튜닝 요청에 실행 패키지 대신 검토 보고서와 '결정해 주세요' 두 줄로 답했다 | 차단 사유는 R-6 위반·테스트 실패·회수 불가 셋뿐이다. 어느 것도 아니면 패키지를 만든다 | `GO2_NOW.md` | 패키지를 만들고 관문을 돌린 뒤 보고해야 한다 |
| M04 | 감사자 | 반대 행(A018: 벌점 완화인데 정지)을 contradicting 에 넣지 않은 판단을 제작자 스스로 내렸다 | 제작자가 자기 사슬의 반대 행 유무를 스스로 판정하면 이해충돌이다 | `reports/evidence/go2_reward_mechanism_20260917/RUN_MARGIN.csv` | 감사자가 원장·분석에서 반대 행을 직접 찾아 판정해야 한다 |
| M05 | 분석가 | 배포 `_finalize.py` 가 REWARD_WEIGHTS 밖 항(extras)을 판정에서 제외한다는 반대 행을, R-6 해석을 세우면서 찾지 않았다 | 우리 해석에 불리한 배포 코드를 읽지 않고 유리한 줄(`env_cfg.py` 의 임의 이름 적용)만 인용하면 판독이 아니라 변론이다 | `workspace/training/quadruped/go2_task/_finalize.py` | 배포가 그 항을 참가자 변경으로 세지 않는다는 사실을 함께 적어야 한다 |
| M06 | 기획자 | "6개 목록 안에는 남은 레버가 없다"를 사실로 적고, 그것을 전제로 U1(R-6 확장)을 사용자에게 승인 권고했다 — 정본 원장이 그 반대를 적고 있는데도 | 규칙을 넓히자는 제안의 전제가 원장 한 줄로 반증된다. 유효 기각 2건을 6항 전체의 소진으로 확대했다. 양방향 유효 기각으로 닫힌 항은 feet_air_time 하나뿐이다 | `GO2_REWARD_EVIDENCE_MASTER.md` | §1-a 가 lin_vel_z_l2·flat_orientation_l2 를 '미탐색', ang_vel_xy_l2 완화와 action_rate_l2 강화를 '미탐색'으로 적는 한 소진을 주장할 수 없다 (관문 tools/test_go2_canonical_consistency.py::test_1e_no_doc_may_claim_the_deployed_six_are_exhausted) |

