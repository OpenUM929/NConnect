# `go2_feet_air_time_020_v1.zip` local verification

- work ID: `G-A007`
- package SHA-256: `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`
- package members: `21`
- deterministic rebuild: same SHA on two consecutive builds
- ZIP CRC: OK
- safe member paths: OK
- internal `PACKAGE_SHA256SUMS.txt`: 20/20 OK
- candidate reward diff: only `feet_air_time 0.01→0.20`
- frozen Default report: telemetry 69/69, model SHA `99ceeaa1…4676`, env SHA `4d1d294b…262c`
- Python compile: OK
- contract tests: 5/5 OK
- packaged runner CRLF: 0
- packaged runner Git Bash `bash -n`: OK
- campaign validator: `GO2_CAMPAIGN_CONTRACT_OK`

Reproduction:

```powershell
python tools/test_go2_feet_air_time_020_contract.py
python tools/build_go2_feet_air_time_020_package.py
& 'C:\Program Files\Git\bin\bash.exe' -n 'workspace/training/quadruped/server_run_go2_feet_air_time_020_v1.sh'
```

Server execution remains `[미측정]` until the user provides the runner output or the result ZIP is recovered.
