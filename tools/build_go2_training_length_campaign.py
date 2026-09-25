"""Build (and optionally publish) the one-command campaign package for a training-length arm (G-A035).

Why this exists.  The first G-A035 package (v1, 2026-09-16, never run) was an arm ZIP with a guide
that ran the arm runner directly.  Four things were wrong, all found by reading the code, none by a
test:
  1  the runner's outer path launches server_run_go2_candidate_staged.sh, which the ZIP does not
     carry -- the run would print [STARTED] and the tmux session would die at once;
  2  baseline.label was "candidate", so the gate and the local verifier would read the candidate's
     own cases as a remeasured baseline and compare the candidate with itself;
  3  evaluation.sentinel_tolerance was absent -- the server gate would raise KeyError, write no
     verdict, and the full stage would never run;
  4  the local verifier did not accept G-A035 at all.

What this module does NOT write.  Everything that ran end to end on the server for G-A033 is reused
byte for byte: server_run_go2_campaign.sh (target stage -> server gate -> full stage -> one result),
go2_target_gate.py and its two dependencies.  They also ship inside the released A031/A032 pair
package, so they are not edited.  The arm ZIP is tools/build_go2_training_length_package.py's
output byte for byte.  What is new is only the stored baseline naming (below), the README and the
guide, which the G-A033 builder hard-codes for A017 and 1000 iterations.

Stored baseline naming.  G-A033 was itself a candidate, so in its harvest it sits in
evaluation/candidate.  The gate reads the stored arm as stored_baseline/evaluation/<label>, so the
summaries are packed under the run label (g_a033), each verified against its raw steps.csv first.

    python tools/build_go2_training_length_campaign.py G-A035            # build and verify
    python tools/build_go2_training_length_campaign.py G-A035 --publish  # also publish upload/G-A035/current
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_campaign_package as campaign  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402
import verify_go2_a027_harvest as harvest  # noqa: E402

RUNNER = campaign.RUNNER
GATE_FILES = pair.GATE_FILES
EXECUTED_CAMPAIGNS = ("G-A038",)
FIXED_TIMESTAMP = length.FIXED_TIMESTAMP
PUBLISHED_AT = length.PUBLISHED_AT
# 2026-09-18: G-A035 v5 / G-A037 v4 / G-A039 v2 — 세 사양이 Isaac Lab 원문을 상류 경로로, 기준선
# 기록을 벌거벗은 steps.csv(같은 이름 69개)로 가리켜 분석가가 열 수 없었다.  reports/evidence/ 보관본
# 경로와 glob 으로 고치고 재발행했다.  값·관문·추론 사슬은 바뀌지 않았다.
CAMPAIGNS = {
    "G-A035": {
        "arms": ("G-A035",),
        "upload_id": "G-A035",
        "release_id": "20260918_a033_iter1500_one_command_v5",
        "published_at": "2026-09-17T00:00:00+00:00",
        "prefix": "go2_campaign_g_a035",
        "upload_zip": "GO2_G_A035_a033_iter1500_one_command.zip",
        "tmux": "go2_campaign_g_a035",
        "keep_name": "go2_campaign_g_a035",
        "result_zip": "GO2_G_A035_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A035_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A035_ONE_COMMAND_RUN_GUIDE.txt",
        "supersede_note": ("직전 판은 옛 판정 규칙(9 case 평균·이득 추정 waiver — G-A038의 10cm 오르기 붕괴를 통과시킴)으로 "
                   "대체됐다. 이 판은 fact_rules_v1·사실 근거 추론 사슬을 싣는다. 그 전 판은 러너 결함(G-A033 영상 로그 "
                   "폴더 미생성)으로 대체됐다(../history 에 보존, 모두 서버에 올린 적 없음).\n"),
    },
    # 2026-09-16: the first reward change on G-A033.  Same campaign runner, gate and stored-baseline
    # handling; the arm comes from tools/build_go2_a033_reward_package.py.
    "G-A037": {
        "arms": ("G-A037",),
        "upload_id": "G-A037",
        "release_id": "20260918_a033_lin_vel_z_m1_one_command_v4",
        "published_at": "2026-09-17T00:00:00+00:00",
        "prefix": "go2_campaign_g_a037",
        "upload_zip": "GO2_G_A037_a033_lin_vel_z_m1_one_command.zip",
        "tmux": "go2_campaign_g_a037",
        "keep_name": "go2_campaign_g_a037",
        "result_zip": "GO2_G_A037_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A037_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A037_ONE_COMMAND_RUN_GUIDE.txt",
        "supersede_note": ("직전 판은 옛 판정 규칙(9 case 평균·이득 추정 waiver — G-A038의 10cm 오르기 붕괴를 통과시킴)으로 "
                   "대체됐다. 이 판은 fact_rules_v1·사실 근거 추론 사슬을 싣는다. 그 전 판은 러너 결함(G-A033 영상 로그 "
                   "폴더 미생성)으로 대체됐다(../history 에 보존, 모두 서버에 올린 적 없음).\n"),
    },
    # 2026-09-17: G3/G6 lever from the reward-mechanism forecast (walk margin + situation margins).
    "G-A038": {
        "arms": ("G-A038",),
        "upload_id": "G-A038",
        "release_id": "20260917_a033_ang_vel_xy_m008_one_command_v1",
        "prefix": "go2_campaign_g_a038",
        "upload_zip": "GO2_G_A038_a033_ang_vel_xy_m008_one_command.zip",
        "tmux": "go2_campaign_g_a038",
        "keep_name": "go2_campaign_g_a038",
        "result_zip": "GO2_G_A038_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A038_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A038_ONE_COMMAND_RUN_GUIDE.txt",
        "supersede_note": ("직전 판은 옛 판정 규칙(9 case 평균·이득 추정 waiver — G-A038의 10cm 오르기 붕괴를 통과시킴)으로 "
                   "대체됐다. 이 판은 fact_rules_v1·사실 근거 추론 사슬을 싣는다. 그 전 판은 러너 결함(G-A033 영상 로그 "
                   "폴더 미생성)으로 대체됐다(../history 에 보존, 모두 서버에 올린 적 없음).\n"),
        "published_at": "2026-09-17T00:00:00+00:00",
    },
    # 2026-09-18: the first RECOMMENDED chain (inference gate test_10-12).  dof_acc_l2 is not one of
    # the six names in the deployed list, so the arm ZIP carries a candidate reward file with one
    # added line; go2_task/env_cfg.py applies it and the server log proves it.
    "G-A039": {
        "arms": ("G-A039",),
        "upload_id": "G-A039",
        # v2 (2026-09-18): 사양의 참조 경로 4곳이 분석가가 열 수 없는 형태였다 — Isaac Lab 상류 경로
        # (`envs/mdp/rewards.py`, `terrain_importer.py`)와 벌거벗은 `steps.csv`(같은 이름 69개).
        # 보관본 경로·glob 으로 고치고 재발행했다.  값·관문·사슬은 그대로다.
        # v3 (2026-09-18, 감사 D4·D5·D6·D7): 정지 회차 원값 범위 오기(224000-404000 ->
        # 224000-532000, A015=532000), seed 별 열이 없는 파일로 편 seed 주장 철회,
        # push 예측의 근거 명시, 15cm 관문이 하한 음수로 무효임을 사양에 기록.
        # v4 (2026-09-18): 발행문이 사양과 어긋난 "추론 사슬 INFORMATION_RUN" 을 달고 있었다
        # (is_reward_change 가 env_reward_weight 를 빼먹어 학습 길이 가지로 샜다).  상태는 이제
        # 사양에서 읽는다.  사양에는 열린 결정 U1-R6-ENV-REWARD-20260918 과 배포 _finalize.py:586
        # 반대 행을 실었다.  v3 바이트는 history 에 그대로 둔다.
        # v5 (2026-09-18): v4 발행문이 history 에 7판이 있는데도 "첫 판이다"라고 적었다 —
        # `supersedes`(이전 회차 칸)를 판 수로 읽은 탓이다. 판 수는 history 에서 센다.
        # v6 (2026-09-18, 사용자 지적 "기획자는 분석자의 자료를 기반으로 기획하는 것 아냐?"):
        # 역할 순서가 거꾸로 적혀 있어 기획자가 원자료를 혼자 읽고 있었다.  분석가(판독) →
        # 기획자(값) → 감사자(결함)로 되돌리고, 사양이 선 판독문을 `inference.readout` 에 지목한다
        # (test_16_a_recommendation_stands_on_an_analyst_readout).  v5 바이트는 history 에 그대로 둔다.
        # v7 (2026-09-18, 감사): 사양의 `contradicting` 이 비어 있는데 반대 행이 있었다(M04) —
        # 3행을 적고 상태를 RECOMMENDED -> HOLD_CONTRADICTED 로 강등했다.  거짓 전제("6개 목록은
        # 모두 측정 기각으로 닫혔다")가 영문으로 decision_ref·why 에 남아 있어 함께 고쳤고,
        # singularity 의 정지 회차 원값 상한이 아직 404000(옛 값)이라 532000(A015)으로 고쳤다.
        "release_id": "20260918_a033_dof_acc_m125e7_one_command_v7",
        "prefix": "go2_campaign_g_a039",
        "upload_zip": "GO2_G_A039_a033_dof_acc_m125e7_one_command.zip",
        "tmux": "go2_campaign_g_a039",
        "keep_name": "go2_campaign_g_a039",
        "result_zip": "GO2_G_A039_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A039_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A039_ONE_COMMAND_RUN_GUIDE.txt",
        "supersede_note": ("직전 판은 옛 판정 규칙(9 case 평균·이득 추정 waiver — G-A038의 10cm 오르기 붕괴를 통과시킴)으로 "
                   "대체됐다. 이 판은 fact_rules_v1·사실 근거 추론 사슬을 싣는다. 그 전 판은 러너 결함(G-A033 영상 로그 "
                   "폴더 미생성)으로 대체됐다(../history 에 보존, 모두 서버에 올린 적 없음).\n"),
        "published_at": "2026-09-18T00:00:00+00:00",
    },
    # 2026-09-20: the relaxation side of ang_vel_xy_l2 (-0.05 -> -0.04).  The dial is one of the six
    # deployed names, so the arm replaces a number and needs no open decision; the chain is an
    # INFORMATION_RUN because the same probe row that gives it its climb direction also predicts the
    # sway and push losses, and the loss channel is the better calibrated one (forecast section 9).
    "G-A041": {
        "arms": ("G-A041",),
        "upload_id": "G-A041",
        # v2 (2026-09-20): v1 의 발행문이 "직전 판은 옛 판정 규칙으로 대체됐다"를 달고 나왔다 — 첫
        # 발행인데도 그렇다.  그 문단은 G-A035/37/38/39 의 이력이고, 조건이 history 폴더 유무였기
        # 때문에 arm 빌더가 남긴 staged 판을 보고 붙었다.  이유를 회차별 `supersede_note` 로 옮겨
        # 고쳤고, v1 바이트는 history 에 그대로 둔다(서버에 올린 적 없음).
        # v3 (2026-09-20): `base_data.walk_margin.worse` 가 ["sway", "push"] 로 적혀 있어
        # tools/go2_tuning_base_data.py 의 정렬된 기대값과 어긋났다(생성기가 잡았다). arm 판도
        # staged_v2 로 다시 냈다. v1·v2 바이트는 history 에 그대로 둔다(서버에 올린 적 없음).
        # v4 (2026-09-20): 안내문의 한국어 세 곳이 깨져 있었다("잎는 쪽", "함께 재다", "잴다").
        # 사양 campaign_text 에서 고쳤다. v3 바이트는 history 에 보존(서버에 올린 적 없음).
        "release_id": "20260920_a033_ang_vel_xy_m004_one_command_v4",
        "prefix": "go2_campaign_g_a041",
        "upload_zip": "GO2_G_A041_a033_ang_vel_xy_m004_one_command.zip",
        "tmux": "go2_campaign_g_a041",
        "keep_name": "go2_campaign_g_a041",
        "result_zip": "GO2_G_A041_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A041_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A041_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-20T00:00:00+00:00",
    },
    # 2026-09-21: the first campaign built from a user plan rather than from an audit of our own
    # (upload/plan/GO2_FORWARD_STAIRS_POLICY_20260921.md section 3, decision G-D-FORWARD-STAIRS-
    # 20260921).  track_lin_vel_xy_exp 1.5 -> 1.6 is one of the six deployed names, so the arm
    # replaces a number.  Two things are new in the package: the 15 cm stairs are measured in stage 1
    # as required records (G-A041 lost that height to a target FAIL), and three of the four baseline
    # videos are reused by SHA instead of re-rendered, so both stair heights are filmed on both arms
    # while only one baseline video is produced here.
    "G-A042": {
        "arms": ("G-A042",),
        "upload_id": "G-A042",
        # v2 (2026-09-21): v1 의 사실 근거 행이 seed 3개를 **더한 값**을 적었다 — 합계는 원자료의
        # 칸이 아니라서 `tools/test_go2_detectability_gate.py::test_2`(selector 가 정확히 한 레코드,
        # cells 가 그 레코드의 칸)가 잡았다.  행을 seed 101 단일 레코드로 고치고, 세 seed 합은
        # `reads` 산문으로 옮겼다.  같은 검사가 지적한 것 셋을 함께 고쳤다: `_finalize.py`(같은 이름
        # 3개 → `go2_task/_finalize.py`), ZIP 내부 경로 두 개(파일 경로가 아니다), 그리고
        # `inference.readout` 이 판독 계열 문서가 아니었던 것.  값·관문·판정은 그대로다.
        # v1 바이트는 history 에 보존한다(서버에 올린 적 없음).
        # v3 (2026-09-21): 계획 §4 의 "초기 보호 표지에는 평지·좌우·양방향 밀침 case 를 포함한다"를
        # v1·v2 가 빠뜨렸다.  평지 좌·우와 표적이 아닌 밀침 세 방향을 seed 101 로 1단계 기록에 넣었다
        # (채점하지 않는다; 평지 전진은 이미 파국 case).  1단계 측정 case 는 15 -> 20 이다.
        "release_id": "20260921_a033_track_lin_vel_xy_160_one_command_v4",
        "prefix": "go2_campaign_g_a042",
        "upload_zip": "GO2_G_A042_a033_track_lin_vel_xy_160_one_command.zip",
        "tmux": "go2_campaign_g_a042",
        "keep_name": "go2_campaign_g_a042",
        "result_zip": "GO2_G_A042_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A042_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A042_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-21T00:00:00+00:00",
    },
    # 2026-09-22: the arm the plan written after G-A042's failure selected
    # (upload/plan/GO2_POST_A042_PLAN_20260922.md section 2).  lin_vel_z_l2 -2.0 -> -1.5 is one of the six
    # deployed names, so the arm replaces a number.  One thing is new in the package: the plan screening
    # version post_a042_push_v1 adds both G6 x directions to the protection block, so push_neg_x is measured
    # at three seeds (it was one marker seed in G-A042) and both push cases are filmed on both arms - the two
    # baseline videos this run renders.  The two lateral push markers move to the full stage in exchange,
    # under the stage-1 cap (tools/build_go2_a033_reward_package.MAX_STAGE1_CASES).
    "G-A043": {
        "arms": ("G-A043",),
        "upload_id": "G-A043",
        # v2 (2026-09-22): v1 의 수집 계약이 좌우 밀침(±y) 표지 2개를 뺐고, 그 근거로 "±y 는 예측 손실에
        # 지목되지 않았다" 를 적었다.  코드가 반대다 — tools/go2_reward_mechanism.py PUSH_CASES 는 밀침
        # 상황을 네 방향에서 계산한다.  표지를 되살려 1단계 22 case 로 만들고(상한은 69 의 1/3 로 다시
        # 적었다), 결함 C-8(기준선 reward 파일이 작업본 값)도 이 판에서 고쳤다.  v1 바이트는 history 에
        # 보존한다(서버에 올린 적 없음).  근거 `reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md`.
        # v3 (2026-09-22): 2차 검토가 사양 산문 두 곳의 과장을 잡았다. ①±y 를 "단일 seed 라 짝
        # 비교 불가" 로 적은 것 — 같은 seed 비교는 가능하고, 없는 것은 seed 간 일관성이다.
        # ②상한 23 을 "1단계 전체" 라 부르면서 빌더는 파국 case 를 빼고 세고 있었다 — 이제
        # 1단계가 실제로 재는 목록과 같게 센다(파국 1 + 채점 12 + 기록 10 = 23). v2 바이트는
        # history 에 보존한다(서버에 올린 적 없음).
        "release_id": "20260922_a033_lin_vel_z_m15_one_command_v3",
        "prefix": "go2_campaign_g_a043",
        "upload_zip": "GO2_G_A043_a033_lin_vel_z_m15_one_command.zip",
        "tmux": "go2_campaign_g_a043",
        "keep_name": "go2_campaign_g_a043",
        "result_zip": "GO2_G_A043_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A043_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A043_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-22T00:00:00+00:00",
    },
}

# Campaign texts that differ per reward arm.  G-A037's are the strings its release was built with;
# a spec may override them with a `campaign_text` block (G-A038 on).
G_A037_TEXT = {
    "analysis": "sections 8-9",
    "target_summary_en": "(15cm climb, 10cm climb, rough side-step)",
    "basis_ko": "§8(계단 오르기)·§9(험지 옆걸음)",
    "levers_ko": "바꾸지 않은 레버: `ang_vel_xy_l2`(좌우 구르기도 벌한다, 옆걸음 뒤집힘), `track_lin_vel_xy_exp`(옆걸음 종료 31→48→58), "
                 "`feet_air_time`(내리면 경사, 올리면 붕괴).",
    "target_summary_ko": "15cm 오르기·10cm 오르기·험지 옆걸음 각 3 seed",
    "target_note_ko": "험지 옆걸음이 표적 묶음에 들어 있어, 뒤집힘이 늘면 1단계 평균이 내려가 2단계 전에 멈춘다.",
    "readout_ko": "python tools/go2_stairs_behavior.py   (오르기 단수·옆걸음 뒤집힘을 기준선과 같은 규칙으로 판독)",
    "not_claimed_ko": "학습 seed가 42 하나라, 한 회차로는 레버 효과와 seed 운을 가를 수 없다. 이득 추정은 없다.",
    "publish_status_ko": "권고 상태: 이득 추정 없음·학습 seed 1개라 단일 회차로는 판정 불가(분석 §8-4). 서버 실행은 미해제.",
}

# G-A035(학습 길이)가 발행된 줄. 그 릴리스의 바이트라 글자 하나도 바꾸지 않는다.
LEGACY_LENGTH_LINE = "권고 상태: 추론 사슬 INFORMATION_RUN — 재계획 §5는 새 규칙으로 재판정 대기."


def campaign_text(spec: dict) -> dict:
    return {**G_A037_TEXT, **(spec.get("campaign_text") or {})}


def chain_status_line(spec: dict) -> str:
    """발행문의 권고 상태는 **사양에서 읽는다**.

    2026-09-18 분석가 판독: 발행된 `CURRENT_UPLOAD.txt` 가 "추론 사슬 INFORMATION_RUN" 이라고
    적었는데 같은 회차의 사양은 `RECOMMENDED` 였다.  두 줄 다 손으로 박은 문자열이었기 때문이다
    (여기 137행과 아래 tail 의 else 가지).  회차마다 갱신을 기억해야 하는 문장은 반드시 어긋난다 —
    상태는 한 곳(사양 `inference.status`)에서만 나온다.
    """
    # 이미 발행·실행된 사양(G-A035·G-A037·G-A038)은 발행 당시의 완성된 한 줄을 그대로 싣는다.
    # 그 줄을 새 형식으로 바꾸면 릴리스 ZIP 바이트가 달라진다 — 실행된 회차는 바뀌면 안 된다
    # (2026-09-18 실제로 G-A038 재빌드가 깨져 관문이 잡았다).
    written = spec.get("campaign_text", {})
    if "publish_status_ko" in written:
        return written["publish_status_ko"]
    note = written.get("publish_note_ko")
    if not note:
        return LEGACY_LENGTH_LINE
    status = (spec.get("inference") or {}).get("status", "NOT_STATED")
    return f"권고 상태: 추론 사슬 {status} — " + note


def derivation_lines(spec: dict) -> str:
    derivation = spec["value_derivation"]
    if "measured_10cm_share" in derivation:
        return (f"- 측정: {derivation['measured_10cm_share']}\n- 추정: {derivation['estimated_15cm_share']}\n"
                f"- 규칙: {derivation['rule']}\n- 주장하지 않는 것: {derivation['not_claimed']}")
    labels = {"role": "원문 역할", "walk_margin": "걷기 구간", "situations": "계단·흔들림·밀침",
              "rule": "규칙", "not_claimed": "주장하지 않는 것"}
    return "\n".join(f"- {label}: {derivation[key]}" for key, label in labels.items())


def fact_gate_lines(prereg: dict) -> str:
    """fact_rules_v1 설명.  이전 규칙 사양(G-A038)은 빈 문자열이라 안내문 바이트가 그대로다."""
    if prereg.get("rule_version") != "fact_rules_v1":
        return ""
    floors = " · ".join(f"{k} {v:+}" for k, v in prereg["target_group_floor"].items())
    climbs = " · ".join(f"{k} {g['baseline_sum']}-{g['max_drop']}"
                        for k, g in prereg["climb_guard"]["groups"].items())
    baseline = prereg["climb_guard"]["baseline"]
    return ("\n- 묶음별 하한(fact_rules_v1): 평균이 한 묶음의 붕괴를 덮지 못한다. "
            f"묶음 평균 proxy 변화 ≥ {floors}"
            f"\n- 계단 오른 로봇 수 하한(3 seed 합, 기준 {baseline}): {climbs}. "
            "1단계에 세 seed가 모두 있는 묶음은 여기서, 나머지는 로컬 판정에서 본다.")


def fact_local_lines(prereg: dict) -> str:
    if prereg.get("rule_version") != "fact_rules_v1":
        return ""
    target, guard = "+".join(prereg["target_axes"]), "·".join(prereg["guard_axes"])
    return (f"\n- 목표 축 {target}의 가중 점수 합이 올라야 한다(분석 §8-3b). 보호 축은 {guard}이다."
            "\n- 계단 오른 로봇 수 하한(1단계 안내의 목록 전부)")


# 2026-09-21 결함 C-4: 아래 두 안내문에서 표적 case 수가 상수 `9` 로 박혀 있었다.  회차마다 갱신을
# 기억해야 하는 수는 반드시 어긋난다(같은 파일 `chain_status_line` 의 교훈) — G-A041 은 12 case 를
# 재면서 발행문·안내문에 "9 target cases" 를 달고 서버에서 실행됐다.  이제 사양에서 센다.
# 이미 실행된 판의 바이트는 바꾸지 않으므로, 그 판이 적은 수만 여기 남긴다(`reports/GO2_DEFECT_LEDGER.md`).
FROZEN_TARGET_COUNT = {"G-A041": 9}


def scored_case_count(camp: dict, spec: dict) -> int:
    """The cases the server gate scores: the target groups only, never the required records."""
    if camp["upload_id"] in FROZEN_TARGET_COUNT:
        return FROZEN_TARGET_COUNT[camp["upload_id"]]
    return len(length.targets(spec))


def target_case_count(camp: dict, spec: dict) -> int:
    """The number of cases the target stage measures, as the release says it."""
    if camp["upload_id"] in FROZEN_TARGET_COUNT:
        return FROZEN_TARGET_COUNT[camp["upload_id"]]
    return len(arm_builder(spec["work_id"]).targets(spec))


def arm_builder(work_id: str):
    """The builder that owns an arm: a reward change on G-A033, or a training-length run."""
    return reward if work_id in reward.SPECS else length


def is_reward_change(spec: dict) -> bool:
    # 2026-09-18: `env_reward_weight` 가 빠져 있어서 G-A039(보상 항 변경)가 학습 길이 가지로 새고,
    # 발행문이 그 가지에 박힌 "INFORMATION_RUN" 을 달았다 — 사양은 RECOMMENDED 였다.
    # 이 분류가 R-6 안이라는 해석은 아직 사용자 승인 전이다: 열린 결정 U1-R6-ENV-REWARD-20260918
    # (`reports/GO2_OPEN_DECISIONS.md`).
    return spec.get("change_class") in ("reward_weight", "env_reward_weight")
# Scripts a shipped .sh launches with `bash <literal>.sh`.  Each must be in the package it runs
# from, unless it sits in a runner's outer path that the campaign never takes (it always passes
# --inner).  v1 failed exactly this.
BASH_CALL = re.compile(r"\bbash\s+([A-Za-z0-9_./-]+\.sh)\b")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_specs(camp: dict) -> list[dict]:
    return [arm_builder(work).load(work) for work in camp["arms"]]


def package_root(camp: dict) -> str:
    return "/workspace/" + camp["prefix"]


def output_path(camp: dict) -> Path:
    return GO2 / "upload" / camp["upload_id"] / "history" / camp["release_id"] / camp["upload_zip"]


def validate(camp: dict, specs: list[dict]) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"campaign {'+'.join(camp['arms'])}: {message}")

    need(len(specs) == 1, "a training-length campaign carries one arm")
    spec = specs[0]
    # 2026-09-17: a campaign that has not run judges with fact_rules_v1 (per-group floor, climbed-robot
    # floor, target axes G3+G5).  G-A038 passed stage 1 while its 10cm climb collapsed under the old rule.
    if camp["upload_id"] not in EXECUTED_CAMPAIGNS:
        need(spec["preregistered"].get("rule_version") == "fact_rules_v1",
             "an unexecuted campaign must preregister fact_rules_v1 (tools/go2_fact_rules_spec.py --write)")
    arm_builder(spec["work_id"]).validate_spec(spec)
    need(spec["runner"] in ("server_run_go2_candidate_staged.sh", "server_run_go2_candidate_iter_pinned.sh"),
         "the campaign runner accepts only the staged arm runners")
    base = spec["baseline"]
    need(base["label"] != "candidate", "baseline.label candidate makes the gate compare the candidate with itself")
    out = spec["output"]
    need(package_root(camp) != out["package_root"], "the campaign folder must not be the arm folder")
    for key, arm_key in (("tmux", "tmux_name"), ("keep_name", "keep_dir_name"), ("result_zip", "result_zip")):
        need(camp[key] != out[arm_key], f"campaign {key} must not be the arm's {arm_key}")


def stored_entries(spec: dict) -> list[str]:
    evaluation = spec["evaluation"]
    entries = [evaluation["catastrophe_case"], *length.targets(spec), *evaluation["sentinel_cases"]]
    return sorted(set(entries), key=entries.index)


def stored_payload(spec: dict) -> dict[str, bytes]:
    """Stored baseline summaries under the run label, each verified against its raw steps.csv."""
    base = spec["baseline"]
    arm = ROOT / base["stored_arm"] / "evaluation" / base["stored_label"]
    identity = json.loads((arm / "identity.json").read_text(encoding="utf-8"))
    for key in ("model_sha256", "env_sha256", "evaluator_sha256", "registry_sha256"):
        if identity.get(key) != base[key]:
            raise RuntimeError(f"stored arm identity {key}={identity.get(key)!r}, expected {base[key]}")
    out = f"stored_baseline/evaluation/{base['label']}"
    payload = {f"{out}/identity.json": (arm / "identity.json").read_bytes()}
    for entry in stored_entries(spec):
        scenario, case_id, seed = entry.split(":")
        case_dir = arm / "cases" / f"seed_{seed}" / case_id
        checked = harvest.verify_case(case_dir, scenario, case_id, int(seed))
        if checked["faults"]:
            raise RuntimeError(f"stored case {entry} does not verify: {checked['faults'][:3]}")
        payload[f"{out}/cases/seed_{seed}/{case_id}/summary.json"] = (case_dir / "summary.json").read_bytes()
    return payload


def arm_zip(spec: dict) -> bytes:
    """The arm ZIP as its own builder makes it; it must equal any copy already written for this release."""
    builder = arm_builder(spec["work_id"])
    data = builder.build_zip(spec)
    written = builder.output_path(spec)
    if written.is_file() and written.read_bytes() != data:
        raise RuntimeError(f"{written} differs from a rebuild of {spec['work_id']}")
    return data


def outer_only_calls(runner: str) -> set[str]:
    """`bash X.sh` calls that sit only in the block a runner runs without --inner."""
    head = runner.find('if [[ "${1:-}" != "--inner" ]]; then')
    if head < 0:
        return set()
    tail = runner.index("\nfi\n", head)
    outer = set(BASH_CALL.findall(runner[head:tail]))
    inner = set(BASH_CALL.findall(runner[:head] + runner[tail:]))
    return outer - inner


def unreachable_scripts(payload: dict[str, bytes], arm: dict[str, bytes], arm_runner: str) -> list[str]:
    """Scripts some shipped runner launches that are not in the package it runs from."""
    missing = []
    for name, data in payload.items():
        if name.endswith(".sh"):
            for called in BASH_CALL.findall(data.decode("utf-8")):
                if called != "$ARM_RUNNER" and Path(called).name not in {Path(n).name for n in payload}:
                    missing.append(f"{name} -> {called}")
    text = arm[arm_runner].decode("utf-8")
    skipped = outer_only_calls(text)   # the campaign runs the arm runner with --inner only
    for called in BASH_CALL.findall(text):
        if called in skipped:
            continue
        if Path(called).name not in {Path(n).name for n in arm}:
            missing.append(f"{arm_runner} -> {called}")
    return missing


def readme(camp: dict, spec: dict, zip_sha: str) -> str:
    if is_reward_change(spec):
        return reward_readme(camp, spec, zip_sha)
    root, out, base = package_root(camp), spec["output"], spec["baseline"]
    stages, single = spec["stages"], spec["single_change"]
    title = f"GO2 {spec['work_id']} CAMPAIGN — one upload, one command, one result"
    return f"""{title}
{'=' * len(title)}

