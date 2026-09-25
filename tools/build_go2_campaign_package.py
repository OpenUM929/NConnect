"""Build (and optionally publish) a one-file campaign package: one upload, one command, one result.

Successor of tools/build_go2_basic_motion_pair.py (G-A031 + G-A032, run 2026-09-15, kept as
released).  A campaign is one or more staged candidate arms; the campaign ZIP carries:
  arms/                        each arm ZIP, byte for byte as tools/build_go2_candidate_package.py builds it
  server_run_go2_campaign.sh   runs every target stage, gates, then the full stages
  go2_target_gate.py           criterion 1 on the server (with its two stdlib dependencies)
  stored_baseline/             the stored A017 (G-A027) summaries the gate reads, verified here
                               in full against their raw steps.csv before they are packed
The runner reads the gate verdict from the gate's JSON: on the server the gate ran through
isaaclab.sh -p, which did not pass python's exit code through (plan section 9-2).

    python tools/build_go2_campaign_package.py G-A033            # build and verify
    python tools/build_go2_campaign_package.py G-A033 --publish  # also publish upload/G-A033/current
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

import build_go2_basic_motion_pair as pair  # noqa: E402
import build_go2_candidate_package as pkg  # noqa: E402

RUNNER = "server_run_go2_campaign.sh"
GATE_FILES = pair.GATE_FILES
FIXED_TIMESTAMP = pkg.FIXED_TIMESTAMP
PUBLISHED_AT = pkg.PUBLISHED_AT
CAMPAIGNS = {
    "G-A033": {
        "arms": ("G-A033",),
        "upload_id": "G-A033",
        "release_id": "20260915_track_lin_vel_xy_150_iter900_one_command_v2",
        "prefix": "go2_campaign_g_a033",
        "upload_zip": "GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip",
        "tmux": "go2_campaign_g_a033",
        "keep_name": "go2_campaign_g_a033",
        "result_zip": "GO2_G_A033_CAMPAIGN_RESULT.zip",
        "done_marker": "[DONE] GO2_G_A033_CAMPAIGN_RESULT_READY",
        "guide": "GO2_G_A033_ONE_COMMAND_RUN_GUIDE.txt",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# A campaign that was already published keeps the runner bytes it shipped, so its published ZIP
# still rebuilds after the runner is fixed (defect C-2's shape; the arm runners do the same
# through tools/build_go2_candidate_package.py EXECUTED_RUNNERS).  Pinned 2026-09-24 when
# C-27/C-28 changed full_complete.  "Published", not "executed": G-A033/G-A038/G-A041/G-A042/
# G-A043 ran on the server, G-A035/G-A037/G-A039 did not (C-2), but all eight shipped a ZIP
# whose bytes are frozen, and every one of those ZIPs carries this same copy (verified by
# reading the runner out of each current/ ZIP, 2026-09-24).
RUNNER_HISTORY = GO2 / "runner_history"
RAN_2026_09_15 = "server_run_go2_campaign.e185b75752ef3da8.sh"
PUBLISHED_RUNNERS = {
    "G-A033": RAN_2026_09_15,
    "G-A035": RAN_2026_09_15,
    "G-A037": RAN_2026_09_15,
    "G-A038": RAN_2026_09_15,
    "G-A039": RAN_2026_09_15,
    "G-A041": RAN_2026_09_15,
    "G-A042": RAN_2026_09_15,
    "G-A043": RAN_2026_09_15,
}


def runner_bytes(campaign_id: str) -> bytes:
    """The copy a published campaign shipped, the working tree for one not yet published."""
    name = PUBLISHED_RUNNERS.get(campaign_id)
    if name is None:
        runner = (GO2 / RUNNER).read_bytes()
    else:
        path = RUNNER_HISTORY / name
        runner = path.read_bytes()
        if path.name.rsplit(".", 2)[1] != sha(runner)[:16]:
            raise RuntimeError(f"{path.name} is not the executed runner it names")
    if b"\r" in runner:
        raise RuntimeError("campaign runner has CR bytes")
    return runner


def load_specs(campaign: dict) -> list[dict]:
    return [pkg.load(work) for work in campaign["arms"]]


def package_root(campaign: dict) -> str:
    return "/workspace/" + campaign["prefix"]


def output_path(campaign: dict) -> Path:
    return GO2 / "upload" / campaign["upload_id"] / "history" / campaign["release_id"] / campaign["upload_zip"]


def validate(campaign: dict, specs: list[dict]) -> None:
    def need(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError(f"campaign {'+'.join(campaign['arms'])}: {message}")

    need(len(specs) >= 1 and len({spec["work_id"] for spec in specs}) == len(specs), "arms must be distinct")
    for spec in specs:
        pkg.validate_spec(spec)
    # One stored arm serves every gate, so every arm must read the same cases the same way.
    for spec in specs[1:]:
        for key in ("runner", "baseline", "evaluation", "preregistered", "stages", "videos", "training"):
            need(spec[key] == specs[0][key], f"{key} must be identical across the arms")
    for key in ("package_root", "keep_dir_name", "result_zip", "tmux_name", "upload_zip", "done_marker"):
        values = [spec["output"][key] for spec in specs]
        need(len(set(values)) == len(values), f"output.{key} must differ between the arms")
    need(package_root(campaign) not in [spec["output"]["package_root"] for spec in specs],
         "the campaign folder must not be an arm folder")
    need(campaign["tmux"] not in [spec["output"]["tmux_name"] for spec in specs], "campaign tmux must not be an arm's")
    need(campaign["keep_name"] not in [spec["output"]["keep_dir_name"] for spec in specs],
         "campaign keep folder must not be an arm's")
    need(campaign["result_zip"] not in [spec["output"]["result_zip"] for spec in specs],
         "campaign result ZIP must not be an arm's")


def campaign_config(campaign: dict, specs: list[dict], zips: dict[str, bytes]) -> str:
    names = [spec["output"]["upload_zip"] for spec in specs]

    def array(values: list[str]) -> str:
        return "(" + " ".join(shlex.quote(value) for value in values) + ")"

    return "".join([
        "# generated by tools/build_go2_campaign_package.py; do not edit\n",
        f"CAMPAIGN_ID={shlex.quote('+'.join(campaign['arms']))}\n",
        f"CAMPAIGN_RELEASE_ID={campaign['release_id']}\n",
        f"CAMPAIGN_TMUX={campaign['tmux']}\n",
        f"CAMPAIGN_KEEP_NAME={campaign['keep_name']}\n",
        f"CAMPAIGN_RESULT_ZIP={campaign['result_zip']}\n",
        f"CAMPAIGN_DONE_MARKER={shlex.quote(campaign['done_marker'])}\n",
        f"ARM_RUNNER={specs[0]['runner']}\n",
        f"ARM_WORK={array([spec['work_id'] for spec in specs])}\n",
        f"ARM_ZIP={array(names)}\n",
        f"ARM_ZIP_SHA={array([sha(zips[name]) for name in names])}\n",
        f"ARM_ROOT={array([spec['output']['package_root'] for spec in specs])}\n",
    ])


def readme(campaign: dict, specs: list[dict], zips: dict[str, bytes]) -> str:
    arms = "\n".join(
        f"  {spec['work_id']}  {spec['single_change']['name']} {spec['single_change']['from']} -> "
        f"{spec['single_change']['to']}   arms/{spec['output']['upload_zip']}  sha256 {sha(zips[spec['output']['upload_zip']])}"
        for spec in specs)
    root = package_root(campaign)
    title = f"GO2 {' + '.join(campaign['arms'])} CAMPAIGN — one upload, one command, one result"
    iters = sorted({str(spec["evaluation"].get("checkpoint_iter")) for spec in specs})
    pin = (f"\nCHECKPOINT\n  Each candidate is evaluated at the iter-{'/'.join(iters)} checkpoint, the iteration A017 was\n"
           f"  evaluated at, not at train.py finalize's reward pick ({specs[0]['runner']}).\n"
           if specs[0]["runner"] == pkg.PINNED_RUNNER else "")
    return f"""{title}
{'=' * len(title)}

