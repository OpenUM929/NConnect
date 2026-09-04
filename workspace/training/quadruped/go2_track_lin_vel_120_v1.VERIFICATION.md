# G-A009 package verification — 2026-09-02

- package: `C:\dev\Nconnect\workspace\training\quadruped\go2_track_lin_vel_120_v1.zip`
- size: `6,467,257 bytes`
- SHA-256: `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`
- deterministic rebuild: identical SHA twice
- ZIP: 46 members, CRC OK, unsafe path 0
- internal manifest: 45/45 match
- reward diff: `track_lin_vel_xy_exp 1.0→1.2` only; four control rewards unchanged
- baseline identity: Default-01 model `99ceeaa1…4676`, env `4d1d294b…262c`, source result ZIP SHA `af41ccc5…2b25`
- G5 repair: verified Default seed-101 `stairs_15_up` summary rebuilt from per-env body-frame velocity integration
- G7 repair: evaluation-only `NCRC_EVAL_DR=1`; G3 and G7 use distinct runner mode/fingerprint
- cost gate: 7 candidate + 1 Default DR case; failure packages immediately; only pass adds 14 candidate cases for 21 total
- video: candidate G1 forward-fast, seed 101, 4 env, 500 step, 1 file
- Python: compile OK
- tests: `tools.test_go2_evaluator_v2_contract` + `tools.test_go2_track_lin_vel_120_contract`, 9/9 OK
- runner: Git Bash `bash -n` OK, CRLF 0
- official status: `OFFICIAL_RESULT_UNMEASURED`
