# NConnect 파일·artifact 운영 정본

## G-A045-A046-PACKAGE-20260924 — 학습 seed 43 대칭 쌍(자를 재는 회차) 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v2**. 서버 실행·회수·병합은 **없다** — 실행은 사용자가 한다.
- A044 회수로 `lin_vel_z_l2` 는 걷는 기준선 위에서 세 점이 측정됐는데, **계수기가 서로 다른 말을 한다** — 계단에 오른 로봇 수는 단조로 늘고(10cm ≥2단 `43→62→94`/96, 15cm ≥1단 `4→39→88`/96) 자세 낙상 수는 가운데 값에서만 솟는다(계단10cm `34→65→17`, 험지 옆걸음 `59→80→24`, 밀침 4방향 `22→66→10`/384). 총점 비단조(`42.53→38.89→44.62`)는 낙상 쪽을 따라간 결과다. 이것이 다이얼의 성질인지 학습 경로 갈라짐인지는 **학습 seed 대조군이 0건**이라 가를 수 없고, 회차 간 총점 차이(`−3.63`·`+2.10`)는 승급 문턱(`+2.53`)과 같은 자리에 있다. 그래서 이 회차는 값을 찾지 않고 **자를 잰다**: G-A045 는 G-A033 의 보상 파일 그대로를 학습 seed 43 으로 다시 학습하고(보상 diff 0줄), G-A046 은 같은 seed 위에서 `lin_vel_z_l2 −1.5`(G-A043 과 같은 값)를 걸어 대칭 쌍을 만든다. **판정 문턱·평가 조건·screening 판은 하나도 바꾸지 않았다** — 자를 재는 회차가 자를 바꾸면 읽을 수 없다. **두 팔 다 승급 대상이 아니다**(`promotion: forbidden_not_a_reward_change`): 학습 seed 는 보상 가중치가 아니다. R-6 해석은 열린 결정 **U2-SEED-REPLICATE-20260918** 이고 사용자 결정 대기다 — 사용자가 「실행도 하지 말라」로 닫으면 이 패키지는 폐기한다.
- 계획 `workspace/training/quadruped/upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md`, 기준 변경 `workspace/training/quadruped/reports/GO2_A045_CRITERIA_CHANGES_20260924.md`, 사양 `config/experiments/G_A045_seed43_a033_rewards.json`·`G_A046_seed43_lin_vel_z_m15.json`, 발행 도구 `tools/build_go2_seed_pair_package.py`.
- 발행: `upload/G-A045_A046/current/GO2_G_A045_A046_seed43_pair_full69_v8.zip` SHA256 `02c1b36c59e9a5c499b43c46776d69bce7e4d74f63c740ca8719e75d9c3df151` (release `20260924_seed43_pair_full69_v8`). v1 은 같은 날 만든 **로컬 초안**이고 발행된 적이 없다 — 러너 머리말에 열린 결정 번호를 적기 전 바이트다. history 의 바이트는 고치지 않으므로 덮어쓰지 않고 다음 판으로 냈다. 팔 ZIP 둘은 `GO2_G_A045_seed43_a033_rewards_full69_v7.zip` `a6a20361…` · `GO2_G_A046_seed43_lin_vel_z_m15_full69_v7.zip` `4be46723…` 다 — 사양의 「학습 18회」를 원장에서 다시 센 수로 고치면서 팔 바이트도 바뀌어 v2 로 냈다. 쌍 ZIP 안 `arms/` 에 들어 있고 따로 올리지 않는다.
- 러너 `workspace/training/quadruped/server_run_go2_full69_campaign.sh`(신규): 기존 campaign 러너에서 **게이트만 뺀** 판이고 공유 헬퍼 11개는 바이트가 같다. 팔마다 전수 69 로 직행하고, 팔이 팔을 막지 않으며, 재진입은 이름이 아니라 `$SELF` 경로로 한다(결함 C-14 의 교훈). 기존 campaign 발행 경로는 한 글자도 건드리지 않았다.
- v4 사유: **독립 검토가 사전등록한 「읽는 법」 의 오류 넷을 잡았다**(결함 C-26). ① 계단 재현을 B 의 절대값만으로 판정한 것(A 가 70 인데 B 가 50 이면 오히려 나빠진 것이다) — 이제 행동 수준(절대값)과 보상 효과(**같은 seed 의 B−A**)를 따로 읽는다. ② 작은 seed 차이를 「A044 의 비단조는 다이얼 탓」의 근거로 쓴 것 — 이 쌍은 `−1.75` 를 반복하지 않으므로 그 원인은 **미확정**이고, 보상 효과와 학습 경로는 배타적이지도 않다. ③ 큰 차이에서 승급 규칙 폐기·장기 학습 전환을 적은 것 — 한 표본은 그 결론을 지지하지 않고 기존 `INTERNAL_GATE_FAIL` 관측을 무효로 만들지도 않는다. ④ R-6 을 닫힌 것처럼 적은 것 — CLI 인자 전달은 규정 허용의 증거가 아니고, 반대로 공식 제출 불가도 단정하지 않는다(우리 금지는 내부 보수 규칙이며 열린 결정 U2 는 운영진 답변·공식 근거로 닫는 것이 안전하다). **판정 문턱·평가 조건·러너·수집 계약은 하나도 바뀌지 않았다** — 바뀐 것은 읽는 법이다. 같은 판에서 총점이 어디로 갔는지를 산문 대신 같은 채점기의 반사실로 쟀다(`tools/go2_score_decomposition.py` → `SCORE_SPLIT.csv`: A044 는 생존 `−4.62775` · 추종 `+0.99438` · 교차항 `−0.00144`). 관문 `ReviewCorrectionsTest` 7 검사가 네 정정을 고정한다.
- v5 사유: **검토 3차** — 점수 분해를 「기여 분해」로 고쳐 적었다. 세 항의 합이 총점 차이와 같은 것은 교차항을 잔차로 두기 때문이라 **검증이 아니라 정의**이고, 읽을 것은 교차항의 크기다(A044 `0.04%` 대 A043 `79.89%` — 후자는 두 인수로 나누는 것 자체가 약하다는 뜻이다). 어느 쪽이든 **「보상 변경이 낙상을 일으켰다」는 인과는 나오지 않는다.** 값·문턱·러너·수집 계약은 그대로이고 사양 산문과 안내문만 바뀐다. 관문 `ReviewCorrectionsTest::test_32` 가 고정한다.
- v6 사유: **검토 4차** — 잔차 비율의 **분모**를 갈라 적었다. `|교차항|/|순변화|` 는 큰 반대 몫들이 상쇄되면 튀므로 **인과적 기여율도 설명 실패율도 아니다**. 크기합을 분모로 한 값을 함께 싣는다(A044 `0.04%`/`0.03%`, A043 `79.89%`/`30.75%`, A043 순변화는 크기합의 `38.49%`). 두 수가 벌어지는 것 자체가 「상쇄가 심하다」는 신호다. 값·문턱·러너·수집 계약 불변.
- v7 사유: **검토 5차** — ① 「최악이라도 GPU 시간만 잃는다」로 **손실 상한을 긋지 않는다**. G-A033 산출물이 보존된다는 사실과 팀 제출 자격에 영향이 없다는 판단은 별개이고, 서버 실행 자체가 허용되지 않는 행위로 판정될 경우 **제재 범위는 미확정**이다(위반 확정도 아니다 — 허용도 손실 상한도 확정할 수 없다는 뜻). **사용자의 실행 결정만으로 U2 가 닫히지도 않는다.** ② A043 기각을 G2 하나로 좁히지 않는다 — 총점 `+2.09593`이 `+2.53`에 미달(기준 2)했고 비열등 4건(G2 proxy `−0.44161`, `combined_yaw_right` 3 seed 생존)과 screening 3건(`rough_forward`·`push_pos_x`·`push_neg_x`)이 함께 있었다. **유망한 신호와 채택 자격은 분리해 읽는다.** 관문 `test_33`·`test_34` 가 고정한다.
- 로컬 검증: 관문 `tools/test_go2_g_a045_package_contract.py` **31검사 통과**(러너 이름 붙인 차이·공유 헬퍼 바이트 동일·재진입 실행·문턱 불변·승급 금지·영상 짝·ZIP manifest·재빌드 결정성·안내문의 실패 경로 진술). 네 관문은 **반대 방향으로도 확인했다** — 이름 없는 러너 편집, 문턱 한 개 이동, 승급 금지 삭제, 자 팔에 보상 변경을 심으면 각각 떨어진다.
- **느린 관문은 옵트인이다(2026-09-24).** `tools/test_go2_g_a044_package_contract.py` 는 회수물이 생긴 뒤 69 case 의 `steps.csv` 를 통째로 읽게 되어 한 번에 **38분**이 걸렸다 — 그렇게 느린 관문은 일상 스윕에서 돌지 않고, 돌지 않는 관문은 없는 것과 같다. 이제 전수 판독 8 검사는 `GO2_SLOW_TESTS=1` 에서만 돌고(기본은 이유를 말하며 건너뜀), 돌 때는 스스로 시간을 재 예산(`GO2_SLOW_BUDGET_S`, 기본 3000초)을 넘기면 **실패**한다. 같은 수확물을 두 번 읽던 자리는 캐시로 묶었다. **범위를 갈라 적는다**: 같은 범위(34 검사 전부 실행)는 `2288초 → 857초`(중복 읽기 캐시와 배선 검사의 I/O 제거), 기본 경로는 `92초`이며 그때는 **34 중 8 건너뜀**이다 — `38분 → 92초` 는 범위가 다른 두 수를 나란히 놓은 것이라 쓰지 않는다. **회차를 발행하기 전에는 `GO2_SLOW_TESTS=1` 로 한 번 돌린다**(실측 857초) — 건너뛴 관문이 조용히 사라지지 않는지는 `SlowGateIsWiredTest` 가 지킨다.
- **실행 규칙 두 가지를 실측으로 확인했다(2026-09-24).** ① `timeout N cmd | tail` 은 timeout 의 종료 코드를 **가린다**(실측: 파이프 있으면 exit 0, 없으면 124) — 그래서 파이프를 쓸 때는 `set -o pipefail` 을 먼저 켜거나 파일로 받고 `$?` 를 본다. ② `timeout` 은 이 환경에서 손자 프로세스까지 정리했다(1회 실측: 자식을 띄운 python 을 5초에 끊고 2초 뒤 잔존 python 0개). 다만 **테스트 안의 경과시간 검사는 멈춘 작업을 끊지 못한다** — 그것은 끝난 뒤에야 실패를 알리는 사후 신호이고, 실제로 끊는 것은 바깥 `timeout` 과 `subprocess.run(timeout=...)` 이다.
- **로컬 검증 완료는 성능 판정이 아니다.** 서버 실행·GPU 소비 **0**, 잔여 예산 변동 없음.

## G-A044-LOCAL-REVIEW-20260924 — 결과 보존·검증·다음 튜닝 분석
- 상태: PLANNED → RUNNING → RECEIVED → VERIFIED. SHA `10824d2d3025769d101faf150248feccce169eed4a738b3b6439d0b68d5c20c0`; CRC·내부548 SHA·해제본549파일 일치. canonical 병합은 하지 않아 MERGED로 표시하지 않는다.
- 원본은 덮어쓰지 않고 보존하며 `workspace/server_returns/G-A044/`에 검증 기록을 격리한다. 서버 실행 사실은 회수 로그로 확인하며 신규 서버 실행은 하지 않는다.
- 회수 완결: report 원본·학습로그/env·평가900 checkpoint·69case·sentinel5·신규 영상14(전편499프레임 디코딩/지문 일치)·재사용6 SHA/지문 확인. 서버 종료 가능, 추가 필수 회수 없음. VIDEO_UNKNOWN(행동 전체 관찰 미완료), OFFICIAL_RESULT_UNMEASURED.
- 내부 정량 INTERNAL_GATE_FAIL: 42.528610→38.893793/70(-3.634817), A033 유지. 판독문 `workspace/training/quadruped/reports/GO2_G_A044_READOUT.md`, 다음 정책 분석 `workspace/training/quadruped/upload/plan/GO2_POST_A044_POLICY_ANALYSIS_20260924.md`. 분석/보고 기록은 별도 보존하며 원본 lifecycle의 병합을 가장하지 않는다.

