#!/usr/bin/env python3
"""전수 수집 회차의 발행 — 한 파일·한 명령·한 결과 ZIP, 1단계도 서버 게이트도 없다.

왜 따로 있는가.  지금까지의 회차는 `tools/build_go2_training_length_campaign.py` 가 만드는 campaign
껍데기(회차 ZIP + `go2_target_gate.py` + 저장 기준선)로 나갔다.  그 껍데기의 존재 이유는 **1단계를
싸게 돌려보고 통과할 때만 2단계 GPU 를 쓰는 것**이다.  계획 `upload/plan/GO2_POST_A043_PLAN_20260922.md`
§5 는 다음 회차에서 그 비용절감 분기를 쓰지 않기로 했다 — A043 의 결정적 손실(G2 `combined_yaw_right`,
평가 seed 3개 전부)이 1단계 23 case 밖에 있었고 전수 69 를 돌린 뒤에야 보였기 때문이다(결함 C-11).

게이트가 없으면 껍데기가 할 일이 없다.  회차 ZIP 자체가 실행 단위이고, 러너는 `run_config.env` 가
`GO2_STAGE=full` 을 쓰는 것만으로 학습 → 파국 게이트 → 69 case → sentinel → 영상 → 결과 ZIP 을 한 번에
돈다(`server_run_go2_candidate_iter_pinned.sh`).  그래서 이 모듈은 campaign 을 만들지 않고 **회차 ZIP 을
그대로 발행**한다.  기존 campaign 발행 경로는 글자 하나 건드리지 않는다 — 과거 릴리스는 재빌드로 대조된다.

이 모듈은 **성능을 판정하지 않는다.**  발행은 산출물 무결성(ARTIFACT_VERIFIED)이고, 서버 실행은 사용자
결정이다.  판정은 회수 뒤 `tools/verify_go2_basic_motion_harvest.py` 와 `tools/go2_screening_gate.py` 가 한다.

    python -B tools/build_go2_full_collection_release.py G-A044             # 만들고 검증만
    python -B tools/build_go2_full_collection_release.py G-A044 --publish   # upload/<ID>/current 까지
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_a033_reward_package as reward  # noqa: E402
import build_go2_training_length_package as length  # noqa: E402

RELEASES = {
    "G-A044": {
        # v9 (2026-09-23): 사용자 검토 3회차 — 안내문이 실패 경로를 잘못 적고 있었다(결함 C-24).
        # ① **[DONE] 은 늘 나오지 않는다.**  러너의 `on_exit` crash 경로는 부분 ZIP 을 만들고
        # `COLLECTION_STATUS=INCOMPLETE_CRASH` 를 적은 뒤 표식 없이 끝난다.  "어느 경우에도 표식이
        # 나온다"고 읽히는 안내를 따르면 사용자는 오지 않을 줄을 기다리며 휘발 서버의 예산을 태운다.
        # ② **불완전 상태를 하나로 묶어 「69 를 채운 뒤 종료」로 적었다.**  복구 가능한 누락과 파국
        # 게이트의 안전 중단은 대응이 반대다 — 후자는 정책이 실행되지 않은 판이고, 자료를 얻자고
        # 시뮬레이터를 다시 띄우지 않는 것이 러너의 계약이다(C-14 의 STOP_UNSAFE).  §4 를 세 상태로
        # 나누고, §5-a 와 종료 문장이 그 구분을 따르게 했다.  FULL_69_COMPLETE 가 개수 확인일 뿐
        # SHA·지문·identity·report 검사를 대신하지 않는다는 것도 명시한다.
        # 관문 test_22 는 발행된 러너의 crash 경로를 **실행**해 표식이 없음을 보이고 안내문과 대조한다.
        # 러너 바이트는 그대로다 — 바뀐 것은 안내문과 사양의 판 번호뿐이다.
        # v8 (2026-09-23): 사용자 검토 2회차가 두 가지를 더 잡았다.
        # ① **ZIP 안의 사양이 아직 `--keep` 을 적고 있었다**(C-15 의 나머지 절반).  안내문은 v4 에서
        # 고쳤지만 같은 명령이 `experiment.json` 의 readout 에도 있었고, 사양은 ZIP 에 실려 서버로 간다.
        # 관문 test_14 는 이제 안내문**과 발행된 ZIP 안의 사양** 양쪽에서 판독 명령을 뽑아 전부 실행한다.
        # ② **수집이 중단돼도 전수 완료처럼 보였다**(C-21).  `finish` 는 목록을 다 잰 실행과 파국 게이트의
        # 조기 종료 양쪽에서 불리는데 둘 다 RESULT_STATE=FULL 과 같은 [DONE] 표식을 냈다.  이제 러너가
        # 디스크의 개수에서 `COLLECTION_STATUS` 를 따로 적고(FULL_69_COMPLETE / INCOMPLETE_*),
        # 결손이면 `[INCOMPLETE COLLECTION]` 두 줄을 찍는다.  [DONE] 은 여전히 나온다 — 그것은 회수
        # 준비 신호이고, 전수 완료는 별개이기 때문이다.  안내문 §4·§5 가 그 구분을 싣는다.
        # 관문 test_21 은 발행된 러너의 finish 를 **실행**해 세 경우(조기 종료·전수 완료·69 중 68)를 본다.
        # 러너 바이트가 바뀐다 — 값·문턱·수집 계약은 그대로다.
        # v7 (2026-09-23): 사용자 검토가 안내문 §5 의 exit code 설명이 틀렸다고 잡았다(결함 C-20).
        # "두 명령의 exit 1 은 성능 기준 미충족" 은 두 번 틀렸다. ① 첫 명령은 성능 FAIL 에 exit **0**
        # 을 낸다 — FAIL 이 PASS_VERDICTS 안에 있다(판정을 했다는 뜻).  exit 1 은 INCONCLUSIVE 나
        # BASELINE_REMEASURE_REQUIRED, 곧 **판정 불가**다.  ② 둘째 명령은 FAIL 과 INCONCLUSIVE 를
        # 같은 exit 1 에 담는다.  즉 옛 문장을 따르면 **서버가 살아 있을 때만 메울 수 있는 결손을
        # 성능 실패로 읽고 서버를 끈다.**  §5 는 회수 완결 게이트이므로 이 오독의 대가가 영상·report 다.
        # 관문은 test_go2_g_a044_package_contract.py::test_20 — 두 판독기를 빈 수확물로 **실행**해
        # exit 1 이 성능이 아님을 보이고, 안내문이 그 상태 이름들을 담는지 본다.  값·문턱은 그대로다.
        # v6 (2026-09-22): 계획서 대조에서 나온 기록 공백 셋을 메웠다 — 판정에 닿지 않는다.
        # ① 안내문이 서버 실행 시간 110분만 적고 계획 §7 의 세션 계획치 120~150분(회수 포함)을
        # 옮기지 않았다.  사용자는 안내문을 읽으므로 TTL 을 실행 시간으로 잡을 수 있었다.
        # ② 사양이 G-A043 을 63번 인용하면서 그 정책의 model/env SHA 를 한 번도 고정하지 않았다
        # (`comparison_arm`, 값은 G-A043_LOCAL_VERIFY.json 에서 읽었다 — 계획 산문이 아니라).
        # ③ 계획 §9-1 의 c3 상한 0.567/70 이 서술로만 있어 읽는 사람이 0.054 x 10.5 를 다시
        # 계산해야 했다.  **값·문턱·수집 계약·러너 바이트는 v5 와 같다.**
        # v5 (2026-09-22): 사용자 결정 — 올릴 ZIP 이름에 판 번호를 넣는다.  release_id 는 판마다
        # `_v<N>` 이 붙는데 ZIP 이름에는 붙지 않아 history 에 같은 이름의 ZIP 이 넷 쌓였고, 그중
        # v3 는 올리면 아무것도 돌지 않는 판이다(C-14).  올릴 파일을 고르는 근거가 SHA 손대조
        # 한 줄뿐이었다 — 이제 이름이 판을 말한다(결함 C-18).  관문은
        # build_go2_candidate_package.check_release_version_in_zip_name 이고 사양 검증에서 막는다.
        # 내용은 v4 와 같다: 바뀐 것은 파일 이름과 그 이름을 적는 안내문·manifest 뿐이다.
        # v3 (2026-09-22): 관문 `test_go2_detectability_gate.py::test_14` 가 사양 산문의 맨 이름
        # `FORECAST_CHECK.csv` 를 잡았다 — 같은 이름이 저장소에 둘이라(A038·A043 판독 증거) 어느
        # 파일인지 특정할 수 없다.  네 자리를 전체 경로로 고쳤다.  값·문턱·수집 계약은 그대로다.
        # v2 (2026-09-22): v1 안내문이 소요 시간 근거를 사양의 영어 원문 그대로 한 줄에 쏟아 넣어,
        # 한국어 안내문 안에서 읽히지 않았다.  근거 문장을 한국어 두 줄로 옮겼다.  회차 ZIP 은
        # `experiment.json` 의 release_id 한 줄만 다르고 나머지는 같다.  v1 은 history 에 보존하며
        # 서버에 올린 적 없다 — 발행물은 고치지 않고 다음 판으로 낸다(불변 원칙).
        # 2026-09-26: 소요 시간 문단은 회차 실측을 인용하므로 회차 자료다(G-A047 이 이 모듈을 함께 쓰게 되며 옮겼다).
        # 글자는 v9 안내문 그대로다 — 발행된 안내문은 재빌드로 바이트 대조된다.
        "estimate_ko": (
            '   110분 안팎으로 본다. 근거는 A043 campaign 로그 실측이다 — 학습+23 case+sentinel+영상 8 이\n'
            '   73분 49초, 남은 46 case 가 15분 58초였다. 이 회차는 그 46 case 를 첫 판에 합치고 영상을 14편 찍는다.\n'
            '   이것은 계획치이고 보장이 아니다 — 스크립트는 시간 제한을 걸지 않는다(사양 stages.full.estimate_basis).\n'
            '   **서버 세션은 120~150분으로 잡는다.** 위 110분은 서버가 도는 시간이고, 회수(결과 ZIP 내려받기\n'
            '   · 영상 14편 · telemetry · report 확인)는 그 뒤에 온다 — 계획 §7 의 세션 계획치다.'),
        "guide": "GO2_G_A044_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-22T00:00:00+00:00",
    },
    "G-A047": {
        # v1 (2026-09-26): G3 험지 생존 탐색 — flat_orientation_l2 0.0 -> -0.5 (계획
        # upload/plan/GO2_G_A047_PLAN_20260926.md).  U2 가 허용으로 오면 v10 이 먼저다.
        # v2 (같은 날): v1 은 계획 screening 을 통째로 빼 밀침 네 방향이 G6 합산 한도로만 판정됐다.
        # 보호 묶음만 남긴 판 g3_guard_push4_v1 을 쓴다.  v1 은 실행되지 않았고 history 에 불변으로 남는다.
        "estimate_ko": (
            '   95분 안팎으로 본다. 근거는 G-A044 실측이다 — 같은 계약(학습+69 case+sentinel+영상 14편)의 한 팔이\n'
            '   94분(학습 58분 21초)이었다. 이 회차는 후보 영상 8편만 찍고 기준선 영상은 전부 저장본을 재사용한다.\n'
            '   이것은 계획치이고 보장이 아니다 — 스크립트는 시간 제한을 걸지 않는다(사양 stages.full.estimate_basis).\n'
            '   **서버 세션은 120~150분으로 잡는다.** 위 95분은 서버가 도는 시간이고, 회수(결과 ZIP 내려받기\n'
            '   · 영상 8편 · telemetry · report 확인)는 그 뒤에 온다.\n'
            '   **v10(G-A045·G-A046)과 같은 세션에서 돌리지 않는다.** 한 서버 세션에 한 패키지다.'),
        "guide": "GO2_G_A047_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-26T00:00:00+00:00",
    },
    "G-A048": {
        # v1 (2026-09-26): lin_vel_z_l2 -2.0 -> -1.25, U2 미해결 분기의 탐색 회차(계획
        # upload/plan/GO2_A043_YAW_RIGHT_AND_NEXT_20260926.md §4).  채택 계약은 G-A044 그대로이고,
        # 가설 판정(tools/go2_dial_hypothesis.py)은 별도 판독이다.  U2 가 허용으로 오면 v10 재발행이 먼저다.
        "estimate_ko": (
            '   95분 안팎으로 본다. 근거는 G-A044 실측이다 — 같은 계약(학습+69 case+sentinel+영상)의 한 팔이\n'
            '   94분(학습 58분 21초)이었다. 이 회차는 후보 영상 10편만 찍고 기준선 영상은 전부 저장본을 재사용한다.\n'
            '   이것은 계획치이고 보장이 아니다 — 스크립트는 시간 제한을 걸지 않는다(사양 stages.full.estimate_basis).\n'
            '   **서버 세션은 120~150분으로 잡는다.** 위 95분은 서버가 도는 시간이고, 회수(결과 ZIP 내려받기\n'
            '   · 영상 10편 · telemetry · report 확인)는 그 뒤에 온다.\n'
            '   **v10(G-A045·G-A046)과 같은 세션에서 돌리지 않는다.** 한 서버 세션에 한 패키지다.'),
        "guide": "GO2_G_A048_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-26T00:00:00+00:00",
    },
    "G-A049": {
        # v1 (2026-09-27): lin_vel_z_l2 -2.0 -> -1.0, 분기 B(계획 upload/plan/GO2_NEXT_CANDIDATE_20260927.md §2,
        # 사용자 결정 G-D-BRANCH-B-20260927).  fact_rules_v1 문턱은 G-A048 그대로, 계획 screening 은 사전등록 판
        # post_a048_guard_margin_v1.  가설 판정은 별도 판독이다.  U2 허용이 확인되면 분기 A(seed 43 짝)는 따로 발행한다.
        "estimate_ko": (
            '   95분 안팎으로 본다. 근거는 G-A044 실측이다 — 같은 계약(학습+69 case+sentinel+영상)의 한 팔이\n'
            '   94분(학습 58분 21초)이었다. 이 회차는 후보 영상 10편만 찍고 기준선 영상은 전부 저장본을 재사용한다.\n'
            '   이것은 계획치이고 보장이 아니다 — 스크립트는 시간 제한을 걸지 않는다(사양 stages.full.estimate_basis).\n'
            '   **서버 세션은 120~150분으로 잡는다.** 위 95분은 서버가 도는 시간이고, 회수(결과 ZIP 내려받기\n'
            '   · 영상 10편 · telemetry · report 확인)는 그 뒤에 온다.\n'
            '   **다른 패키지(v10·분기 A)와 같은 세션에서 돌리지 않는다.** 한 서버 세션에 한 패키지다.'),
        "guide": "GO2_G_A049_ONE_COMMAND_RUN_GUIDE.txt",
        "published_at": "2026-09-27T00:00:00+00:00",
    },
}


# G-A050 is an unpublished draft; validation, not this registry, authorizes publication.
RELEASES["G-A050"] = {
    "estimate_ko": RELEASES["G-A049"]["estimate_ko"],
    "guide": "GO2_G_A050_ONE_COMMAND_RUN_GUIDE.txt",
    "published_at": "2026-09-27T00:00:00+00:00",
}


# G-A051 (2026-09-27): A048 보상 위 ang_vel_xy_l2 -0.05 -> -0.06.  같은 전수 수집 계약이다.
RELEASES["G-A051"] = {
    "estimate_ko": RELEASES["G-A049"]["estimate_ko"],
    "guide": "GO2_G_A051_ONE_COMMAND_RUN_GUIDE.txt",
    "published_at": "2026-09-27T00:00:00+00:00",
}


# G-A053 (2026-09-28): A048 보상 위 목록 밖 항 dof_acc_l2 -2.5e-7 -> -3.0e-7 한 줄 추가.  같은 전수 수집 계약이다.
RELEASES["G-A053"] = {
    "estimate_ko": RELEASES["G-A049"]["estimate_ko"],
    "guide": "GO2_G_A053_ONE_COMMAND_RUN_GUIDE.txt",
    "published_at": "2026-09-28T00:00:00+00:00",
}


# G-A055 (2026-09-29): A043 보상 위 ang_vel_xy_l2 -0.05 -> -0.08.  같은 전수 수집 계약이다.
# 조건부 준비·실행 미승인(Codex 2026-09-29) — G-A056 진단 판독 뒤 Codex 가 실행 여부를 정한다.
RELEASES["G-A055"] = {
    "estimate_ko": RELEASES["G-A049"]["estimate_ko"],
    "guide": "GO2_G_A055_ONE_COMMAND_RUN_GUIDE.txt",
    "published_at": "2026-09-29T00:00:00+00:00",
    # 안내문 선택 필드(이 회차만): 상태 줄과 다섯째 판독 줄.  두 필드가 없는 회차의 안내문 글자는 그대로다.
    "status_ko": ("**조건부 준비·실행 미승인**(Codex 2026-09-29). G-A056 진단 재생의 회수·판독 뒤 Codex 가 실행 여부를 정한다\n"
                  "(관측 → 원인 설명 가능 범위 → 강좌 예측 → 반례 대조 → 실행/미실행). 판독이 불명확하면 그 세션에서 돌리지 않는다.\n"
                  "G-A056 러너는 이 패키지를 부르지 않는다 — 진단이 끝나도 이 학습은 자동으로 돌지 않는다.\n"),
    "extra_readers": [(
        "     python -B tools/go2_g_a055_readout.py --harvest workspace/_keep/go2_g_a055_a043_ang_vel_xy_m008\n",
        "   다섯째 명령은 사전등록 §4 의 1순위 case 판독이다(험지 옆걸음 + 조건 C, 복합 우회전 + 조건 S, 밀침 네 방향 따로,\n"
        "   험지 전진·계단 공개). G-A043 대비이고 채택 판정과 합치지 않는다. exit 1 은 결손·미검증뿐이다.\n")],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(work_id: str) -> dict:
    return reward.load(work_id)


def validate(spec: dict) -> None:
    """발행 전에 이 경로가 실제로 전수 수집 회차인지 확인한다."""
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"{spec.get('work_id')}: {message}")

    reward.validate_spec(spec)
    # 결함 C-37(2026-09-27): 추론 행의 인용 검사(tools/test_go2_detectability_gate.py _check_rows)를 발행 전에
    # 돌린다.  G-A050 v2 는 이 검사를 거치지 않고 나가 CSV 칸에 없는 값을 인용했다.
    import unittest
    import test_go2_detectability_gate as gate
    block = spec.get("inference") or {}
    try:
        gate._check_rows(unittest.TestCase(), str(spec.get("work_id")),
                         list(block.get("rows") or []) + list(block.get("contradicting") or []),
                         spec.get("work_id"), spec)
    except AssertionError as exc:
        raise RuntimeError(f"{spec.get('work_id')}: inference row citation fails the detectability gate: {exc}") from exc
    # 결함 C-38(2026-09-27): 위 검사는 인용 행만 본다.  G-A051 v1 은 같은 관문 모듈의 다른 사양 검사(test_12 원장
    # 인용, test_14 경로 열기)와 정본 정합성 검사를 거치지 않고 발행됐다.  두 모듈 전체를 돌려 **이 사양 파일 이름이
    # 붙은** 실패만 모은다 — 다른 사양의 기존 실패(A045·A046 test_10 등)는 이 발행을 막지 않는다.
    import test_go2_canonical_consistency as canonical
    spec_file = reward.SPECS[spec["work_id"]].name
    result = unittest.TestResult()
    for module in (gate, canonical):
        unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
    mine = [f"{test}: {trace.strip().splitlines()[-1]}" for test, trace in result.failures + result.errors
            if spec_file in str(test) or spec_file in trace]
    need(not mine, "spec fails a gate it will be judged by after publication:\n  " + "\n  ".join(mine))
    need(length.collection_mode(spec) == length.FULL_COLLECTION,
         "this publisher is for full-collection runs only; a staged arm goes through the campaign builder")
    config = reward.run_config(spec)
    need("GO2_STAGE=full\n" in config, "run_config.env must pin GO2_STAGE=full")
    need("COLLECT_REQUIRED_ON_STATIONARY=1\n" in config,
         "a stationary policy must still leave the full collection")
    need(int(spec["evaluation"]["case_count"]) == 69, "the full evaluation is 69 cases")
    need(spec["runner"] == length.RUNNER, f"runner must be {length.RUNNER}")


def build(work_id: str) -> Path:
    spec = load(work_id)
    validate(spec)
    data = reward.build_zip(spec)
    target = reward.output_path(spec)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.read_bytes() != data:
        raise RuntimeError(f"immutable release conflict: {target}")
    target.write_bytes(data)
    (target.parent / f"{target.name}.sha256").write_text(
        f"{sha(data)}  {target.name}\n", encoding="utf-8", newline="\n")
    print(f"{work_id}: {target}  sha256 {sha(data)}  {len(data)} bytes")
    return target


def run_guide(work_id: str, digest: str) -> str:
    spec = load(work_id)
    release = RELEASES[work_id]
    out, single, base = spec["output"], spec["single_change"], spec["baseline"]
    root, runner = out["package_root"], spec["runner"]
    stage = spec["stages"]["full"]
    videos = len(spec["videos"]["candidate"]) + len(spec["videos"]["baseline"])
    reused = len(spec["videos"].get("baseline_reuse") or {})
    # 2026-09-26 (G-A047): 계획 screening 을 쓰지 않는 회차는 둘째 판독 줄이 screening 이 아니라 정체시간
    # 필수 기록이다.  screening 을 쓰는 회차(G-A044)의 글자는 그대로다.
    screening = (spec["preregistered"].get("plan_screening") or {}).get("version")
    if screening:
        reader_two = f"""     python -B tools/go2_screening_gate.py --candidate workspace/_keep/{out['keep_dir_name']} \\
         --rule-version {screening}