This package TRAINS one policy and measures it.  status: {spec['status']}.
Plan: {Path(spec['plan']).name}.

ARM (byte for byte what tools/build_go2_training_length_package.py builds)
  {spec['work_id']}  {single['name']} {single['from']} -> {single['to']}, no reward weight changes
  arms/{out['upload_zip']}  sha256 {zip_sha}

BASELINE
  {base['name']} (model {base['model_sha256'][:12]}...), stored arm {base['stored_arm_work_id']}.
  Its summaries travel under stored_baseline/evaluation/{base['label']}.

RUN
  unzip -oq {camp['upload_zip']} -d /workspace
  bash {root}/{RUNNER}
  Resume after an interruption: GO2_RESUME=1 bash {root}/{RUNNER}

WHAT HAPPENS
  1 target stage (~{stages['target']['estimate_minutes']}m): training {spec['training']['max_iterations']} iter, catastrophe gate,
    the {target_case_count(camp, spec)} target cases, the {len(spec['evaluation']['sentinel_cases'])} sentinel cases, the videos.
  2 go2_target_gate.py reads criterion 1; the runner takes the verdict from the gate's JSON:
      TARGET_PASS -> full stage (~{stages['full']['estimate_minutes']}m); FAIL -> ends;
      REMEASURE_BASELINE -> target stage again with {base['name']} remeasured, gate again;
      UNDECIDED -> no full stage.
  3 one result ZIP.  The gate only schedules GPU time; the local verifier
    (tools/verify_go2_basic_motion_harvest.py) decides every verdict.

