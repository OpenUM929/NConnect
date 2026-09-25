# Go2 server upload staging

This directory is the only user-facing source for files uploaded to a volatile server.

## Layout

- `plan/`: planning documents only; never place ZIP packages, SHA sidecars, deployment manifests or executable files here.
- `<EXPERIMENT_ID>/review/`: numbered review-only bundles and SHA sidecars; not approved server execution releases. Never publish an unnumbered bundle directly under `upload/`.
- Package filenames include the campaign ID (for example `GO2_G_A028_...zip`). Check the ledgers for collisions before reserving the next ID; a reservation does not authorize execution. Follow G-D98, G-D175 and G-D178.
- `<EXPERIMENT_ID>/current/`: upload files for the active release. Upload only the files named in `CURRENT_UPLOAD.txt`.
- `<EXPERIMENT_ID>/history/<RELEASE_ID>/`: immutable release snapshot for audit and rollback.
- `<EXPERIMENT_ID>/UPLOAD_HISTORY.tsv`: append-only release ledger with SHA-256 values and status.

## Current experiment

- Current baseline, latest execution and next decision: root `GO2_NOW.md` (single current-state entry point).
- A directory under `current/` preserves a published package; it does not by itself mean it is the next approved server run.
- 2026-09-19: local judgment-validator repair and tuning-strategy review only; no new execution package issued in this review.
- 2026-09-22 (latest): `G-A044/current/` holds the newest issued package (`lin_vel_z_l2 -2.0 -> -1.75` on G-A033, release `..._full69_v9`; v9 fixes what the guide said about the failure paths (defect C-24, third user review): [DONE] does not always appear - the runner's on_exit crash path leaves a partial ZIP and COLLECTION_STATUS=INCOMPLETE_CRASH without printing the marker, so a reader waiting for it burns the volatile server's budget waiting for a line that never comes; and 'fill it in, then shut down' is right only for a recoverable gap - a run the catastrophe gate stopped is a run whose policy did not execute, and forcing 69 cases there contradicts the runner's own STOP_UNSAFE contract. Section 4 now separates three states (complete / recoverable gap / crash or unsafe-to-evaluate), section 5a and the shutdown sentence follow that split, and the guide says FULL_69_COMPLETE is a count, not a substitute for the SHA, fingerprint, identity and report checks. Gate test_22 runs the published runner's crash path and shows the marker is absent. Runner bytes are identical to v8. The same edition closed defect C-23 by fixing only the gate: the old `pinned = staged + pin blocks` equality had been red since C-14 and was hiding the next regression; the runners were not touched and the v8 ZIP rebuilds to the same SHA. v8 closes two more defects a second user review found: the spec shipped inside the ZIP still named the `--keep` flag the CLI does not have (C-21 - C-15 had been fixed in the guide only, and the spec travels to the server inside the package), and a run stopped by the catastrophe gate reported itself like a full harvest (C-22 - `finish` printed the same done marker and RESULT_STATE=FULL on both paths). The runner now counts what is on disk and writes a separate COLLECTION_STATUS, prints [INCOMPLETE COLLECTION] when something is missing, and the shutdown gate requires COLLECTION_STATUS=FULL_69_COMPLETE. Runner bytes changed; thresholds did not. v7 rewrites the shutdown gate's exit-code paragraph (defect C-20, found by user review): the old line said exit 1 from both readers meant a performance miss, but the first reader exits 0 on a performance FAIL and its exit 1 means the judgement could not be made (INCONCLUSIVE / BASELINE_REMEASURE_REQUIRED), while the second puts FAIL and INCONCLUSIVE behind the same exit 1 - read the old way, a recovery gap gets taken for bad performance and the volatile server is powered off, losing the videos and the report. Gate `test_20` runs both readers on an empty harvest and reads the non-pass verdict names out of the reader's own source. Thresholds, runner and rewards are byte-identical to v6. v6 closed three record gaps a plan-versus-spec comparison found - the guide now carries the plan's 120-150 minute session budget (the 110 minutes is server runtime, recovery comes after), the spec pins the comparison arm G-A043's model and env SHA read from the recovered artifact, and section 9-1's c3 cap is written as a number. No threshold moved: all 19 pre-registered numbers still equal G-A043's. the uploaded ZIP now carries its edition in the file name (defect C-18, user's point: four same-named ZIPs sat in history and one of them runs nothing, so picking the right one rested on a hand-compared SHA). v5's payload differs from v4 in two lines of `experiment.json`; v4 fixes three defects a user review surfaced — the runner re-entered a file the package does not ship (C-14), the recovery command named a flag the CLI does not have (C-15), and the shutdown section read as if a matching SHA were enough to power the server off (C-16)). It is NOT a campaign bundle: this round runs the whole 69-case evaluation in one pass with no target stage and no server gate, so the arm ZIP itself is the unit of execution (`run_config.env` pins `GO2_STAGE=full`). Builder `tools/build_go2_full_collection_release.py`. Every criterion this package does not take as given is listed, with its authority, in `../reports/GO2_G_A044_CRITERIA_CHANGES_20260922.md`. Server execution is a user decision and had not happened when the package was issued.
- 2026-09-22: `G-A043/current/` holds the previous issued package (`lin_vel_z_l2 -2.0 -> -1.5` on G-A033, release `..._one_command_v2`). Every criterion this package does not take as given is listed, with its authority, in `../reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md`. Server execution is a user decision and had not happened when the package was issued.

## Historical staging note (not the current execution instruction)

- `G-A010/current/`
- Active engine: `go2_tuning_engine_v1_1.zip`
- Active spec: `G_A010_lin_vel_z_m2.json`
- The older engine v1.0 is `BUGGY_DO_NOT_REUSE` and is not placed in `current/`.

## Publishing the next release

Use `tools/publish_go2_upload_bundle.py`. It verifies every copy by SHA-256, updates `current/`, creates a release snapshot, and appends the ledger without duplicating an existing release identity.

### G-A045_A046 — 학습 seed 43 대칭 쌍 (2026-09-24)
- 실행 정본: `G-A045_A046/current/GO2_G_A045_A046_seed43_pair_full69_v8.zip` SHA `02c1b36c59e9a5c499b43c46776d69bce7e4d74f63c740ca8719e75d9c3df151`
- 팔 ZIP 둘은 쌍 ZIP 안 `arms/` 에 들어 있다. **따로 올리지 않는다.**
- 러너 `server_run_go2_full69_campaign.sh`(게이트 없음, 팔마다 전수 69). 결과 `_keep/GO2_SEED_PAIR_RESULT.zip`.
- **두 팔 다 승급 대상이 아니다**(학습 seed 회차 · 열린 결정 U2-SEED-REPLICATE-20260918). 기준선은 G-A033 그대로.
