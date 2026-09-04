# Run06 로컬 수신·검증 기록

- 작업 ID: `A260831-03`
- RUN_ID: `train_260831-06_run05cfg_10000`
- 원본 격리: `original/`
- 검증 해제본: `extracted/train_260831-06_run05cfg_10000/`
- 서버 결과: `TRAIN_RC=0`, `MAX_ITERS=10000`, `[DONE] DOWNLOAD=` 확인
- 필수 bundle SHA256: `69a7b0dba8330f25fd4f30e01507f152c6d783b6bc7a512cef35f03b2c558267`
- 전체 snapshot SHA256: `04807530578d54403d1d09e25d2bf5dd934bde28dea50988b8841d1bc452735f`
- tar 검사: 필수 bundle PASS, 전체 snapshot PASS
- bundle 내부 checksum: `18/18 PASS`
- 설정: seed `42`, num_envs `4096`, max_iterations `10000`
- 최종 모델: `model_best.pt`와 `model_9900.pt` SHA256 일치
- 최종 환경: `final/env.yaml`과 `run/params/env.yaml` SHA256 일치
- 서버 종료 판정: **가능**

## 알려진 한계

- `ckpt/`가 비어 있어 3k·5k intermediate checkpoint는 회수되지 않았다.
- tfevents에는 전체 학습 곡선이 있으므로 3k·5k·10k 지표 구간 분석은 가능하지만, 3k·5k 정책 재생은 불가능하다.
- `policy.pt`는 이번 train bundle에 포함되지 않는 것이 스크립트 설계상 정상이다. 최종 후보 채택 후 별도 export와 tensor 동일성 검증이 필요하다.
- 서버 mirror의 `launcher.log`에는 tar 생성 뒤 출력된 다운로드 SHA와 `[DONE]` 두 줄이 추가되어 사전 생성된 내부 checksum과 다르다. tar 내부 `launcher.log`는 `SHA256SUMS.txt`와 일치하며 나머지 파일 포함 `18/18 PASS`이므로 전송 손상이 아니다.

## 병합 상태

아직 로컬 `workspace/training`에 병합하지 않았다. `MERGE_PLAN.tsv`의 `HOLD_ANALYSIS` 항목은 Run06 곡선 분석과 승급 판정 후에만 전진한다.