CHECKPOINT
  The candidate is evaluated at iter {spec['evaluation']['checkpoint_iter']}, the last checkpoint save_interval guarantees
  for {spec['training']['max_iterations']} iterations.  {base['name']} was evaluated at iter 900 of 1000.

DOWNLOAD
  /workspace/_keep/{camp['result_zip']}
  /workspace/_keep/{camp['result_zip']}.sha256
  Finish marker: {camp['done_marker']}
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def reward_readme(camp: dict, spec: dict, zip_sha: str) -> str:
    root, out, base = package_root(camp), spec["output"], spec["baseline"]
    stages, single = spec["stages"], spec["single_change"]
    limits = ", ".join(f"{k} {v}" for k, v in spec["preregistered"]["max_scenario_weighted_loss_70_by_scenario"].items())
    title = f"GO2 {spec['work_id']} CAMPAIGN — one upload, one command, one result"
    text = campaign_text(spec)
    return f"""{title}
{'=' * len(title)}

This package TRAINS one policy and measures it.  status: {spec['status']}.
Analysis: {Path(spec['plan']).name} {text['analysis']}.

ARM (byte for byte what tools/build_go2_a033_reward_package.py builds)
  {spec['work_id']}  {single['name']} {single['from']} -> {single['to']} on {base['name']}; every other weight, seed 42,
  4096 envs and 1000 iterations are {base['name']}'s
  arms/{out['upload_zip']}  sha256 {zip_sha}

BASELINE
  {base['name']} (model {base['model_sha256'][:12]}...), stored arm {base['stored_arm_work_id']}.
  Its summaries travel under stored_baseline/evaluation/{base['label']}.

RUN
  unzip -oq {camp['upload_zip']} -d /workspace
  bash {root}/{RUNNER}
  Resume after an interruption: GO2_RESUME=1 bash {root}/{RUNNER}

WHAT HAPPENS
  1 target stage (~{stages['target']['estimate_minutes']}m): training 1000 iter, catastrophe gate, the {target_case_count(camp, spec)} target cases
    {text['target_summary_en']}, the {len(spec['evaluation']['sentinel_cases'])} sentinel cases, the videos.
  2 go2_target_gate.py reads criterion 1; the runner takes the verdict from the gate's JSON:
      TARGET_PASS -> full stage (~{stages['full']['estimate_minutes']}m); FAIL -> ends;
      REMEASURE_BASELINE -> target stage again with {base['name']} remeasured, gate again;
      UNDECIDED -> no full stage.
  3 one result ZIP.  The gate only schedules GPU time; the local verifier
    (tools/verify_go2_basic_motion_harvest.py) decides every verdict, including the
    per-scenario loss limits ({limits}).

CHECKPOINT
  The candidate is evaluated at iter {spec['evaluation']['checkpoint_iter']}, the iteration {base['name']} was evaluated at.

DOWNLOAD
  /workspace/_keep/{camp['result_zip']}
  /workspace/_keep/{camp['result_zip']}.sha256
  Finish marker: {camp['done_marker']}
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build_payload(campaign_id: str) -> dict[str, bytes]:
    camp = CAMPAIGNS[campaign_id]
    specs = load_specs(camp)
    validate(camp, specs)
    spec = specs[0]
    # 2026-09-24 (defect C-28): the working tree runner moved, and these campaigns are already
    # published, so they must still rebuild from the bytes they shipped.  The pin and the CR
    # check both live in the campaign builder now (campaign.PUBLISHED_RUNNERS).
    runner = campaign.runner_bytes(campaign_id)
    data = arm_zip(spec)
    name = spec["output"]["upload_zip"]
    payload: dict[str, bytes] = {RUNNER: runner}
    # G-A038 ran with the gate that predates fact_rules_v1; the unexecuted campaigns ship the new one.
    payload.update(pair.gate_payload(executed=campaign_id in EXECUTED_CAMPAIGNS))
    payload.update(stored_payload(spec))
    payload[f"arms/{name}"] = data
    payload["campaign_config.env"] = campaign.campaign_config(camp, specs, {name: data}).encode("utf-8")
    payload["README.txt"] = readme(camp, spec, sha(data)).encode("utf-8")

    arm = arm_builder(spec["work_id"]).build_payload(spec)
    missing = unreachable_scripts({k: v for k, v in payload.items() if not k.startswith("arms/")},
                                  arm, spec["runner"])
    if missing:
        raise RuntimeError(f"shipped runners launch scripts the package does not carry: {missing}")

    checksums = "".join(f"{sha(blob)}  {member}\n" for member, blob in sorted(payload.items()))
    payload["CAMPAIGN_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def build(campaign_id: str) -> Path:
    camp = CAMPAIGNS[campaign_id]
    spec = load_specs(camp)[0]
    payload = build_payload(campaign_id)
    arm_path = arm_builder(spec["work_id"]).output_path(spec)
    arm_path.parent.mkdir(parents=True, exist_ok=True)
    arm_bytes = payload[f"arms/{spec['output']['upload_zip']}"]
    if not arm_path.is_file():
        arm_path.write_bytes(arm_bytes)
        arm_path.with_suffix(".zip.sha256").write_text(f"{sha(arm_bytes)}  {arm_path.name}\n",
                                                       encoding="utf-8", newline="\n")
    output = output_path(camp)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for member, blob in sorted(payload.items()):
            info = zipfile.ZipInfo(f"{camp['prefix']}/{member}", date_time=FIXED_TIMESTAMP)
            info.external_attr = (0o755 if member.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, blob)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(payload):
            raise RuntimeError("member count mismatch")
        if any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise RuntimeError("unsafe member")
    built = temporary.read_bytes()
    temporary.unlink()
    if output.exists() and output.read_bytes() != built:
        raise RuntimeError(f"immutable release conflict: {output} differs from this build")
    output.write_bytes(built)
    output.with_suffix(".zip.sha256").write_text(f"{sha(built)}  {output.name}\n", encoding="utf-8", newline="\n")
    return output


def run_guide(campaign_id: str, digest: str) -> str:
    camp = CAMPAIGNS[campaign_id]
    spec = load_specs(camp)[0]
    if is_reward_change(spec):
        return reward_run_guide(camp, spec, digest)
    root, base, stages = package_root(camp), spec["baseline"], spec["stages"]
    target_m, full_m = stages["target"]["estimate_minutes"], stages["full"]["estimate_minutes"]
    keep = spec["output"]["keep_dir_name"]
    prereg = spec["preregistered"]
    return f"""GO2 {spec['work_id']} ONE-COMMAND RUN GUIDE (파일 하나, 명령 하나, 결과 하나)

