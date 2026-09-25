"""Build (and optionally publish) the one-file pair package for G-A031 + G-A032.

The user asked (2026-09-15) for one file and one command in place of two staged
uploads.  The pair ZIP carries:
  arms/                 the two arm ZIPs, byte for byte as tools/build_go2_candidate_package.py
                        builds and publishes them; nothing inside an arm changes
  server_run_go2_basic_motion_pair.sh   runs both target stages, gates, then the full stages
  go2_target_gate.py    criterion 1 on the server (with its two stdlib dependencies)
  stored_baseline/      the stored A017 (G-A027) summaries the gate reads, verified here
                        in full against their raw steps.csv before they are packed
Plan: workspace/training/quadruped/upload/plan/GO2_BASIC_MOTION_TUNING_PLAN_20260915.md.

    python tools/build_go2_basic_motion_pair.py            # build and verify
    python tools/build_go2_basic_motion_pair.py --publish  # also publish upload/G-A031_A032
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT / "workspace" / "training" / "quadruped"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(GO2))

import build_go2_candidate_package as pkg  # noqa: E402
import verify_go2_a027_harvest as harvest  # noqa: E402

ARMS = ("G-A031", "G-A032")
PAIR_ID = "G-A031+G-A032"
UPLOAD_ID = "G-A031_A032"
RELEASE_ID = "20260915_basic_motion_pair_v1"
PREFIX = Path("go2_basic_motion_pair")
PACKAGE_ROOT = "/workspace/" + PREFIX.as_posix()
RUNNER = "server_run_go2_basic_motion_pair.sh"
UPLOAD_ZIP = "GO2_G_A031_A032_basic_motion_pair.zip"
TMUX = "go2_basic_motion_pair"
KEEP_NAME = "go2_basic_motion_pair_a031_a032"
RESULT_ZIP = "GO2_BASIC_MOTION_PAIR_RESULT.zip"
DONE_MARKER = "[DONE] GO2_BASIC_MOTION_PAIR_RESULT_READY"
GATE_FILES = {
    "go2_target_gate.py": ROOT / "tools" / "go2_target_gate.py",
    "verify_go2_a027_harvest.py": ROOT / "tools" / "verify_go2_a027_harvest.py",
    "go2_fixed_eval_report.py": GO2 / "go2_fixed_eval_report.py",
}
# 2026-09-17: the working-tree gate reads fact_rules_v1 (tools/go2_fact_rules.py) and needs two more
# files.  The gate the pair, G-A033 and G-A038 ran is kept byte for byte; their releases rebuild from it.
FACT_RULE_FILES = {
    "go2_fact_rules.py": ROOT / "tools" / "go2_fact_rules.py",
    "go2_climb_count.py": ROOT / "tools" / "go2_climb_count.py",
}
EXECUTED_GATE = GO2 / "runner_history" / "go2_target_gate.199439080c47a816.py"


def gate_payload(executed: bool) -> dict[str, bytes]:
    """The server gate files: what ran (executed releases) or the working tree (new releases)."""
    payload = {name: path.read_bytes() for name, path in GATE_FILES.items()}
    if executed:
        frozen = EXECUTED_GATE.read_bytes()
        if not hashlib.sha256(frozen).hexdigest().startswith(EXECUTED_GATE.name.split(".")[1]):
            raise RuntimeError("executed gate copy does not match its recorded sha")
        payload["go2_target_gate.py"] = frozen
    else:
        payload.update({name: path.read_bytes() for name, path in FACT_RULE_FILES.items()})
    for name, data in payload.items():
        if b"\r" in data:
            raise RuntimeError(f"gate file {name} has CR bytes")
    return payload
FIXED_TIMESTAMP = pkg.FIXED_TIMESTAMP
PUBLISHED_AT = pkg.PUBLISHED_AT
GUIDE = "GO2_G_A031_A032_PAIR_RUN_GUIDE.txt"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_specs() -> list[dict]:
    return [pkg.load(work) for work in ARMS]


def output_path() -> Path:
    return GO2 / "upload" / UPLOAD_ID / "history" / RELEASE_ID / UPLOAD_ZIP


def validate(specs: list[dict]) -> None:
    a, b = specs

    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"pair: {message}")

    for spec in specs:
        pkg.validate_spec(spec)
    need(a["pair"]["other_work_id"] == b["work_id"] and b["pair"]["other_work_id"] == a["work_id"],
         "the two specs must name each other as the pair")
    # One stored arm serves both gates, so both arms must read the same cases the same way.
    for key in ("baseline", "evaluation", "preregistered", "stages", "videos", "training"):
        need(a[key] == b[key], f"{key} must be identical across the pair")
    for key in ("package_root", "keep_dir_name", "result_zip", "tmux_name", "upload_zip", "done_marker"):
        need(a["output"][key] != b["output"][key], f"output.{key} must differ between the arms")
    need(PACKAGE_ROOT not in (a["output"]["package_root"], b["output"]["package_root"]),
         "the pair folder must not be an arm folder")


def stored_entries(spec: dict) -> list[str]:
    evaluation = spec["evaluation"]
    entries = [evaluation["catastrophe_case"], *pkg.targets(spec), *evaluation["sentinel_cases"]]
    return sorted(set(entries), key=entries.index)


def stored_payload(spec: dict) -> dict[str, bytes]:
    """The stored A017 summaries the gate reads, each verified against its raw steps.csv."""
    base = spec["baseline"]
    arm = ROOT / base["stored_arm"] / "evaluation" / base["label"]
    identity = json.loads((arm / "identity.json").read_text(encoding="utf-8"))
    for key, expected in (("model_sha256", base["model_sha256"]), ("env_sha256", base["env_sha256"]),
                          ("evaluator_sha256", base["evaluator_sha256"]),
                          ("registry_sha256", base["registry_sha256"])):
        if identity.get(key) != expected:
            raise RuntimeError(f"stored arm identity {key}={identity.get(key)!r}, expected {expected}")
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


def arm_zips(specs: list[dict]) -> dict[str, bytes]:
    """Each arm ZIP as its own builder makes it; it must equal the published copy."""
    zips = {}
    for spec in specs:
        data = pkg.build(spec).read_bytes()
        current = pkg.upload_dir(spec) / "current" / spec["output"]["upload_zip"]
        if current.is_file() and current.read_bytes() != data:
            raise RuntimeError(f"{current} differs from a rebuild of {spec['work_id']}")
        zips[spec["output"]["upload_zip"]] = data
    return zips


def pair_config(specs: list[dict], zips: dict[str, bytes]) -> str:
    names = [spec["output"]["upload_zip"] for spec in specs]

    def array(values: list[str]) -> str:
        return "(" + " ".join(shlex.quote(value) for value in values) + ")"

    return "".join([
        "# generated by tools/build_go2_basic_motion_pair.py; do not edit\n",
        f"PAIR_ID={shlex.quote(PAIR_ID)}\n",
        f"PAIR_RELEASE_ID={RELEASE_ID}\n",
        f"PAIR_TMUX={TMUX}\n",
        f"PAIR_KEEP_NAME={KEEP_NAME}\n",
        f"PAIR_RESULT_ZIP={RESULT_ZIP}\n",
        f"PAIR_DONE_MARKER={shlex.quote(DONE_MARKER)}\n",
        f"ARM_WORK={array([spec['work_id'] for spec in specs])}\n",
        f"ARM_ZIP={array(names)}\n",
        f"ARM_ZIP_SHA={array([sha(zips[name]) for name in names])}\n",
        f"ARM_ROOT={array([spec['output']['package_root'] for spec in specs])}\n",
    ])


def readme(specs: list[dict], zips: dict[str, bytes]) -> str:
    arms = "\n".join(
        f"  {spec['work_id']}  {spec['single_change']['name']} {spec['single_change']['from']} -> "
        f"{spec['single_change']['to']}   arms/{spec['output']['upload_zip']}  sha256 {sha(zips[spec['output']['upload_zip']])}"
        for spec in specs)
    title = "GO2 G-A031 + G-A032 BASIC-MOTION PAIR — one upload, one command, one result"
    return f"""{title}
{'=' * len(title)}

