"""역할 회귀 자료 — 실제로 저지른 실수를 버리지 않고 시험 자료로 보존한다.

왜 있는가.  2026-09-18 세션에서 같은 종류의 실수가 반복됐다(원장 미독, 옛 초안 재사용, R-6 밖 추천,
예측을 측정처럼 인용, 이득 구간 무시).  사람이 매번 알아채는 방식은 실패했다.  그래서
  1) 각 실수를 **사례**로 적고(무엇을 했나 / 왜 틀렸나 / 어떤 원본이 반증하나 / 옳은 판정은 무엇인가),
  2) 기계로 잡을 수 있는 사례는 **고장난 사양(fixture)** 으로 만들어 관문이 실제로 무는지 확인하고,
  3) 사람·역할 에이전트(감사자·분석가·기획자)에게 던져 같은 실수를 하는지 보는 시험지로 쓴다.

fixture 는 실제 사양(G-A039)을 **일부러 망가뜨려** 만든다 — 손으로 쓰지 않는다.  그래야 사양 형식이
바뀌어도 시험지가 같이 따라간다.

    python -B tools/go2_role_regression.py        # 사례표·fixture·문서 재생성
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
EXPERIMENTS = QUAD / "config/experiments"
OUT_DIR = QUAD / "reports/evidence/go2_role_regression_20260918"
FIXTURES = OUT_DIR / "fixtures"
OUT_CSV = OUT_DIR / "CASES.csv"
OUT_DOC = QUAD / "reports/GO2_ROLE_REGRESSION_CASES.md"
BASE_SPEC = EXPERIMENTS / "G_A039_a033_dof_acc_m125e7.json"


def _old_number(spec: dict) -> dict:
    spec["work_id"] = "G-A035"
    return spec


def _outside_r6(spec: dict) -> dict:
    spec["change_class"] = "training_length"
    return spec


def _no_ledger_row(spec: dict) -> dict:
    spec["inference"]["rows"] = [r for r in spec["inference"]["rows"]
                                if not r["source"].startswith("reports/runs/")]
    return spec


def _mean_terrain_falsification(spec: dict) -> dict:
    spec["inference"]["falsified_if"] = (
        "terrain level at the evaluated iteration is not above the baseline's level at iteration 999")
    return spec


def _forecast_as_measurement(spec: dict) -> dict:
    spec["inference"]["predictions"]["sway"] = {
        "direction": "up",
        "basis": "PROBE_SITUATIONS.csv sway column for this term (measured)"}
    spec["inference"]["predictions"]["push"] = {
        "direction": "up",
        "basis": "PROBE_SITUATIONS.csv push column for this term (measured)"}
    return spec


def _open_decision_unnamed(spec: dict) -> dict:
    """우리가 넓힌 규칙에 기대면서 그 열린 결정 번호를 지운다 (2026-09-18 C07)."""
    spec.pop("open_decisions", None)
    return spec


def _planned_without_a_readout(spec: dict) -> dict:
    """분석가 판독 없이 원자료만 혼자 읽고 기획한다 (2026-09-18 C08)."""
    spec["inference"].pop("readout", None)
    return spec


def _gain_inside_noise(spec: dict) -> dict:
    spec["detectability"] = {**(spec.get("detectability") or {}), "expected_weighted_gain_70": 0.74}
    return spec


# (id, 역할, 무엇을 했나, 왜 틀렸나, 반증하는 원본, 옳은 판정, 막는 관문, fixture 변형)
CASES = (
    ("C01", "기획자",
     "실행된 최신 회차(G-A038)보다 앞 번호인 미실행 초안 G-A035를 1순위로 추천했다",
     "원장 시간순이 깨지고, 근거가 아니라 '이미 빌드돼 있어 편한 것'이 순서를 정했다",
     "reports/runs/LEDGER.csv", "번호가 원장 최신 실행 회차보다 크지 않으면 추천 불가",
     "tools/test_go2_detectability_gate.py::test_10_a_recommendation_is_newer_than_every_executed_run", _old_number),
    ("C02", "기획자",
     "학습 길이(1500 iter)와 학습 seed 반복을 1·2순위 추천으로 올렸다",
     "둘 다 R-6(보상 가중치만) 밖이다. 사용자에게 우리 규칙의 예외 승인을 요구한 꼴이 됐다",
     "GO2_NOW.md", "R-6 밖 변경은 RECOMMENDED 불가",
     "tools/test_go2_detectability_gate.py::test_11_only_a_reward_weight_change_can_be_recommended", _outside_r6),
    ("C03", "분석가",
     "커리큘럼 지연 수치를 텐서보드에서 다시 뽑아 '새로 찾았다'고 보고했다",
     "같은 값이 이미 원장 TERRAIN_AT_PIN.csv 에 있었다. 원장을 읽지 않은 것이 원인이다",
     "reports/runs/TERRAIN_AT_PIN.csv", "추천 사슬은 reports/runs/ 원장을 최소 한 행 인용해야 한다",
     "tools/test_go2_detectability_gate.py::test_12_a_recommendation_cites_the_run_ledger", _no_ledger_row),
    ("C04", "기획자",
     "반증 조건을 '평균 지형 레벨이 기준선보다 높지 않으면'으로 적었다",
     "커리큘럼은 마지막 레벨에 닿은 로봇을 무작위 행으로 되돌려 평균에 상한이 걸린다 — 포화를 볼 수 없다",
     "reports/evidence/go2_curriculum_source_20260918/CURRICULUM_FACTS.csv",
     "평균 지형 레벨은 반증 조건으로 쓸 수 없다",
     "tools/test_go2_curriculum_facts_contract.py::test_6_the_mean_level_may_not_be_used_as_a_saturation_metric", _mean_terrain_falsification),
    ("C05", "분석가",
     "계산된 예측(PROBE_SITUATIONS.csv)을 측정값처럼 인용해 방향을 주장했다",
     "그 칸은 비어 있다 — 빈 칸은 0이 아니라 '측정 없음'이다. 예측과 측정을 섞으면 근거가 무너진다",
     "reports/evidence/go2_reward_mechanism_20260917/PROBE_SITUATIONS.csv",
     "빈 칸을 근거로 방향을 주장하면 결함",
     "tools/test_go2_detectability_gate.py::test_13_an_unmeasured_situation_may_not_be_quoted_as_measured", _forecast_as_measurement),
    ("C06", "기획자",
     "잡음 구간 안의 차이를 이득으로 적었다(총점 sd 1.264, 검출 한계 2.528 미만 값)",
     "이득 구간 밖이어야 이득이다. 안쪽 값은 seed 운과 구별되지 않는다",
     "reports/runs/BASELINE_MARGIN.csv", "검출 한계 미만의 이득 수치는 근거로 쓸 수 없다",
     "tools/test_go2_detectability_gate.py::test_6_a_stated_point_gain_must_clear_the_limit", _gain_inside_noise),
    ("C07", "기획자",
     "우리가 스스로 넓힌 규칙(R6_CHANGE_CLASSES 에 env_reward_weight 추가)으로 추천을 통과시키고,"
     " 그 해석이 승인 전이라는 사실을 사양에 적지 않았다",
     "관문 통과는 규칙 준수의 증거가 아니다 — 경계를 검증한 것이 아니라 경계를 넓힌 것이다."
     " 사양만 읽는 역할은 이 사실을 알 수 없어 우리 해석을 기성 사실로 읽는다",
     "reports/GO2_OPEN_DECISIONS.md",
     "권한을 넓히는 열린 결정에 기대는 추천은 그 번호를 open_decisions 에 적어야 한다",
     "tools/test_go2_detectability_gate.py::test_15_a_recommendation_that_leans_on_an_open_decision_must_name_it",
     _open_decision_unnamed),
    ("C08", "기획자",
     "분석가 판독문 없이 원자료를 혼자 읽고 회차를 기획했다(사양에 inference.readout 이 없다)",
     "순서는 분석가(판독) → 기획자(값) → 감사자(결함)다. 기획자가 혼자 읽으면 R-6 같은 판단을"
     " 자기 역할 문서의 문장 하나에 기대게 되고(상황 인지 시험 Q12 실패), 사후 검증은 이미"
     " 감사자 몫이라 분석가가 감사자와 겹친다",
     "reports/GO2_G_A038_READOUT.md",
     "추천 사양은 기준선 회차를 판독한 문서를 지목하고, 그 판독문에 기준선 이름이 실제로 있어야 한다",
     "tools/test_go2_detectability_gate.py::test_16_a_recommendation_stands_on_an_analyst_readout",
     _planned_without_a_readout),
)

# 기계로 잡히지 않는 사례 — 역할 에이전트 시험지로만 쓴다(정답은 '무엇을 찾아내야 하는가').
MANUAL_CASES = (
    ("M01", "분석가",
     "G-A038의 10cm 오르기 붕괴를 레버 효과로 단정했다",
     "평가 고정 iter 900 에서 두 팔의 지형 레벨이 4.4937 대 1.9499 였다 — 커리큘럼 지연과 구별되지 않는다",
     "reports/evidence/go2_g_a038_readout_20260917/CURRICULUM_LAG.csv",
     "레버 효과와 학습 진도 차이를 가를 수 없다고 적어야 한다"),
    ("M02", "감사자",
     "받아 온 Isaac Lab 원문을 scratchpad 에만 두고 결론을 보고했다",
     "저장소에 없는 파일은 아무도 재검증할 수 없다. 증거가 아니라 주장이 된다",
     "reports/evidence/go2_curriculum_source_20260918/SOURCES.csv",
     "원문은 URL·SHA256과 함께 저장소에 등록돼야 인용 가능하다"),
    ("M03", "기획자",
     "튜닝 요청에 실행 패키지 대신 검토 보고서와 '결정해 주세요' 두 줄로 답했다",
     "차단 사유는 R-6 위반·테스트 실패·회수 불가 셋뿐이다. 어느 것도 아니면 패키지를 만든다",
     "GO2_NOW.md", "패키지를 만들고 관문을 돌린 뒤 보고해야 한다"),
    ("M04", "감사자",
     "반대 행(A018: 벌점 완화인데 정지)을 contradicting 에 넣지 않은 판단을 제작자 스스로 내렸다",
     "제작자가 자기 사슬의 반대 행 유무를 스스로 판정하면 이해충돌이다",
     "reports/evidence/go2_reward_mechanism_20260917/RUN_MARGIN.csv",
     "감사자가 원장·분석에서 반대 행을 직접 찾아 판정해야 한다"),
    ("M05", "분석가",
     "배포 `_finalize.py` 가 REWARD_WEIGHTS 밖 항(extras)을 판정에서 제외한다는 반대 행을,"
     " R-6 해석을 세우면서 찾지 않았다",
     "우리 해석에 불리한 배포 코드를 읽지 않고 유리한 줄(`env_cfg.py` 의 임의 이름 적용)만 인용하면"
     " 판독이 아니라 변론이다",
     "workspace/training/quadruped/go2_task/_finalize.py",
     "배포가 그 항을 참가자 변경으로 세지 않는다는 사실을 함께 적어야 한다"),
    ("M06", "기획자",
     "\"6개 목록 안에는 남은 레버가 없다\"를 사실로 적고, 그것을 전제로 U1(R-6 확장)을 사용자에게"
     " 승인 권고했다 — 정본 원장이 그 반대를 적고 있는데도",
     "규칙을 넓히자는 제안의 전제가 원장 한 줄로 반증된다. 유효 기각 2건을 6항 전체의 소진으로"
     " 확대했다. 양방향 유효 기각으로 닫힌 항은 feet_air_time 하나뿐이다",
     "GO2_REWARD_EVIDENCE_MASTER.md",
     "§1-a 가 lin_vel_z_l2·flat_orientation_l2 를 '미탐색', ang_vel_xy_l2 완화와 action_rate_l2"
     " 강화를 '미탐색'으로 적는 한 소진을 주장할 수 없다"
     " (관문 tools/test_go2_canonical_consistency.py::test_1e_no_doc_may_claim_the_deployed_six_are_exhausted)"),
)

HEADER = ["case", "role", "what_happened", "why_wrong", "refuting_source", "correct_verdict",
          "gate", "fixture", "machine_checkable"]


def rows() -> list[list[str]]:
    out = [HEADER]
    for case, role, what, why, source, verdict, gate, _ in CASES:
        out.append([case, role, what, why, source, verdict, gate,
                    f"fixtures/{case}.json", "YES"])
    for case, role, what, why, source, verdict in MANUAL_CASES:
        out.append([case, role, what, why, source, verdict, "-", "-", "NO"])
    return out


def healthy_base() -> dict:
    """시험지의 출발점은 **건강한 추천 사양**이어야 한다.

    2026-09-18: `BASE_SPEC`(G-A039)을 감사 결과대로 `HOLD_CONTRADICTED` 로 강등하고 반대 행을
    적었더니, 거의 모든 관문이 "추천일 때만" 검사하므로 고장난 사양 6개가 **아무 관문에도 걸리지
    않게** 되었다(C01~C04·C07·C08).  시험지가 조용해진 것이지 규칙이 지켜진 것이 아니다.
    살아 있는 사양의 상태가 시험 자체를 끄지 못하도록, 변형 전에 출발점을 건강한 쪽으로 고정한다.
    """
    spec = json.loads(BASE_SPEC.read_text(encoding="utf-8"))
    spec["inference"]["status"] = "RECOMMENDED"
    spec["inference"]["contradicting"] = []
    return spec


def write_fixtures() -> list[Path]:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    written = []
    for case, _role, what, _why, _source, _verdict, _gate, mutate in CASES:
        spec = mutate(healthy_base())
        spec["_regression_case"] = {
            "case": case, "source_spec": BASE_SPEC.name,
            "broken_on_purpose": what,
            "note": "이 파일은 시험지다. 회차 사양이 아니다 — config/experiments 에 두지 않는다.",
        }
        path = FIXTURES / f"{case}.json"
        path.write_bytes((json.dumps(spec, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        written.append(path)
    return written


def document(table: list[list[str]]) -> str:
    body = table[1:]
    lines = [
        "# Go2 역할 회귀 사례 — 실제로 저지른 실수를 시험 자료로 보존한다",
        "",
        "> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_role_regression.py` 가 만든다.",
        f"> 증거 `{OUT_CSV.relative_to(QUAD).as_posix()}`, 시험지 `{FIXTURES.relative_to(QUAD).as_posix()}/`,",
        "> 관문 `tools/test_go2_role_regression_contract.py`.",
        "",
        "쓰는 법:",
        "1. **관문 회귀** — 기계로 잡히는 사례는 고장난 사양(fixture)으로 보존한다. 관문이 그것을 *실패*시키지 못하면 관문이 썩은 것이다.",
        "2. **역할 시험** — 감사자·분석가·기획자에게 사례를 주고, `correct_verdict` 를 스스로 찾아내는지 본다. 정답을 미리 보여주지 않는다.",
        "3. **새 실수는 지우지 않고 여기에 추가한다.** 사례를 지우는 것은 규칙 위반이다.",
        "",
        "## 기계로 잡는 사례",
        "",
        "| 사례 | 역할 | 무엇을 했나 | 왜 틀렸나 | 반증 원본 | 옳은 판정 | 관문 |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in body:
        if r[8] != "YES":
            continue
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` | {r[5]} | `{r[6]}` |")
    lines += ["", "## 사람·역할 에이전트 시험지 (기계 관문 없음)", "",
              "| 사례 | 역할 | 무엇을 했나 | 왜 틀렸나 | 반증 원본 | 찾아내야 하는 것 |",
              "|---|---|---|---|---|---|"]
    for r in body:
        if r[8] != "NO":
            continue
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` | {r[5]} |")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table = rows()
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(table)
    written = write_fixtures()
    OUT_DOC.write_text(document(table), encoding="utf-8")
    print(OUT_CSV.relative_to(ROOT).as_posix())
    print(OUT_DOC.relative_to(ROOT).as_posix())
    print(f"fixtures {len(written)}개, 사례 {len(table) - 1}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