## G-A044-PACKAGE-20260922 — A033 위 `lin_vel_z_l2 −2.0→−1.75` 전수 수집 패키지 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v9 · 사용자 실행 승인(2026-09-23)**. 회수·병합은 아직 **없다** — 서버 실행은 사용자가 하고, 이 줄은 승인 기록이다.
- **2026-09-23 사용자 결정 (G-D-A044-RUN-20260923): v9 로 진행한다.** 사용자가 ZIP SHA·CRC·내부 manifest 32/32 일치, v8→v9 변경이 사양의 발행 식별자와 manifest 뿐(러너·보상·판정 코드 불변), C-23 관문 4개와 C-24 관문 1개 5/5 성공을 직접 확인했다. **C-17 과 C-2 는 이번 실행 전에 고치지 않고 별도 유지보수로 둔다.** 서버 실행은 사용자가 한다 — 이 줄은 승인 기록이지 실행 기록이 아니다. 실행 뒤의 회수 완결 판정은 안내문 §5 의 다섯 줄과 §4 의 세 상태로 내린다.
- 계획 근거: `workspace/training/quadruped/upload/plan/GO2_POST_A043_PLAN_20260922.md` §1~§6·§9. 사양 `workspace/training/quadruped/config/experiments/G_A044_a033_lin_vel_z_m175.json`.
- 발행: `upload/G-A044/current/GO2_G_A044_a033_lin_vel_z_m175_full69_v9.zip` SHA256 `2e12a5667f9ef93015dfcc7247bd10f5b83fcc07473c1ec29f4bca6d18f77ce6`(release `20260922_a033_lin_vel_z_m175_full69_v9`). 대체된 v2 `b3321fb3…acedc`·v1 `f588d9cd…06c09`은 history 보존, 둘 다 서버에 올린 적 없음. v2 사유: v1 안내문이 소요 시간 근거를 영어 원문 그대로 실어 읽히지 않았다. v3 사유: 관문 `test_go2_detectability_gate::test_14`가 사양 산문의 맨 이름 `FORECAST_CHECK.csv`(저장소에 같은 이름 2개)를 잡아 네 자리를 전체 경로로 고쳤다. v4 사유: **v3 는 서버에서 아무것도 돌지 않았을 것이다** — 팔 러너가 tmux 안에서 자기 자신을 다시 부를 때 패키지에 없는 조상 파일 이름(`server_run_go2_candidate_staged.sh`)을 글자로 박고 있었다(결함 C-14). 같은 판에서 회수 명령의 `--keep`(실존하지 않는 선택지, C-15)과 SHA 한 줄로 읽히던 종료 절(C-16)도 고쳤다. **v4 는 산문만 바뀐 판이 아니다 — 러너 바이트가 바뀌었다.** 값·문턱·수집 계약은 여전히 불변이고, 이미 발행된 회차의 바이트도 불변이다(G-A042·G-A043 을 실행된 러너 `6fd78eeb8eac5342` 로 고정했다). v2·v3 은 산문만 바뀐 판이다. campaign 껍데기를 쓰지 않는다 — **1단계 분기도 서버 게이트도 없는 회차**라 회차 ZIP 자체가 실행 단위다. v5 사유: **올릴 ZIP 이름에 판 번호를 넣었다**(결함 C-18, 사용자 지적). 판은 `release_id` 에만 있었고 이름에는 없어 history 에 같은 이름의 ZIP 이 넷 쌓였는데 그중 v3 는 올리면 아무것도 돌지 않는 판이다 — 어느 것인지 가리는 근거가 사람의 SHA 손대조뿐이었다. 이제 사양 검증이 `upload_zip` 끝과 `release_id` 의 `_v<N>` 이 같은지 보고 다르면 빌드를 거부한다(관문 `test_16`). **v5 페이로드는 v4 와 두 줄만 다르다** — `experiment.json` 의 이름·판. 러너·보상·설정 바이트는 v4 와 동일하다. v6 사유: **계획서 `GO2_POST_A043_PLAN_20260922.md` 대조에서 나온 기록 공백 셋**을 메웠다 — ① 안내문이 서버 실행 시간 110분만 적고 계획 §7 의 세션 계획치 120~150분(회수 포함)을 옮기지 않았다 ② 사양이 G-A043 을 63번 인용하면서 그 정책의 model/env SHA 를 고정하지 않았다(`comparison_arm`, 값은 회수 산출물 `G-A043_LOCAL_VERIFY.json` 에서 읽었다) ③ 계획 §9-1 의 c3 상한 `0.567/70` 이 서술로만 있었다. **판정 문턱 19개는 여전히 A043 과 숫자 단위로 동일하고(차이 0), 러너·보상·run_config 바이트는 v5 와 같다** — v6 페이로드 차이는 `experiment.json` 과 그 해시 줄뿐이다. v7 사유: **안내문 §5 의 exit code 설명이 틀렸다**(결함 C-20, 사용자 검토). `두 명령의 exit 1 은 성능 기준 미충족` 은 두 번 틀렸다 — 첫 판독기는 성능 FAIL 에 exit **0** 을 내고(FAIL 이 `PASS_VERDICTS` 안에 있다), 그 명령의 exit 1 은 INCONCLUSIVE·BASELINE_REMEASURE_REQUIRED 곧 **판정 불가**다. 둘째 판독기는 FAIL 과 INCONCLUSIVE 를 같은 exit 1 에 담는다. 이 줄이 **서버 종료 게이트**에 있었으므로 대가는 회수 결손을 성능 실패로 읽고 서버를 끄는 것 — 그때 잃는 것이 영상과 report 다. 관문 `test_20` 은 두 판독기를 빈 수확물로 **실행**해 exit 1 이 성능이 아님을 보이고, 판독기 소스에서 비통과 판정 이름을 읽어 안내문이 그것을 담는지 본다. **값·문턱·러너 바이트는 v6 과 같다** — 페이로드 차이는 안내문과 `experiment.json`·해시 줄뿐이다. v8 사유: **사용자 검토 2회차가 둘을 더 잡았다.** ① ZIP 안의 사양이 아직 `--keep` 을 적고 있었다(결함 C-21 — C-15 를 안내문에서만 고쳤고, 사양은 패키지에 실려 서버로 간다). ② 수집이 중단된 실행이 전수 완료와 똑같이 보였다(결함 C-22 — `finish` 가 조기 종료 경로에서도 `RESULT_STATE=FULL` 과 같은 `[DONE]` 표식을 냈다). 러너가 이제 개수를 세어 `COLLECTION_STATUS` 를 따로 적고 결손이면 `[INCOMPLETE COLLECTION]` 을 찍으며, 종료 게이트가 `COLLECTION_STATUS=FULL_69_COMPLETE` 를 요구한다. **v8 은 러너 바이트가 바뀐 판이다** — 값·문턱·수집 계약은 그대로다. 관문 test_14(안내문+사양 양쪽 명령 실행)·test_21(finish 실행). v9 사유: **안내문이 실패 경로를 잘못 적고 있었다**(결함 C-24, 사용자 검토 3회차). ① `[DONE]` 은 늘 나오지 않는다 — 러너의 `on_exit` crash 경로는 부분 ZIP 과 `COLLECTION_STATUS=INCOMPLETE_CRASH` 만 남기고 표식 없이 끝나므로, 표식을 기다리는 사용자는 오지 않을 줄을 기다리며 휘발 서버의 예산을 태운다. ② 「불완전하면 메운 뒤 종료」는 복구 가능한 누락에만 맞다 — 파국 게이트가 멈춘 판은 정책이 실행되지 않은 판이고 69 를 채우는 것이 오히려 러너의 계약(STOP_UNSAFE)과 충돌한다. 안내문 §4 를 세 상태(정상 완료 / 복구 가능한 누락 / crash·안전상 평가 불가)로 나누고 §5-a 와 종료 문장이 그 구분을 따르게 했으며, `FULL_69_COMPLETE` 가 개수 확인일 뿐 SHA·지문·identity·report 검사를 대신하지 않는다고 적었다. 관문 test_22 가 발행된 러너의 crash 경로를 실행해 표식 부재를 보인다. **러너 바이트는 v8 과 같다** — v9 페이로드 차이는 `experiment.json` 의 판 이름 두 줄과 그 해시 줄뿐이고, 안내문이 바뀌었다. 같은 판에서 결함 C-23(옛 `pinned = staged + 핀 블록` 동치 관문이 C-14 이후 빨간 채로 남아 다음 회귀를 가리고 있었다)을 **관문만 고쳐** 닫았다 — 러너를 건드리지 않았고 v8 ZIP 은 같은 SHA 로 재빌드된다. 발행 도구 `tools/build_go2_full_collection_release.py`.
- 수집 계약: `run_config.env`가 `GO2_STAGE=full`을 고정한다(러너가 그 파일을 source 한 **뒤** STAGE를 정하므로 명령줄 선택이 아니라 패키지 계약이다). 학습 → 파국 게이트 → **69 case 전수**(평가 seed 101/202/303 × 32env) → sentinel 5 → 영상 → 결과 ZIP 하나. 근거는 결함 C-11(A043의 결정적 손실이 1단계 23 case 밖이었다).
- 영상 사전 판정: **필수.** 후보 10개(`combined_yaw_left`·`combined_yaw_right`·`rough_forward`·`rough_lateral`·`stairs_10_down`·`stairs_15_down`·`push_pos_x`·`push_neg_x`·`push_pos_y`·`push_neg_y`, 모두 seed 101, 4env×500step) + 기준선 신규 4개(G2 양방향·G6 ±y — 이 네 case의 G-A033 영상이 없다). 기준선 나머지 6개는 SHA·지문 대응 확인된 기존 영상 재사용(`go2_g_a041_*` 2 · `go2_g_a042_*` 1 · `go2_g_a033_*` 1 · `go2_g_a043_*` 2). 밀침 영상 재사용은 결함 C-13(빌더 지문이 `PUSH_X`/`PUSH_Y`를 상수로 박아 둠)을 고친 뒤에 가능했다.
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a044_a033_lin_vel_z_m175/exported/report.html` 원본·**69 case 전부**의 telemetry·sentinel 5·영상 14개(후보10+기준선4)·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`로 기록하며 회수 완결로 보고하지 않는다.
- 기준 변경 근거는 별도 문서: `workspace/training/quadruped/reports/GO2_G_A044_CRITERIA_CHANGES_20260922.md`. **판정 문턱은 하나도 바꾸지 않았다** — 넓힌 것은 수집(전수)과 보호(밀침 네 방향, screening 판 `post_a043_push4_v1`)뿐이다. 결함 C-12·C-13은 원천 수정(대장 `reports/GO2_DEFECT_LEDGER.md`).
- **서버 실행은 사용자 결정 사항이다.** 로컬 검증 완료는 산출물 무결성이며 성능·통과 판정이 아니다.

## G-A043-LOCAL-REVIEW-20260922 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED → VERIFIED. 원자료는 workspace/_keep에 보존하며 기존 정본 병합·덮어쓰기 없음.
- 결과 ZIP SHA256: `9a5e7d2858702c1a766421cf221c8b3233e3b98043c914bb65b345366c68c8c6`. 외부 SHA·CRC·안전경로·내부 SHA 530항목·압축 해제본 531파일 대조 불일치 0. campaign ZIP도 외부 SHA·CRC·내부 SHA 5항목 일치. generic tar 검증기는 ZIP 비지원이므로 ZIP 전용 대조로 확인.
- 필수 회수: 원 학습 report·env·로그·iter900 checkpoint, 후보69 telemetry, sentinel5, 신규 영상 후보6+기준선2, 재사용 기준선4 SHA 일치. 서버 종료 가능; 추가 필수 회수 없음. 성능 판독은 진행 중이며 무결성 검증을 성능 판정으로 쓰지 않는다.

- Review complete: INTERNAL_GATE_FAIL; A033 retained. See reports/GO2_G_A043_READOUT.md and workspace/server_returns/G-A043_LOCAL_VERIFY.json. No MERGED transition: raw files retained in inbox without canonical merge. Analysis and user reporting completed.

## G-A043-PACKAGE-20260922 — A033 위 `lin_vel_z_l2 −2.0→−1.5` 실행 패키지 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증). 서버 실행·회수·병합은 **없다.** 새 학습도 없다.
- 발행: `upload/G-A043/current/GO2_G_A043_a033_lin_vel_z_m15_one_command.zip` SHA256 `68480a13f96bf7032462ce852238fcbbaaeb726e66638a9d7502cbc154dcda45`(release `20260922_a033_lin_vel_z_m15_one_command_v3`). 대체된 v2 `69f20613…1891c`·v1 `90661e80…f0b11c`는 history 보존, 둘 다 서버에 올린 적 없음. v3 사유: 2차 검토가 사양 산문 두 곳(±y "짝 비교 불가" 오기, 상한 집계 범위)을 잡았다.
- 영상 사전 판정: **필수.** 후보 6개(`stairs_10_down`·`stairs_15_down`·`rough_forward`·`rough_lateral`·`push_pos_x`·`push_neg_x`, 모두 seed 101, 4env×500step) + 기준선 신규 2개(`push_pos_x`·`push_neg_x` — 이 두 case의 G-A033 영상이 없다). 기준선 나머지 4개는 SHA·지문 대응 확인된 기존 영상 재사용(`go2_g_a041_*` 2개, `go2_g_a042_*` 1개, `go2_g_a033_*` 1개). 근거: reward 변경 run이고 후보 채택/폐기 판단에 쓰므로 §2에 따라 필수.
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a043_a033_lin_vel_z_m15/exported/report.html` 원본·1단계 22 case telemetry(계단 15cm 3seed·밀침 −x 3seed·±y 2 포함)·sentinel 5·영상 8개(후보6+기준선2)·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`로 기록하며 회수 완결로 보고하지 않는다.
- 기준 변경 8건의 근거는 별도 문서: `workspace/training/quadruped/reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md`. v1의 ±y 제외 근거는 `tools/go2_reward_mechanism.py` `PUSH_CASES`(네 방향)와 충돌해 철회했고, 표지를 복원해 1단계 22 case로 확대했다. 결함 C-8·C-10은 원천 수정(대장 `reports/GO2_DEFECT_LEDGER.md`).
- 로컬 검증 완료: 사양 `validate_spec` 통과, 재빌드 일치, 계약 테스트 `tools/test_go2_g_a043_campaign_contract.py` **32/32 통과**(v3 발행 바이트 기준 — `PackageTest` 21 · `GateAndVerifierTest` 6 · `PlanReadersTest` 5). 원장·관문 재확인 53/53(`test_go2_canonical_consistency`·`detectability_gate`·`tuning_base_data`·`defect_ledger`). 남은 기존 실패는 결함 C-2(G-A035·A037·A039 발행 ZIP 재빌드 불일치)뿐이고 G-A043과 무관하다. **로컬 검증 완료는 성능·통과 판정이 아니다.**

## G-A042-LOCAL-REVIEW-20260921 — 다운로드 분석
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 회수 `workspace/_keep/GO2_G_A042_RESULT.zip` 및 campaign ZIP·SHA와 풀린 run을 읽기 전용 검사한다. 기존 정본 병합·덮어쓰기는 하지 않는다.
- 필수: 해당 학습 report·로그·env·iter900 checkpoint, 사전등록 표적 telemetry(10/15cm 포함), 후보4·기준선1 신규 영상 및 재사용 영상 대응. SHA·필수 목록 확인 전 서버 종료 판정 보류.
- 분석: A033 대비 계단 진행·정체·낙상·험지 추종, fact_rules와 계획 screening을 분리 확인. 파일 존재는 VIDEO_OBSERVED가 아니다.
- RECEIVED → VERIFIED. 결과 ZIP SHA `7c6b3439f3f5cbe6d19b95f62208f6d1fac36d5c4780f775a72f66b09e856c89`, 외부 SHA/CRC/안전경로/内部232 SHA 항목/풀린 파일 대응 불일치0. 로컬 판독 artifact/stage/identity faults0. generic tar 검사기는 ZIP 비지원이며 ZIP 검사로 대체했다.
- 후보21 telemetry·sentinel5·후보4/A0331 신규 영상(각499frame,9.98s) 및 원 학습 report 회수 확인. 영상 후보4종 표본 직접 관찰; 전수 연속행동 미확인. 사전등록 재사용 기준선과 sentinel5/5 일치. **서버 종료 가능**, 필수 추가 회수 없음. 전체69case는 TARGET_FAIL로 미실행(회수 누락 아님).
- 분석·보고 완료, 기존 정본 병합은 비해당이므로 MERGED로 기록하지 않는다. INTERNAL_GATE_FAIL, A033 유지. 보고 `workspace/training/quadruped/reports/GO2_G_A042_READOUT.md`; 원 자료는 변경하지 않음.

## G-A042-REPAIR-20260921 — 계획·감사에 따른 실행 패키지 수정
- 상태: PLANNED → RUNNING. 사용자 지정 제작 계획·감사·재개 지점에 따른 로컬 수정/검증/재발행. 서버 실행·새 학습·회수·병합 없음.
- 기존 A042 current 전체를 SHA 대조하여 history에 보존한 뒤 새 release ID로 발행한다. 기존 회수 자료와 다른 회차 release는 변경하지 않는다.
- 회귀검사: required case 삭제, wrong/missing identity, 통합 fact_rules+계획 screening, stationary/TARGET_FAIL 필수 수집, env별 진단·coverage, 테스트 출력 격리.
- 새 실행의 영상 필수: rough_forward/rough_lateral/stairs_10_down/stairs_15_down seed101 양팔. 기준선 3개는 기존 사양 SHA·identity로 재사용, 15cm만 신규. 두 높이 포함 12 표적+초기 보호 기록은 성능 실패와 무관하게 수집한다.
- 원 학습 report는 평가 전에 `_keep/go2_g_a042_a033_track_lin_vel_xy_160/exported/report.html`에 보존하고 결과 ZIP/SHA에 포함. 로컬 도구 변경 자체는 VIDEO_NOT_REQUIRED. 서버 결과/행동/공식 점수는 미측정.
- REPORT_READ_STATUS=READ_MATCHED(학습 run 대응, 평가 성능 판정 아님): A033/A041의 `_keep/<run>/exported/report.html` 본문을 직접 읽고 TRAIN_STATUS/CHECKPOINT_PIN과 대조. A033 09-15 21:29~22:27, 1000iter, report-best700·최고19.28@651·track1.5; 평가900 model `ccd60e19…6044`. A041 09-21 10:02~10:59, 1000iter, report-best700·최고19.79@681·ang_vel_xy−0.04; 평가900 `f4c0b929…c8e8`. HTML의 학습 평균/일반 설명을 행동·기전 증거로 승격하지 않는다. A042 report는 아직 생성되지 않음.
- C-6 테스트 출력 격리: feet_air_time builder 시험은 TemporaryDirectory에서만 생성하며 기존 발행 파일 SHA 불변을 검사(6 tests 성공). 수정 릴리스 외 과거 ZIP을 재생성하지 않음.
- 로컬 수정 완료·보고: A042 v4 `current/` SHA `a95d3b6d2164354381e850ed7749d4c97d3a6df6ae02ef5bb4f29ef8dda06133`, ARTIFACT_VERIFIED. 집중53개 성공; A04226개 중25개 성공+기존 문구 기대1개 수정 후 단독 재검사 성공. `upload/G-A042/REPAIR_VALIDATION.json`에 실패·재검사·비관련 A040 경로검사 실패를 구분 보존. 서버 실행/회수/병합 상태를 완료로 올린 것이 아니다.

## G-A042-PACKAGE-REVIEW-20260921 — 실행 전 패키지 감사
- 상태: PLANNED → RUNNING. 발행 ZIP·사양·러너·계획 §4 판독기를 읽기 전용 대조한다. 서버 실행·결과 회수·병합 없음.
- 발행 ZIP을 재작성하는 전체 테스트는 실행하지 않는다. 한정 테스트와 합성 반례만 임시 경로에서 수행한다.
- 영상: VIDEO_NOT_REQUIRED — 이번은 새 정책 행동 평가가 아닌 실행 패키지 계약 감사다.
- 로컬 감사 완료: ZIP CRC/외부·내부 SHA 일치, 전용26검사26/26 OK. 계획 판정 미연결·지문 검사 누락·정지 early-stop 수집 누락 등으로 서버 실행 미해제 유지. 보고서 `workspace/training/quadruped/reports/GO2_G_A042_PACKAGE_AUDIT_20260921.md`. 다운로드 lifecycle의 RECEIVED/MERGED는 이번 작업 비해당; 과거 발행물 변경 없음.

## G-A041-LOCAL-REVIEW-20260921 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 제공 `workspace/_keep/GO2_G_A041_RESULT.zip` 및 campaign ZIP, SHA, 풀린 폴더를 검사한다. 외부 실행은 회수 로그로 확인하며 기존 정본에 덮어쓰기/병합하지 않는다.
- 목적: A041 단일변수·iter900 대응, 원 학습 report, 표적 telemetry·영상 회수 및 예측/실측 대조. 서버 종료 여부는 필수 목록 검증 후 결정한다.
- 영상: 필수; 사양의 후보 4개·기준선 2개 신규 영상과 기존 재사용 영상 대응을 확인한다. 영상 파일 존재와 행동 관찰은 구분한다.