"""
        reader_two_note = """   둘째 명령은 INTERNAL_GATE_PASS 에만 exit 0 이고 FAIL 과 INCONCLUSIVE 가 같은 exit 1 이다.
   둘은 다른 상태다 — SCREENING 줄의 이름으로 구분하고, INCONCLUSIVE 면 missing 목록을 회수 대상으로 본다.
"""
    else:
        reader_two = ("     python -B tools/go2_stall_diagnostics.py --candidate "
                      f"workspace/_keep/{out['keep_dir_name']}/evaluation/candidate\n")
        reader_two_note = ("   둘째 명령은 판정이 아니라 정체시간 필수 기록이다 — 이 회차는 계획 screening 을 쓰지 않고\n"
                           "   fact_rules_v1 만으로 판정한다. 결과는 reports/evidence/go2_stall_diagnostics/<회차>/ 에 쓰인다.\n")
    # 2026-09-26 (G-A048): 가설 판정을 사전등록한 회차는 셋째 판독 줄이 붙는다.  채택 판정과 섞지 않는다.
    # 가설 블록이 없는 회차(G-A044·G-A047)의 글자는 그대로다.
    reader_three = reader_three_note = ""
    if (spec["preregistered"].get("hypothesis") or {}).get("reader"):
        reader_three = (f"     python -B {spec['preregistered']['hypothesis']['reader']} {work_id} "
                        f"--harvest workspace/_keep/{out['keep_dir_name']}\n")
        reader_three_note = ("   셋째 명령은 채택이 아니라 사전등록 가설의 지표별 판정이다(지지·미지지·불충분, 비용은 있음·없음·불충분).\n"
                             "   채택 판정과 합치지 않는다. exit 1 은 기록 결손(MISSING)뿐이고 미지지는 exit 0 이다.\n")
    # 2026-09-27 (G-A051): 보상 기준이 채택 기준선과 다른 회차는 무엇이 몇 줄 다른지와 넷째 판독 줄(보상 기준 대비
    # 효과 판정)을 적는다.  reward_base 가 없는 회차의 글자는 그대로다.
    rbase = spec.get("reward_base")
    reader_four = reader_four_note = ""
    if rbase:
        own = rbase["change"]
        what = (f"바꾸는 것은 보상 가중치 한 항이다: {rbase['name']} 보상 위에서 {single['name']} {single['from']} -> {single['to']}.\n"
                f"채택 기준선 {base['name']} 대비로는 두 항이 다르다: {own['name']} {own['from']} -> {own['to']}({rbase['name']}의 변경)와 이 항.\n"
                f"효과는 후보 - {rbase['name']}, 채택은 후보 - {base['name']}로 따로 읽는다. "
                f"학습 seed 42·4096 env·1000 iter·평가 iter {spec['evaluation']['checkpoint_iter']}는 그대로다.\n")
        if spec.get("change_class") == reward.ENV_REWARD_CLASS:
            # G-A053: 목록 밖 항은 배포 report.html 의 보상 변화 표에 나오지 않는다(go2_task/_finalize.py 의
            # _REP_BASELINE·_REP_INTENT 에 없다).  적용 증거는 학습 env.yaml 과 서버 env-rewards 검사다.
            what += (f"{single['name']}은 배포 REWARD_WEIGHTS 목록 밖의 기존 보상 항이라 보상 파일에 한 줄을 더한다"
                     f"(사용자 승인 G-D-U1-APPROVED-20260928). 배포 report.html 의 보상 변화 표에는 이 변경이 나오지 않는다 —\n"
                     f"적용 증거는 학습 env.yaml 과 training/ENV_REWARD_CHECK.txt 다.\n")
        comparison = spec["preregistered"]["reward_base_comparison"]
        reader_four = (f"     python -B {comparison['reader']} {work_id} "
                       f"--harvest workspace/_keep/{out['keep_dir_name']}\n")
        reader_four_note = (f"   넷째 명령은 {rbase['name']} 대비 효과 판독이다(REVIEW_CANDIDATE · NOT_REVIEW_CANDIDATE · INCONCLUSIVE). 채택 판정과 합치지 않는다.\n"
                            f"   REVIEW_CANDIDATE 는 정량 후보 검토 대상일 뿐 최종 진보 판정이 아니다 — {rbase['name']} 대비 계단·밀침·복합 회전의\n"
                            f"   허용 손실은 사전등록하지 않았으므로, 출력된 차이를 사람이 읽기 전에는 진보라고 보고하지 않는다.\n"
                            f"   첫 명령의 QUANT_SUCCESS_VIDEO_REVIEW_PENDING 은 영상 검토 전 정량 조건 충족이지 채택 PASS 가 아니다.\n")
    else:
        what = (f"바꾸는 것은 보상 가중치 한 항이다: {single['name']} {single['from']} -> {single['to']}.\n"
                f"기준선 {base['name']}의 나머지 가중치·학습 seed 42·4096 env·1000 iter·평가 iter {spec['evaluation']['checkpoint_iter']}는 그대로다.\n")
    extra_cmds = "".join(cmd for cmd, _ in release.get("extra_readers", []))
    extra_notes = "".join(note for _, note in release.get("extra_readers", []))
    return f"""GO2 {work_id} 실행 안내 — 한 파일 · 한 명령 · 결과 ZIP 하나
{'=' * 60}