- {spec['work_id']}: {base['name']} 보상 그대로, 학습 {spec['single_change']['from']} → {spec['single_change']['to']} iter. 보상 가중치 변경 0.
계획서: {spec['plan']} §15 · 재계획 upload/plan/GO2_REPLAN_20260916.md P1
서버 실행은 사용자 결정 사항이다. 이 문서는 실행 절차이지 실행 승인이 아니다.

체크포인트 고정: 후보는 iter {spec['evaluation']['checkpoint_iter']}(1500 iter에서 save_interval이 보장하는 마지막 저장점)로 평가한다.
기준선 {base['name']}은 1000 중 iter 900에서 평가됐다. iteration 차이가 이 시험의 변수 자체다.
학습 중 러너가 그 체크포인트를 복사해 둔다. 복사를 못 하면 평가 전에 멈춘다.

LOCAL FILE TO UPLOAD (이것 하나만)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{camp['upload_id']}\\current\\{camp['upload_zip']}
   SHA256 {digest}
안에 회차 ZIP이 빌더 출력과 바이트 동일하게 들어 있다. 회차 ZIP을 따로 올리지 않는다.

SERVER DESTINATION
/workspace/{camp['upload_zip']}

ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {camp['upload_zip']}' | sha256sum -c - && unzip -oq {camp['upload_zip']} && bash {root}/{RUNNER}

