# `_keep` download inbox

`workspace/_keep` is the local landing area that mirrors server `/workspace/_keep` downloads. It is not the canonical long-term artifact store.

## Required flow

1. Download the server result and its `.sha256` companion into this directory.
2. Register the download in root `ARTIFACT_MANAGEMENT.md`.
3. Map the server path, inbox path, isolated path, size, checksum, lifecycle, and next action in `workspace/server_returns/DOWNLOAD_MAP.tsv`.
4. Move the received original into `workspace/server_returns/<RUN_ID>/original/`.
5. Create `STATUS.txt`, `FILE_MANIFEST.tsv`, `LOCAL_SHA256SUMS.txt`, `MERGE_PLAN.tsv`, `MERGE_RESULT.tsv`, and `INGEST_STATUS.md` before selective merge.
6. Never overwrite `workspace/training` with this inbox.

## Current Go2 mapping

- The downloaded partial directory was isolated under `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/` as work `G-A006`.
- The 0-byte SHA companion was preserved with suffix `.empty`; it is not valid integrity evidence.
- The required complete ZIP and valid SHA companion remain `MISSING_REQUIRED` in `DOWNLOAD_MAP.tsv`.
