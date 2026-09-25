"""산문 숫자 게이트 — 근거 없는 소수의 개수를 래칫으로 조인다.

왜 이 파일이 필요한가.  계약 테스트 212건이 전부 통과하는 동안에도 내가 보고서와
대화에서 말한 숫자가 7건 회수됐다.  게이트가 코드에만 있고 주장에는 없었기 때문이다.
`go2_claim_check`가 그 빈자리를 재고, 이 파일이 그 값을 되돌아가지 못하게 못 박는다.

래칫: CEILING 은 내려가기만 한다.  새 숫자를 손으로 써넣으면 테스트가 깨진다.
고치는 법은 두 가지뿐이고 둘 다 정당하다.
  1. 그 숫자를 만든 도구가 파일로 내보내게 한다 (권장 — 생성기는 대개 이미 있다).
  2. 유도식을 달아 `go2_claim_check.DERIVED` 에 등록한다.
등록부를 늘려 통과시키는 길은 열려 있지만, 등록부 크기 자체도 아래에서 조인다.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_claim_check as claim  # noqa: E402

# 2026-09-16 측정치.  착수 시점은 문서 2개에 74건이었고, 생성기를 붙여 0 으로 내렸다.
#   74 -> 64  SCENARIO_SCORES.csv    (rescore 가 이미 만들던 G축 점수를 내보냄)
#   64 -> 39  BASELINE_MARGIN.csv    (go2_eval_resolution 이 화면에만 찍던 sd·구간)
#   39 -> 37  DIAL_MODEL.csv         (go2_dial_model 의 교차검증 + 대안 모델 둘)
#   37 ->  8  TIER1_REGRESSION.csv   (§8 회귀·LOO·대안 예측변수)
#    8 ->  1  ARM_DELTAS.csv         (arm 사이 차이, 양방향 + 감점 열)
#    1 ->  0  tracking_xy_rmse_mean  (§4 의 대조군 지표를 원장이 들고 나오게 함)
#
# 그 뒤 검사 범위를 문서 2개에서 MEASURED 8개로 넓혔다.  범위를 넓히면 총계는 올라가므로
# 총계 하나로 조이면 '넓혔더니 느슨해졌다'가 숨는다.  그래서 **파일별** 상한으로 조인다.
# 어느 파일도 자기 숫자를 넘길 수 없고, 넓히는 것과 나빠지는 것이 섞이지 않는다.
CEILING = {
    "GO2_NOW.md": 0,
    "GO2_PROJECT_STATE.md": 51,
    "GO2_REWARD_EVIDENCE_MASTER.md": 37,
    "ARTIFACT_MANAGEMENT.md": 4,
    "workspace/training/quadruped/reports/GO2_RUN_SYNTHESIS_20260916.md": 0,
    "workspace/training/quadruped/reports/GO2_G_A029_TUNING_AUDIT_20260914.md": 3,
    "workspace/training/quadruped/reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md": 2,
    "workspace/training/quadruped/reports/GO2_TUNING_CAMPAIGN_AUDIT_20260914.md": 10,
    "workspace/training/quadruped/reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md": 0,
    "workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md": 0,
    "workspace/training/quadruped/reports/GO2_VARIABLE_INFLUENCE.md": 0,
    "workspace/training/quadruped/reports/GO2_REWARD_MECHANISM_FORECAST.md": 0,
    "workspace/training/quadruped/reports/GO2_G_A038_READOUT.md": 0,
    "workspace/training/quadruped/reports/GO2_SEED_SENSITIVITY.md": 0,
    # 2026-09-18 튜닝 정책 판독문.  새 문서이므로 상한을 여기서 처음 선언한다(기존 상한은
    # 올리지 않았다).  0 으로 연다 — 손으로 계산한 값(감점 합·채움률·축별 2σ·한계 초과 폭)은
    # 등록부에 넣지 않고 문서에서 지웠고, 남은 숫자는 전부 원장·증거 CSV 의 칸이다.
    "workspace/training/quadruped/reports/GO2_TUNING_POLICY_READOUT_20260918.md": 0,
    # 2026-09-19 축 병목 판독(신규, 생성 문서).  표 칸이 전부 AXIS_BOTTLENECK.csv 에서 나온다.
    "workspace/training/quadruped/reports/GO2_AXIS_BOTTLENECK.md": 0,
    # 2026-09-19 G-A038 재판독(신규).  이 문서는 어느 부류에도 없어 test_2b 가 잡았다 — 분류되지 않은
    # 문서가 바로 다음에 아무 표시 없이 인용할 문서다.  MEASURED 로 분류하고 DOC_SOURCES 로 증거 CSV 에
    # 묶었다.  묶은 뒤에도 남는 10건은 손으로 계산한 값이다: 산문의 어림 구간 넉 (`−0.84~−0.90`,
    # `−0.95대`/`−0.85대`), 채점 변형표의 차이 셋, 전진거리 하나, 백분율 변화 둘.  상한은 래칫이므로
    # 여기서 처음 선언하고 다음 판에서 올릴 수 없다 — 줄이는 길은 그 값들을 생성기가 CSV 칸으로
    # 내놓게 하거나 문서에서 지우는 것이다.
    "workspace/training/quadruped/reports/GO2_A038_REREAD_20260919.md": 10,
    # 2026-09-19 결함 대장(생성 `tools/go2_defect_ledger.py`).  인용 수치가 전부 증거 CSV 의
    # `figure` 표에 한 칸씩 들어 있어 0 이다.  신규 문서라 기존 상한을 올린 것이 아니다.
    "workspace/training/quadruped/reports/GO2_DEFECT_LEDGER.md": 0,
    # 2026-09-19 PM 보고(생성 `tools/go2_pm_brief.py`).  PM 이 사용자에게 내는 수치를 관문 안으로
    # 들이려고 만든 문서다 — 표의 수가 전부 BRIEF.csv 의 칸이라 0 이다.
    "workspace/training/quadruped/reports/GO2_PM_BRIEF.md": 0,
}

# 손으로 친 숫자는 적을수록 좋다.  늘리려면 이 상수를 같이 올려야 한다.
#
# 2026-09-19 결함 D-0.  여기에는 "그러면 커밋에 그 의도가 남는다"고 적혀 있었다.  그 집행 수단은
# 존재하지 않는다 — 도구가 전부 untracked 이고 이 저장소에서 커밋은 허용되지 않는다.  래칫을
# 커밋에 기대게 두면 집행되지 않는 규칙이 된다.  그래서 **세 래칫을 모두 실측에 묶는다**:
# 상한과 실제 값의 간격이 5 이상 벌어지면 "내려라"고 깨진다(test_2 · test_2f · test_3b).
# 상한을 미리 부풀려 두는 길이 막히므로 커밋 이력 없이도 래칫이 작동한다.
DERIVED_CEILING = 8

# 게이트의 맹점.  존재 게이트는 풀이 커질수록 약해진다 — 2026-09-16 실측으로
# 소수 1자리는 무작위 숫자의 98.9%가, 2자리는 55.0%가 그냥 통과했다.
# 그러므로 "근거 없는 소수 0건"은 검증이 아니다.  아래 수는 **애초에 검사되지 않는**
# 숫자의 개수이고, 이것도 래칫으로 조인다.  줄이는 길은 둘이다.
#   1. 자릿수를 늘려 적는다 (아티팩트에 있는 자리 그대로 — §11-3 에서 그렇게 했다).
#   2. 귀속 바인딩을 건다 (`go2_table_audit.BINDINGS`) — 존재가 아니라 자리를 지킨다.
BLIND_CEILING = {
    "GO2_NOW.md": 41,
    "GO2_PROJECT_STATE.md": 355,
    "GO2_REWARD_EVIDENCE_MASTER.md": 224,
    "ARTIFACT_MANAGEMENT.md": 18,
    "workspace/training/quadruped/reports/GO2_RUN_SYNTHESIS_20260916.md": 100,
    "workspace/training/quadruped/reports/GO2_G_A029_TUNING_AUDIT_20260914.md": 21,
    "workspace/training/quadruped/reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md": 14,
    "workspace/training/quadruped/reports/GO2_TUNING_CAMPAIGN_AUDIT_20260914.md": 26,
    # 계단 분석(2026-09-16 신규).  2자리 이하 33개는 DOC_SOURCES 글자 일치로 묶여 있다.
    "workspace/training/quadruped/reports/GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md": 33,
    # 튜닝 기반 데이터(2026-09-16 신규 생성 문서).  2자리 이하 99개는 전부 표 칸이며 DOC_SOURCES 글자 일치로
    # 묶여 있고, 문서 전체가 CSV 재생성과 같은지는 test_go2_tuning_base_data_contract 가 검사한다.
    "workspace/training/quadruped/reports/GO2_TUNING_BASE_DATA.md": 99,
    # 변수별 영향도 전수 판독(2026-09-17 신규 생성 문서).  설정값은 백틱으로 가리고 측정값은 3자리로 적어 맹점 0.
    "workspace/training/quadruped/reports/GO2_VARIABLE_INFLUENCE.md": 0,
    # 보상 기전 예측(2026-09-17 신규 생성 문서).  설정값은 백틱으로 가리고 계산값은 3자리 이상으로 적어 맹점 0.
    "workspace/training/quadruped/reports/GO2_REWARD_MECHANISM_FORECAST.md": 0,
    # G-A038 판독(2026-09-17 신규).  2자리 이하 12개는 표의 속도 칸이며 REPORT_VALUES.csv 글자 일치로 묶여 있다.
    "workspace/training/quadruped/reports/GO2_G_A038_READOUT.md": 12,
    # seed 흔들림 판독(2026-09-17 신규 생성 문서).  표 칸과 설정값을 백틱으로 적어 맹점 0.
    "workspace/training/quadruped/reports/GO2_SEED_SENSITIVITY.md": 0,
    # 2026-09-18 튜닝 정책 판독문(신규).  맹점은 2자리 이하 숫자 — 대부분 배포 가중치 값
    # (1.5 · 0.2 · -3.0 처럼)과 축 만점(10.5 · 14)이다.  줄이는 길은 자릿수를 늘려 적거나
    # 귀속 바인딩을 거는 것이고, 래칫이므로 다음 판에서 늘릴 수 없다.
    "workspace/training/quadruped/reports/GO2_TUNING_POLICY_READOUT_20260918.md": 42,
    # 2026-09-19 축 병목 판독(신규).  맹점은 축 만점(10.5 · 14 · 7)과 채점식 상수다.
    "workspace/training/quadruped/reports/GO2_AXIS_BOTTLENECK.md": 12,
    # 2026-09-19 G-A038 재판독(신규).  맹점은 2자리 이하 — 자세 게이트 상수(0.18 · -0.5)·명령 속도·
    # 축 만점·백분율이다.  줄이는 길은 자릿수를 늘려 적거나 귀속 바인딩을 거는 것이다.
    "workspace/training/quadruped/reports/GO2_A038_REREAD_20260919.md": 18,
    # 2026-09-19 결함 대장(생성 `tools/go2_defect_ledger.py`).  인용 수치를 CSV 의 `figure`
    # 표에 한 칸에 하나씩 내보내므로 맹점 0 이다 — 산문 칸 안의 숫자는 `own_values` 가
    # 칸 전체만 보기 때문에 근거가 되지 못한다(그래서 별도 표로 낸다).
    "workspace/training/quadruped/reports/GO2_DEFECT_LEDGER.md": 0,
    # PM brief 는 건수·결정 ID만 인용한다.  실측 맹점도 0이며 새 문서 상한을 빠뜨리지 않는다.
    "workspace/training/quadruped/reports/GO2_PM_BRIEF.md": 0,
}

# 어느 자릿수를 '맹점'으로 선언할 것인가의 기준.  풀이 커져 3자리까지 이 선을 넘으면
# BLIND_PLACES 를 올려야 하고, 그러면 위 래칫이 한꺼번에 깨진다 — 조용히 약해지지 않는다.
BLIND_THRESHOLD = 0.25


def counts():
    from collections import Counter
    tally = Counter(path.replace("\\", "/") for path, _n, _t, _l in claim.check())
    return {name: tally.get(name, 0) for name in CEILING}


class ClaimCheckContractTest(unittest.TestCase):
    def test_1_unbacked_numbers_do_not_grow(self) -> None:
        for name, seen in counts().items():
            with self.subTest(name):
                self.assertLessEqual(seen, CEILING[name],
                                     f"{name} 의 근거 없는 소수가 {CEILING[name]} -> {seen}")

    def test_2_ceiling_is_not_stale(self) -> None:
        """고쳐놓고 상한을 안 내리면 래칫이 풀린다. 5 이상 벌어지면 조이라고 말한다."""
        for name, seen in counts().items():
            with self.subTest(name):
                self.assertLess(CEILING[name] - seen, 5,
                                f"{name} 상한을 {seen} 로 내려라 (현재 {CEILING[name]})")

    def test_2b_every_go2_document_is_classified(self) -> None:
        """어느 부류도 아닌 문서가 내가 다음에 아무 표시 없이 인용할 문서다."""
        unknown = [str(p.relative_to(ROOT)) for p in claim.unclassified()]
        self.assertEqual(unknown, [], "\n" + "\n".join(unknown))

    def test_2c_the_gate_covers_every_measured_document(self) -> None:
        """MEASURED 에 넣어놓고 상한을 안 적으면 그 파일은 검사되지 않는다."""
        declared = {str(p.relative_to(ROOT)).replace("\\", "/") for p in claim.MEASURED}
        self.assertEqual(declared, set(CEILING))

    def test_2d_the_gate_declares_its_own_blind_spot_honestly(self) -> None:
        """오탐률이 문턱을 넘는 자릿수는 '검사한다'고 말하면 안 된다.

        풀이 커지면 존재 게이트는 약해진다.  이 검사가 없으면 산출물을 늘리는 것만으로
        게이트가 조용히 무력화되고, 나는 그걸 '0건'이라고 보고하게 된다.
        """
        pool = claim.measured()
        for places in range(1, claim.BLIND_PLACES + 1):
            self.assertGreater(claim.false_pass_rate(places, pool), BLIND_THRESHOLD,
                               f"소수 {places}자리는 이제 쓸 만하다 — BLIND_PLACES 를 내려라")
        checked = claim.BLIND_PLACES + 1
        self.assertLessEqual(
            claim.false_pass_rate(checked, pool), BLIND_THRESHOLD,
            f"소수 {checked}자리 오탐률이 문턱을 넘었다 — BLIND_PLACES 를 올리고 "
            "BLIND_CEILING 을 다시 세라. 게이트가 약해진 것이지 문서가 좋아진 게 아니다")

    def test_2e_unchecked_numbers_do_not_grow(self) -> None:
        """게이트가 못 보는 숫자도 래칫한다. 안 그러면 1자리로 적어서 통과시킬 수 있다."""
        for name, (_checked, blind) in claim.strength().items():
            with self.subTest(name):
                self.assertLessEqual(blind, BLIND_CEILING[name],
                                     f"{name} 의 검사 불가 숫자가 {BLIND_CEILING[name]} -> {blind}")

    def test_2f_blind_ceiling_is_not_stale(self) -> None:
        """상한을 부풀려 두면 래칫이 아니라 여유분이 된다 — test_2 와 같은 조임을 맹점에도 건다.

        2026-09-19 결함 D-0: 이 래칫의 집행 근거가 커밋 이력이라고 적혀 있었으나 그 이력이
        존재하지 않는다.  실측에 묶으면 커밋 없이도 집행된다.
        """
        for name, (_checked, blind) in claim.strength().items():
            with self.subTest(name):
                self.assertLess(BLIND_CEILING[name] - blind, 5,
                                f"{name} 맹점 상한을 {blind} 로 내려라 (현재 {BLIND_CEILING[name]})")

    def test_3b_derived_ceiling_is_not_stale(self) -> None:
        """등록부 상한도 같은 이유로 조인다."""
        self.assertLess(DERIVED_CEILING - len(claim.DERIVED), 5,
                        f"DERIVED_CEILING 을 {len(claim.DERIVED)} 로 내려라 (현재 {DERIVED_CEILING})")

    def test_3_derived_registry_stays_small_and_justified(self) -> None:
        self.assertLessEqual(len(claim.DERIVED), DERIVED_CEILING)
        for token, why in claim.DERIVED.items():
            self.assertGreater(len(why.strip()), 15, f"{token} 에 유도식이 없다")

    def test_4_the_generated_tables_the_gate_depends_on_exist(self) -> None:
        """게이트는 산출물을 읽어야 작동한다. 표가 사라지면 조용히 느슨해진다."""
        for name in ("LEDGER.csv", "SCENARIO_SCORES.csv",
                     "BASELINE_MARGIN.csv", "DIAL_MODEL.csv"):
            self.assertTrue((claim.RUNS / name).is_file(), name)

    def test_5_the_gate_actually_catches_a_planted_number(self) -> None:
        """통과하는 게이트가 아무것도 안 하고 있을 수 있다. 심어서 확인한다."""
        # `runs/` 안에 심으면 안 된다 — 그 폴더는 진실 집합이라 심은 숫자가 자기 자신을
        # 근거로 삼는다. 처음 판이 그래서 통과했다(=게이트가 아무것도 안 했다).
        planted = ROOT / "scratchpad_gate_probe.md"
        planted.write_text("기준선이 **77.7777점** 올랐다.\n", encoding="utf-8")
        try:
            found = claim.check([planted])
            self.assertEqual([t for _p, _n, t, _l in found], ["77.7777"])
        finally:
            planted.unlink()

    def test_5b_document_sources_back_only_their_own_document(self) -> None:
        """문서 전용 CSV가 다른 문서의 숫자를 근거해 주면 전역 풀에 넣은 것과 같다.

        2026-09-16: 계단 CSV 3개를 전역 풀에 넣자 PROJECT_STATE·MASTER의 근거 없는 숫자가
        11건씩 우연히 통과했다.  그래서 문서 하나에만 묶었다.  그 경계를 심어서 확인한다.
        """
        pool = claim.measured()
        for doc, sources in claim.DOC_SOURCES.items():
            self.assertEqual(claim.classify(doc), "MEASURED", doc)
            for source in sources:
                self.assertTrue(source.is_file(), source)
                self.assertNotIn(claim.RUNS, source.parents, "문서 전용 CSV를 전역 풀 폴더에 두지 않는다")
            own = claim.own_values(doc)
            # 2026-09-19: `claim.numbers_in(v)` 조건을 더했다.  마스크(sha256 조각 `[0-9a-f]{8,}`)에
            # 먹히는 값은 애초에 주장으로 세지 않으므로 경계를 시험할 수 없다 — 그런 값을 심으면
            # 게이트가 놓친 것이 아니라 볼 대상이 아닌 것인데, 실패가 그 둘을 구분하지 못했다.
            probes = [v for v in sorted(own)
                      if claim.NUMBER.fullmatch(v) and claim.decimals(v) >= 3
                      and claim.numbers_in(v) and not claim.supported(v, pool)]
            if not probes:
                # PM brief 처럼 CSV 에 정수/ID만 있으면 이 소수 격리 실험의 표본이 없다.
                # CSV-문서 일치는 생성기 계약에서 별도로 확인한다.
                continue
            probe = probes[0]
            planted = ROOT / "scratchpad_gate_probe.md"
            planted.write_text(f"값은 **{probe}** 이다.\n", encoding="utf-8")
            try:
                self.assertEqual([t for _p, _n, t, _l in claim.check([planted])], [probe])
            finally:
                planted.unlink()

    def test_6_masked_regions_are_not_claims(self) -> None:
        """코드·해시·날짜·버전 안의 숫자를 주장으로 세면 잡음이 신호를 덮는다."""
        for text in ("`terrain 9.9999 입니다`", "sha256 deadbeef1234 9999.9999 아님".replace("9999.9999", ""),
                     "2026-09-16 에 정했다", "Isaac Lab v2.3.1 기준"):
            self.assertEqual(claim.numbers_in(text), [], text)


if __name__ == "__main__":
    unittest.main()