## G-DATA-STANDARD-20260920 — 데이터 의미 명세 및 표준 뷰
- 상태: PLANNED → RUNNING. 기존 집계표 다섯 종의 생성 정의 감사와 표준화. 신규 서버 작업/학습/회수/병합 없음.
- 입력: TILT.csv, SITUATIONS.csv, PROBE_SITUATIONS.csv, FALL_CHANNEL_ROLLUP.csv, CLIMB_REWARD.csv 및 해당 생성 코드, 보관 Isaac 원문, 강좌 14·15 HTML.
- 출력: config/go2_evidence_data_dictionary.json, GO2_DATA_STANDARD.md, 로컬 표준 뷰 reports/evidence/go2_standardized_v1/standardized.json. 기존 CSV는 불변.
- 영상: VIDEO_NOT_REQUIRED — 행동 성능이 아닌 데이터 정의와 변환 무손실성 검사. 실제 정책 개선 판정 없음.
- 로컬 결과: 5개 표 129행 표준 뷰 생성, 원본 셀/명세/고유키/유한수/누락·대리식 분류 회귀 검증. 신규 회수·병합 단계는 비해당. 전체 raw 재계산/정책 성능 개선 검증이 아님. 자세한 완료 범위는 GO2_DATA_STANDARD.md §5.

## G-AUDIT-EVIDENCE-LIVE-20260920 — 역할 인계 동작 감사
- 상태: PLANNED. 사용자 요청: 증거 관리자 추가 산출물을 실제로 동작시키고 결과 감사.
- 범위: 기존 A033 보존 자료의 모집단·수식 출처를 읽기 전용 재확인하고 증거 관리자 → 분석가 → 기획자 → 독립 감사자 → PM 인계를 시험한다. 새 학습·다운로드·병합·정책 변경 없음.
- 검증: 역할 계약/정본 일치 및 추론·역할 회귀 테스트. 테스트 성공과 사실적 추론의 타당성을 별도로 보고한다.
- 영상: VIDEO_NOT_REQUIRED — 새 정책/행동 평가가 아닌 기존 수치의 출처·모집단 인계 감사. 기존 영상의 행동을 새로 판정하지 않는다.
- 기록: 이 작업 행과 에이전트 응답; 새 성능 원장이나 실행 패키지 생성 없음.
- 진행: PLANNED → RUNNING. 기존 로컬 자료 재독해 작업 완료; 신규 회수·병합이 없어 RECEIVED/VERIFIED/MERGED를 새로 주장하지 않는다.
- 로컬 검증: `python -B -m unittest tools.test_go2_evidence_role_contract tools.test_go2_canonical_consistency -q` 19/19, `python -B -m unittest tools.test_go2_inference_integrity_contract tools.test_go2_role_situation_exam_contract tools.test_go2_role_regression_contract -q` 17/17 성공(총 36, 서로 다른 테스트). 독립 감사의 evidence+detectability 19검사는 이 수에 합산하지 않음.
- 실제 인계: evidence_live(증거 관리자) → data_reaudit(분석가) → plan_reaudit(기획자) → audit_reaudit(독립 감사) → PM. READ_ONLY로 A033 rough_lateral의 FALL_CHANNEL_ROLLUP tilt-only 9/8/13과 TILT seed101 base-contact19 대 non-base-contact13의 .31123/.05106/AUC .838을 분리했다. 원자료: `workspace/training/quadruped/reports/evidence/go2_a038_reread_20260919/FALL_CHANNEL_ROLLUP.csv`, `workspace/training/quadruped/reports/evidence/go2_reward_mechanism_20260917/TILT.csv`. 독립 감사가 per-env로 세 seed의 tilt-only가 base-contact 집합에 포함됨을 확인했으나 정의상 일반 관계는 아님.
- 수식 한계: Isaac 보관 원문 gx²+gy²와 계측 1-gz²의 동치는 unit-norm 가정 필요. 이번 감사에서는 norm 미확인. 종료 전 창과 전체 episode 평균의 비대칭도 유지. report best700과 평가 iter900 구분. 연관 근거이지 reward 효과나 -0.5 최적값 근거가 아님.
- 감사 결함 재현: `_check_rows`는 `run,score,other / A,1.5,9.8`에서 A의 score를9.8로 잘못 설명해도 수용. INFORMATION_RUN은 RECOMMENDED 전용 R6/번호/readout/원장 등 검사를 우회. 역할 계약 테스트는 링크·필드 존재만 검사. 이 턴은 실행·감사이며 결함 수정을 수행하지 않음.
- PM 결과: 제한된 실제 인계의 사실 분리 확인. 자동 검증의 충분성은 기각. 가장 쉬운 점수 상승/특정 가중치 우월성은 미확정. 서버 실행·학습·패키지 발행 없음. 보고 완료, 다음 수정 대상은 열 단위 근거 연결과 실행 후보 공통 검증이다.

> **역할:** 서버 작업의 계획, 파일 목록, 다운로드, 검증, 선택 병합, 작업 이력을 한곳에서 추적한다.  
> **대상:** 메인 팀장, 스케줄러, 기획자, 분석가, 보고서 작성자, 서버 실행 사용자.  
> **갱신 방식:** 작업 시작 전에 행을 만들고, 증거가 생길 때 같은 행의 상태만 전진시킨다. 과거 행은 삭제하지 않는다.  
> **갱신일:** 2026-08-31

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 후보의 H1~H7 실제 행동과 설계 의도 20점·리포트 10점의 영상 증거를 확보한다.
- [현재 단계] **단계 1/6 — H4 정량 기본 행동 게이트.** H4 yaw 추종량이 가장 이른 미완료 증거다.
- [확보] Run06 10,000 iter·model_9900·학습/영상 artifact 정합, 사전등록 수치 게이트 5/5 PASS, H1~H3·H5 시각 PASS.
- [미확보] H4 양방향 yaw 추종량, H6 tracking·termination, H7 밀침 회복시간, 독립 seed.
- [이번 테스트] 추가 학습 없이 Run06 고정 정책의 H4·H6·H7 원시 telemetry를 회수한다.
- [흐름] Run06 분석 완료 → **A260831-08 고정 평가** → 정량 판정 → 최종 문서·제출물 정합 → 제출.
- [지금 할 일] 검증된 평가 ZIP을 서버에 올리고 런북의 한 줄 명령만 실행한다.
- [보장하지 않음] 영상 1세트나 단일 seed만으로 공식 survival_rate, 최적 reward, 예선 점수 또는 통과 가능성을 보장하지 않는다.

## 1. 이 문서가 해결하는 문제

서버는 접속마다 초기화되고, 사용자는 서버 명령 실행과 다운로드를 담당한다. 반면 로컬
`C:\dev\Nconnect\workspace\training`은 과거 run·원장·보고서를 보존하는 정본이다. 서버의
`training` 전체를 로컬에 덮어쓰면 새 run뿐 아니라 업로드 당시의 오래된 문서도 함께 돌아와
로컬 정본을 과거 상태로 되돌릴 수 있다.

따라서 모든 서버 작업은 다음 두 결과를 별도로 관리한다.

1. **필수 run bundle:** 해당 run의 checkpoint·tfevents·로그·설정·상태·해시
2. **보험 snapshot:** 서버 `/workspace/training` 전체 사본. 직접 병합하지 않고 복구·누락 확인에만 사용

## 2. 정본 우선순위

충돌할 때 아래에서 위로 덮지 않는다. 위 항목이 우선한다.

1. 실제 회수 artifact와 검증된 내용(`STATUS.txt`, params YAML, tfevents, checkpoint tensor)
2. 이 문서의 artifact 작업 원장과 파일 변경 원장
3. `PROJECT_STATE.md`의 고정 사실·결정·LATEST NEXT
4. `H1_REWARD_EVIDENCE_MASTER.md`의 reward·run 과학 판정
5. `CAMPAIGN_SCHEDULE.md`의 현재 단계·일정
6. `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md`의 장기 방향
7. 개별 보고서와 과거 계획

파일 SHA256은 전송 무결성 증거다. `policy.pt` 동일성은 비결정적 직렬화 때문에 checkpoint
iter + `model_best.pt` SHA256과 `torch.jit.load(...).state_dict()` tensor 비교로 판정한다.

## 3. 역할과 기록 책임

| 역할 | 실행 책임 | 반드시 갱신할 곳 |
|---|---|---|
| 사용자 | 서버 시작, 제공 명령 실행, 결과 tar 다운로드 | 외부 실행 결과를 메인 팀장에게 전달. 원장 갱신 책임은 없음 |
| 메인 팀장 | 명령·회수 경로 확정, 검증, 선택 병합, 최종 상태 보고 | 이 문서, `PROJECT_STATE.md`, 관련 계획·보고서 |
| 스케줄러 | 가장 이른 미완료 단계와 필수/개선/조사 등급 관리 | `CAMPAIGN_SCHEDULE.md`, 이 문서 작업 상태 |
| 기획자 | 단일 변수, 통제 변수, 성공/실패/INCONCLUSIVE, 회수물 사전등록 | `experiment_history.csv`, `H1_REWARD_EVIDENCE_MASTER.md` |
| 분석가 | SHA·설정·seed·지표·checkpoint·H1~H7 측정 범위 판정 | 이 문서 검증 결과, reward 마스터, 해당 보고서 |
| 보고서 작성자 | 검증된 run 식별자와 근거만 인용 | `REPORT_*.md`, `TECH_REPORT_H1.md`, evidence index |

## 4. 관리 파일 목록

### 4-a. 운영·판정 정본

| 경로 | 역할 | 갱신 시점 |
|---|---|---|
| `AGENTS.md` | 모든 담당자가 따라야 할 최상위 운영 계약 | 불변 규칙 변경 시 |
| `ARTIFACT_MANAGEMENT.md` | 파일 목록·artifact lifecycle·작업 내역의 단일 진입점 | 모든 서버 작업 전/후 |
| `PROJECT_STATE.md` | 사실(F)·결정(D)·LATEST NEXT 원장 | 새 사실·결정 즉시 |
| `CAMPAIGN_SCHEDULE.md` | 현재 단계·등급·게이트·다음 일정 | 상태 전이 시 |
| `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md` | 목표·점수축·장기 단계 계획 | 전제·범위 변경 시 |
| `H1_REWARD_EVIDENCE_MASTER.md` | reward 9개와 Run별 과학적 지위 | 새 분석 결과 수용 시 |
| `SERVER_SESSION_RUNBOOK.md` | 서버에서 복사해 실행할 검증된 명령 | 서버 패키지·경로 변경 시 |
| `REPORT_260831.md` | 현재 사용자용 종합 보고 | 캠페인 판정 변경 시 |

### 4-b. 학습·제출 artifact

| 경로/패턴 | 내용 | 병합 규칙 |
|---|---|---|
| `workspace/server_returns/<RUN_ID>/` | 서버 다운로드 최초 격리 위치 | 원본 보존, 여기서 직접 수정 금지 |
| `workspace/training/humanoid/logs/rsl_rl/humanoid/<run>/` | checkpoint, tfevents, params | 검증된 새 run 디렉터리만 추가 |
| `workspace/training/humanoid/reports/experiment_history.csv` | 실험 사전등록·결과 이력 | 기존 행 삭제 금지, Run06은 bundle 판정 후 갱신 |
| `workspace/training/humanoid/reports/*_add.md` | run별 분석 보고 | 대응 run 식별자와 근거 필수 |
| `workspace/training/humanoid/reports/EVIDENCE_INDEX_S0.md` | H1~H7 영상·근거 색인 | 최종 후보 평가 후 갱신 |
| `workspace/training/humanoid/exported/model_best.pt` | 현재 export 기준 checkpoint | 명시적 승급 결정 전 교체 금지 |
| `workspace/training/humanoid/exported/env.yaml` | 제출 환경 설정 | 채택 checkpoint와 일치 검증 후 교체 |
| `workspace/training/humanoid/exported/policy.pt` | 제출 정책 | checkpoint tensor 동일성 확인 후 교체 |
| `workspace/training/humanoid/humanoid_rewards.py` | 현재 보상 소스 | 사전등록된 단일 변경만 허용 |
| `workspace/training/humanoid/run06_server_package.zip` | 현재 서버 패키지 | SHA256 `1478e6a20d068dcbecd64ef648f1e3d1a7d5adf6e24dd6907d95b0430e8eaf86` |
| `workspace/training/humanoid/server_run06_videos.sh` | Run06 H1~H7 고정 영상 러너 | SHA256 `793ca0546d5cea3d0c63e96f61b850404e8d072e59eee6d4ac541c072e59df9f`, CRLF 0, Git Bash `bash -n` PASS; terrain seed 오류 제거·resume·3종 지형 preflight 지원 |
| `workspace/training/humanoid/run06_fixed_eval_package.zip` | Run06 H4·H6·H7 정량 평가 업로드 package | SHA256 `bf90f1943d36f5538da6aa861eab655a6fd28c2c244c4a544bc26282e05aac93`, 14 members, ZIP CRC PASS, Run06 model_9900 내장 |
| `workspace/training/humanoid/server_run06_fixed_eval.sh` | 학습 없는 32환경 고정 evaluator 러너 | CRLF 0, Git Bash `bash -n` PASS, H4 좌우·H6 ±10°·H7 push 원시 CSV 회수 |
| `workspace/training/quadruped/server_run_Go2_videos.sh` | **LEGACY_INVALID_MAPPING — 실행·G1~G7 판정 금지** | H1형 G1 stand/G2 forward/G3 lateral/G4 complex/G5 rough/G6 ±10°/G7 push로, 제공 Go2 registry와 불일치. 역사 보존만 하며 신규 evaluator가 대체해야 함 |
| `workspace/training/quadruped/quadruped_rewards.py` | Go2 실질 4변수 동시 변경 pilot 1,000 iter | `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05`; action -0.01은 불변. `MULTIVARIABLE_EXPLORATORY_BASELINE`, 개별 인과효과 미측정 |
| `workspace/training/quadruped/config/go2_self_eval_registry.json` | Go2 G1~G7 canonical 내부평가 registry | G1 forward·G2 omni·G3 rough·G4 ±20°·G5 10~15cm stairs·G6 push·G7 DR, weight sum 1.0 |
| `tools/verify_download_artifact.py` | 서버 다운로드 정형 검증기 | 외부/내부 SHA, 안전한 tar 경로, 시나리오 수, model SHA를 JSON으로 판정 |
| `.codex/agents/artifact-verifier.md` | 저비용 artifact 검증 역할 | `explore`/`gpt-5.6-luna` 전용, 의미 판정·병합·서버 종료 권한 없음 |
| `workspace/server_returns/train_260831-06_run05cfg_10000/` | Run06 검증 격리본 | bundle SHA·내부 18/18·snapshot tar 검증 완료, 아직 training 미병합 |

## 5. 서버 artifact lifecycle

```text
PLANNED → RUNNING → RECEIVED → VERIFIED → MERGED → ANALYZED → REPORTED → SUBMISSION_READY
               ↘ FAILED / INCONCLUSIVE / BLOCKED
```

| 상태 | 완료 기준 |
|---|---|
| `PLANNED` | 목적·변수·seed·iter·시간·중단점·회수물·다음 분기 기록 |
| `RUNNING` | 사용자 제공 서버 출력으로 실행 시작 확인. 실제 iter는 로그 전까지 미측정 |
| `RECEIVED` | 원본 tar가 `workspace/server_returns/<RUN_ID>/`에 있고 파일 SHA 기록 |
| `VERIFIED` | tar SHA, `TRAIN_RC`, source hash, params, seed, checkpoint, tfevents 확인 |
| `MERGED` | 병합 전/후 목록과 대상 경로 기록, 기존 정본 비파괴 확인 |
| `ANALYZED` | 사전 기준으로 `INTERNAL_GATE_PASS/FAIL/INCONCLUSIVE`와 H1~H7 측정 범위 판정 |
| `REPORTED` | reward 마스터·상태·일정·보고서가 같은 판정으로 동기화 |
| `SUBMISSION_READY` | 최종 `policy.pt`·`env.yaml`·리포트 일치와 H1~H7 증거 확인 |

## 6. 회수·병합 불변식