{what}{release.get('status_ko', '')}추론 사슬 상태 {spec['inference']['status']}. 서버 실행은 사용자 결정이다.

1. 업로드 — 이 파일 하나만 올린다
   {out['upload_zip']}
   SHA256 {digest}
   서버 경로 /workspace/{out['upload_zip']}

2. 실행 — 한 줄
   unzip -oq /workspace/{out['upload_zip']} -d /workspace && bash {root}/{runner}

   끊겼을 때 이어서: GO2_RESUME=1 bash {root}/{runner}
   진행 보기:       tmux attach -t {out['tmux_name']}

3. 무엇이 도는가 — 1단계도 서버 게이트도 없다
   학습 1000 iter -> 파국 게이트(학습 손실 유한 · 후보가 {spec['evaluation']['catastrophe_case']}에서 움직이는가)
   -> **69 case 전부**(평가 seed 101/202/303 x 32 env) -> 기준선 sentinel {len(spec['evaluation']['sentinel_cases'])} case
   -> 영상 {videos}개(후보 {len(spec['videos']['candidate'])} · 기준선 신규 {len(spec['videos']['baseline'])}, 나머지 {reused}개는 저장본을 SHA로 재사용)
   -> 결과 ZIP 하나.
{release['estimate_ko']}
   실행 시간으로 TTL 을 잡으면 회수 도중에 시간이 끊기고, 그때 잃는 것은 영상과 report 다.

   정책이 서 있어도(파국 게이트 STATIONARY) 필수 수집과 영상은 그대로 회수한다
   (run_config.env `COLLECT_REQUIRED_ON_STATIONARY=1`). 성능이 나쁘다는 이유로 자료를 버리지 않는다.

