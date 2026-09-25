"""보상 기전 예측 관문 — 원문 역할에 기반한 추론이 산출물과 같고, 지침이 그것을 가리킨다.

지키는 것:
  1. 보고서가 증거 CSV 재생성과 글자 단위로 같고, CSV는 학습 로그·가중치표에서 다시 계산한 값과 같다.
  2. 방법의 전제가 원문·산출물과 맞다: 고정 가중치가 모든 학습 env.yaml에서 같고,
     멈춘 로봇의 추종 식 값이 원문 식·명령 분포 계산과 맞는다.
  3. 사후 대조 결과(경계대 밖 불일치 0, LOO 포함)와 핵심 예측이 표에서 계산한 값과 같다.
  4. 새 reward 사양은 네 구간(걷기·계단·흔들림·밀침) 예측을 적어야 하고, 걷기 구간이 아니거나
     계단·흔들림·밀침이 나빠지면 이유가 필요하다.
  4b. 상황 식 값(계단·흔들림·밀침)이 평가 기록에서 다시 계산한 값과 같고, 부호 일치 판정이 표와 같다.
  5. 튜닝 정책을 읽는 지침(루트·4족 AGENTS, MASTER §1-b, 역할 파일 두 개, NOW)이 이 문서를 가리킨다.
"""
from __future__ import annotations

import copy
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_reward_mechanism as mech  # noqa: E402
import go2_tuning_base_data as base  # noqa: E402


class RewardMechanismContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.built = mech.build(with_eval=False)
        cls.rows = {r["name"]: r for r in mech.read("RUN_MARGIN.csv")}
        cls.probes = {(p["term"], p["to"]): p for p in mech.read("PROBES.csv")}

    def test_1_report_and_csv_are_regenerated(self) -> None:
        self.assertEqual(mech.DOC.read_text(encoding="utf-8"), mech.render(),
                         "python tools/go2_reward_mechanism.py --report 를 돌려라")
        for name, rows in self.built.items():
            with self.subTest(name):
                self.assertEqual(mech.read(name), rows, "python tools/go2_reward_mechanism.py 를 돌려라")
        # 기울기 표는 평가 기록 전체를 읽어 느리다 — 표본 하나만 다시 계산한다.
        steps = (mech.KEEP / "go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate/cases/seed_101/rough_lateral/steps.csv")
        row = next(r for r in mech.read("TILT.csv")
                   if (r["name"], r["case"], r["seed"]) == ("G-A033", "rough_lateral", "101"))
        self.assertEqual({k: row[k] for k in mech.tilt_case(steps)}, mech.tilt_case(steps))
        self.assertEqual(len(mech.read("TILT.csv")), len(mech.TILT_ARMS) * len(mech.TILT_CASES) * len(mech.SEEDS))
        self.assertIn("PROBE_SITUATIONS.csv", self.built)   # 상황 식 값(SITUATIONS.csv)은 test_4b가 다시 계산한다

    def test_2_premises_match_the_source(self) -> None:
        fixed = mech.fixed_weights()
        envs = sorted(mech.KEEP.glob("*/training/env.yaml")) + sorted(mech.KEEP.glob("*/policy/*_env.yaml"))
        self.assertGreaterEqual(len(envs), 18)
        for path in envs:
            with self.subTest(str(path.relative_to(mech.KEEP))):
                terms = base.env_terms(str(path.relative_to(mech.KEEP)))
                for term, weight in fixed.items():
                    self.assertEqual(float(terms[f"rewards.{term}"]["weight"]), weight)
        env = (mech.KEEP / base.ROLE_ENV).read_text(encoding="utf-8")
        self.assertRegex(env, r"lin_vel_x: !!python/tuple\n\s+- -1\.0\n\s+- 2\.0")
        self.assertRegex(env, r"lin_vel_y: !!python/tuple\n\s+- -0\.6\n\s+- 0\.6")
        self.assertEqual(mech.env_scalar("rel_standing_envs"), 0.02)
        _walk, stand = mech.pools(mech.read("TERM_VALUES.csv"))
        self.assertAlmostEqual(mech.stand_track_value(0.5, 0.02), stand["track_lin_vel_xy_exp"], delta=0.005)
        manager = (base.ROLES / "isaaclab_managers_reward_manager.py").read_text(encoding="utf-8")
        self.assertIn("episodic_sum_avg / self._env.max_episode_length_s", manager)
        self.assertIn('extras["Episode_Reward/" + key]', manager)
        self.assertAlmostEqual(mech.flat_stand_value(), 0.011)
        for rel, needle in ((mech.ENV_CFG, "국소최적"), (mech.ENV_CFG, "attr.weight = float(weight)"),
                            (mech.REWARDS_PY, "cudnn")):
            self.assertIn(f"{mech.line_of(rel, needle)}행", mech.DOC.read_text(encoding="utf-8"))

    def test_3_retrodiction_and_key_predictions(self) -> None:
        values = mech.read("TERM_VALUES.csv")
        rows = mech.read("RUN_MARGIN.csv")
        f = mech.findings(values, rows, mech.read("PROBES.csv"), [])
        self.assertEqual(f["wrong"], [], "경계대 밖에서 margin과 실제 걷기가 어긋났다 — 보고서 §2·정책을 고쳐라")
        self.assertEqual(f["wrong_loo"], [])
        self.assertEqual({r["name"] for r in f["band_rows"]}, {"Pilot-01", "A018"})
        self.assertEqual(len(rows), len(base.weights()))
        top = max(rows, key=lambda r: float(r["margin"]))
        # 2026-09-16~21 에는 동결 기준선이 margin 최대였고 이 줄이 그것을 지켰다.  2026-09-22 A043
        # (`lin_vel_z_l2 -1.5`)이 표에 들어오면서 최대가 옮겨갔다 — 벌점 한 항을 덜어냈으니 산수상
        # 당연하고, 그런데도 A043 은 G2 를 잃었다.  즉 **margin 최대는 좋은 정책이라는 뜻이 아니다**.
        # 기대값을 관측으로 옮기고, 원래 지키려던 것(기준선이 걷는 회차 중 상위)만 남긴다.
        self.assertEqual(top["name"], "A043")
        walking = sorted((float(r["margin"]), r["name"]) for r in rows
                         if base.walking(next(w for w in base.weights() if w["name"] == r["name"])))
        self.assertEqual([name for _m, name in walking][-2:], [mech.BASELINE, "A043"])
        for name in ("A016", "A024", "Default-01", "chain01", *mech.STOPPED_CHILDREN):
            self.assertEqual(self.rows[name]["zone"], "STOP", name)
        # 원문 식: 걷기로 늘어나는 보상은 track 하나뿐이다.
        walk, stand = mech.pools(values)
        gains = [t for t in mech.MARGIN_TERMS if mech.weights_of(
            next(r for r in base.weights() if r["name"] == mech.BASELINE))[t] * (walk[t] - stand[t]) > 0]
        self.assertEqual(gains, ["track_lin_vel_xy_exp"])
        self.assertEqual(max(mech.MARGIN_TERMS[1:], key=lambda t: -float(self.rows[mech.BASELINE]["part_" + t])),
                         "dof_acc_l2")
        self.assertEqual(self.probes[("track_lin_vel_xy_exp", "1.4")]["zone"], "WALK")    # A017 실제 걷기
        self.assertEqual(self.probes[("ang_vel_xy_l2", "-0.15")]["zone"], "STOP")         # A016과 같은 값
        self.assertEqual(self.probes[("dof_acc_l2", "-5e-07")]["zone"], "STOP")
        self.assertEqual(self.probes[("lin_vel_z_l2", "-1.0")]["zone"], "WALK")
        self.assertEqual(self.probes[("dof_acc_l2", "-1.25e-07")]["range_status"], "NEVER_CHANGED")

    def test_4_tilt_facts(self) -> None:
        tm = mech.tilt_means(mech.read("TILT.csv"))
        lateral = tm[("G-A033", "rough_lateral")]
        self.assertGreater(lateral["tilt_pre_term"], 5 * lateral["tilt_survivors"])
        self.assertGreater(lateral["pre_term_auc"], 0.8)
        self.assertEqual(lateral["terminated"], 58)   # 기반 데이터 §2 험지 옆걸음 종료와 같은 수
        self.assertLess(tm[("G-A033", "stairs_15_down")]["pre_term_auc"], 0.5)
        self.assertGreater(tm[("chain01", "forward_nominal")]["tilt_mean"], mech.flat_stand_value())

    def test_4b_situation_zones(self) -> None:
        """계단·흔들림·밀침: 표본 정책 하나를 평가 기록에서 다시 계산하고, 핵심 방향을 고정한다."""
        sit = mech.read("SITUATIONS.csv")
        again = {(k[0], k[1]): v for k, v in mech.situation_groups("go2_g_a033_a017_track_lin_vel_xy_150", "candidate").items()}
        for r in (r for r in sit if r["policy"] == mech.BASELINE):
            robots = again[(r["situation"], r["group"])]
            self.assertEqual(int(r["robots"]), len(robots))
            for term in mech.SITUATION_TERMS:
                self.assertAlmostEqual(float(r[term]), sum(x[term] for x in robots) / len(robots), places=4)
        # 계단 '오름' 로봇 수는 기반 데이터 §3 오르기 보상률 표와 같은 정의다.
        climb_src = {(c["group"], c["case"]): c for c in base.read("CLIMB_REWARD.csv")
                     if (c["run"], c["arm"]) == base.CLIMB_OF[mech.BASELINE]}
        by = {(r["situation"], r["group"]): r for r in sit if r["policy"] == mech.BASELINE}
        self.assertEqual(by[("climb", "climb")]["robots"], climb_src[("climb", "stairs_10_down")]["robots"])
        self.assertEqual(by[("climb", "stall")]["robots"], climb_src[("stall", "stairs_15_down")]["robots"])
        self.assertAlmostEqual(1.5 * float(by[("climb", "climb")]["track_lin_vel_xy_exp"]),
                               float(climb_src[("climb", "stairs_10_down")]["track_rate"]), places=3)
        self.assertEqual(by[("sway", "prefall")]["robots"], "58")   # 기반 데이터 §2 험지 옆걸음 종료
        agree = mech.sign_agreement(sit)
        self.assertTrue(agree[("sway", "ang_vel_xy_l2")].startswith("일치(−) 3"))
        self.assertTrue(agree[("sway", "lin_vel_z_l2")].startswith("일치(−) 3"))
        self.assertTrue(agree[("sway", "flat_orientation_l2")].startswith("불일치"))
        self.assertTrue(agree[("sway", "track_lin_vel_xy_exp")].startswith("불일치"))
        ps = {(q["term"], q["to"]): q for q in mech.read("PROBE_SITUATIONS.csv")}
        g37 = ps[("lin_vel_z_l2", "-1.0")]
        self.assertGreater(float(g37["climb_delta"]), 0)
        self.assertLess(float(g37["sway_delta"]), 0)
        self.assertLess(float(g37["push_delta"]), 0)
        ang = ps[("ang_vel_xy_l2", "-0.08")]
        self.assertGreater(float(ang["sway_delta"]), 0)
        self.assertEqual(self.probes[("ang_vel_xy_l2", "-0.08")]["zone"], "WALK")
        self.assertEqual(ps[("dof_acc_l2", "-1.25e-07")]["climb_delta"], "")
        doc = mech.DOC.read_text(encoding="utf-8")
        self.assertIn("## 5-1. 상황별 구간", doc)
        self.assertIn("### 6-0. 네 구간 함께 보기", doc)
        # 2026-09-17: G-A038 ran this lever; the policy no longer names it first, and §9 holds the check.
        self.assertNotIn("1순위 `ang_vel_xy_l2`", doc)
        self.assertIn("## 9. 사후 대조", doc)
        self.assertIn("단독 레버로 다시 쓰지 않는다", doc)
        # 2026-09-22: A043 도 회수 뒤 §9 로 대조했다(계획 §7).  회수된 회차가 대조 없이 지나가면
        # 예측력 검사가 사라지므로, 이 목록은 늘어나는 것이 정상이고 계수에는 여전히 들어가지 않는다.
        self.assertEqual([w for w, *_ in mech.HELD_OUT], ["G-A038", "G-A043"])
        for work in ("G-A038", "G-A043"):
            self.assertNotIn(work, mech.train_runs(), "held-out runs must not enter the coefficients")
        self.assertIn("네 상황 중 둘이 방향까지 틀렸다", doc)

    def test_5_new_reward_specs_declare_walk_margin(self) -> None:
        spec = json.loads((base.EXPERIMENTS / "G_A037_a033_lin_vel_z_m1.json").read_text(encoding="utf-8"))
        expected = base.expected_base_data(spec)
        self.assertEqual(expected["walk_margin"]["zone"], "WALK")
        self.assertAlmostEqual(expected["walk_margin"]["margin"], float(self.probes[("lin_vel_z_l2", "-1.0")]["margin"]), places=4)
        self.assertEqual(expected["walk_margin"]["worse"], ["push", "sway"])
        good = copy.deepcopy(spec)
        good["base_data"] = copy.deepcopy(expected)
        good["base_data"]["terms"]["lin_vel_z_l2"]["out_of_range_reason"] = "관측 밖임을 알고 정보 측정으로 탐색한다"
        self.assertEqual(base.spec_problems(good), ["base_data.walk_margin.reason"],
                         "흔들림·밀침이 나빠지는 후보가 이유 없이 통과했다")
        good["base_data"]["walk_margin"]["reason"] = "흔들림·밀침 악화를 알고 계단 정보 측정으로 만든다"
        self.assertEqual(base.spec_problems(good), [])
        missing = copy.deepcopy(good)
        del missing["base_data"]["walk_margin"]
        self.assertTrue(any("walk_margin" in p for p in base.spec_problems(missing)))
        risky = copy.deepcopy(spec)
        risky["rewards"]["candidate"].update({"lin_vel_z_l2": -2.0, "ang_vel_xy_l2": -0.15})
        risky["base_data"] = base.expected_base_data(risky)
        risky["base_data"]["terms"]["ang_vel_xy_l2"]["out_of_range_reason"] = "관측 밖임을 알고 정보 측정으로 탐색한다"
        self.assertEqual(risky["base_data"]["walk_margin"]["zone"], "STOP")
        self.assertEqual(base.spec_problems(risky), ["base_data.walk_margin.reason"])
        risky["base_data"]["walk_margin"]["reason"] = "정지 구간임을 알고 경계를 재기 위해 만든다"
        self.assertEqual(base.spec_problems(risky), [])

    def test_6_guidelines_point_here(self) -> None:
        texts = {
            "root AGENTS": (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "quad AGENTS": (mech.QUAD / "AGENTS.md").read_text(encoding="utf-8"),
            "campaign-manager": (ROOT / ".codex/agents/go2-campaign-manager.md").read_text(encoding="utf-8"),
            "test-planner": (ROOT / ".codex/agents/go2-test-planner.md").read_text(encoding="utf-8"),
            "NOW": (ROOT / "GO2_NOW.md").read_text(encoding="utf-8"),
        }
        for name, text in texts.items():
            with self.subTest(name):
                self.assertIn("GO2_REWARD_MECHANISM_FORECAST.md", text)
        quad = texts["quad AGENTS"]
        self.assertIn("test_go2_reward_mechanism_contract.py", quad)
        self.assertIn("base_data.walk_margin", quad)
        master = (ROOT / "GO2_REWARD_EVIDENCE_MASTER.md").read_text(encoding="utf-8")
        section = master[master.index("## 1-b."):master.index("**A. reward 가중치**")]
        self.assertIn(mech.DOC_REL, section)
        self.assertIn("A-0. 항의 역할과 기전", section)
        for term in mech.MARGIN_TERMS + ("flat_orientation_l2",):
            self.assertIn(f"| `{term}` |", section)
        self.assertIn("## 8. 향후 튜닝 정책", mech.DOC.read_text(encoding="utf-8"))
        self.assertTrue(re.search(r"reports/GO2_REWARD_MECHANISM_FORECAST\.md", texts["NOW"]))


if __name__ == "__main__":
    unittest.main()