1. 서버 `training` 전체 다운로드는 허용하지만 **보험 snapshot**으로만 취급한다.
2. 로컬 `workspace/training`에 전체 압축을 직접 해제하거나 폴더를 통째로 덮어쓰지 않는다.
3. `/workspace/_keep/<RUN_ID>_DOWNLOAD.tar.gz`를 별도 다운로드하거나 snapshot 전 `training/_server_returns/<RUN_ID>/`로 복사한다.
4. 원본 tar는 `workspace/server_returns/<RUN_ID>/original/`에 보존하고, 분석용 해제본은 `extracted/`에 둔다.
5. 검증 전 `exported/model_best.pt`, `env.yaml`, `policy.pt`, 보고서, 원장을 교체하지 않는다.
6. 병합 전 `MERGE_PLAN.tsv`, 병합 후 `MERGE_RESULT.tsv`와 `LOCAL_SHA256SUMS.txt`를 남긴다.
7. 같은 이름의 파일은 자동 overwrite하지 않는다. 내용 비교 후 `add / replace / keep-local / conflict`를 명시한다.
8. 서버 snapshot에만 있고 필수 bundle에 없는 파일은 누락 원인을 확인한 뒤 별도 판정한다.

## 7. Run별 필수 회수 파일

| 분류 | 필수 파일/검사 |
|---|---|
| 실행 상태 | `STATUS.txt`, `TRAIN_RC`, `RUN_ID`, `MAX_ITERS`, 시작·종료 시각 |
| 무결성 | 다운로드 tar SHA256, 내부 `SHA256SUMS.txt`, source hash |
| 학습 설정 | `params/agent.yaml`, `params/env.yaml`, seed, num_envs, max_iterations |
| 곡선 | TensorBoard tfevents, `train.log` |
| 모델 | 3k/5k/10k milestone과 마지막 checkpoint |
| 소스 | `train.py`, `humanoid_rewards.py`, `h1_task/*.py`, restore 결과 |
| 제출 후보 | `model_best.pt`, `env.yaml`; `policy.pt`는 별도 export·tensor 검증 전 제출 후보 아님 |
| 분석 | Run05 대비 xy/yaw, episode length, base_contact, mean_std, H1~H7 직접/미측정 표 |

### 7-a. 학습 후 영상 필요성 판정·종료 게이트

학습 작업에는 학습 artifact와 행동 영상 artifact를 별도 상태로 둔다. 학습 bundle이
`VERIFIED`여도 영상이 필요한 run의 행동 평가는 `PENDING`이며 `ANALYZED`로 승급하지 않는다.

| 판정 | 적용 조건 | 종료 전 필수 조치 |
|---|---|---|
| `VIDEO_REQUIRED` | 새 reward/env/policy/checkpoint, 장기 학습, 후보 채택·폐기, H1~H7·survival·tracking 주장 | 고정 evaluator 영상 생성 → 로그·policy/checkpoint 식별자 포함 tar 생성 → tar와 `.sha256` 로컬 다운로드 확인 |
| `VIDEO_CONDITIONAL` | 학습 결과나 이상 징후에 따라 추가 시나리오가 달라짐 | 기본 CORE 영상을 확보하고 종료 직후 재판정; 추가 영상 필요 시 같은 세션에서 FULL로 확장 |
| `VIDEO_NOT_REQUIRED` | checkpoint 없는 smoke test 또는 동일 tensor·동일 evaluator 영상이 이미 검증됨 | 예외 근거와 대체 영상 경로·정책 식별자 기록 |
| `VIDEO_REQUIRED_NOT_ACQUIRED` | 필수 영상 생성/패키징/다운로드 실패 | 실패 로그와 재현 checkpoint·source·config 회수; 평가 완료 금지; 다음 세션 첫 작업으로 이관 |

**서버 종료 가능 조건:** 영상 판정이 기록되고, `VIDEO_REQUIRED`이면 영상 tar와 SHA가 로컬에
도착했으며 파일 존재·외부 SHA 일치까지 확인돼야 한다. 내부 파일 수·정책 대응 검증은
`RECEIVED → VERIFIED` 단계에서 수행한다. 영상이 없는 학습은 성능상 실패가 아니라
**행동 평가 미완료**다.

영상 사전등록에는 `RUN_ID / checkpoint iter+SHA / suite(CORE·FULL) / H1~H7 매핑 / seed /
num_envs / video_length / 명령 고정값 / 예상 파일 수 / 서버 경로 / 로컬 회수 경로 / 실패 시
부분 bundle 경로`를 모두 적는다.

## 8. Artifact 작업 원장 — append-only

| 작업 ID | 일시 | 등급 | RUN_ID/범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|---|
| `A260831-01` | 260831 | 조사 | 서버 회수 정책 | `REPORTED` | 없음 | 전체 snapshot 격리·선택 병합 규칙 확정 | 이 문서, `AGENTS.md`, `SERVER_SESSION_RUNBOOK.md`, 담당 지침 3종 | 완료 — 후속 작업은 이 규칙 유지 |
| `A260831-02` | 260831 | 개선 | `train_260831-06_run05cfg_10000` | `ANALYZED` | Run06 10k 자연 완료·두 tar 다운로드 | 종료·bundle·설정·곡선 검증 | `TRAIN_RC=0`, model_9900, `INTERNAL_GATE_PASS` 5/5 | Run06 동결 기준선 유지 |
| `A260831-03` | 260831 | 필수(제출요건) | Run06 필수 bundle 회수 | `VERIFIED` | 필수 bundle·전체 snapshot 다운로드 | `server_returns/<RUN_ID>/` 격리, tar·SHA·내부 18/18 검증 | `INGEST_STATUS.md`, `FILE_MANIFEST.tsv`, `LOCAL_SHA256SUMS.txt`, `MERGE_PLAN.tsv` | 원본 보존, 분석 전 병합 금지 |
| `A260831-04` | 260831 | 조사 | Run06 분석·선택 병합 | `ANALYZED` | 없음 | Run05 대비 Run06 마지막500 곡선·영상 분석 | xy·yaw·episode·base_contact·std 개선; 영상 증거 계층 정정 | 제출 후보 문서에 한계 반영 |
| `A260831-05` | 260831 | 필수(제출요건) | Run06 H1~H7 고정 영상 10종 | `VERIFIED` | resume 완료·FULL tar와 SHA 다운로드 | FULL 원본 격리·외부/내부 SHA·시나리오·model 대응 검증 | verifier PASS, 내부 47/47, video 10, policy 10, model SHA `8eb06e2…b636` | 서버 종료; A260831-04 영상·곡선 분석 시작 |
| `A260831-07` | 260831 | 개선 | 저비용 다운로드 검증 역할 | `VERIFIED` | 없음 | Luna용 read-only agent와 결정론적 검증 CLI 작성 | `artifact-verifier.md`, `verify_download_artifact.py`, Run06 FULL PASS JSON | 메인 팀장이 입력 계약·최종 의미 판정 유지 |
| `A260831-08` | 260831 | 필수(제출요건) | Run06 H4·H6·H7 고정 정량 평가 | `ANALYZED` | ZIP 업로드·한 줄 실행·FULL tar 다운로드 | 원본 telemetry 회수·로컬 보고서 재생성 | H4 yaw, H6 양방향, H7 회복 내부 측정 양호; threshold·공식 결과 없음 | 제출 후보의 보조 근거로만 사용 |
| `A260831-10` | 260831 | 개선 | 판정 지침·후속 학습 방향 | `REPORTED` | 없음 | 증거 4계층, TTL 우선 보고, 단일변수 screening·승급 규칙 확정 | `AGENTS.md`, 마스터 §9, 일정·상태·제출 리포트 동기화; candidate manifest 검증 | 공식 결과 대기 계획 철회; A260831-11로 자체 점수 확보 |
| `A260831-11` | 260831 | 필수(제출요건) | Run06 H1~H7 전체 자체 점수 | `PLANNED` | 다음 서버 접속에서 평가 전용 ZIP 업로드·한 줄 실행·FULL tar와 SHA 다운로드 | H1~H7 10 case 20초 telemetry, 내부 proxy v1 scorecard, package SHA `e897fa10…05551` | `run06_fixed_eval_package.zip`, `FIXED_EVAL_REPORT.json/md`; 학습 없음 | 회수 후 70점 게이트 판정, 최대 감점 시나리오만 screening |
| `A260831-09` | 260831 | 조사 | Go2 pilot·구형 영상 스위트 | `INCONCLUSIVE` | 실행 금지 | 제공 Go2 registry와 구형 runner 매핑 대조 | pilot artifact는 존재하나 구형 runner는 `LEGACY_INVALID_MAPPING`; G1~G7 미측정 | `G-A002` 신규 evaluator로 대체 |
| `G-A001` | 260901 | 조사 | Go2 운영체계·자체평가 재설계 | `REPORTED` | 없음 | 별도 원장·전용 역할 4종·canonical registry·protocol·handoff·validator 작성 | `GO2_*`, `.codex/agents/go2-*`, `validate_go2_campaign.py` | 새 세션에서 G-A002 evaluator 구현 |
| `G-A002` | 260901 | 필수(제출요건) | Pilot-01 정확한 G1~G7 평가 package | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | telemetry/report/lineage/worst-case video runner와 package builder/test 구현 완료 | package 로컬 검증 완료; 서버 결과는 `[미측정]` | `G-A005` package로 실행 |
| `G-A003` | 260901 | 조사 | Pilot-01 기반 초기 캠페인 계획 | `REPORTED` | 없음 | frozen artifact·control 유효성 감사, 평가→조건부 control→단일변수 ablation→승급 계획 작성 | `workspace/training/quadruped/upload/plan/go2-post-pilot-initial-work-plan.md`, G-F10·G-D08, 일정·reward 원장 동기화 | `G-A002` evaluator/package 구현 |
| `G-A004` | 260901 | 조사 | Default-01 1,000 iter + Pilot-01 쌍대 G1~G7 평가 | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | Default test PRD·상세계획·통합 runner 구현 완료 | Default 결과는 `[미측정]`; `VIDEO_REQUIRED`: 정책별 worst-case G1~G7 7개, seed 101/202/303 중 정량 최악 seed, 500 steps, 결과 ZIP `evaluation/<policy>/videos/` | `G-A005` 실행 → 정책별 69 telemetry·7 영상 회수 |
| `G-A005` | 260901 | 필수(제출요건) | Go2 Default-vs-Pilot 단일 실행·회수 package | `VERIFIED` | `/workspace/go2_default_vs_pilot_v1.zip` 업로드 후 검증된 한 줄 실행 | deterministic ZIP build, reward-only default staging, embedded Pilot SHA, manifest, runner syntax·contract test | `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`; 28 members; ZIP CRC·manifest·CRLF·Git Bash `bash -n` 검증 | 서버 실행 후 `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`과 SHA 회수 |

## 9. 파일 변경 원장 — append-only

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260831 | `A260831-01` | `ARTIFACT_MANAGEMENT.md` | 중앙 파일 목록·artifact lifecycle·작업 원장 신설 | 필수 절·표·링크 검사 |
| 260831 | `A260831-01` | `AGENTS.md` | 서버 snapshot 비덮어쓰기와 중앙 문서 선조회 규칙 | 규칙 중복·마커 확인 |
| 260831 | `A260831-01` | `SERVER_SESSION_RUNBOOK.md` | Run06 완료 후 필수 bundle·보험 snapshot 회수 명령 | package SHA 일치·shell 명령 정적 검토 |
| 260831 | `A260831-01` | `PROJECT_STATE.md` | F48~F51, D39~D42, LATEST NEXT 기록 | append-only 확인 |
| 260831 | `A260831-01` | `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md`, `CAMPAIGN_SCHEDULE.md`, `REPORT_260831.md` | 현재 단계 2/6 및 Run06 자연 완료·격리 회수 동기화 | 첫 화면 8항목 검사 |
| 260831 | `A260831-01` | `.codex/agents/*.md` | 기획·일정·분석·보고 시 중앙 운영 문서와 작업 원장 참조 | 3개 담당 지침 검색 |
| 260831 | `A260831-03` | `workspace/server_returns/train_260831-06_run05cfg_10000/` | 원본 bundle·snapshot 격리, tar 해제본, manifest·merge plan·수신 기록 작성 | bundle SHA 일치, tar 2종 PASS, 내부 checksum 18/18 PASS |
| 260831 | `A260831-05` | `workspace/training/humanoid/server_run06_videos.sh` | H1~H7 10종 고정 명령 영상·로그·policy를 CORE/FULL tar로 회수하는 러너 신설 | 8,155 B, CRLF 0, Git Bash `bash -n` PASS |
| 260831 | `A260831-06` | `AGENTS.md`, `ARTIFACT_MANAGEMENT.md`, `SERVER_SESSION_RUNBOOK.md`, `.codex/agents/*.md` | 학습 전·후 영상 필요성 재판정과 영상 다운로드 전 서버 종료 금지 게이트 신설 | 중앙 규칙·역할별 체크리스트·종료 보고 필드 대조 |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/`, `server_run06_videos.sh` | CORE/PARTIAL 원본 격리·검증 및 H5 terrain seed 타입 오류 제거·resume 기능 추가 | 외부 SHA 2종 PASS, tar 2종 PASS, 내부 36/36 PASS, model SHA 일치, Git Bash `bash -n` PASS |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/` | FULL tar·SHA 격리, 해제본·검증 JSON 보존 | tar SHA `c80f972c…9be`, 내부 47/47 PASS, video/policy 10/10, model SHA 일치 |
| 260831 | `A260831-07` | `.codex/agents/artifact-verifier.md`, `tools/verify_download_artifact.py` | 저비용 정형 다운로드 검증 역할·JSON 검증기 신설 | Run06 FULL 입력에서 rc=0, status PASS |
| 260831 | `A260831-08` | `eval_telemetry.py`, `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `run06_fixed_eval_package.zip`, `tools/test_fixed_eval_contract.py` | 기존 play 경로에 opt-in step telemetry를 추가하고 Run06 model_9900 고정 평가 package 생성 | unittest 5/5, Python compile, Git Bash `bash -n`, ZIP CRC·14 members·내장 model SHA PASS |
| 260831 | `A260831-09` | `SERVER_SESSION_RUNBOOK.md` | Go2 G1~G7 영상 스위트 절차 추가 — H1 `server_run06_videos.sh` 벤치마킹 문단 신설 | H1 10종 구조·CORE/FULL·fingerprint·검증 동일 명시, Go2 10종 매핑·명령 인자 대조 |
| 260831 | `A260831-09` | `workspace/training/quadruped/server_run_Go2_videos.sh` | H1 `server_run06_videos.sh`(8,155B) 벤치마킹해 Quadruped-v0 10종 포팅 — G1·G2·G3×2·G4×2·G5·G6×2·G7, seed 42·4 env·1000 step | CRLF 0, model SHA `C4D78ADF…`, Quadruped-v0 task 전환·G시나리오 매핑 확인 |
| 260831 | `A260831-09` | `workspace/training/quadruped/quadruped_rewards.py` | 이미지 5변수 반영 — `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05` (실질 4개 변경) | `grep` 4/4 일치, `report.html` 4/4 주황 점, Python AST PASS |
| 260831 | `A260831-10` | `AGENTS.md`, `.codex/agents/prelim-campaign-manager.md`, `.codex/agents/humanoid-test-planner.md`, `.codex/agents/humanoid-report-writer.md` | artifact·영상·내부 gate·공식 결과 분리, 서버 TTL 우선 답변, 학습 승인 규칙 추가 | 필수 제목·용어 검색, `git diff --check` |
| 260831 | `A260831-10` | `H1_REWARD_EVIDENCE_MASTER.md`, `CAMPAIGN_SCHEDULE.md`, `PROJECT_STATE.md`, `experiment_history.csv` | Run06 단계 5/6 동기화, 공식 산식과 내부 proxy 경계 정정, 후속 screening 순서 확정 | H1~H7 증거 행렬·F69~F70/D56~D58·현재 단계 대조 |
| 260831 | `A260831-10` | `workspace/submission_candidates/h1_run06_model9900/`, `workspace/training/humanoid/exported/TECHNICAL_REPORT.md`, `workspace/training/humanoid/reports/TECH_REPORT_H1_RUN06_FINAL.md` | 제출 리포트 판정 용어·공식 산식 출처 정정 및 3개 사본 동기화 | report SHA 동일, candidate `SHA256SUMS.txt` 5/5 일치; policy/env/model hash 불변 |
| 260831 | `A260831-11` | `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `RUN06_FIXED_EVAL_README.txt`, `tools/test_fixed_eval_contract.py` | H4·H6·H7 부분 평가를 H1~H7 10 case 전체 20초 평가로 확장하고 내부 시뮬 proxy /70 게이트 추가 | unittest 8/8, compile, Git Bash `bash -n`, ZIP 14 members·SHA `e897fa10…05551` |
| 260831 | `A260831-11` | `AGENTS.md`, 담당 agent 3종, 마스터·일정·상태 원장 | 부분 PASS 점수 제외, 공식 결과 대기 철회, 총 자체예상 70/100 최소·75/100 목표 규칙 | `SELF_ASSESSMENT_INCOMPLETE`, threshold, NEXT 문구 대조 |
| 260831 | `A260831-11` | `SELF_ASSESSMENT_RUBRIC.md`, 제출 후보 리포트 3개 사본·manifest | 문서 자체감사 27/30 고정, 부분 평가를 성능 승급에서 제외 | report 3개 SHA 동기화, candidate manifest 6/6 PASS |
| 260901 | `G-A003` | `workspace/training/quadruped/upload/plan/go2-post-pilot-initial-work-plan.md`, `GO2_PROJECT_STATE.md`, `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`, `ARTIFACT_MANAGEMENT.md` | 1차 튜닝 이후 평가 우선 초기계획, 유효 control 부재, 최소 경로·예산·재평가점 기록 | `validate_go2_campaign.py` PASS, `git diff --check` PASS |
| 260901 | `G-A004` | `GO2_DEFAULT_BASELINE_TEST_PRD.md`, `workspace/training/quadruped/upload/plan/go2-default-baseline-experiment-plan.md`, Go2 상태·일정·reward·handoff, `ARTIFACT_MANAGEMENT.md` | 조건부 control 계획을 Default-01 필수 생성·Pilot 쌍대평가·기본값 one-at-a-time 계보로 정정 | `validate_go2_campaign.py`, 문서 계약 검사, `git diff --check` |
| 260901 | `G-A004` | Default test PRD·상세계획, Go2 역할 지침 5종, 상태·일정 | PRD를 매 기획 턴 참조·동일 턴 갱신하는 living contract로 승격하고 `PRD_CHANGE`·`LEDGER_SYNC` 게이트 추가 | `validate_go2_campaign.py`, PRD lifecycle 계약 검사, `git diff --check` |
| 260901 | `G-A005` | Go2 evaluator·lineage·통합 runner·builder·tests·README, `play.py`, `train.py`, `go2_task/env_cfg.py` | Default 1k와 Default/Pilot 69-case·worst-video 평가를 단일 업로드/명령/결과 ZIP 구조로 구현 | Python compile·5 unit tests, Git Bash `bash -n`, CRLF 0, ZIP CRC·safe paths·27-file internal manifest, Pilot SHA, reward-only 4-line diff |
| 260901 | `G-A005` | Go2 PRD·상태·일정·상세계획·AGENTS·handoff·planner brief | G-D13 사용자 실행 package 자동 제공 계약과 실제 경로·SHA·완료표식·회수 게이트 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 10. 새 작업 기록 템플릿