시작 전 러너가 하는 일
회차 ZIP의 SHA 확인 → /workspace 아래로 풀기 → 회차 preflight(평가기·registry·{base['name']} SHA) → 학습·play 프로세스, tmux 세션, 이전 결과가 있으면 거부.

순서와 시간 [추정]
1. 1단계 약 {target_m}분: 학습 {spec['training']['max_iterations']} iter, 파국 게이트, 표적 {target_case_count(camp, spec)} case, {base['name']} 표지 {len(spec['evaluation']['sentinel_cases'])} case, 영상 {len(spec['videos']['candidate'])}+{len(spec['videos']['baseline'])}개.
2. 서버 게이트가 통과시키면 2단계(나머지 case) 약 {full_m}분.
3. 결과 ZIP 하나로 묶는다.
1단계에서 끝나면 약 {target_m // 60}시간 {target_m % 60}분, 통과하면 약 {(target_m + full_m) // 60}시간 {(target_m + full_m) % 60}분. 접속 직후 잔여 GPU 시간을 실측해 기록한다.

서버 게이트 (go2_target_gate.py) — 2단계를 돌릴지만 정한다
판정 1항(표적 {scored_case_count(camp, spec)} case proxy 평균 +{prereg['min_target_mean_proxy_delta']} 이상, 세 묶음 중 {prereg['min_target_groups_improved']}개 이상 상승)을 로컬 검증기와 같은 함수로 읽는다.{fact_gate_lines(prereg)}
- TARGET_PASS: 2단계를 돈다.
- FAIL: 끝이다. 파국 게이트 정지·발산도 FAIL이다. 그래도 학습 로그의 도달 지형 레벨(1차 관측량)은 결과에 남는다.
- REMEASURE_BASELINE: 표지 case가 저장 {base['name']}과 어긋났다. 1단계를 {base['name']} 재측정으로 한 번 더 돌리고 다시 판정한다.
- UNDECIDED: 결측·계측 불일치다. 2단계를 돌리지 않고 로컬 검증으로 넘긴다.

MONITOR
tmux attach -t {camp['tmux']}
진행 기록: /workspace/_keep/{camp['keep_name']}/CAMPAIGN_LOG.txt ([ARM], [GATE], [GATE READ], [RESULT] 줄)

첫 10분에 볼 것
학습 로그 머리에 max_iterations {spec['training']['max_iterations']}이 찍히는지, reward 표가 {base['name']}과 같은지 본다.

재시작 규칙
중단되면 `GO2_RESUME=1 bash {root}/{RUNNER}`로 잇는다. 끝난 단계·case·영상은 건너뛴다.
기본 재실행은 이전 결과를 지우지 않고 거부한다. 버리려면 `GO2_DISCARD_PREVIOUS=1`.

DONE MARKER
{camp['done_marker']}

DOWNLOAD TO LOCAL workspace\\_keep (이것 하나)
/workspace/_keep/{camp['result_zip']}
/workspace/_keep/{camp['result_zip']}.sha256
패키징이 실패하면 `_keep/{keep}`, `_keep/{camp['keep_name']}`를 그대로 가져온다.

결과를 받은 뒤 (로컬, GPU 0)
python -B tools/verify_go2_basic_motion_harvest.py {spec['work_id']} --harvest workspace/_keep/{keep} --out workspace/_keep/{keep}/harvest_verification.json
python tools/build_go2_run_reports.py   (도달 지형 레벨은 reports/runs/TERRAIN_AT_PIN.csv)
게이트 판정과 로컬 판정이 다르면 로컬 판정을 따르고, 차이를 기록한다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.

RESULT INTERPRETATION — 실행 전에 고정 (사후 재협상 금지)
판정 기준은 {prereg['source']}이다(기준값 불변).{fact_local_lines(prereg)}
학습을 늘리면 점수가 오른다는 보장은 없다. 보장되는 것은 도달 지형 레벨이 관측된다는 것뿐이다.
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.
"""


def reward_run_guide(camp: dict, spec: dict, digest: str) -> str:
    root, base, stages = package_root(camp), spec["baseline"], spec["stages"]
    target_m, full_m = stages["target"]["estimate_minutes"], stages["full"]["estimate_minutes"]
    keep, prereg, single = spec["output"]["keep_dir_name"], spec["preregistered"], spec["single_change"]
    text = campaign_text(spec)
    limits = " · ".join(f"{k} {v}" for k, v in prereg["max_scenario_weighted_loss_70_by_scenario"].items())
    guide = f"""GO2 {spec['work_id']} ONE-COMMAND RUN GUIDE (파일 하나, 명령 하나, 결과 하나)

- {spec['work_id']}: {base['name']} 위에서 `{single['name']}` {single['from']} → {single['to']} 하나만 바꾼다. 나머지 가중치·seed 42·4096 env·1000 iter는 {base['name']}과 같다.
근거: {spec['plan']} {text['basis_ko']}
서버 실행은 사용자 결정 사항이다. 이 문서는 실행 절차이지 실행 승인이 아니다.

값을 고른 방법
{derivation_lines(spec)}
{text['levers_ko']}

체크포인트 고정: 후보는 iter {spec['evaluation']['checkpoint_iter']}로 평가한다. 기준선 {base['name']}도 1000 중 iter 900에서 평가됐다.

LOCAL FILE TO UPLOAD (이것 하나만)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{camp['upload_id']}\\current\\{camp['upload_zip']}
   SHA256 {digest}
안에 회차 ZIP이 빌더 출력과 바이트 동일하게 들어 있다. 회차 ZIP을 따로 올리지 않는다.

SERVER DESTINATION
/workspace/{camp['upload_zip']}

ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {camp['upload_zip']}' | sha256sum -c - && unzip -oq {camp['upload_zip']} && bash {root}/{RUNNER}

시작 전 러너가 하는 일
회차 ZIP의 SHA 확인 → /workspace 아래로 풀기 → 회차 preflight(평가기·registry·{base['name']} SHA) → 학습·play 프로세스, tmux 세션, 이전 결과가 있으면 거부.

순서와 시간 [추정]
1. 1단계 약 {target_m}분: 학습 1000 iter, 파국 게이트, 표적 {target_case_count(camp, spec)} case({text['target_summary_ko']}), {base['name']} 표지 {len(spec['evaluation']['sentinel_cases'])} case, 영상 {len(spec['videos']['candidate'])}+{len(spec['videos']['baseline'])}개.
2. 서버 게이트가 통과시키면 2단계(나머지 case) 약 {full_m}분.
3. 결과 ZIP 하나로 묶는다.
1단계에서 끝나면 약 {target_m // 60}시간 {target_m % 60}분, 통과하면 약 {(target_m + full_m) // 60}시간 {(target_m + full_m) % 60}분. 접속 직후 잔여 GPU 시간을 실측해 기록한다.

서버 게이트 (go2_target_gate.py) — 2단계를 돌릴지만 정한다
판정 1항(표적 {scored_case_count(camp, spec)} case proxy 평균 +{prereg['min_target_mean_proxy_delta']} 이상, 세 묶음 중 {prereg['min_target_groups_improved']}개 이상 상승)을 로컬 검증기와 같은 함수로 읽는다.
{text['target_note_ko']}{fact_gate_lines(prereg)}
- TARGET_PASS: 2단계를 돈다.
- FAIL: 끝이다. 파국 게이트 정지·발산도 FAIL이다.
- REMEASURE_BASELINE: 표지 case가 저장 {base['name']}과 어긋났다. 1단계를 {base['name']} 재측정으로 한 번 더 돌리고 다시 판정한다.
- UNDECIDED: 결측·계측 불일치다. 2단계를 돌리지 않고 로컬 검증으로 넘긴다.

로컬 판정 (2단계 후) — 다른 축을 지키는 조건
- 총점 +{prereg['min_total_points_delta']}/70 이상(2σ 검출 한계)
- 평지 G1·G2: 시나리오 proxy 하락 ≤ {prereg['max_flat_scenario_proxy_drop']}, case 생존 하락 ≤ {prereg['max_flat_case_survival_drop']}
- 나머지 축: 시나리오별 가중 손실 ≤ 자기 평가 표집 sd의 2배 ({limits} /70)
- 새 정지 case 0, POLICY_LOCOMOTES{fact_local_lines(prereg)}

MONITOR
tmux attach -t {camp['tmux']}
진행 기록: /workspace/_keep/{camp['keep_name']}/CAMPAIGN_LOG.txt ([ARM], [GATE], [GATE READ], [RESULT] 줄)

첫 10분에 볼 것
학습 로그 머리의 reward 표에서 {single['name']}가 {single['to']}이고 나머지가 {base['name']}과 같은지 본다.

재시작 규칙
중단되면 `GO2_RESUME=1 bash {root}/{RUNNER}`로 잇는다. 끝난 단계·case·영상은 건너뛴다.
기본 재실행은 이전 결과를 지우지 않고 거부한다. 버리려면 `GO2_DISCARD_PREVIOUS=1`.

DONE MARKER
{camp['done_marker']}

DOWNLOAD TO LOCAL workspace\\_keep (이것 하나)
/workspace/_keep/{camp['result_zip']}
/workspace/_keep/{camp['result_zip']}.sha256
패키징이 실패하면 `_keep/{keep}`, `_keep/{camp['keep_name']}`를 그대로 가져온다.

결과를 받은 뒤 (로컬, GPU 0)
python -B tools/verify_go2_basic_motion_harvest.py {spec['work_id']} --harvest workspace/_keep/{keep} --out workspace/_keep/{keep}/harvest_verification.json
{text['readout_ko']}
게이트 판정과 로컬 판정이 다르면 로컬 판정을 따르고, 차이를 기록한다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.

RESULT INTERPRETATION — 실행 전에 고정 (사후 재협상 금지)
판정 기준은 {prereg['source']}이다.
{text['not_claimed_ko']}
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.
"""
    if spec['preregistered'].get('plan_screening'):
        guide = guide.replace('- FAIL: 끝이다. 파국 게이트 정지·발산도 FAIL이다.',
            '- FAIL: 필수 평가·영상 수집을 마친 뒤 끝낸다. 유효 정지 정책도 수집한다. 비유한/실행 불능은 실패 근거를 회수하고 중단한다.')
        guide = guide.replace('DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.',
            'DONE 표시만으로 종료하지 않는다. 결과 ZIP·SHA/manifest, 해당 학습 원본 report.html·env·로그·checkpoint, '
            '필수 telemetry 20 case+평지 전진, 후보 영상4개·새 기준선 영상1개 및 SHA로 재사용한 기준선 영상3개의 '
            '로컬 도착·무결성을 확인한다. 누락하면 종료 불가이며 성능 FAIL과 회수 완결은 별개다.')
        guide += ('\nPLAN SCREENING — 1단계 회수부터 적용\n'
                  '위 단일 verifier 명령은 artifact/identity → fact_rules_v1 → go2_screening_gate.py(계획 §4)를 '
                  '통합한다. 10·15cm 각각 전진거리 증가, 등반수 비열등(최소 한 항 증가), 정체 감소, '
                  '네 표적의 생존 보호와 험지 추종 보호를 모두 요구한다. 누락/지문 불일치는 INCONCLUSIVE다.\n'
                  '서버 게이트는 GPU 배분만 한다. screening 성공도 후보 승급이 아니며 전수69case·영상·독립 학습seed 양팔 반복이 남는다.\n'
                  '예산: 기존 A033/A041 학습 약59/57분, 본 사양 1단계100분·확장55분은 추정이다. '
                  '실제 잔여 GPU/TTL은 미측정이다. 회수 여유를 포함한 약3시간 이상 창을 확인하고 시작한다. '
                  '재측정 분기는 추가 시간이 필요하므로 해당 러너의 회수/중단 절차를 따른다.\n')
    return guide


def publish(campaign_id: str, zip_path: Path) -> None:
    camp = CAMPAIGNS[campaign_id]
    spec = load_specs(camp)[0]
    digest = sha(zip_path.read_bytes())
    upload = GO2 / "upload" / camp["upload_id"]
    history, current = upload / "history" / camp["release_id"], upload / "current"
    current.mkdir(parents=True, exist_ok=True)
    guide = camp["guide"]
    if is_reward_change(spec):
        single = spec["single_change"]
        note = (f"{spec['work_id']} {spec['baseline']['name']} + {single['name']} {single['from']}->{single['to']}. "
                "One upload: the arm ZIP byte-identical to its builder, target stage, a server gate read from its "
                f"JSON, full stage only on a pass, one result ZIP. {spec['status']}.")
    else:
        note = (f"{spec['work_id']} {spec['baseline']['name']} rewards unchanged, max_iterations "
                f"{spec['single_change']['from']}->{spec['single_change']['to']}. One upload: the arm ZIP byte-identical "
                "to its builder, target stage, a server gate read from its JSON, full stage only on a pass, one "
                f"result ZIP. Supersedes {spec['output']['supersedes'].split(' ')[0]}. {spec['status']}.")
    manifest = {
        "experiment_id": spec["work_id"], "note": note, "published_at_utc": camp.get("published_at", PUBLISHED_AT),
        "release_id": camp["release_id"], "status": "ARTIFACT_VERIFIED", "support_files": [guide],
        "upload_files": [{"name": camp["upload_zip"], "server_path": f"/workspace/{camp['upload_zip']}",
                          "sha256": digest}],
    }
    # Why the previous release was replaced (2026-09-17: first the video-log runner defect G-A038 found,
    # then the old judgement rule).  Each generation's reason stays in its own history folder.
    # 2026-09-20: 이 문단은 G-A035/37/38/39 의 실제 이력(옛 판정 규칙판, 그 전의 러너 결함판)을 적은
    # 것이라 그 넷에만 참이다.  그런데 조건이 "history 에 폴더가 하나라도 있으면"이었고, 회차 ZIP 을
    # 만들면 arm 빌더가 staged 판을 history 에 남기므로, **첫 발행인 G-A041 의 안내문이 자기가 옛
    # 판정 규칙판을 대체했다고 적었다**.  G-A039 v5 결함(판 수를 supersedes 로 읽음)과 같은 자리의
    # 반대 방향 오류다.  이유는 이제 회차별로 CAMPAIGNS 에 적고, 없는 회차는 아무 말도 하지 않는다.
    runner_note = camp.get("supersede_note", "")
    if is_reward_change(spec):
        # 2026-09-18: `supersedes` 는 **이전 회차**(다른 work_id)를 가리키는 칸인데 이 줄이 그것을
        # "이전 판 없음"으로 읽어, history 에 7판이 쌓인 G-A039 발행문이 "첫 판이다"라고 적었다.
        # 판 수는 history 폴더에서 센다 — 발행문이 자기 이력을 스스로 세도록.
        releases = upload / "history"
        earlier = sorted(d.name for d in releases.glob("*") if d.is_dir() and d.name != camp["release_id"])
        tail = (("첫 판이다(이전 판 없음).\n" if not earlier else
                 f"이전 판 {len(earlier)}개는 ../history 에 보존한다(가장 최근 {earlier[-1]}), 모두 서버에 올린 적 없다.\n"
                 + runner_note)
                + chain_status_line(spec) + "\n")
    else:
        tail = ("이전 판 staged_v1 은 실행 불가로 폐기, one_command_v1 은 안내문의 거짓 서술 때문에 대체됐다"
                "(../history 에 보존, 둘 다 서버에 올린 적 없음).\n"
                + runner_note + chain_status_line(spec) + "\n")
    current_text = (
        f"CURRENT GO2 UPLOAD — {spec['work_id']} (one command)\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{camp['upload_id']}\\current\\{camp['upload_zip']}\n"
        f"   SHA256 {digest}\n\n"
        "한 파일·한 명령으로 1단계 → 서버 게이트 → 통과 시 2단계 → 결과 ZIP 하나.\n"
        f"절차는 같은 폴더의 {guide}. 회차 ZIP은 이 파일 안에 이미 들어 있다.\n"
        "서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {camp['release_id']}\nSTATUS ARTIFACT_VERIFIED\n"
        + tail
    )
    files = {
        guide: run_guide(campaign_id, digest).encode("utf-8"),
        "UPLOAD_MANIFEST.json": (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "CURRENT_UPLOAD.txt": current_text.encode("utf-8"),
    }
    for name, data in files.items():
        target = history / name
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"immutable release conflict: {target}")
        target.write_bytes(data)
    (history / f"{guide}.sha256").write_text(f"{sha(files[guide])}  {guide}\n", encoding="utf-8", newline="\n")
    published = [zip_path, zip_path.with_suffix(".zip.sha256"), *(history / name for name in files),
                 history / f"{guide}.sha256"]
    names = {path.name for path in published}
    for stale in sorted(current.iterdir()):
        if stale.name in names:
            continue
        data = stale.read_bytes()
        if not any(copy.read_bytes() == data for copy in (upload / "history").rglob(stale.name)):
            raise RuntimeError(f"{stale} is not preserved under history/; refusing to remove it")
        stale.unlink()
    for source in published:
        (current / source.name).write_bytes(source.read_bytes())
    ledger = upload / "UPLOAD_HISTORY.tsv"
    header = "published_at_utc\texperiment_id\trelease_id\tstatus\tengine_file\tengine_sha256\tnote\n"
    row = "\t".join([camp.get("published_at", PUBLISHED_AT), spec["work_id"], camp["release_id"], "ARTIFACT_VERIFIED",
                     camp["upload_zip"], digest, note]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"published current={current}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_id", choices=sorted(CAMPAIGNS))
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    path = build(args.campaign_id)
    digest = sha(path.read_bytes())
    print(f"built   {path}")
    print(f"size    {path.stat().st_size / 1_048_576:.1f} MB")
    print(f"sha256  {digest}")
    if args.publish:
        publish(args.campaign_id, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
