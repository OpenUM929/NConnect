# `go2_tuning_engine_v1_2` 로컬 검증 (260903)

- engine version: `1.1.0`
- engine ZIP: `workspace/training/quadruped/go2_tuning_engine_v1_2.zip`
- engine SHA-256: `9e79a9dff6a9f6a7636692df7780634f0d1ffe47372ef703e8c86c8fbdeb640e`
- size: 6,419,244 bytes / members 34
- canonical experiment: `workspace/training/quadruped/config/experiments/G_A013_flat_orientation_m1.json`
- colocated experiment: `workspace/training/quadruped/G_A013_flat_orientation_m1.json`
- experiment SHA-256: `2e255c1e18165f2be7e17f09893503262a1c846998d12f20cb7ddbd9273cecb2`
- canonical↔colocated JSON bytes: identical (SHA 대조)

## 검증 항목

| 항목 | 결과 |
|---|---|
| ZIP CRC / unsafe path | OK / 0 |
| 내부 manifest | 33/33 OK |
| 결정적 재빌드 | 동일 SHA (연속 빌드 3회) |
| runner CRLF | 0 |
| `bash -n server_run_go2_tuning_engine_v1.sh` | OK |
| 추출본에서 `go2_tuning_config.py validate` | `{"status":"VALID","work_id":"G-A013"}` |
| 추출본에서 `shell-env` | 20개 변수 전부 기대값 |
| 추출본에서 `materialize_runtime` | candidate `-1.0`, default `0.0` |
| 계약 테스트 | `tools/` 44/44 통과 |

## v1.1 대비 변경 (근거)

1. `flat_orientation_l2`를 조정 가능 reward 키로 승격 (default `0.0`).
   근거: G-A012 서버 `env.yaml` 실측에서 `undesired_contacts: null`,
   `termination_penalty` 항 부재. 계획이 지목했던 생존 레버 두 개가 실재하지 않는다.
2. `evaluation.gates.target_scenario`를 G1..G7 중 하나로 허용 (기존 G1 고정).
   근거: G-A010은 가중 총점 `+2.26/70`, G3 survival `+0.094`를 얻고도
   목표가 G1로 고정돼 있어 `target_G1_improvement_below_0.05` 하나로 조기 종료됐다.
3. archive 이름을 `v1_2`로 분리해 구버전 업로드 사고를 차단.
   engine_version 상수와 실험 JSON의 `engine_version`이 서로 다르면 validate 단계에서
   즉시 실패하므로, 버전 교차 업로드는 학습 시작 전에 소리 내어 죽는다.

## 증거 경계

로컬 `ARTIFACT_VERIFIED`까지다. G-A013의 checkpoint·telemetry·영상·내부 성능,
그리고 공식 결과는 서버 실행 전까지 전부 `[미측정]`이다.
`flat_orientation_l2 = -1.0`이 낙상을 줄인다는 것은 **가설**이며, 이 실행이 그것을 시험한다.