```markdown
| `A<YYMMDD>-<NN>` | <일시> | 필수(제출요건)/개선/조사 | <RUN_ID/범위> | `PLANNED` | <사용자 실행> | <로컬 작업> | <사전 증거> | <첫 NEXT> |
```

작업 완료 시 새 행을 만들지 않고 같은 작업 ID의 상태와 증거를 전진시킨다. 범위가 달라지거나
새 서버 비용이 생기는 경우에만 새 작업 ID를 만든다. 외부 시스템의 사용자 행동은 로그·파일로
확인되기 전 `[미측정]`으로 두며, 우리가 지시한 사실과 사용자가 실제 수행한 사실을 구분한다.

### A260831-11 상태 전이 — 260901

- 상태: `PLANNED → RECEIVED → VERIFIED → ANALYZED`
- 원본: `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz`
- 외부 SHA-256: `4e552b2caea4f9a33475bf7a93bc35a383c9aa9b79a42e308b002c01674b860f`
- 검증: 안전 경로 0, 내부 69/69, case 10/10, `RUNNER_RC=0`, model SHA 일치
- 분석: 66.0414/70, `CALIBRATION_PASS / GENERALIZATION_UNVERIFIED`

### A260901-01 — 독립 multi-seed 검증

| 항목 | 값 |
|---|---|
| 등급 | 필수(제출요건) |
| 상태 | `SUBMISSION_READY` |
| 정책 | Run06 model_9900, SHA `8eb06e2…b636` 동결 |
| seeds | 101, 202, 303 사전등록 |
| 범위 | seed별 H1~H7 10 case, 32 env, 1,000 step |
| 판정 | 시나리오별 최악 seed, 세 seed 모두 통과 |
| 영상 | `VIDEO_NOT_REQUIRED` — 동일 checkpoint 영상 10종 VERIFIED, 이번 작업은 seed telemetry |
| 패키지 | `workspace/training/humanoid/run06_independent_eval_package.zip` |
| package SHA-256 | `ed235d67f2f2f4decb2fec71cc1d2664a45f2304b928dff5d20d9be343f584d2` |
| 예상 서버 시간 | 15~25분, 학습 없음 |
| 필수 회수 | `..._INDEPENDENT_EVAL_FULL.tar.gz`와 `.sha256` |
| 결과 | 외부 SHA 일치, 내부 189/189, 30/30 case, 실패 seed·시나리오 0, 65.73/70 |
| 후보 | `workspace/submission_candidates/h1_run06_model9900/UPLOAD_READY/` 3종, manifest 3/3 |
| NEXT | 팀 대시보드 업로드·접수 증거 회수 |

## 11. Go2 partial 수신 및 복구 — `G-A006` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 확보 | 미확보 / NEXT |
|---|---|---|---|---|---|
| `G-A006` | 필수(제출요건) | Default-vs-Pilot 결과 회수·복구 | `RECEIVED` | Default 학습 artifact, Default telemetry 69/69, 부분 결과 461파일 | Pilot telemetry 0/69, 영상 0/14, 비교 보고서, FULL ZIP 및 유효 SHA. 서버 종료 불가; hotfix resume 후 재회수 |

- 서버 원본: `/workspace/_keep/go2_default_vs_pilot_v1/`
- 최초 로컬 inbox: `workspace/_keep/go2_default_vs_pilot_v1/`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/`
- 부분 결과: `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`, 519,957,865 bytes
- 로컬 directory manifest SHA-256: `2b7867626065552ee1fe1a73a07a79a8ac577cb3ef0a03e481b6b0607e00b8a4`
- 수신한 `GO2_DEFAULT_VS_PILOT_RESULT.zip.sha256`는 0 byte라 무결성 증거로 사용할 수 없다.
- 원인: Default 평가 후 Pilot의 `exported/`를 삭제한 뒤 같은 경로에서 checkpoint를 복사했고, 실패 packaging이 서버에 없는 bare `python3`를 호출했다.
- 현재 서버용 hotfix: `workspace/training/quadruped/go2_default_vs_pilot_v1_hotfix.zip`, SHA-256 `b2fa2d57aee9ab55ea9765171d8230c8aeac8c38bbe46285548c864b4eee2d39`.
- 새 서버용 수정 통합 package: `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA-256 `db239f77fe3336209ecb8d4f38478c1fc1dd605fbf5c0351e95a9ba1b7e74cfd`.
- 폐기된 최초 package는 격리 원본에 `go2_default_vs_pilot_v1_buggy.zip`으로 보존했다. SHA-256 `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`이며 다시 실행하지 않는다.
- 다운로드 매핑 정본: `workspace/server_returns/DOWNLOAD_MAP.tsv`.
- 병합: `NOT_PERFORMED`; FULL 결과 검증 전 `workspace/training/quadruped`에 run 결과를 병합하지 않는다.

### G-A006 FULL 회수 검증 — 260901

- 상태: `RECEIVED → VERIFIED`
- 회수물: `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` 및 `.sha256`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/`
- 외부 SHA-256: `af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b` 일치
- package: 925 entries, unsafe path 0, `RESULT_STATE=FULL`, `RUNNER_RC=0`
- 필수 telemetry: Default 69/69, Pilot 69/69
- 필수 영상: Default 7/7, Pilot 7/7, 14개 모두 non-empty; 관찰 판정은 `VIDEO_UNKNOWN`
- 내부 manifest: launcher.log 1건만 packaging 종료행 후첨으로 불일치, 나머지 923건 일치·누락 0
- 판정: `ARTIFACT_VERIFIED`; 서버 종료 가능. 병합은 `NOT_PERFORMED`, 다음 상태는 `ANALYZED`.
- 상세: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/VERIFICATION_STATUS.md`

### G-A006 선택 병합·분석·보고 — 260901

- 상태: `VERIFIED → MERGED → ANALYZED → REPORTED`
- 선택 병합: paired/self-eval JSON·MD 4개와 14개 영상 contact sheet만 `workspace/training/quadruped/reports/evidence/go2_default_vs_pilot_260901/`에 추가했다.
- 원본 MP4·FULL ZIP은 `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/`에서 보존하며 로컬 training 정본에 통째로 덮어쓰지 않았다.
- 병합 증거: `MERGE_PLAN.tsv`, `MERGE_RESULT.tsv`, `LOCAL_SHA256SUMS.txt`; 18개 대상 모두 `OK`.
- 영상 판정: 각 MP4의 3%~97% 구간 12프레임 직접 관찰, `VIDEO_OBSERVED`; 연속 gait timing·foot contact는 미측정.
- 분석: Default `17.90699/70`, Pilot `41.97990/70`, delta `+24.07291/70`; 둘 다 `INTERNAL_GATE_FAIL`; 분기 `SHARED_WEAKNESS_FOUND`.
- 보고서: `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.
- NEXT: Default 계보 `feet_air_time .01→.2` 단일변수 1,000-iter screening을 별도 작업 ID로 사전등록한다.

## 12. Go2 단일변수 screening package — `G-A007` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A007` | 개선 | Default 계보 `feet_air_time 0.01→0.20` only, 1,000 iter | package `VERIFIED` / result `RECEIVED(PARTIAL)` | 학습 완료, evaluator 8건 뒤 Isaac Sim crash; 재개 실행 표식은 아직 `[미측정]` | PARTIAL ZIP·SHA 격리, CRC·safe path·training artifact·8 telemetry 확인 | result SHA `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5` | 동일 서버에서 `GO2_RESUME=1`; FULL ZIP·SHA 재회수 전 서버 종료 불가 |

### 사전등록된 artifact·영상 계약

- RUN_ID: `train_260901-Go2_feet_air_time_020_1000`
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `feet_air_time 0.01→0.20`; 나머지 네 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1~G7 정량 worst-case 각 1개, 총 7개, 평가 seed 101/202/303 중 worst seed, 4 env, 500 steps, 약 10초.
- Default 영상은 `VIDEO_NOT_REQUIRED`: 동일 Default-01 tensor·동일 registry/evaluator의 7영상이 G-A006에서 `ARTIFACT_VERIFIED`·`VIDEO_OBSERVED`; `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/default/`을 재사용한다.
- telemetry: candidate 69건, G1~G7 survival·tracking·G5 completion·G6 recovery·G7 실현값.
- 필수 정책 증거: `model_best.pt`, `env.yaml`, `policy.pt`, `POLICY_LINEAGE.json`, source·diff·log·checkpoint·tfevents·params.
- 실패 회수: `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`이 `PARTIAL`로 만들어져 가능한 checkpoint·source·config·launcher log를 보존한다.
- 정상 회수: 같은 결과 ZIP이 `FULL`, `RUNNER_RC=0`, telemetry 69, video 7을 포함해야 한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 위 두 파일 로컬 도착·외부 SHA 일치·ZIP CRC·내부 manifest·69 telemetry·7영상·lineage 확인 전 종료 불가.

### 로컬 검증 증거

- 사전등록 PRD: `workspace/training/quadruped/upload/plan/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`.
- package: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip`.
- package SHA companion: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip.sha256`.
- 상세 검증: `workspace/training/quadruped/go2_feet_air_time_020_v1.VERIFICATION.md`.
- 검증: deterministic rebuild SHA 일치, ZIP CRC·safe path, 내부 manifest 94/94, 단일 reward diff, frozen baseline 69/69·identity, Python compile, contract 5/5, CRLF 0, Git Bash `bash -n`.
- 예상 실행 창: 이전 artifact 실측을 기준으로 1시간 35분~2시간. 전체 서버 과금 시간은 보장하지 않는다.

### PARTIAL 결과 회수 — 260901

- 로컬 원본 보존: `workspace/server_returns/go2_feet_air_time_020_v1_partial_260901/original/`.
- 외부 SHA: `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, companion과 일치.
- ZIP: 96 members, CRC 정상, unsafe path 0, `RESULT_STATE=PARTIAL`, `RUNNER_RC=5`.
- 학습: `TRAIN_RC=0`, seed 42, 4096 env, 1,000 iter; candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`.
- 평가: telemetry 8/69, candidate video 0/7, `POLICY_LINEAGE.json` 미생성. 따라서 `ARTIFACT_VERIFIED` 미달, `VIDEO_UNKNOWN`, `INTERNAL_GATE_INCONCLUSIVE`, `OFFICIAL_RESULT_UNMEASURED`.
- 실패점: `G2/combined_yaw_left`, eval seed 101 시작 시 Isaac Sim startup segmentation fault; 이미 완료된 8건은 fingerprint로 재사용 가능하다.
- 내부 manifest: 95건 중 94건 일치, `launcher.log` 1건은 manifest 생성 뒤 tee가 계속 기록하는 기존 packaging 순서 문제로 불일치. 외부 ZIP SHA와 CRC는 일치하지만 FULL 결과에서 다시 감사한다.
- 고정 검사 도구 `tools/verify_download_artifact.py`는 tar/gzip 전용이라 ZIP 입력을 `ESCALATE`했다. 메인 루프가 ZIP CRC·safe path·manifest·count를 직접 검증했다.
- 재개 명령: `cd /workspace/go2_feet_air_time_020_v1 && GO2_RESUME=1 bash server_run_go2_feet_air_time_020_v1.sh`.
- 서버 종료 게이트: FULL 결과 ZIP·SHA를 다시 내려받아 telemetry 69·video 7·lineage·policy와 무결성을 로컬 검증하기 전까지 **종료 불가**.

### 파일 변경 원장 추가

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260901 | `G-A007` | screening PRD·runner·reporter·builder·tests·README·ZIP | Default report 재사용 + candidate 1회 학습/69-case/7영상/단일 결과 ZIP 구현 | deterministic SHA, ZIP CRC·manifest, compile, tests 5/5, `bash -n`, CRLF 0 |
| 260901 | `G-A007` | Go2 PRD·상태·일정·reward master·planner brief·AGENTS | 단계 3 현재 위치, 사전 gate, package 경로·실행·회수·종료 조건 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 13. Go2 evaluator graceful-shutdown hotfix ? `G-A008` (260901)
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 확인한 정상 기록: `workspace/training/quadruped/go2_feet_air_time_020_v2.VERIFICATION.md`(v2 원인·수정·패키지 SHA·검증, 정상 영문), `GO2_OPUS_REAUDIT_INDEPENDENT_260907.md:296`(G-A008 요약 1행). 이 절의 표·파일 변경 원장 문구는 대체 기록 미확보.

| ?? ID | ?? | ?? | ?? | ??? ?? | ?? ?? | ?????? | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A008` | ??(????) | G-A007 candidate ??? ?? evaluator ?????? ?? ?? | `VERIFIED` | v1 ?? ?? `[???]`; v2 ?? ?? ?? ?? | PARTIAL ?? ??, graceful stop, bounded retry, stable manifest, deterministic package | `go2_feet_air_time_020_v2.zip`, SHA `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`, tests 6/6 | ?? v1 ??? ?? ?? ??; v2? completed case?checkpoint ??? ?? |

### ????? ??

- `BUGGY_DO_NOT_REUSE`: v1 telemetry? hard process exit ??? retry ?? runner.
- ?? ??: v1? 8 case ?? ? ?? Isaac startup? `XOpenDisplay` ?? segmentation fault? ?? ??? ????.
- ?? ?? ??? ??: ?? horizon?? `env.step()` ???? ????? ?? ??? upstream `env.close()`?`simulation_app.close()`? ????.
- v2: hard-exit AST call 0, `simulation_app.is_running()` false? ?? loop exit, case/video ?? 3? bounded retry, ?? case fingerprint ???.
- manifest ??: active `launcher.log`? ???? immutable `launcher.snapshot.log`? package??.
- ??: deterministic SHA, ZIP CRC, safe path, manifest 94/94, Python compile, contract 6/6, Git Bash `bash -n`.
- ??: NVIDIA Kit ?? segmentation fault ??? ???? ???? ???. v2? ?? cleanup? ???? transient startup failure? ?? ??? ?? ???? ??? ??.

### ?? ?? ??

| ?? | ?? ID | ?? | ?? ?? | ?? |
|---|---|---|---|---|
| 260901 | `G-A008` | `go2_eval_telemetry.py`, runner, result packager | hard exit ??, graceful close, bounded retry, live-log manifest race ?? | compile, contract 6/6, AST hard-exit 0, `bash -n` |
| 260901 | `G-A008` | builder, v2 README, v2 ZIP, verification | ??? ?? ?? ?? resume hotfix package | SHA `73c6ba1f?8dbc`, deterministic rebuild, CRC, manifest 94/94 |

## 14. Go2 feet_air_time 0.20 FULL 재수신 — `G-A007` (260901)

- 등급: `개선`
- lifecycle: `RECEIVED`
- 로컬 inbox: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`
- 수신 시각: 2026-09-01 20:53 KST
- 파일 크기: 207,738,612 bytes
- 외부 ZIP SHA-256: `ec45628bae08092f7d671ea5c4cc409d9a247bde80e5bd4214d13b191239effc` (companion 일치)
- 1차 비파괴 검사: ZIP CRC 정상, unsafe path 0, `RESULT_STATE=FULL`, 69개 case `EVAL_RC=0`, 영상 7개, `policy.pt`·`POLICY_LINEAGE.json`·`model_best.pt`·`env.yaml` 존재.
- 격리 예정 경로: `workspace/server_returns/go2_feet_air_time_020_v1_full_260901/`
- NEXT: 격리 추출 → 내부 manifest/정책 lineage/69 telemetry/7 영상 검증 → 선택 병합·분석·원장 갱신.