4. 완료 표식과 내려받을 것 — 표식은 「회수 준비」이지 「전수 완료」가 아니다
   [DONE] 표식: {out['done_marker']}
   /workspace/_keep/{out['result_zip']}
   /workspace/_keep/{out['result_zip']}.sha256
   **[DONE] 은 결과 ZIP 이 만들어졌다는 뜻뿐이고, 늘 나오는 것도 아니다.** 러너가 도중에 죽으면
   `on_exit` 가 부분 ZIP 을 만들고 `COLLECTION_STATUS=INCOMPLETE_CRASH` 를 적은 채 끝난다 —
   **그 판에는 [DONE] 이 없다.** 그러니 표식 하나를 기다리지 말고 아래 세 상태를 구분한다.
   무엇이 실제로 수집됐는지는 `_keep/{out['keep_dir_name']}/RESULT_STATUS.txt` 와 `RUNNER_STATUS.txt` 의
   `COLLECTION_STATUS` 에 적힌다.

   ① 정상 완료 — [DONE] 있음 · COLLECTION_STATUS=FULL_69_COMPLETE
      69 case · sentinel · 영상이 계획한 개수만큼 있다. §5 의 다섯 줄을 확인하고 끈다.
      **이것은 개수 확인이다.** SHA · 지문 · identity · report 검사를 대신하지 않는다.
   ② 복구 가능한 수집 누락 — [DONE] 있음 · COLLECTION_STATUS=INCOMPLETE_COLLECTION
      로그에 `[INCOMPLETE COLLECTION]` 두 줄이 함께 찍힌다. 빠진 case 와 영상은 서버가 살아
      있을 때만 다시 잴 수 있다. 메우고 다시 회수한 뒤에 끈다.
   ③ crash · 안전상 평가 불가 — [DONE] **없음**(INCOMPLETE_CRASH) 또는 [DONE] 있음 ·
      COLLECTION_STATUS=INCOMPLETE_EARLY_STOP
      **여기서는 69 를 채우지 않는다.** 파국 게이트가 멈춘 판은 학습이 비유한하거나 정책이
      실행되지 않은 판이고, 자료를 얻자고 시뮬레이터를 다시 띄우지 않는 것이 러너의 계약이다.
      [DONE] 을 기다리지 말고 `launcher.log` 와 `RUNNER_STATUS.txt`(RUNNER_RC · FAILED_AT)를
      읽고 부분 ZIP 에 무엇이 들어왔는지 본다. 안전하게 회수할 수 있는 것 — 학습 로그 ·
      checkpoint · env.yaml · exported/report.html · 거기까지 찍힌 telemetry — 을 보존하고,
      없는 것을 결측 목록으로 적은 뒤에 종료를 판단한다.
      이 판은 「성능 실패」가 아니라 「판정 불가」다.
   원 학습 report 는 평가 재생 전에 _keep/{out['keep_dir_name']}/exported/report.html 로 보존된다.
   REPORT_STATUS 가 REPORT_ACQUIRED 가 아니면 회수 완결이 아니다.

