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

- `G-A028/current/`: `GO2_G_A028_P1.zip`, P1 frozen-policy fall diagnosis, no training. Read `GO2_G_A028_RUN_GUIDE.txt`; locally tested, IsaacLab runtime unmeasured.

## Historical staging note (not the current execution instruction)

- `G-A010/current/`
- Active engine: `go2_tuning_engine_v1_1.zip`
- Active spec: `G_A010_lin_vel_z_m2.json`
- The older engine v1.0 is `BUGGY_DO_NOT_REUSE` and is not placed in `current/`.

## Publishing the next release

Use `tools/publish_go2_upload_bundle.py`. It verifies every copy by SHA-256, updates `current/`, creates a release snapshot, and appends the ledger without duplicating an existing release identity.