## 15. Go2 track-linear 단일변수 screening — `G-A009` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A009` | 개선 | Default 계보 `track_lin_vel_xy_exp 1.0→1.2` only, 1,000 iter + 저비용 단계평가 | `REPORTED` | ZIP 업로드·한 줄 실행·결과 ZIP 2종 다운로드 완료 | 격리·무결성·정량 비교·G1 영상 판독·원장 갱신 완료 | result SHA `d9d84f68…61c3`, manifest 125/125, candidate/baseline 7/7, G1 `VIDEO_OBSERVED`, 분석 보고서 | G-A010 engine+JSON 로컬 준비 |

### 사전등록 artifact·영상 계약

- RUN_ID: `train_260902-Go2_track_lin_vel_120_1000`.
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `track_lin_vel_xy_exp 1.0→1.2`; 나머지 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1 forward-fast seed 101, 4 env, 500 step, 1개.
- telemetry: 조기중단 candidate 7 + baseline 7; 조기통과 때 candidate 21 + baseline 7.
- 결과 ZIP: `/workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 실패도 `PARTIAL` ZIP으로 checkpoint·source·config·log·완료 case를 자동 보존한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 두 파일 로컬 도착·외부 SHA·ZIP CRC·manifest·예상 case 수·영상 1·policy lineage를 검증하기 전 종료 판정 금지.

### package 검증

- 경로: `workspace/training/quadruped/go2_track_lin_vel_120_v1.zip`.
- SHA-256: `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`.
- 6,467,257 bytes, 46 members, CRC OK, unsafe path 0, manifest 45/45.
- deterministic rebuild SHA 동일, Python compile, contract 9/9, Git Bash `bash -n`, CRLF 0.
- evaluator: G5 per-env body-velocity integral v2, G7 `NCRC_EVAL_DR=1`, 공식 등가성 주장 없음.

### result 회수·종료 게이트 검증

- 수신 파일: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 격리 원본: `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/original/`.
- 외부 ZIP SHA-256: `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`; companion 일치.
- package: 126 members, CRC 정상, unsafe path 0, 내부 manifest 125/125 일치, `RESULT_STATE=FULL`, `RUNNER_RC=0`, `TRAIN_RC=0`.
- 학습물: model SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`, `model_900.pt`, `env.yaml`, tfevents, params, source, reward diff 확인.
- 평가물: candidate/baseline telemetry 7/7, candidate G1 영상 1/1(1,932,776 bytes), `POLICY_LINEAGE=ACTOR_TENSORS_MATCH` 8/8.
- 증거 계층: `ARTIFACT_VERIFIED`, G1 `VIDEO_OBSERVED`, runner decision `INTERNAL_EARLY_KILL_FAIL`, `OFFICIAL_RESULT_UNMEASURED`.
- 종료 판정: 필수 회수물 누락 0; 서버 종료 가능. 상세 검증은 격리 경로의 `VERIFICATION.json`, `INGEST_STATUS.md`, `LOCAL_SHA256SUMS.txt`에 보존.

### result 분석·영상 증거 보존

- 분석 보고서: `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`.
- 찾기 쉬운 영상: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/videos/G1_forward_fast_seed_101.mp4`.
- contact sheet: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/contact_sheets/G1_forward_fast_seed_101_contact_sheet.jpg`.
- 영상 원본↔복사본 SHA-256: `9d81170136efebbcfb1e708a36b438900365a1da47a32d1cc25a83ba303c6cdb`, 일치.
- 정량 CSV: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/G_A009_COMPARISON.csv`.
- 기계판독 요약·해시: 같은 폴더의 `ANALYSIS_SUMMARY.json`, `SHA256SUMS.txt`.
- 최종 계층: `ARTIFACT_VERIFIED`; G1 `VIDEO_OBSERVED`; G-A009 `INTERNAL_EARLY_KILL_FAIL`; `OFFICIAL_RESULT_UNMEASURED`.

## 16. Go2 `lin_vel_z_l2` 단일변수 screening — `G-A010` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A010` | 개선 | Default 계보 `lin_vel_z_l2 -3.0→-2.0` only, 1,000 iter + tier-1 조기평가 | `PLANNED` | `upload/G-A010/current`의 engine ZIP·JSON 업로드 후 한 줄 실행 | 고정 engine v1.1·JSON·PRD·run guide·contract 검증 완료 | engine SHA `e8f8b3cd…b7cd`, spec SHA `e59dcb93…f8c9`, 34 members, manifest 33/33, tests 8/8, `bash -n` | 서버 실행 → 결과 ZIP 2종 회수 |

- 기준 policy: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `lin_vel_z_l2 -3.0→-2.0`.
- 고정 reward: `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 고정 학습: from-scratch, seed 42, 4096 env, 1,000 iter.
- `VIDEO_REQUIRED`: candidate G1 `forward_fast`, seed 101, 4 env, 500 step, 1개. 학습 종료 뒤 이상 징후가 있으면 추가 시나리오를 재판정한다.
- 조기평가: candidate G1~G7 대표 7-case, repaired-v2 baseline과 paired 비교. G1 proxy `+0.05` 미만 또는 어느 G survival `-0.10` 초과 하락이면 즉시 종료·회수한다.
- 대표평가·69-case·장기학습은 tier-1 조기통과 전 금지한다.
- 현재 upload engine ZIP: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA-256 `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 현재 upload JSON: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA-256 `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 검증: deterministic rebuild, ZIP CRC, unsafe path 0, manifest 33/33, extracted-engine materialization, contract 8/8, Python compile, CRLF 0, Git Bash `bash -n`.
- 서버 한 줄 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.
- 완료 표식: `[DONE] GO2_LIN_VEL_Z_M2_RESULT_READY`.
- 결과 ZIP: `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256`; 성공·실패 모두 가능한 artifact를 단일 ZIP으로 자동 묶는다.
- 실행 지침: `workspace/training/quadruped/upload/G-A010/current/GO2_G_A010_RUN_GUIDE.txt`; package 상세: 같은 폴더의 `go2_tuning_engine_v1_1.VERIFICATION.md`.
- 현재 계층: upload package만 `ARTIFACT_VERIFIED`; 외부 실행·checkpoint·telemetry·영상은 `[미측정]`, `OFFICIAL_RESULT_UNMEASURED`.

## 17. G-A010 server-preflight Python launcher hotfix — `G-A012` (260902)

- 최초 engine v1.0은 bare `python3`를 호출해 서버에서 `command not found`로 종료됐다. tmux·학습은 시작되지 않아 iteration 소비는 0이다.
- v1.0 SHA `4489bef4…8a5a`는 `BUGGY_DO_NOT_REUSE`다.
- hotfix engine: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 같은 폴더의 spec: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 수정: validate·shell-env·materialize를 모두 `/workspace/IsaacLab/isaaclab.sh -p`로 실행하고 bare `python3` 의존을 제거했다.
- 검증: ZIP 34 members, CRC, unsafe 0, manifest 33/33, contract 8/8, extracted materialization, compile, CRLF 0, `bash -n`.
- 새 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.

## 18. Go2 업로드 staging·이력 체계 — `G-A013` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A013` | 필수(운영) | Go2 서버 입력의 단일 업로드 진입점과 버전 이력 | `REPORTED` | `upload/<ID>/current`에서 지시된 두 파일만 선택 | current/history 분리·SHA copy 검증·append-only ledger 자동화 | `upload/README.md`, `G-A010/UPLOAD_HISTORY.tsv`, `tools/publish_go2_upload_bundle.py` | 이후 모든 Go2 실행 package를 동일 체계로 publish |

- 사용자 업로드 진입점은 `workspace/training/quadruped/upload/<EXPERIMENT_ID>/current/`로 고정한다.
- `history/<RELEASE_ID>/`는 release snapshot이며 과거 파일을 현재 사용본으로 승격하지 않는다.
- `UPLOAD_HISTORY.tsv`는 v1.0 `WITHDRAWN_BUGGY_DO_NOT_REUSE`와 v1.1 `ACTIVE_ARTIFACT_VERIFIED`를 분리 기록한다.
- publisher는 원본과 current/history 복사본 SHA를 비교하고, 같은 release identity는 ledger에 중복 추가하지 않는다.


## G-A027-RESULT-AUDIT-20260909 — 독립 결과 감사 착수
- 대상 실행: G-A027 (기존 A017/Pilot 재평가). 등급: 조사.
- 상태: PLANNED. 회수 여부부터 확인하며 외부 실행/수신을 추정하지 않는다.
- 범위: 승인 입력 고정, 로컬 회수물 탐색, 실제 입력이 있을 때만 검증·비교. 기존 파일 병합·삭제 없음.
- 예정 증거: workspace/server_returns/G-A027/audit_20260909/INPUT_INVENTORY.json 및 root 결과 감사 보고서.

### G-A027-RESULT-AUDIT-20260909 — 2026-09-10 재개 / H1-CAL-20260910
- 새 관찰: `_keep/GO2_A017_FULL_SUITE_RESULT.zip`, 동명 SHA, 결과 디렉터리 존재. 과거 미회수 관찰을 현재 상태로 사용하지 않는다.
- 상태: RECEIVED → VERIFIED. 외부 실행은 회수 RUNNER_STATUS의 rc=0·TRAINING=none과 대조했다. 새 학습이 아니다.
- 범위 확장: 사용자 전사 H1 공식 57.45/70과 자체 점수 비교, 보정 참고점수 추가, Go2 별도 적용 검토. 기존 채점·원자료 보존은 사용자 명시 결정이다.
- 격리: `workspace/server_returns/G-A027/received/`. training 병합 없음(MERGED 해당 없음); 상태를 임의로 건너뛰어 REPORTED로 표기하지 않는다. 로컬 감사 보고서는 별도 완료 기록.
- 검증: 반환 ZIP SHA `5108b047175c6fc0cb0982b1434c686e413bac5d75469ae9c71cb2d17d144ace`, ZIP CRC·안전 경로, 내부 manifest 882/882, 승인 package 대비 model/env 4/4 일치. tar 전용 공용 도구는 ZIP 적용 대상 밖이므로 ZIP 검사와 전용 harvest 도구를 사용했다.
- 정량: 전용 검증기 exit 0, 두 arm 69/69 `INTERNAL_MEASUREMENT_OK`. 파일 무결성 및 측정 유효성 판정이지 정책 성능 통과가 아니다.
- 산출물: `workspace/server_returns/G-A027/audit_20260910/`, `GO2_RESULT_AUDIT_G-A027_20260910.md`, `H1_OFFICIAL_CALIBRATION_20260910.md`. 초기 예정 디렉터리 audit_20260909 대신 실제 재개일 audit_20260910 사용.

### G-A027-RESULT-AUDIT-20260909 / H1-CAL-20260910 — 2026-09-11 로컬 감사 마감
- 파일 lifecycle VERIFIED 유지, training 선택병합 미실시(MERGED 해당없음). 별도 로컬 감사·보고 산출물 완료.
- H1 공식 전사·raw/보정 비교를 workspace/calibration/h1_official_20260910/에 보존. 기존 결과 덮어쓰기 없음.
- Go2 기존/보정 결과와 원자료를 workspace/server_returns/G-A027/에 격리보존. 영상7개 관찰판정 별도, 하강영상 미확보.
- 보고서 날짜260910은 감사입력일이며 마감일은260911. GO2_RESULT_AUDIT_G-A027_20260910.md와 H1_OFFICIAL_CALIBRATION_20260910.md 참조.

## 2026-09-11 사용자 결정 — 계획 경로·H1 report 회수
- 작업 ID: DOC-20260911-PLAN-REPORT. 상태: PLANNED. 로컬 문서 이동·회수 스크립트 보완이며 서버 실행은 하지 않는다.
- 계획: 기체별 upload/plan으로 계획서·실험 PRD·기획 브리프를 이동하고 참조/빌더 입력을 갱신한다. 회수 snapshot·승인 ZIP·실험 JSON·상태/일정 원장은 이동하지 않는다.
- H1: training/humanoid/exported/report.html을 _keep/<RUN_ID>/exported/report.html에 보존한다. 누락/이전 실행 report는 성공 회수로 표시하지 않는다. 기존 final 경로는 호환 보존한다.
- 검증: 이동 전후 SHA256, 링크·빌더 경로, report 복사 정상/누락/stale 테스트, bash -n. 학습·채점 로직은 변경하지 않는다.

### DOC-20260911-PLAN-REPORT 완료 기록
- 상태: REPORTED (로컬 작업). 서버 실행·배포는 미수행.
- 이동 11건: H1 2건, Go2 9건. 이동 직후 원본 SHA 일치 확인. 경로 참조 수정 후 해시는 PLAN_MIGRATION_20260911.json의 post_reference_sha256에 별도 보존. 참조 갱신 파일은 PLAN_REFERENCE_UPDATES_20260911.json.
- 검증: `python -m unittest tools.test_h1_report_recovery -v` 5 tests, exit 0; `python -m unittest tools.test_go2_feet_air_time_020_contract tools.test_go2_track_lin_vel_120_contract -q` 12 tests, exit 0; `python tools/validate_go2_campaign.py` exit 0; `git diff --check` exit 0. H1 test에 LF·bash -n·정상/누락/빈/stale report 검사가 포함된다.
- 한계: .codex/agents는 호스트 읽기 전용이므로 옛 참조를 직접 수정하지 않았다. 상위 AGENTS의 migration 매핑 우선 규칙으로 경로를 해석한다. 회수 snapshot·승인 upload release는 변경하지 않았다. 기존 패키지 빌더 테스트는 개발용 ZIP을 재생성하므로 새 서버 승인본으로 취급하지 않는다.
- 학습 배포 원본(train.py/play.py/task/reward), 채점식 및 A027 튜닝 제안값은 변경하지 않았다. H1 회수 변경은 server_run06_long.sh에 적용, 평가 전용 runner에는 현재 exported의 오래된 report를 자동 연결하지 않는다.

### H1-CAL-20260910 — 2026-09-11 제출 안내본 역추적
- 사용자 요청: 실제 제출하도록 안내했던 파일·기록으로 H1 정책과 report 대응을 확인한다. 기존 작업 ID 재사용, 로컬 읽기·해시 대조만 수행한다.
- 승인 기대값: PROJECT_STATE.md:1203-1208, UPLOAD_READY/SHA256SUMS.txt 및 RUN06_PROMOTION_SHA256SUMS.txt. 회수 report의 자체 주장만으로 제출본을 정하지 않는다.
- 역추적 완료: 제출 지시 경로 Run06 UPLOAD_READY 확인, manifest 3/3·회수 model/env 기대 SHA 2/2 일치(exit 0). SUBMISSION_INSTRUCTION_TRACE_20260911.json 보존. 외부 업로드 identity와는 분리. 서버 실행 없음.