5. SERVER SHUTDOWN GATE — SHA 일치만으로 끄지 않는다
   SHA 는 파일이 깨지지 않았다는 증거일 뿐 회수 완결이 아니다. 아래 다섯 줄이 모두 채워진 뒤에 끈다
   (루트 AGENTS.md 「학습 종료 후 영상 증거 게이트」 §5·§7).
   a. 결과 ZIP {out['result_zip']} 과 .sha256 로컬 도착 · SHA 일치, 그리고
      `RESULT_STATUS.txt` 의 `COLLECTION_STATUS` 를 §4 의 세 상태 중 하나로 읽었다.
      FULL_69_COMPLETE 는 개수 확인이지 아래 b~e 의 면제가 아니다.
      INCOMPLETE_COLLECTION 이면 서버를 켠 채로 메우고 다시 회수한다.
      INCOMPLETE_CRASH · INCOMPLETE_EARLY_STOP 이면 **채우지 않는다** — §4 ③ 대로 회수 가능한
      것을 보존하고 결측을 적는다.
   b. 원 학습 report.html = REPORT_ACQUIRED ( _keep/{out['keep_dir_name']}/exported/REPORT_STATUS.txt )
      그리고 같은 학습의 env.yaml · 로그 · checkpoint
   c. 69 case telemetry 전부와 기준선 sentinel {len(spec['evaluation']['sentinel_cases'])} case
   d. 영상 {videos}편(후보 {len(spec['videos']['candidate'])} · 기준선 신규 {len(spec['videos']['baseline'])})의 파일과 지문 도착,
      SHA 로 재사용하는 저장본 {reused}편의 대조 성공
   e. 아래 로컬 판독 두 줄을 실제로 실행하고 그 verdict 를 기록했다
   하나라도 비면 종료 불가다 — 단 §4 ③ 은 예외다. 거기서는 없는 자료를 만들 수 없으므로
   게이트는 「전부 채웠다」가 아니라 「무엇이 없고 왜 없는지 적었다」로 닫는다.
   성능 FAIL 과 회수 완결은 별개다 — 실패한 정책의 자료도 똑같이 회수한다.

   로컬 판독 (GPU 0):
     python -B tools/verify_go2_basic_motion_harvest.py {work_id} \\
         --harvest workspace/_keep/{out['keep_dir_name']} \\
         --out workspace/_keep/{out['keep_dir_name']}/harvest_verification.json
{reader_two}{reader_three}{reader_four}{extra_cmds}   **exit code 만으로 성능도 서버 종료 여부도 판단하지 않는다.** 출력 VERDICT 와 결측·identity 오류를
   읽고, 서버에서 더 회수하거나 재측정할 것이 없는지 확인한 뒤에 끈다.
   첫 명령은 **성능 FAIL 에도 exit 0** 을 낸다 — 판정을 했다는 뜻이다
   (`verify_go2_basic_motion_harvest.PASS_VERDICTS`). exit 1 은 INCONCLUSIVE 나
   BASELINE_REMEASURE_REQUIRED, 즉 **판정을 못 했다**는 뜻이고 그때 볼 것은 성능이 아니라
   `artifact_faults`·`ruler_mismatches` — 무엇이 없어서 못 했는지다. 그 결손은 서버가 살아 있을 때만 메운다.
{reader_two_note}{reader_three_note}{reader_four_note}{extra_notes}   서버 게이트는 이 회차에 없다 — 판정은 처음부터 끝까지 로컬 검증기가 한다.

