# 19. go2_a017_full_suite

- 시각: `2026-09-09_20-43-00` (평가 로그 내장값)
- 산출물: `workspace/_keep/go2_a017_full_suite`
- 4족 판별 근거: `go2_self_eval_registry.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

학습 `env.yaml`이 회수되지 않았다. reward 가중치 **모름**.

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `a017` | 39.76495 | 39.76495 | 69 | `posture_gate_v2` | POLICY_LOCOMOTES |
| `pilot` | 33.67132 | 33.67132 | 69 | `posture_gate_v2` | POLICY_LOCOMOTES |

`a017` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 9.39 | 9.37 | 4.97 | 5.36 | 0.00 | 6.10 | 4.57 |

`pilot` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 9.37 | 7.90 | 1.03 | 5.55 | 0.00 | 6.55 | 3.27 |

## 계측 한계

- `posture_gate_v2` — 낙상 검출 + 측정 계약 고정(양 채널 필수·v1 대체 금지·커버리지 0.99).

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