## GO2 next tuning preparation - 2026-09-13
- User requested preparation for the next quadruped tuning. Work ID: GO2-P1-PREP-20260913. Lifecycle: PLANNED. No server execution or new training performed.
- Plan: workspace/training/quadruped/upload/plan/GO2_A027_NEXT_TUNING_PREP_20260913.md; adjacent JSON fixes 18 diagnostic cases. Existing policies, rewards and approved releases preserved.
- Evidence: existing CSV stores actual_wz, not wx/wy; run_video does not request simultaneous telemetry. Prior assumption that existing angular channels suffice is withdrawn.
- Four review findings addressed in the plan. Numeric diagnostic thresholds, separate instrumentation and independent review remain open. HOLD: package unverified, training evidence insufficient. Historical schedule remains CLOSED.
- Local verification: 5 preparation-contract assertions passed (18 unique cases); git diff --check passed. No runtime/package test claimed.
`n### GO2-P1-PREP-20260913 report follow-up`n- 2026-09-13: user requested returned A027 report review. Local discovery/content and identity checks only; no merge or server execution.

<!-- GO2:REPORT-FIRST:START -->
## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
<!-- GO2:REPORT-FIRST:END -->

### GO2-P1-PREP-20260913 — review bundle packaging
- Local documentation packaging only; preparation remains PLANNED. No server execution, training approval, artifact merge or policy change.
- Output (corrected by G-D-UPLOAD-PATH-20260913): workspace/training/quadruped/upload/GO2_TUNING_REVIEW_MATERIALS_20260913.zip. Includes source snapshots and manifest; not a server execution package.

### GO2-P1-PREP-20260913 — package path correction
- User decision G-D-UPLOAD-PATH-20260913: plan/ is for planning documents only; packages belong in upload/ or existing release directories.
- Local relocation of review ZIP and SHA only. Verify SHA before/after; preserve contents and historical releases. No server execution approval.

### G-D-UPLOAD-PATH-20260913 — 사용자 경로 정정
- plan/은 계획 문서 전용. ZIP·SHA·배포 manifest·실행 파일은 upload/ 또는 기존 작업별 release 경로에 저장한다.
- 검토 ZIP·SHA를 workspace/training/quadruped/upload/로 이동했고 이동 전후 SHA가 일치한다. 검토용이며 실행 승인본은 아니다.

### G-D-NUMBERING-20260913 — G-A028 예약
- G-D98/G-D175/G-D178 재확인. 원장·upload 검색에서 G-A028 기존 등록 없음; 다음 준비 회차로 예약한다.
- GO2-P1-PREP-20260913은 G-A028 준비 작업 별칭이다. 상태 PLANNED, 미실행, 학습 승인 없음.
- 검토 자료 경로: workspace/training/quadruped/upload/G-A028/review/GO2_G_A028_TUNING_REVIEW_MATERIALS_20260913.zip. 실행 정본 current/는 아직 발행하지 않는다.
- 이전 무번호 upload 루트 경로는 이 경로로 대체한다. 기존 승인 release는 보존한다.

### G-A028 — 2026-09-13 실행 준비 선행조건 실측
- 기존 G-A027 current의 RUN_GUIDE·builder·runner·발행 도구를 직접 확인했다. 다음 실행 정본도 같은 current/history/manifest/guide 체계를 사용한다.
- workspace 내 upload/history 제외 ZIP·tar.gz 52개 내부 목록까지 검색했다. A017 원 학습 report.html은 발견하지 못했다. A017 결과 ZIP(GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip)에도 없다. 검색 오류 0건.
- 증거: workspace/training/quadruped/upload/G-A028/review/REPORT_RECOVERY_SEARCH.json. 기존 Pilot 계열 exported/report.html로 A017 보고서를 대신하지 않는다.
- 실제 차단: REPORT_REQUIRED_NOT_ACQUIRED 및 다음 단일 변경값 미확정. 실행 패키지 완성·서버 실행을 주장하지 않는다. report 원본은 외부 보관 사본 회수가 필요하며 과거 checkpoint로 당시 학습 HTML을 꾸며 생성하지 않는다.
- 배포 train.py/play.py/go2_task/quadruped_rewards.py 변경 없음. 학습 미실행. G-A028은 PLANNED 유지.

### GO2-REPORT-RECOVERY-20260913 — PLANNED
- User requires server-generated report.html in every future tuning _keep and result bundle. Scope: active Go2 tuning engine recovery, regression tests, guidance; no training-path edits or historical release replacement.
- Plan: preserve model/env/logs before report gate, copy report to _keep/<run>/exported/report.html, pin SHA and freshness, reject missing/empty/stale reports and incomplete resume; exercise local fixtures and ZIP/SHA inclusion.

### GO2-REPORT-RECOVERY-20260913 — 로컬 구현·검증
- 사용자 결정: 앞으로 튜닝 결과 _keep/<튜닝명칭>/exported/report.html에 서버 생성 원본을 필수 회수한다. ZIP·SHA에도 포함하며 누락/빈 파일/이전 실행 report는 REPORT_REQUIRED_NOT_ACQUIRED다.
- 공용 server_run_go2_tuning_engine_v1.sh에 학습 시작 marker, 평가 전 report 보존, SHA, resume 재검증, 누락 시 PARTIAL 회수 및 비정상 종료를 구현했다. report 검사 전에 model/env/policy/log를 보존한다. train.py/play.py/go2_task와 기존 승인 ZIP은 수정하지 않았다.
- 검증: report 전용 5개(정상 ZIP/SHA 포함·누락·빈 파일·stale·bash -n/LF), 기존 report 지침 8개: 총13개 성공. py_compile 성공.
- 전체 engine 계약19개 중16개 성공,3개는 baseline model/env identity mismatch로 실행 차단. 새 실행 ZIP 발행 완료로 주장하지 않는다. 테스트 build 출력은 임시 디렉터리로 격리했다.

### G-A028 P1 — 실행 패키지 사전등록
- PLANNED. 기존 계획 P1(학습 없는 낙상 진단)을 실행 파일로 구현한다. 보존 A017/Pilot × G5 하강10/15cm·G4 +20도 × seed101/202/303,18영상,4env,1000step. 같은 재생 telemetry 필수.
- 기존 A027 32env 정량은 재사용. 4env 새 영상 telemetry를 기존 rollout에 결합하지 않는다. wx/wy·발접촉 채널은 없으며 회전 인과와 /70 점수를 판정하지 않는다.
- report: 새 학습 없음으로 신규HTML NOT_APPLICABLE, 원 A017 MISSING/Pilot READ_UNMATCHED 유지. 실패에도 model/env·로그·부분 결과 ZIP 회수. 실제 서버 실행은 미측정.
- 종료:18영상·18유효summary·telemetry·로그·SHA 확보. 판독은 별도 VIDEO_UNKNOWN부터 시작. 새 학습은 자동 착수하지 않는다.

### G-A028 P1 — 실행 패키지 발행(2026-09-13)
- current: workspace/training/quadruped/upload/G-A028/current/GO2_G_A028_P1.zip. SHA256 0d9843681e7d1b852273a09c0964c94cef47d3ac4a8c153d5d84ee6bc25eaacf. history/20260913_p1 및 UPLOAD_HISTORY.tsv 보존.
- 기존 계획 P1의 서버 재생 실행 패키지다. P2 새 튜닝 학습 패키지와 구별한다. 가중치 변경/학습 없음. 18영상·동일 실행 telemetry/summary·로그·model/env를 단일 결과 ZIP으로 회수.
- 검증:15 tests 성공(모의18case완료·실패부분회수·기존결과보존·report 회수 포함), CRC/내부SHA30개·bash -n·py_compile·diff check 정상. 실제 IsaacLab 실행은 미측정. ARTIFACT_VERIFIED_LOCAL_TESTED, 성능 판정 아님.
- 공용 학습 engine의 Default baseline hash 문제는 P1에 해당하지 않는다. P1은 승인 A027 ZIP SHA를 직접 검증하고 두 보존 정책과 계측 소스를 그대로 사용한다. 일반 학습 engine의 남은 문제를 해결했다고 주장하지 않는다.
- 원 학습 report 공백은 유지, 새 학습 HTML은 평가 전용으로 NOT_APPLICABLE. 신규 튜닝의 report 필수회수는 공용 학습 runner에 별도 구현한 상태.
- 외부 실행 상태 PLANNED. 다음: 사용자 서버 실행·단일결과ZIP/SHA 회수, 로컬 18영상/정량/로그/identity 확인 후 판독. P2 자동 학습 없음.

### G-A028-RESULT-AUDIT-20260913 ? PLANNED ? RUNNING ? RECEIVED
- User reports download complete. Found workspace/_keep/GO2_G_A028_RESULT.zip and SHA, plus extracted GO2_G_A028_P1. Read-only source analysis; preserve original downloads. ZIP-only verification escalated from tar-only artifact verifier. Audit scope: manifest/policy identity, 18 simultaneous video/telemetry cases, report relationship and preregistered expectations. No training or source modification.

### G-A028-RESULT-AUDIT-20260913 ? result/report relationship correction
- Download verified: ZIP SHA 6e4a807b276e566e01aa58e5f12a61f01e74df999809e975220f69722794ed1e; internal SHA192/192, model/env4/4,18 valid telemetry cases.18 videos decoded, each999frames/19.98s; exact step/frame alignment unverified. ARTIFACT_VERIFIED only.
- Report body read: existing Pilot HTML READ_UNMATCHED; A017 HTML MISSING; A028 new HTML NOT_APPLICABLE(TRAINING=none). No new training occurred.
- Frozen proxy survivors (3seeds x4env): A017 stairs10=0/12, stairs15=0/12, slope+20=11/12; Pilot2/12,0/12,12/12. No /70 score. SELF_ASSESSMENT_INCOMPLETE.
- IMPORTANT correction: stairs_down label does not establish actual descent. Sampled video shows approach/stalling inside inverted stairs. Withdraw unconditional descent-fall explanation; descent coverage VIDEO_UNKNOWN.
- IMPORTANT measurement limit: approved telemetry uses mean scanner ray height, not ground directly under body. Stair boundary bias can contribute to low-height verdict; physical fall interpretation INTERNAL_GATE_INCONCLUSIVE. Applies to same A027 measurement method too; preserve historic numeric outputs, do not promote them to verified physical falls.
- Report does not replace videos,steps.csv,execution logs or policy/config identity. Current strongest observed problem is stair stalling, not proven excessive roll/pitch. -0.06 remains DEFERRED_HYPOTHESIS; no new training or reward change authorized by these results.
- Evidence/report: workspace/server_returns/G-A028/audit_20260913/REPORT_RELATIONSHIP_AUDIT.md; case_metrics.json, artifact_verification.json, video_validation.json, contact sheets. Original downloads preserved; ZIP/SHA copied to workspace/server_returns/G-A028/received/. No training merge.
- File lifecycle RECEIVED ? VERIFIED. MERGED not performed (no training merge); separate analysis/report work completed. Future action: resolve scenario/height semantic gaps before selecting a reward; no server action requested.

### GO2-ALL-SCENARIO-PRIORITY-20260913 ? PLANNED ? RUNNING
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 대체 기록 미확보(저장소에서 `GO2-ALL-SCENARIO-PRIORITY-20260913`의 정상 기록을 찾지 못했다).
- ??? ??: ?? ??? ????? ?? G1~G7? ?? ??? ????? ?? ????? ????? ??. ?? A027/A028 ?? ??? ??? ????? ????? ??? ???? ???. ?? ??? ?? ??? ????.

### G-A029 — 2026-09-14 난이도 기반 튜닝 파일·회수 계약 점검
- 작업 상태 PLANNED. 원장 및 upload에서 G-A029/G_A029 중복 없음 확인 후 예약.
- 사용자 요청: 난이도 기반 튜닝 정책에 맞는 파일 준비, 서버 원본 report.html 회수와 파일 양식 검증.
- 범위: 로컬 검토 spec·계획·회수 테스트. 새 reward 후보 확정/서버 실행/학습/기존 release 변경 없음.
- REPORT_REQUIRED_NOT_ACQUIRED(A017) 및 다음 단일변수 근거 미확정으로 current 실행본 발행 금지. review 자료만 생성.
- 영상: 이번 로컬 테스트는 정책 미생성으로 VIDEO_NOT_REQUIRED. 향후 실제 튜닝 영상은 필수이며 대상 case/seed/수량은 실행 전 동결.

### G-A029 — 2026-09-14 로컬 검토 파일 및 회수 검증 결과
- 사용자 요청을 난이도 기반 검토 정책으로 기록: 낙상 완치 대신 기대 이득·비용·원인 확실성을 함께 비교. G3 또는 특정 reward의 실행 우선순위 확정은 아님.
- 계획: workspace/training/quadruped/upload/plan/GO2_G_A029_DIFFICULTY_SCREENING.md.
- 검토 파일: workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_TUNING_REVIEW.zip (+SHA). 실행 JSON과 구별되는 NON_EXECUTABLE_TUNING_REVIEW, execution/training=false, single_change=null. current 미발행.
- 회수·지침·엔진 계약 총32 tests 성공. 정상 report의 ZIP/SHA 포함, missing/empty/stale 거부, bash -n/LF 확인. 회수 후 본문과 정책 의미 대응은 별도 필요.
- 발견/수정: 러너 CRLF를 LF로 정규화하고 .gitattributes로 고정. Windows shell fixture PATH 고정. 엔진 계약 테스트가 기존 ZIP을 덮어쓰던 부작용을 임시폴더 빌드로 차단.
- 이번 테스트가 변경한 기존 엔진 ZIP/SHA 두 파일만 초기 clean 상태 및 HEAD=index 확인 후 원 바이트 복원. 후속 테스트에서 두 파일 불변 확인. 승인 upload/current/history 변경 없음.
- 증거: review/GO2_G_A029_VALIDATION.json 및 GO2_G_A029_TEST_OUTPUT.txt. ZIP CRC/내부SHA 확인. 실제 서버/성능 미측정.
- A017 원 학습 report MISSING 및 변경값 미확정 유지. 로컬 파일 준비 완료이나 학습 작업 상태 PLANNED, 실행본 생성은 HOLD. 이전 engine baseline 실패 기록은 이번 로컬19개 계약 테스트 성공으로 현 상태 정정하며 A017 실행 spec 검증 완료를 뜻하지 않음.

### G-A029 ? ?? ?? ?? ? ?? ??? ?? ?? (2026-09-14)
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 관련 정상 기록: 같은 파일 위 「G-A029 — 2026-09-14 난이도 기반 튜닝 파일·회수 계약 점검」 절. 두 절의 내용이 같은지는 확인할 수 없다.
- ?? ?? ID ??. ?? ???? ??? reward ?? ??/?? ??. ?? lifecycle PLANNED ??. ? ?? report ???? ? ?? ??/?? ??/?? current ?? ??. ?? artifact ? ?? release ??.

### G-A029 ? 2026-09-14 ?? ?? ?? ? ?? ??? ??
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 같은 주제의 확인한 정상 기록: `workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md`, `workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_ACTION_RATE_M0008_DRAFT.json`. 손상 줄의 "35 unittest" 검증 결과는 대체 기록 미확보(`review/GO2_G_A029_TEST_OUTPUT.txt`는 32 tests로 다른 회차다).
- ??? ??: ?? ?? ??? ???? ???? ????? ?? ?? ?? ??. ?????? ?? ??? ?? ???.
- ?? ???: workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md. G3/G7 ?? ??? ?? ???? G1/G2 ???G4/G6 ?? ??, G5 ??? ?? ????. ?? ??? ?? ??? ?????? ?? ???.
- A017 ??? ??: action_rate_l2 -0.01?-0.008(20% ?? ???, ??/??? ???). ?? Python reward ?? ??? baseline ??, ??? JSON? upload/G-A029/review? ??. ?? ??? ?? ??? ??.
- REPORT_READ_STATUS: A017 MISSING, Pilot READ_UNMATCHED ??. ?? ??: ?? engine? A017 frozen baseline ???, ?? manifest ? ?? ?? ?? ???. ?? ?? ??/current/history ?? ??.
- ?? ??: 35 unittest ??(?????Python ??/LF??????report fresh/missing/empty/stale?ZIP/SHA?shell ???engine ??). ?? ??/?? ?? ???. ?? lifecycle PLANNED, ?? ?? ??.

### G-A029 — 2026-09-14 continuation resume audit
- NEW-CONTINUATION; existing work ID retained, lifecycle PLANNED. Scope: plan section 3 only; inspect newly available report copies, no repeat of 52-archive scan, no server/training/release mutation. Local read-only checks require no new video (VIDEO_NOT_REQUIRED: no policy generated).