6. 이 패키지가 보장하지 않는 것
   점수 이득을 약속하지 않는다. 학습 seed 는 42 하나뿐이라 한 회차로는 레버 효과와 seed 운을 가를 수 없다.
   공식 결과는 OFFICIAL_RESULT_UNMEASURED 다.
"""


def publish(work_id: str, zip_path: Path) -> None:
    spec = load(work_id)
    release = RELEASES[work_id]
    out = spec["output"]
    digest = sha(zip_path.read_bytes())
    upload = GO2 / "upload" / work_id
    history, current = zip_path.parent, upload / "current"
    current.mkdir(parents=True, exist_ok=True)
    guide = release["guide"]
    single = spec["single_change"]
    # G-A051: 보상 기준이 채택 기준선과 다르면 그 이름을 적는다(없는 회차의 글자는 그대로).
    on = (f"{spec['reward_base']['name']} rewards (adoption vs {spec['baseline']['name']})"
          if spec.get("reward_base") else spec['baseline']['name'])
    note = (f"{work_id} {on} + {single['name']} {single['from']}->{single['to']}. "
            "One upload: the arm ZIP byte-identical to its builder, the whole 69-case evaluation in one "
            "pass (GO2_STAGE=full pinned in run_config.env), no target stage and no server gate, one "
            f"result ZIP. {spec['status']}.")
    manifest = {
        "experiment_id": work_id, "note": note, "published_at_utc": release["published_at"],
        "release_id": out["release_id"], "status": "ARTIFACT_VERIFIED", "support_files": [guide],
        "upload_files": [{"name": out["upload_zip"], "server_path": f"/workspace/{out['upload_zip']}",
                          "sha256": digest}],
    }
    earlier = sorted(d.name for d in (upload / "history").glob("*")
                     if d.is_dir() and d.name != out["release_id"])
    tail = ("첫 판이다(이전 판 없음).\n" if not earlier else
            f"이전 판 {len(earlier)}개는 ../history 에 보존한다(가장 최근 {earlier[-1]}), 모두 서버에 올린 적 없다.\n")
    status_line = (f"권고 상태: 추론 사슬 {spec['inference']['status']} — "
                   + spec["campaign_text"]["publish_note_ko"] + "\n")
    current_text = (
        f"CURRENT GO2 UPLOAD — {work_id} (one command, full 69)\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{work_id}\\current\\{out['upload_zip']}\n"
        f"   SHA256 {digest}\n\n"
        "한 파일·한 명령으로 학습 → 69 case 전수 → sentinel → 영상 → 결과 ZIP 하나.\n"
        "1단계 분기와 서버 게이트는 이 회차에 없다(계획 §5).\n"
        f"절차는 같은 폴더의 {guide}.\n"
        "서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {out['release_id']}\nSTATUS ARTIFACT_VERIFIED\n" + tail + status_line)
    files = {
        guide: run_guide(work_id, digest).encode("utf-8"),
        "UPLOAD_MANIFEST.json": (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "CURRENT_UPLOAD.txt": current_text.encode("utf-8"),
    }
    for name, data in files.items():
        target = history / name
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"immutable release conflict: {target}")
        target.write_bytes(data)
    (history / f"{guide}.sha256").write_text(f"{sha(files[guide])}  {guide}\n", encoding="utf-8", newline="\n")
    published = [zip_path, zip_path.parent / f"{zip_path.name}.sha256",
                 *(history / name for name in files), history / f"{guide}.sha256"]
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
    row = "\t".join([release["published_at"], work_id, out["release_id"], "ARTIFACT_VERIFIED",
                     out["upload_zip"], digest, note]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"published current={current}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work_id", choices=sorted(RELEASES))
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args(argv)
    zip_path = build(args.work_id)
    if args.publish:
        publish(args.work_id, zip_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