This package TRAINS {len(specs)} polic{'y' if len(specs) == 1 else 'ies, one after the other on one GPU,'} and measures
{'it' if len(specs) == 1 else 'them'}.  status: exploratory.  Plan: {Path(specs[0]['plan']).name}.

ARMS (byte for byte what tools/build_go2_candidate_package.py builds)
{arms}

RUN
  unzip -oq {campaign['upload_zip']} -d /workspace
  bash {root}/{RUNNER}
  Resume after an interruption: GO2_RESUME=1 bash {root}/{RUNNER}

WHAT HAPPENS
  1 the target stage of each arm (~1h25m each): training, catastrophe gate, the
    9 target cases, the sentinel, the videos.
  2 after each target stage, go2_target_gate.py reads criterion 1 (plan 6-1); the
    runner takes the verdict from the gate's JSON:
      TARGET_PASS -> full stage (~55m); FAIL -> the arm ends;
      REMEASURE_BASELINE -> target stage again with A017 remeasured, gate again;
      UNDECIDED -> no full stage.
  3 full stage of each arm the gate passed.
  4 one result ZIP.  The gate only schedules GPU time; the local verifier
    (tools/verify_go2_basic_motion_harvest.py) decides every verdict.
{pin}
DOWNLOAD
  /workspace/_keep/{campaign['result_zip']}
  /workspace/_keep/{campaign['result_zip']}.sha256
  Finish marker: {campaign['done_marker']}
  Official results remain OFFICIAL_RESULT_UNMEASURED.
