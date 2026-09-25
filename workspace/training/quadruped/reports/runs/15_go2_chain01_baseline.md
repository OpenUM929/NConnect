# 15. go2_chain01_baseline

- 시각: `2026-09-05_14-08-59` (평가 로그 내장값)
- 산출물: `workspace/_keep/go2_chain01_baseline`
- 4족 판별 근거: `go2_self_eval_registry.json` 외 2건 (이름이 아니라 산출물 경로로 가렸다)

## reward 설정

학습 `env.yaml`이 회수되지 않았다. reward 가중치 **모름**.

## 평가 — 정본 registry로 재채점

당시 쓰던 registry가 아니라 `config/go2_self_eval_registry.json` 하나로 다시 채점했다.

| arm | 정본 registry 재채점 | 당시 보고서 기록값 | case | 계측 세대 | 보행 판정 |
|---|---|---|---|---|---|
| `chain01` | 1.57910 | 보고서 없음 | 69 | `posture_gate_v1` | POLICY_DOES_NOT_LOCOMOTE |

> 이 arm은 표준 평가 보고서(`SELF_EVAL_REPORT.json`)가 생성되지 않았다. 당시 판정이 쓴 숫자를 산출물에서 확인할 수 없고, 위 재채점값만 근거로 남는다.

`chain01` 시나리오별 배점:

| G1 | G2 | G3 | G4 | G5 | G6 | G7 |
|---|---|---|---|---|---|---|
| 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.58 | 0.00 |

## 계측 한계

- `posture_gate_v1` — 자세 기반 낙상 검출 도입. 측정 계약 필드는 아직 없다.

---

이 파일은 `tools/build_go2_run_reports.py`가 산출물에서 생성한다. 직접 고치지 않는다.
