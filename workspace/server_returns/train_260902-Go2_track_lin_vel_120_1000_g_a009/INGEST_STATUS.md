# G-A009 ingest status

- lifecycle: `RECEIVED → VERIFIED → MERGED → ANALYZED → REPORTED`
- outer ZIP SHA-256: `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`
- companion SHA: `MATCH`
- package verification: `PASS`
- result: `FULL`, runner `0`, training `0`
- decision recorded by runner: `INTERNAL_EARLY_KILL_FAIL`
- telemetry: candidate 7/7, baseline 7/7
- video: 1/1, 직접 판독 완료(G1 `VIDEO_OBSERVED`; G2~G7 `VIDEO_UNKNOWN`)
- policy lineage: `ACTOR_TENSORS_MATCH` (8/8)
- model identifier: `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`
- merge: 원본 ZIP은 격리 보존; G1 영상만 evidence 폴더로 SHA 일치 선택 복사, 분석 CSV·JSON·contact sheet 생성
- report: `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`