This package TRAINS two policies, one after the other on one GPU, and measures
them.  status: exploratory.  Plan: GO2_BASIC_MOTION_TUNING_PLAN_20260915.md.

ARMS (byte for byte the published single-arm packages)
{arms}

RUN
  unzip -oq {UPLOAD_ZIP} -d /workspace
  bash {PACKAGE_ROOT}/{RUNNER}
  Resume after an interruption: GO2_RESUME=1 bash {PACKAGE_ROOT}/{RUNNER}

WHAT HAPPENS
  1 target stage of G-A031, then of G-A032 (~1h25m each): training, catastrophe
    gate, the 9 target cases, the sentinel, 5 videos.
  2 after each target stage, go2_target_gate.py reads criterion 1 (plan 6-1):
      TARGET_PASS -> full stage (~55m); FAIL -> the arm ends;
      REMEASURE_BASELINE -> target stage again with A017 remeasured, gate again;
      UNDECIDED -> no full stage.
  3 full stage of each arm the gate passed.
  4 one result ZIP.  The gate only schedules GPU time; the local verifier
    (tools/verify_go2_basic_motion_harvest.py) decides every verdict.

DOWNLOAD
  /workspace/_keep/{RESULT_ZIP}
  /workspace/_keep/{RESULT_ZIP}.sha256
  Finish marker: {DONE_MARKER}
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build_payload() -> dict[str, bytes]:
    specs = load_specs()
    validate(specs)
    runner = (GO2 / RUNNER).read_bytes()
    if b"\r" in runner:
        raise RuntimeError("pair runner has CR bytes")
    zips = arm_zips(specs)
    payload: dict[str, bytes] = {RUNNER: runner}
    payload.update(gate_payload(executed=True))
    payload.update(stored_payload(specs[0]))
    for name, data in zips.items():
        payload[f"arms/{name}"] = data
    payload["pair_config.env"] = pair_config(specs, zips).encode("utf-8")
    payload["README.txt"] = readme(specs, zips).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["PAIR_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def build() -> Path:
    payload = build_payload()
    output = output_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo((PREFIX / name).as_posix(), date_time=FIXED_TIMESTAMP)
            info.external_attr = (0o755 if name.endswith(".sh") else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        names = archive.namelist()
        if len(names) != len(payload):
            raise RuntimeError("member count mismatch")
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise RuntimeError("unsafe member")
    built = temporary.read_bytes()
    temporary.unlink()
    if output.exists() and output.read_bytes() != built:
        raise RuntimeError(f"immutable release conflict: {output} differs from this build")
    output.write_bytes(built)
    output.with_suffix(".zip.sha256").write_text(f"{sha(built)}  {output.name}\n", encoding="utf-8", newline="\n")
    return output


def run_guide(digest: str) -> str:
    specs = load_specs()
    a, b = specs
    keeps = {spec["work_id"]: f"workspace/_keep/{spec['output']['keep_dir_name']}" for spec in specs}
    videos = ", ".join(entry.split(":")[1] for entry in a["videos"]["candidate"])
    return f"""GO2 G-A031 + G-A032 PAIR SERVER RUN GUIDE (파일 하나, 명령 하나, 결과 하나)

두 회차를 한 파일로 올리고 한 명령으로 이어서 돌린다.
- G-A031: A017 + `feet_air_time` 0.2→{a['single_change']['to']}(Isaac Lab Go2 rough 값)
- G-A032: A017 + `feet_air_time` 0.2→{b['single_change']['to']}(중간값)
계획서: {a['plan']}
서버 실행은 사용자 결정 사항이다. 이 문서는 실행 절차이지 실행 승인이 아니다.

LOCAL FILE TO UPLOAD (이것 하나만)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{UPLOAD_ID}\\current\\{UPLOAD_ZIP}
   SHA256 {digest}
안에 두 회차 ZIP이 공개본과 바이트 동일하게 들어 있다(upload/G-A031, upload/G-A032 current). 그 두 파일은 따로 올리지 않는다.

SERVER DESTINATION
/workspace/{UPLOAD_ZIP}

ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {UPLOAD_ZIP}' | sha256sum -c - && unzip -oq {UPLOAD_ZIP} && bash {PACKAGE_ROOT}/{RUNNER}

시작 전 러너가 하는 일
두 회차 ZIP의 SHA 확인 → /workspace/go2_g_a031, go2_g_a032로 풀기 → 회차별 preflight(평가기·registry·A017 SHA) → 학습·play 프로세스, tmux 세션, 이전 결과가 있으면 거부.

순서와 시간 (한 GPU에서 차례로. 동시에 돌리지 않는다)
1. G-A031 1단계 → 서버 게이트 → G-A032 1단계 → 서버 게이트. 1단계는 학습 1,000 iter, 파국 게이트, 표적 9 case, A017 표지 5 case, 영상 5개({videos})다. 회차당 약 1시간 25분, 둘이면 약 2시간 50분.
2. 게이트가 통과시킨 회차만 2단계(나머지 59 case)를 돈다. 회차당 약 55분.
3. 결과 ZIP 하나로 묶는다.
두 회차 모두 1단계에서 떨어지면 약 2시간 50분, 둘 다 통과하면 약 4시간 40분이다. 접속 직후 잔여 GPU 시간을 실측해 기록한다.

서버 게이트 (go2_target_gate.py) — 2단계를 돌릴지만 정한다
판정 1항(험지·오르막·DR 9 case proxy 평균 +0.05 이상, 세 묶음 중 둘 이상 상승)을 로컬 검증기와 같은 함수로 읽는다.
- TARGET_PASS: 그 회차 2단계를 돈다.
- FAIL: 그 회차는 끝이다. 파국 게이트 정지·발산도 FAIL이다.
- REMEASURE_BASELINE: 표지 case가 저장 A017과 어긋났다. 그 회차 1단계를 A017 재측정으로 한 번 더 돌리고(+약 20분) 다시 판정한다. 통과하면 2단계도 A017을 재측정한다(+약 45분).
- UNDECIDED: 결측·계측 불일치다. 2단계를 돌리지 않고 로컬 검증으로 넘긴다.
게이트 결과는 GPU 일정만 정한다. 최종 판정은 결과를 받은 뒤 로컬 검증기가 한다.
한 회차가 실패(러너 오류)해도 다른 회차는 계속 돈다.

MONITOR
tmux attach -t {TMUX}
진행 기록: /workspace/_keep/{KEEP_NAME}/PAIR_LOG.txt ([ARM], [GATE], [RESULT] 줄)

첫 10분에 볼 것
학습 로그의 reward 표에 `feet_air_time` 가중치 {a['single_change']['to']}이 찍히는지 본다. 두 번째 회차 시작 때는 {b['single_change']['to']}.

재시작 규칙
중단되면 `GO2_RESUME=1 bash {PACKAGE_ROOT}/{RUNNER}`로 잇는다. 끝난 단계·case·영상은 건너뛴다.
기본 재실행은 이전 결과를 지우지 않고 거부한다. 버리려면 `GO2_DISCARD_PREVIOUS=1`.

DONE MARKER
{DONE_MARKER}

DOWNLOAD TO LOCAL workspace\\_keep (이것 하나)
/workspace/_keep/{RESULT_ZIP}
/workspace/_keep/{RESULT_ZIP}.sha256
안에 PAIR_STATUS.txt(회차별 STATE·GATE·STAGE·DECISION), gate/*.json, arm_results/(회차별 결과 ZIP)가 있다.
패키징이 실패하면 `_keep/{a['output']['keep_dir_name']}`, `_keep/{b['output']['keep_dir_name']}`, `_keep/{KEEP_NAME}`를 그대로 가져온다.

결과를 받은 뒤 (로컬, GPU 0)
회차별 결과 ZIP을 workspace\\_keep에 풀고 검증한다.
python -B tools/verify_go2_basic_motion_harvest.py G-A031 --harvest {keeps['G-A031']} --out {keeps['G-A031']}/harvest_verification.json
python -B tools/verify_go2_basic_motion_harvest.py G-A032 --harvest {keeps['G-A032']} --out {keeps['G-A032']}/harvest_verification.json
게이트 TARGET_PASS·FAIL과 로컬 1단계 판정이 다르면 로컬 판정을 따르고, 차이를 기록한다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.

RESULT INTERPRETATION — 실행 전에 고정 (계획서 §6, 사후 재협상 금지)
회차별 성공 조건은 계획서 §6-1과 각 회차 RUN GUIDE의 같은 절이다. 두 회차를 합친 방향 판정은 §6-3 표를 따른다.
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.
"""


def publish(zip_path: Path) -> None:
    digest = sha(zip_path.read_bytes())
    upload = GO2 / "upload" / UPLOAD_ID
    history, current = upload / "history" / RELEASE_ID, upload / "current"
    current.mkdir(parents=True, exist_ok=True)
    note = ("G-A031 + G-A032 in one upload: both arm ZIPs byte-identical, target stages first, a server gate on "
            "criterion 1, full stages only for passing arms, one result ZIP. exploratory.")
    manifest = {
        "experiment_id": PAIR_ID,
        "note": note,
        "published_at_utc": PUBLISHED_AT,
        "release_id": RELEASE_ID,
        "status": "ARTIFACT_VERIFIED",
        "support_files": [GUIDE],
        "upload_files": [{"name": UPLOAD_ZIP, "server_path": f"/workspace/{UPLOAD_ZIP}", "sha256": digest}],
    }
    current_text = (
        f"CURRENT GO2 UPLOAD — {PAIR_ID} (pair)\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{UPLOAD_ID}\\current\\{UPLOAD_ZIP}\n"
        f"   SHA256 {digest}\n\n"
        "G-A031·G-A032 두 회차를 한 파일·한 명령으로 이어서 돌린다. 1단계 두 개 → 서버 게이트 → 통과 회차만 2단계.\n"
        f"절차는 같은 폴더의 {GUIDE}. upload/G-A031·G-A032의 ZIP은 이 파일 안에 이미 들어 있으니 따로 올리지 않는다.\n"
        "서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {RELEASE_ID}\nSTATUS ARTIFACT_VERIFIED\n"
        "History is preserved under ../history and in ../UPLOAD_HISTORY.tsv.\n"
    )
    files = {
        GUIDE: run_guide(digest).encode("utf-8"),
        "UPLOAD_MANIFEST.json": (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "CURRENT_UPLOAD.txt": current_text.encode("utf-8"),
    }
    for name, data in files.items():
        target = history / name
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError(f"immutable release conflict: {target}")
        target.write_bytes(data)
    (history / f"{GUIDE}.sha256").write_text(f"{sha(files[GUIDE])}  {GUIDE}\n", encoding="utf-8", newline="\n")
    published = [zip_path, zip_path.with_suffix(".zip.sha256"), *(history / name for name in files),
                 history / f"{GUIDE}.sha256"]
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
    row = "\t".join([PUBLISHED_AT, PAIR_ID, RELEASE_ID, "ARTIFACT_VERIFIED", UPLOAD_ZIP, digest, note]) + "\n"
    existing = ledger.read_text(encoding="utf-8") if ledger.exists() else header
    if row not in existing:
        ledger.write_text(existing + row, encoding="utf-8", newline="\n")
    print(f"published current={current}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    path = build()
    digest = sha(path.read_bytes())
    print(f"built   {path}")
    print(f"size    {path.stat().st_size / 1_048_576:.1f} MB")
    print(f"sha256  {digest}")
    if args.publish:
        publish(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
