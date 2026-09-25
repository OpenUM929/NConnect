# Go2 PM 보고 — 생성기 집계와 열린 결정 원장

생성 `tools/go2_pm_brief.py`, 증거 `reports/evidence/go2_pm_brief/BRIEF.csv`,
관문 `tools/test_go2_pm_brief_contract.py`. **이 문서를 손으로 고치지 않는다.**

이 문서가 생긴 이유(2026-09-19). 하루 동안 철회된 주장 4건 중 3건이 서브에이전트의 결함이
아니라 **PM 의 중계**에서 나왔다. 판독문·사양·감사문에는 관문이 있는데 **PM 이 사용자에게
직접 하는 말에만 관문이 없었다.** 그래서 수치와 판정을 산문으로 요약해 내지 않고 이 문서를
만들어 가리킨다. 집계는 계약 테스트로 대조하지만 의미 판단은 별도 감사가 필요하다.

## 결함 현황

| 항목 | 수 |
|---|---:|
| 전체 | 23 |
| OPEN | 16 |
| FIXED | 7 |
| ACCEPTED | 0 |
| 중대 | 19 |
| 경미 | 4 |
| OPEN 중 중대 | 13 |
| 재현 확인(`확인`) | 13 |
| 미재현(`추정`) | 10 |

`확인`은 재현 코드를 관문이 **실제로 돌려** 기대 출력이 나온 것이다. `추정`은 보고만 받고
아직 재현하지 않은 것이므로, 중계할 때 확신을 올리지 않는다.

## 닫힌 결함과 그것을 지키는 관문

| 결함 | 관문 |
|---|---|
| `C-1` | `tools/test_go2_g_a041_campaign_contract.py` |
| `C-5` | `tools/test_go2_g_a042_campaign_contract.py` |
| `D-0` | `tools/test_go2_claim_check_contract.py` |
| `S-2` | `tools/test_go2_fact_rules_contract.py` |
| `S-4` | `tools/test_go2_stationary_guard_contract.py` |
| `X-1` | `tools/test_go2_published_release_contract.py` |
| `C-4` | `tools/test_go2_g_a041_campaign_contract.py · tools/test_go2_g_a042_campaign_contract.py` |

## 사용자 결정 대기 — 결함 대장

차단 사유(R-6 위반 · 테스트 실패 · 회수 불가)와 **다르다**. 과학적 불확실성은 차단 사유가
아니라 사전등록 항목이므로 여기 적지 않는다.

| 결함 | 무엇을 정해야 하나 |
|---|---|
| `C-2` | 사용자 결정이 필요하다. (가) 셋을 각각 다음 판으로 다시 내고 옛 바이트는 history 에 보존한다 — 사양과 발행물이 같은 말을 하게 된다(셋 다 비실행·서버에 올린 적 없음). (나) 사양 변경을 되돌린다. 어긋남을 잡는 관문은 이미 있다(test_6). 고친 뒤에는 tools/test_go2_g_a041_campaign_contract.py 의 KNOWN_DIVERGED 를 줄여야 통과한다 — 래칫이라 조용히 되살아나지 않는다. |
| `C-6` | 테스트가 발행 경로에 쓰지 않게 한다 — G-A041·G-A042 계약처럼 `build_payload()` 를 발행된 ZIP 의 members 와 대조만 한다(접두사 `go2_feet_air_time_020_v1/` 를 붙여서). 그렇게 고치면 위 2개 차이가 **테스트 실패로 드러나고**, 그 다음은 사용자 결정이다: (가) 그 회차를 다음 판으로 다시 내거나 (나) PRD 변경을 되돌린다 — C-2 와 같은 모양이다. 고치기 전까지는 전체 테스트를 돌린 뒤 `git checkout -- <그 ZIP>` 으로 되돌려야 한다. |

## 열린 결정 원장

아래는 결함과 별도로 `tools/go2_open_decisions.py`의 OPEN 행에서 읽었다.
결정 대기는 곧 학습 패키지 발행 차단을 뜻하지 않는다.

| 결정 | 해석 쟁점 |
|---|---|
| `U1-R6-ENV-REWARD-20260918` | 배포 `REWARD_WEIGHTS` 6개 목록 **밖**의 env RewTerm 가중치를 바꾸는 회차가 R-6 안인가? |
| `U2-SEED-REPLICATE-20260918` | 같은 설정·다른 학습 seed 로 다시 돌리는 재현 회차가 R-6 안인가? |

결함 원문과 재현 코드는 `reports/GO2_DEFECT_LEDGER.md` 에 있다.
