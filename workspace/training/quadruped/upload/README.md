# Go2 server upload staging

This directory is the only user-facing source for files uploaded to a volatile server.

## Layout

- `<EXPERIMENT_ID>/current/`: upload files for the active release. Upload only the files named in `CURRENT_UPLOAD.txt`.
- `<EXPERIMENT_ID>/history/<RELEASE_ID>/`: immutable release snapshot for audit and rollback.
- `<EXPERIMENT_ID>/UPLOAD_HISTORY.tsv`: append-only release ledger with SHA-256 values and status.

## Current experiment

- `G-A010/current/`
- Active engine: `go2_tuning_engine_v1_1.zip`
- Active spec: `G_A010_lin_vel_z_m2.json`
- The older engine v1.0 is `BUGGY_DO_NOT_REUSE` and is not placed in `current/`.

## Publishing the next release

Use `tools/publish_go2_upload_bundle.py`. It verifies every copy by SHA-256, updates `current/`, creates a release snapshot, and appends the ledger without duplicating an existing release identity.
