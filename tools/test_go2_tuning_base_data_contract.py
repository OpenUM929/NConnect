"""튜닝 기반 데이터 관문 — 튜닝값은 증거 표에서 도출한다(2026-09-16 사용자 지시).

규칙이 문서에만 있으면 규칙이 아니다.  이 검사가 지키는 것:
  1. 기반 데이터 문서가 증거 CSV 재생성과 글자 단위로 같다(손으로 고친 표가 없다).
  2. 지침 두 곳과 NOW가 이 문서를 필독으로 가리킨다.
  3. 새 reward 사양은 `base_data`에 관측 범위 대조를 적고, 그 값이 계산과 같다.
  4. 특이점 S1~S5가 표에서 계산한 값과 같다(표가 바뀌면 여기서 깨진다).
"""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import go2_tuning_base_data as base  # noqa: E402


class TuningBaseDataContractTest(unittest.TestCase):
    def test_1_document_is_regenerated_from_evidence(self) -> None:
        self.assertTrue(base.DOC.is_file(), "python tools/go2_tuning_base_data.py 를 돌려라")
        self.assertEqual(base.DOC.read_text(encoding="utf-8"), base.render(),
                         "기반 데이터 문서가 CSV와 다르다 — 손으로 고치지 말고 재생성하라")
        for name in base.SOURCES:
            self.assertTrue((base.EVIDENCE / name).is_file(), name)

    def test_2_guidelines_point_to_the_base_data(self) -> None:
        rel = "reports/GO2_TUNING_BASE_DATA.md"
        quad_rules = (base.QUAD / "AGENTS.md").read_text(encoding="utf-8")
        root_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        now = (ROOT / "GO2_NOW.md").read_text(encoding="utf-8")
        self.assertIn(rel, quad_rules)
        self.assertIn("원자료 행 → 특이점 → 값", quad_rules)
        self.assertIn("test_go2_tuning_base_data_contract.py", quad_rules)
        self.assertIn(base.DOC_REL, root_rules)
        self.assertIn(base.DOC_REL, now)

    def test_3_new_reward_specs_declare_their_position_in_the_data(self) -> None:
        specs = base.reward_specs()
        self.assertTrue(any(s["work_id"] == "G-A037" for _p, s in specs))
        for path, spec in specs:
            if spec["work_id"] in base.PRE_RULE_SPECS:
                continue
            with self.subTest(path.name):
                self.assertEqual(base.spec_problems(spec), [])

    def test_4_the_spec_check_bites(self) -> None:
        spec = json.loads((base.EXPERIMENTS / "G_A037_a033_lin_vel_z_m1.json").read_text(encoding="utf-8"))
        self.assertEqual(base.spec_problems(spec), ["base_data 없음"])
        good = copy.deepcopy(spec)
        good["base_data"] = base.expected_base_data(spec)
        self.assertEqual(good["base_data"]["terms"]["lin_vel_z_l2"]["status"], "OUT_OF_RANGE")
        self.assertEqual([p for p in base.spec_problems(good) if "out_of_range_reason" not in p],
                         ["base_data.walk_margin.reason"])
        self.assertTrue(any("out_of_range_reason" in p for p in base.spec_problems(good)))
        good["base_data"]["terms"]["lin_vel_z_l2"]["out_of_range_reason"] = "관측 밖임을 알고 탐색한다: 이유 서술"
        # G-A037은 흔들림·밀침 부분 margin을 낮춘다 — 그 이유도 적어야 통과한다(보상 기전 예측 §6-0).
        good["base_data"]["walk_margin"]["reason"] = "흔들림·밀침 악화를 알고 계단 정보 측정으로 만든다"
        self.assertEqual(base.spec_problems(good), [])
        lying = copy.deepcopy(good)
        lying["base_data"]["terms"]["lin_vel_z_l2"]["status"] = "OBSERVED"
        self.assertNotEqual(base.spec_problems(lying), [])
        no_role = copy.deepcopy(good)
        no_role["base_data"]["terms"]["lin_vel_z_l2"]["role"] = ""
        self.assertNotEqual(base.spec_problems(no_role), [], "원문 역할을 비운 사양이 통과했다")
        self.assertIn("Penalize z-axis base linear velocity", good["base_data"]["terms"]["lin_vel_z_l2"]["role"])
        inside = copy.deepcopy(spec)
        inside["rewards"]["candidate"]["lin_vel_z_l2"] = -2.0
        inside["rewards"]["candidate"]["track_lin_vel_xy_exp"] = 1.45
        self.assertEqual(base.expected_base_data(inside)["terms"]["track_lin_vel_xy_exp"]["status"], "BETWEEN_OBSERVED")

    def test_4b_term_roles_come_from_the_isaac_lab_source(self) -> None:
        """§0-1: 원문 파일은 SHA가 맞고, 식 칸은 원문 함수 본문이며, 함수는 기준선 env.yaml이 실제로 부른 것이다."""
        import hashlib
        import re
        sources = base.role_sources()
        self.assertEqual({r["file"] for r in sources},
                         set(base.ROLE_FILES.values()) | {"isaaclab_tasks_locomotion_velocity_env_cfg.py",
                                                          "isaaclab_managers_reward_manager.py",
                                                          "isaaclab_tasks_go2_rough_env_cfg.py"})
        for row in sources:
            with self.subTest(row["file"]):
                self.assertIn("/isaac-sim/IsaacLab/v2.3.1/", row["url"])
                self.assertEqual(hashlib.sha256((base.ROLES / row["file"]).read_bytes()).hexdigest(), row["sha256"])
        env = base.env_terms()
        rows = base.role_rows()
        self.assertEqual([r["term"] for r in rows], list(base.ROLE_TERMS))
        for row in rows:
            with self.subTest(row["term"]):
                self.assertEqual(env[f"rewards.{row['term']}"]["func"], row["func"])
                source = " ".join((base.ROLES / row["file"]).read_text(encoding="utf-8").split())
                for step in row["code"].split(" ; "):
                    self.assertIn(step, source)
                self.assertIn(f"def {row['func'].split(':')[1]}(", source)
        by = {r["term"]: r for r in rows}
        self.assertEqual(by["feet_air_time"]["threshold"], "0.5")
        self.assertEqual(by["track_lin_vel_xy_exp"]["std"], "0.5")
        self.assertIn("(last_air_time - threshold) * first_contact", by["feet_air_time"]["code"])
        self.assertEqual(env["rewards.undesired_contacts"], {"null": "true"})
        self.assertEqual((env["terminations.base_contact"]["body_names"], env["terminations.base_contact"]["threshold"]),
                         ("base", "1.0"))
        # Isaac Lab 원문 설정: 허벅지 접촉 벌점은 기본에 있고 Go2 험지가 지운다.
        cfg = (base.ROLES / "isaaclab_tasks_locomotion_velocity_env_cfg.py").read_text(encoding="utf-8")
        rough = (base.ROLES / "isaaclab_tasks_go2_rough_env_cfg.py").read_text(encoding="utf-8")
        self.assertRegex(cfg, r'undesired_contacts = RewTerm\(\s*func=mdp\.undesired_contacts,\s*weight=-1\.0')
        self.assertIn("self.rewards.undesired_contacts = None", rough)
        manager = (base.ROLES / "isaaclab_managers_reward_manager.py").read_text(encoding="utf-8")
        self.assertIn("episodic_sum_avg / self._env.max_episode_length_s", manager)
        self.assertIn("term_cfg.weight * dt", manager)
        # 한 항 변경 쌍이 없는 항 — 역할만 있고 측정이 없다.
        grades = base.influence_grades()
        self.assertEqual({t for t in base.ROLE_TERMS if t not in grades},
                         {"track_ang_vel_z_exp", "dof_torques_l2", "dof_acc_l2", "dof_pos_limits"})
        doc = base.DOC.read_text(encoding="utf-8")
        self.assertIn("## 0-1. 보상 항의 역할 — Isaac Lab v2.3.1 원문", doc)
        self.assertAlmostEqual(base.stall_track_reward(0.5, 0.5), 0.3679, places=4)
        self.assertTrue(re.search(r"가장 큰 벌점 `dof_acc_l2`은 \*\*한 번도 바꾼 적이 없다\*\*", doc))
        rules = (base.QUAD / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("§0-1", rules)

    def test_4b_the_published_snapshot_exemption_is_narrow(self) -> None:
        """실행된 사양의 `base_data` 는 발행 시점 스냅샷이다 — 그러나 예외는 관측 위치 하나뿐이다."""
        spec = json.loads((base.EXPERIMENTS / "G_A043_a033_lin_vel_z_m15.json").read_text(encoding="utf-8"))
        self.assertIn("G-A043", base.EXECUTED_SPECS)
        declared = spec["base_data"]["terms"]["lin_vel_z_l2"]
        self.assertEqual(declared["status"], "OUT_OF_RANGE")   # 발행 당시
        self.assertEqual(base.range_status("lin_vel_z_l2", -1.5), "OBSERVED")   # 자기 회수 뒤
        self.assertEqual(base.spec_problems(spec), [])
        for field, value in (("role", "틀린 역할"), ("value", -1.4)):
            worse = copy.deepcopy(spec)
            worse["base_data"]["terms"]["lin_vel_z_l2"][field] = value
            self.assertNotEqual(base.spec_problems(worse), [],
                                f"실행 사양 예외가 {field} 거짓까지 덮었다")

    def test_5_singularities_match_the_tables(self) -> None:
        """2026-09-22: A043(`lin_vel_z -1.5`)이 표에 들어오면서 S1 의 '한 쌍' 이 깨졌다.

        옛 값(쌍 하나, 걷는 회차 5개)을 그대로 두면 이 관문이 **반증된 읽기를 지키는** 쪽으로
        작동한다.  기대값을 새 관측으로 옮기되, 반례가 실제로 하나라는 것과 기준 쌍이 여전히
        G-A033 의 것이라는 것을 함께 검사한다.
        """
        s = base.singularities()
        self.assertEqual(s["pair"], {("-2", "-0.05"), ("-1.5", "-0.05")})
        self.assertEqual(s["reference_pair"], ("-2", "-0.05"))
        self.assertEqual([r["name"] for r in s["walk_other_pair"]], ["A043"])
        self.assertIn("S1 걷기 조건 — 반례가 나왔다", base.DOC.read_text(encoding="utf-8"))
        self.assertEqual(sorted(r["name"] for r in s["walk"]),
                         ["A017", "A031", "A032", "A043", "G-A033", "Pilot-01"])
        self.assertEqual(sorted(r["name"] for r in s["same_pair_stalled"]), ["A015", "A018"])
        self.assertEqual({"A010", "A020", "A021"} - {r["name"] for r in s["one_only"]}, set())
        self.assertEqual([r["name"] for r in s["track_line"]], ["Pilot-01", "A017", "G-A033"])
        self.assertFalse(s["climb15_monotone_in_track"])
        self.assertFalse(s["share_explains_climb15"])
        lat = [int(base.lateral(*base.LATERAL_OF[n])["terminated"]) for n in ("Pilot-01", "A017", "G-A033")]
        self.assertEqual(lat, [31, 48, 58])

    def test_5b_feet_air_section_matches_the_tables(self) -> None:
        """발 들기와 계단(2026-09-16 사용자 요청): 항은 전부 음수, 오르기는 0.2에서만 측정됐다."""
        terms = {r["run"]: r for r in base.read("TRAINING_TERMS.csv")}
        self.assertTrue(all(float(terms[run]["feet_air_time"]) < 0 for run in base.TRAIN_OF.values()))
        climbed = {r["feet_air_time"] for r in base.weights() if base.walking(r) and r["climb10_ge2"]}
        self.assertEqual(climbed, {"0.2"})
        cases = base.read("CASE_BEHAVIOR.csv")
        for name in ("A031", "A032"):
            run, arm = base.STAIRS_OF[name]
            self.assertEqual([c for c in cases if (c["run"], c["arm"]) == (run, arm)], [])
        a015 = [c for c in cases if c["run"] == base.STAIRS_OF["A015"][0] and c["case"] == "stairs_15_up"]
        self.assertEqual({c["arm"]: c["terminated_env_count"] for c in a015}, {"baseline_tier1": "2", "candidate": "31"})
        doc = base.DOC.read_text(encoding="utf-8")
        self.assertIn("## 6. 발 들기(`feet_air_time`)와 계단", doc)
        self.assertIn("A032는 체크포인트 iter 700", doc)
        line = base.master_line(base.MASTER_A032_ITER)
        self.assertIn("iter 700", base.MASTER.read_text(encoding="utf-8").splitlines()[line - 1])
        self.assertIn(f"`GO2_REWARD_EVIDENCE_MASTER.md` {line}행", doc)
        with self.assertRaises(StopIteration):  # 발 수준 열이 생기면 이 문구를 고쳐야 한다
            steps = next((ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/evaluation/candidate/cases/seed_101/stairs_15_down").glob("steps.csv"))
            header = steps.read_text(encoding="utf-8").splitlines()[0].split(",")
            next(h for h in header if any(k in h.lower() for k in ("foot", "feet", "air", "clear")))

    def test_5c_yaw_does_not_explain_lateral_rollover(self) -> None:
        """2026-09-16: '회전 추종 비중 감소 → 옆 뒤집힘' 가설을 로봇별 기록으로 기각했다. 표가 바뀌면 여기서 깨진다."""
        lats = [base.lateral(*base.LATERAL_OF[n]) for n in ("Pilot-01", "A017", "G-A033")]
        self.assertTrue(all(float(l["early_abs_wz_auc"]) < float(lats[-1]["mass_auc"]) for l in lats))
        self.assertTrue(all(float(l["heading_drift_survived_median_rad"]) > float(l["heading_drift_terminated_median_rad"])
                            for l in lats))
        self.assertTrue(all(float(a["abs_wz_mean"]) < float(b["abs_wz_mean"]) for a, b in zip(lats, lats[1:])))
        doc = base.DOC.read_text(encoding="utf-8")
        self.assertIn("회전 추종 가중치를 올리는 후보는 이 표로 뒷받침되지 않는다", doc)
        self.assertIn("normalize_advantage_per_mini_batch: false", doc)

    def test_5d_track_only_pair_moves_further_everywhere(self) -> None:
        """2026-09-16 사용자 지적: track 한 항만 다른 쌍에서 이동 거리는 track과 함께 늘었다."""
        tp = base.track_pairs()
        self.assertEqual(tp["diff"]["A017→G-A033"], ["827: weight: 1.4 → weight: 1.5"])
        self.assertEqual(tp["diff"]["Pilot-01→A017"], ["827: weight: 1.2 → weight: 1.4"])
        self.assertEqual(tp["up"]["A017→G-A033"], len(base.CASE_LABEL))
        self.assertLess(tp["up"]["Pilot-01→A017"], len(base.CASE_LABEL))
        self.assertNotEqual(base.RUN_CKPT["Pilot-01"][0], base.RUN_CKPT["A017"][0])
        pin = (ROOT / "workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/training/CHECKPOINT_PIN.txt").read_text(encoding="utf-8")
        self.assertIn(f"EVAL_CHECKPOINT_ITER={base.RUN_CKPT['G-A033'][0]}", pin)
        line = base.master_line(base.MASTER_A017_CKPT)
        self.assertIn("model_900.pt", base.MASTER.read_text(encoding="utf-8").splitlines()[line - 1])
        self.assertIn(f"{line}행: `model_900.pt`", base.RUN_CKPT["A017"][1])
        self.assertIn("`model_999` · `c4d78adf",
                      (ROOT / "GO2_OPUS_REAUDIT_INDEPENDENT_260907.md").read_text(encoding="utf-8").splitlines()[293])

    def test_5e_lateral_single_change_pairs(self) -> None:
        """2026-09-17 '옆걸음과 연관 있는 리워드': 옆걸음을 잰 한 항 변경 쌍은 track·feet_air뿐이다."""
        pairs = {(p["a"], p["b"]): p for p in base.lateral_pairs()}
        for p in pairs.values():
            self.assertEqual(len(p["changed"]), 1, p)
            self.assertEqual(len(p["diff"]), 1, p)
        self.assertEqual({p["changed"][0] for p in pairs.values()}, {"track_lin_vel_xy_exp", "feet_air_time"})
        clean = pairs[("A017", "G-A033")]
        self.assertTrue(clean["same_ckpt"] and clean["walking"])
        self.assertTrue(all(int(y) > int(x) for x, y in zip(*clean["seeds"])))
        fa = pairs[("Default-01", "feet_air_time_020_v1")]
        self.assertTrue(fa["same_ckpt"])
        self.assertFalse(fa["walking"])
        self.assertTrue(all(abs(float(l["vy_mean"])) < 0.05 for l in fa["lat"]))
        self.assertTrue(all(abs(base.diagonal_vy(run)) < base.STOPPED_VY for run in base.UNMEASURED_DIAGONAL.values()))
        cases = {(c["run"]) for c in base.read("CASE_BEHAVIOR.csv") if c["case"] == "rough_lateral"}
        self.assertEqual(cases & set(base.UNMEASURED_DIAGONAL.values()), set())
        walk3 = [base.lateral(*base.LATERAL_OF[n]) for n in ("Pilot-01", "A017", "G-A033")]
        self.assertTrue(all(float(l["early_vy_auc"]) < 0.6 for l in walk3))
        self.assertIn("295행", base.RUN_CKPT["feet_air_time_020_v1"][1])
        reaudit = (ROOT / "GO2_OPUS_REAUDIT_INDEPENDENT_260907.md").read_text(encoding="utf-8").splitlines()
        self.assertIn("`model_800` · `0dc8815f", reaudit[294])
        self.assertIn("`model_900` · `143871e3", reaudit[296])

    def test_6_g_a037_is_recorded_as_out_of_range(self) -> None:
        doc = base.DOC.read_text(encoding="utf-8")
        # A043 회수 뒤 이 다이얼의 걷는 관측값은 둘이다.  -1.0 은 여전히 그 구간 밖이다.
        self.assertIn("| G-A037 | `lin_vel_z_l2` | `-1.0` | `-2.0`, `-1.5` | `OUT_OF_RANGE` |", doc)
        self.assertIn("| G-A043 | `lin_vel_z_l2` | `-1.5` | `-2.0`, `-1.5` | `OBSERVED` |", doc)
        self.assertIn("업로드 보류", (ROOT / "GO2_NOW.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