"""


def build_payload(campaign_id: str) -> dict[str, bytes]:
    campaign = CAMPAIGNS[campaign_id]
    specs = load_specs(campaign)
    validate(campaign, specs)
    runner = runner_bytes(campaign_id)
    zips = pair.arm_zips(specs)
    payload: dict[str, bytes] = {RUNNER: runner}
    payload.update(pair.gate_payload(executed=True))   # G-A033 is the only campaign here, and it ran
    payload.update(pair.stored_payload(specs[0]))
    for name, data in zips.items():
        payload[f"arms/{name}"] = data
    payload["campaign_config.env"] = campaign_config(campaign, specs, zips).encode("utf-8")
    payload["README.txt"] = readme(campaign, specs, zips).encode("utf-8")
    checksums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(payload.items()))
    payload["CAMPAIGN_SHA256SUMS.txt"] = checksums.encode("utf-8")
    return payload


def build(campaign_id: str) -> Path:
    campaign = CAMPAIGNS[campaign_id]
    payload = build_payload(campaign_id)
    output = output_path(campaign)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(f"{campaign['prefix']}/{name}", date_time=FIXED_TIMESTAMP)
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


def run_guide(campaign_id: str, digest: str) -> str:
    campaign = CAMPAIGNS[campaign_id]
    specs = load_specs(campaign)
    root = package_root(campaign)
    upload_zip = campaign["upload_zip"]
    n = len(specs)
    target_minutes, full_minutes = 85 * n, 55 * n
    arms = "\n".join(f"- {spec['work_id']}: A017 + `{spec['single_change']['name']}` "
                     f"{spec['single_change']['from']}→{spec['single_change']['to']}" for spec in specs)
    verify = "\n".join(
        f"python -B tools/verify_go2_basic_motion_harvest.py {spec['work_id']} "
        f"--harvest workspace/_keep/{spec['output']['keep_dir_name']} "
        f"--out workspace/_keep/{spec['output']['keep_dir_name']}/harvest_verification.json" for spec in specs)
    keeps = ", ".join(f"`_keep/{spec['output']['keep_dir_name']}`" for spec in specs)
    first = specs[0]
    videos = ", ".join(entry.split(":")[1] for entry in first["videos"]["candidate"])
    order = " → ".join(f"{spec['work_id']} 1단계 → 서버 게이트" for spec in specs)
    pin_note = ("\n체크포인트 고정: 후보는 A017이 평가된 학습 시점(iter "
                f"{first['evaluation'].get('checkpoint_iter')})의 체크포인트로 평가한다. 학습 중 러너가 그 파일을 복사해 둔다.\n"
                "train.py finalize가 고른 reward 최고 시점 모델은 결과의 training/model_best_by_reward.pt에 따로 남고, "
                "둘의 iter·SHA는 training/CHECKPOINT_PIN.txt에 기록된다.\n"
                "학습 중 복사를 못 하면 러너가 평가 전에 멈춘다([FAIL] checkpoint model_900.pt was not captured).\n"
                if first["runner"] == pkg.PINNED_RUNNER else "")
    return f"""GO2 {' + '.join(campaign['arms'])} ONE-COMMAND RUN GUIDE (파일 하나, 명령 하나, 결과 하나)

