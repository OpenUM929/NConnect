# Run06 seed-42 전체 평가 회수 검증

- 원본 tar: `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz`
- 외부 SHA-256: `4e552b2caea4f9a33475bf7a93bc35a383c9aa9b79a42e308b002c01674b860f`
- 외부 `.sha256`: 일치
- 안전하지 않은 tar 경로: 0
- 내부 manifest: 69/69 일치
- `RUNNER_RC`: 0
- case `STATUS.txt`: 10/10, 모두 `EVAL_RC=0`
- model SHA-256: `8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636`
- H1~H7 누락: 없음
- 계측 상태: `CALIBRATION_PASS`
- 후속 독립 평가: `INDEPENDENT_VALIDATION_PASS` — seed 101·202·303, 30/30 case 정상 종료,
  H1~H7 전부 내부 gate 통과, 최악 seed 기준 65.73/70

이 문서 자체는 seed-42 다운로드와 실행 완전성을 증명한다. 독립 seed 성능의 원문 근거는
`INDEPENDENT_EVAL_REPORT.md`와 `.json`이며, 어느 문서도 운영진 공식 점수를 증명하지 않는다.