### 2026-09-14 G-A029 §3 종료 — HOLD / 원 보고서 회수
- NEW-CONTINUATION으로 지정 계획 §3을 종료했다. -0.008은 조건부 실험 가치만 인정하며 후보 확정/학습 승인이 아니다. A017 REPORT_READ_STATUS=MISSING / REPORT_REQUIRED_NOT_ACQUIRED로 실행본 발행 차단.
- 기존 52archive 재검색 없이 목록 밖 ZIP 6개를 확인했으나 report.html 0개. 상세 경로·직접 코드/로그 근거·한계는 GO2_REWARD_EVIDENCE_MASTER.md의 같은 날짜 §3 판단 종료 행과 기존 인계 계획에 기록했다. 깨진 과거 append는 판정 근거에서 제외한다.
- NEXT 하나: A017 원 학습 report.html 외부 보관 사본 회수 → run/env/log/model_900 대응 확인 → 기존 계획 §4 패키지 구현·검증. 추가 서버 진단이나 새 검토 ZIP을 만들지 않는다.
- G-A029 PLANNED, 단계0/6, 서버/학습/실행 ZIP 발행 없음. 역사 일정 CLOSED 유지. 원 자료·승인 release 보존.
### GO2-REPLAN-A029-20260914 — PLANNED
- 사용자 요청: G-A029 감사에 따른 문제 진단과 튜닝 계획. 로컬 원자료 읽기 및 계획/원장 동기화만 수행; 서버 실행·패키지 발행 요청으로 확대하지 않는다. G-A029 REJECTED_BY_AUDIT와 review 보존.
- VIDEO_NOT_REQUIRED: 이번 작업은 정책을 생성하지 않는 로컬 기획. 미래 후보 평가 영상은 필수. 외부 실행 [미측정].

### GO2-REPLAN-A029-20260914 — 감사 후 사용자 요청 재계획
- 사용자 결정: G-A029 감사에 따라 메인 문제를 진단하고 튜닝 계획을 수립한다. 이번 요청은 계획이며 서버 실행/패키지 발행으로 확대하지 않는다. 역사 일정 CLOSED는 유지한다.
- G-A029 REJECTED_BY_AUDIT 및 -0.008 NEXT 철회 유지, review 불변. 과거 A017 HTML 누락을 발행 차단으로 복원하지 않는다.
- 계획 정본: workspace/training/quadruped/upload/plan/GO2_POST_A029_TUNING_PLAN_20260914.md.
- 직접 근거: A018 양 arm 각7case 모두 schema2/v2; A013/A025 baseline은 schema1/2 혼재, candidate는 schema2라 합산 비대칭. A027 G3 rough_lateral seed101/202/303의 base-contact 종료는 17/14/17개(/32), 첫 종료 전0.5초 q=1-gz² 평균 .688/.628/.660. 기울기는 연관성이지 최초 원인 확정 아님.
- 계획값: A017 조건 flat_orientation_l2 0→-1.0 단일변수, G3 접촉 종료/생존 표적; G5 정체·경사 회귀 동시 감시. -1은 관측 기반 단위 크기 exploratory 값이지 upstream 최적값/만족 판정 아님.
- REPORT_READ_STATUS: A017 MISSING(기존 복구 불가 확정 유지), Pilot READ_UNMATCHED(이번 HTML 본문 직접 열람, 정책 대응 미완결).
- NEXT: 다음 미사용 번호로 위 계획의 current 실행 패키지 구현·검증. 이번에 번호 예약/실행 ZIP/서버 명령은 발행하지 않았다. 학습·성능·공식 결과 새 측정 없음.
- 작업 완료: 로컬 분석·계획 REPORTED. 외부 artifact lifecycle은 실행/수신/병합이 없어 진행시키지 않는다. 원 artifact 변경 없음.

### G-A030 — 2026-09-14 실행 패키지 발행 (ARTIFACT_VERIFIED, 서버 미실행)
- 근거: 사용자 결정 `G-D-A030-GO-20260914`(`GO2_PROJECT_STATE.md`). A017 + `flat_orientation_l2 0.0→-1.0`, 측정 경로 (나′).
  - C 보류는 로컬 패키지 범위에서만 풀렸다. 서버 실행은 사용자 결정 대기다.
- 업로드 1개: `workspace/training/quadruped/upload/G-A030/current/GO2_G_A030_flat_orientation_m1.zip`.
  - SHA256 `e4fbdc0033866612ca9804f9479416d7d4e188bf403b23078cdb6591f35eab05`.
  - 서버 위치: `/workspace/GO2_G_A030_flat_orientation_m1.zip`.
  - 한 줄 실행·완료 표식·재측정 명령·종료 게이트는 같은 폴더의 `GO2_G_A030_RUN_GUIDE.txt`에 있다.
- 결과: `/workspace/_keep/GO2_G_A030_RESULT.zip`과 `.sha256` → 로컬 `workspace/_keep/`. 압축을 풀면 `workspace/_keep/go2_g_a030_a017_flat_orientation_m1/`이다.
- 필수 회수물:
  - `exported/report.html`(REPORT_ACQUIRED, 평가 전 보존)
  - 학습 model/env/로그/tfevents, `ENV_REWARD_CHECK.txt`
  - 후보 69 case telemetry
  - A017 표지 5건(재측정 시 69건)
  - 영상 14개(후보 12, A017 2)
  - RUNNER_STATUS, SHA256SUMS
- 서버 종료 게이트: 결과 ZIP·SHA를 받고 로컬 검증이 끝나기 전에는 종료 가능이라고 하지 않는다.
- 회수 검증(GPU 0, 수치 판독 전): `python -B tools/verify_go2_g_a030_harvest.py --harvest workspace/_keep/go2_g_a030_a017_flat_orientation_m1 --out workspace/_keep/go2_g_a030_a017_flat_orientation_m1/harvest_verification.json`
  - INCONCLUSIVE면 점수를 읽지 않는다.
  - BASELINE_REMEASURE_REQUIRED면 `GO2_RESUME=1 GO2_REMEASURE_BASELINE=1`로 A017 69건을 같은 evaluator에서 다시 잰다.
- 영상: VIDEO_REQUIRED. 사람 판독 전에는 VIDEO_UNKNOWN이다.
- 로컬 검증 증거:
  - `tools/test_go2_g_a030_package_contract.py` 24/24, 기존 Go2 테스트 46개와 A017 full-suite 계약, `GO2_CAMPAIGN_CONTRACT_OK`.
  - ZIP 재빌드 동일 SHA, current=history 바이트 동일, SHA sidecar 일치.
  - 회수 검증기 합성 smoke 5종 기대 판정 일치.
  - 러너 preflight 모의 실행이 tmux 기동까지 통과했다. 변조 evaluator와 잘못된 플래그는 거부했다.

### G-A031 + G-A032 쌍 — 2026-09-15 서버 실행·회수 (RECEIVED, 로컬 검증 FAIL·FAIL)
- 업로드: `upload/G-A031_A032/current/GO2_G_A031_A032_basic_motion_pair.zip` `e714d948…7e6c` (계획 §9-1).
- 서버 실행: 13:46~15:59, 두 회차 1단계만.
- 회수: `workspace/_keep/GO2_BASIC_MOTION_PAIR_RESULT.zip` `5ad3f8fd7dd6430bfe68697cb39ec29c410f2aa60b1afb49ae14e4b295050c60`.
  - 안의 `arm_results/`: G-A031 `bd154bc6…0ad9`, G-A032 `a9e9db07…7dd0`.
  - 로컬 `_keep`에 풀린 폴더: `go2_basic_motion_pair_a031_a032/`, `go2_g_a031_a017_feet_air_time_001/`, `go2_g_a032_a017_feet_air_time_010/`.
- 검증: SHA·CRC·내부 SHA256SUMS 일치. `tools/verify_go2_basic_motion_harvest.py` 두 회차 FAIL(1_target_basic_motion), 결함 0.
- 서버 종료: 로컬 검증 뒤 종료 가능 보고(2026-09-15).
- 알려진 결함: 쌍 러너가 게이트 FAIL을 UNDECIDED로 기록했다(`isaaclab.sh -p` 종료 코드 변환). 결과 동일. 후속 러너에서 수정(아래 G-A033).

### G-A033 — 2026-09-15 한 파일 패키지 발행 (ARTIFACT_VERIFIED, 서버 미실행)
- 근거: 계획 §6-3 규칙(`feet_air_time` 쌍 실패 → 0.2 유지, `track` 1.4→1.5), 계획 §12.
- 업로드 1개: `workspace/training/quadruped/upload/G-A033/current/GO2_G_A033_track_lin_vel_xy_150_one_command.zip`.
  - SHA256 `4ddb46da3f1f2526c34f0b843f8583d063104598cb29792758de9ec47d311595`.
  - 서버 위치: `/workspace/GO2_G_A033_track_lin_vel_xy_150_one_command.zip`.
  - 한 줄 실행·완료 표식·재시작 규칙은 같은 폴더의 `GO2_G_A033_ONE_COMMAND_RUN_GUIDE.txt`에 있다.
- 안의 회차 ZIP: `GO2_G_A033_track_lin_vel_xy_150_staged.zip` `0e873d6532f1c6bd98cb726a6de9e92ab5eb413e75cc5feb3e93e6a97ddac7a2`(history에만 있음, 따로 올리지 않는다).
- 결과: `/workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip`과 `.sha256` → 로컬 `workspace/_keep/`.
- 회수 검증: `python -B tools/verify_go2_basic_motion_harvest.py G-A033 --harvest workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150`.
- 서버 종료 게이트: 결과 ZIP·SHA를 받고 로컬 검증이 끝나기 전에는 종료 가능이라고 하지 않는다.

### 2026-09-15 G-A034 A017 오르막 정지 로봇 영상 확인 패키지 (학습 없음)
- 업로드: `workspace/training/quadruped/upload/G-A034/current/GO2_G_A034_slope_inspect.zip` SHA256 `fa4772d66ac1ccbac14f298bbb566e6016c08c0a4abc18fa31660e303908dbc8` (6.4 MB)
- 내용: G-A027 패키지의 A017 정책·play.py·evaluator를 바이트 그대로 재사용(model SHA `0563deff…95a4`) + `server_run_go2_slope_inspect.sh` + `go2_slope_stuck_check.py`
- 목적: slope_plus_20 seed 101에서 저장 기록상 넘어진 로봇 4·18·20·22·24·27·31 중 22·24·4와 대조군 0을 카메라로 따라가 원인(제자리걸음·미끄러짐·웅크림·막힘·뒤로 밀림)을 눈으로 확인
- 결과: `/workspace/_keep/GO2_SLOPE_INSPECT_RESULT.zip` (영상 4개, 재측정 기록, STUCK_CHECK.txt의 재현 판정 REPRODUCED/NOT_REPRODUCED)
- 검증: runner bash 문법 통과, 재현 판정 스크립트는 저장 데이터에서 MATCH, 잘못된 기준 목록에서는 NOT_REPRODUCED. 이 Isaac Lab 버전의 viewer에 env_index가 있음은 저장된 env.yaml에서 확인. GPU 실행 0회, 실행 시간은 미측정

### 2026-09-15 G-A033 v2 발행 — `track` 1.4→1.5, iter 900 고정 평가 (서버 미실행)
- 업로드: `workspace/training/quadruped/upload/G-A033/current/GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip` SHA256 `88be31980a05bac6e1cd2ba72be4cd4e5594119641f7b557a732665a6a85ae41` (6.2 MB)
- 한 줄: `cd /workspace && echo '88be31980a05bac6e1cd2ba72be4cd4e5594119641f7b557a732665a6a85ae41  GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip' | sha256sum -c - && unzip -oq GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip && bash /workspace/go2_campaign_g_a033/server_run_go2_campaign.sh`
- 완료 표식 `[DONE] GO2_G_A033_CAMPAIGN_RESULT_READY`, 결과 `/workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip` + `.sha256`
- v1(`GO2_G_A033_track_lin_vel_xy_150_one_command.zip` `4ddb46da…1595`)은 미실행으로 history에 보존. 서버 종료 판단은 결과 수신 후 로컬 검증을 통과한 뒤.
- 회수 확인 항목 추가: `training/CHECKPOINT_PIN.txt`(EVAL_CHECKPOINT_ITER=900), `training/model_best.pt`(평가한 iter 900), `training/model_best_by_reward.pt`(finalize 선택)

### 2026-09-15 G-A033 v2 서버 결과 회수 (서버 종료 가능)
- 결과: `workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip` SHA256 `b136e708eaccd8b985c3334d52f352061c349eebf2f50bcfabe021651f944154`, 회차 `workspace/_keep/GO2_G_A033_RESULT.zip` SHA256 `57019d2513caa118213cca9941e7ac2d69b8690357b86cf8575b83ab3ea9a10c`
- 풀린 폴더: `workspace/_keep/go2_campaign_g_a033/`, `workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/` (ZIP과 파일 단위 동일)
- 로컬 검증: `python -B tools/verify_go2_basic_motion_harvest.py G-A033 --harvest workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150 --out .../reports/LOCAL_VERIFY_G_A033.json` → FAIL, artifact 결함 0, ruler 불일치 0, 핀 900 확인
- 서버에 남길 것 없음: 모델(900·700)·영상 5·로그가 ZIP 안에 있다

## PM-REPAIR-STRATEGY-20260919

User requested local judgment-validator fixes and evidence-based tuning strategy review. No server execution, new package, reward change or artifact merge. Baseline remains G-A033; last training is G-A038 (2026-09-17). G-A040 is INFORMATION_RUN, not a release or performance promotion. Results and limitations: `workspace/training/quadruped/upload/plan/GO2_PM_REPAIR_STRATEGY_20260919.md`. Existing archives unchanged. VIDEO_NOT_REQUIRED for this tool-only change; no fresh video observation claimed.

### G-DATA-STANDARD-20260920 로컬 후속 검증
- 위 명세 누락 시험과 생성기 수정 완료: 관련 51 tests 성공, 5개 표 129행 재생성. 원자료/legacy CSV/배포 학습 코드 변경 없음. 원 집계 생성기 이관과 raw 재계산은 미완료. 회수/병합 작업 아님.

## G-HANDOFF-MONITOR-20260920 — 전달 감시자 대조 시험
- 로컬 시험 완료. 신규 회수·병합·학습 없음. 원자료와 배포 코드는 변경하지 않음.
- 실제 analyst에 증거 관리자 역할을 부여: 오류 5개(T1/T3/T5/T6/T7)를 모두 기각하고 제한적 정상 주장 3개(T2/T4/T8)를 수용. verifier가 원 CSV와 생성 코드를 별도 확인하여 8개 판정에 동의.
- 독립 감사는 추가 오류 M1(both_channels가 동시 발생을 증명), M2(자동 검사 성공이 의미 정확성과 전 인계 자동 감시를 증명)도 기각. M1/M2는 실제 관리자 발언이 아니라 PM이 주입한 시험 주장임.
- 자동 검사: 초기 5개 모듈 51 tests 성공. 메모리 내 formula/kind/population 허위 변조 3개는 normalize가 모두 수용. 구조 검사의 의미 검증 한계를 재현.
- 감사 중 PM의 PowerShell→Python 기록 경로에서 이 항목의 한글이 물음표로 손상된 것을 encoding 검사로 발견. apply_patch로 해당 신규 항목만 복원하고 재검증. 감사자가 사용한 50-test 조합은 초기 51-test 조합과 다름.
- 판정: 이번 사례의 의미 검토 INTERNAL_GATE_PASS. 자동 전 인계 차단, 일반 오류 검출률, 원자료 전체 재계산은 미검증. 이번 시험은 PM이 명시적으로 전달한 1회 대조 시험이며 기획자·분석가 전체 연쇄 실행은 아님.
- VIDEO_NOT_REQUIRED / REPORT_READ_STATUS=NOT_APPLICABLE — 정책 행동·튜닝값 선정이 아닌 데이터 인계 의미 검사.
- 최종 재검증: data_standard + inference_integrity + detectability + canonical_consistency + evidence_role + role_regression 6개 모듈 58 tests, 9.523초, 종료 코드 0. 인코딩 손상 복원 후 결과이며 초기 감사 실패를 은폐하거나 동일 실행으로 합산하지 않음.
# G-HANDOFF-MONITOR-20260920 운영 반영

- 사용자 요청으로 공통 인계 계약과 기체 지침에 INPUT_REVIEW/OUTPUT_REVIEW/PM_REVIEW 및 버전별 검토 기록, 재사용·재검사·UNKNOWN 처리와 감사 독립성 반영.
- 신규 계약 테스트 실패를 먼저 확인한 뒤 명세 수정. 기존 역할 파일은 공통 계약 참조를 유지하며 보호된 역할 디렉터리를 수정하지 않음. 자동 런타임 훅은 추가하지 않음.
- 원자료·배포 학습 코드·역사 ZIP 변경 없음. 영상/학습 report 비해당인 운영 절차 변경.