{arms}
계획서: {first['plan']}
서버 실행은 사용자 결정 사항이다. 이 문서는 실행 절차이지 실행 승인이 아니다.
{pin_note}

LOCAL FILE TO UPLOAD (이것 하나만)
1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{campaign['upload_id']}\\current\\{upload_zip}
   SHA256 {digest}
안에 회차 ZIP이 빌더 출력과 바이트 동일하게 들어 있다. 회차 ZIP을 따로 올리지 않는다.

SERVER DESTINATION
/workspace/{upload_zip}

ONE-LINE RUN (tmux 안에서 시작하고 즉시 리턴)
cd /workspace && echo '{digest}  {upload_zip}' | sha256sum -c - && unzip -oq {upload_zip} && bash {root}/{RUNNER}

시작 전 러너가 하는 일
회차 ZIP의 SHA 확인 → /workspace 아래로 풀기 → 회차별 preflight(평가기·registry·A017 SHA) → 학습·play 프로세스, tmux 세션, 이전 결과가 있으면 거부.

순서와 시간 (한 GPU에서 차례로. 동시에 돌리지 않는다)
1. {order}. 1단계는 학습 1,000 iter, 파국 게이트, 표적 9 case, A017 표지 5 case, 영상 {len(first['videos']['candidate'])}개({videos})다. 회차당 약 1시간 25분.
2. 게이트가 통과시킨 회차만 2단계(나머지 59 case)를 돈다. 회차당 약 55분.
3. 결과 ZIP 하나로 묶는다.
1단계에서 끝나면 약 {target_minutes // 60}시간 {target_minutes % 60}분, 모두 통과하면 약 {(target_minutes + full_minutes) // 60}시간 {(target_minutes + full_minutes) % 60}분이다. 접속 직후 잔여 GPU 시간을 실측해 기록한다.

서버 게이트 (go2_target_gate.py) — 2단계를 돌릴지만 정한다
판정 1항(험지·오르막·DR 9 case proxy 평균 +0.05 이상, 세 묶음 중 둘 이상 상승)을 로컬 검증기와 같은 함수로 읽는다.
러너는 판정을 게이트 JSON의 verdict에서 읽는다. G-A031·A032 실행에서 `isaaclab.sh -p`가 종료 코드를 바꿔 FAIL이 UNDECIDED로 기록된 결함을 고친 것이다(계획 §9-2).
- TARGET_PASS: 그 회차 2단계를 돈다.
- FAIL: 그 회차는 끝이다. 파국 게이트 정지·발산도 FAIL이다.
- REMEASURE_BASELINE: 표지 case가 저장 A017과 어긋났다. 그 회차 1단계를 A017 재측정으로 한 번 더 돌리고(+약 20분) 다시 판정한다. 통과하면 2단계도 A017을 재측정한다(+약 45분).
- UNDECIDED: 결측·계측 불일치다. 2단계를 돌리지 않고 로컬 검증으로 넘긴다.
게이트 결과는 GPU 일정만 정한다. 최종 판정은 결과를 받은 뒤 로컬 검증기가 한다.

MONITOR
tmux attach -t {campaign['tmux']}
진행 기록: /workspace/_keep/{campaign['keep_name']}/CAMPAIGN_LOG.txt ([ARM], [GATE], [GATE READ], [RESULT] 줄)

첫 10분에 볼 것
학습 로그의 reward 표에 `{first['single_change']['name']}` 가중치 {first['single_change']['to']}이 찍히는지 본다.

재시작 규칙
중단되면 `GO2_RESUME=1 bash {root}/{RUNNER}`로 잇는다. 끝난 단계·case·영상은 건너뛴다.
기본 재실행은 이전 결과를 지우지 않고 거부한다. 버리려면 `GO2_DISCARD_PREVIOUS=1`.

DONE MARKER
{campaign['done_marker']}

DOWNLOAD TO LOCAL workspace\\_keep (이것 하나)
/workspace/_keep/{campaign['result_zip']}
/workspace/_keep/{campaign['result_zip']}.sha256
안에 CAMPAIGN_STATUS.txt(회차별 STATE·GATE·STAGE·DECISION), gate/*.json, arm_results/(회차별 결과 ZIP)가 있다.
패키징이 실패하면 {keeps}, `_keep/{campaign['keep_name']}`를 그대로 가져온다.

결과를 받은 뒤 (로컬, GPU 0)
회차별 결과 ZIP을 workspace\\_keep에 풀고 검증한다.
{verify}
게이트 판정과 로컬 1단계 판정이 다르면 로컬 판정을 따르고, 차이를 기록한다.

SERVER SHUTDOWN GATE
DONE 표시만으로 종료하지 않는다. 결과를 받아 로컬 검증을 통과해야 종료 판단을 보고한다.

RESULT INTERPRETATION — 실행 전에 고정 (사후 재협상 금지)
성공 조건은 {first['preregistered']['source']}이다(기준값 불변). 사전등록한 위험은 계획서 §10 표를 따른다.
공식 evaluator·공식 점수는 OFFICIAL_RESULT_UNMEASURED다.
"""


def publish(campaign_id: str, zip_path: Path) -> None:
    campaign = CAMPAIGNS[campaign_id]
    specs = load_specs(campaign)
    digest = sha(zip_path.read_bytes())
    upload = GO2 / "upload" / campaign["upload_id"]
    history, current = upload / "history" / campaign["release_id"], upload / "current"
    current.mkdir(parents=True, exist_ok=True)
    guide = campaign["guide"]
    changes = "; ".join(f"{spec['work_id']} A017 + {spec['single_change']['name']} "
                        f"{spec['single_change']['from']}->{spec['single_change']['to']}" for spec in specs)
    note = (f"{changes}. One upload: arm ZIPs byte-identical to their builder, target stages first, a server gate on "
            "criterion 1 read from its JSON, full stages only for passing arms, one result ZIP. exploratory.")
    campaign_name = "+".join(campaign["arms"])
    manifest = {
        "experiment_id": campaign_name,
        "note": note,
        "published_at_utc": PUBLISHED_AT,
        "release_id": campaign["release_id"],
        "status": "ARTIFACT_VERIFIED",
        "support_files": [guide],
        "upload_files": [{"name": campaign["upload_zip"], "server_path": f"/workspace/{campaign['upload_zip']}",
                          "sha256": digest}],
    }
    current_text = (
        f"CURRENT GO2 UPLOAD — {campaign_name} (one command)\n\n"
        "UPLOAD ONLY THIS ONE FILE\n"
        f"1. C:\\dev\\NConnect\\workspace\\training\\quadruped\\upload\\{campaign['upload_id']}\\current\\{campaign['upload_zip']}\n"
        f"   SHA256 {digest}\n\n"
        "한 파일·한 명령으로 1단계 → 서버 게이트 → 통과 회차만 2단계 → 결과 ZIP 하나.\n"
        f"절차는 같은 폴더의 {guide}. 회차 ZIP은 이 파일 안에 이미 들어 있다.\n"
        "서버 실행은 사용자 결정 사항이다.\n\n"
        f"RELEASE_ID {campaign['release_id']}\nSTATUS ARTIFACT_VERIFIED\n"
        "History is preserved under ../history and in ../UPLOAD_HISTORY.tsv.\n"
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
    row = "\t".join([PUBLISHED_AT, campaign_name, campaign["release_id"], "ARTIFACT_VERIFIED",
                     campaign["upload_zip"], digest, note]) + "\n"
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
