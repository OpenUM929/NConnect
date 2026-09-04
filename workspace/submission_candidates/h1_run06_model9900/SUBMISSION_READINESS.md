# Run06 제출 준비 상태

## 판정 계층

- 제출 파일 정합성: `ARTIFACT_VERIFIED`
- 기존 영상: H1·H2·H3·H5 `VIDEO_OBSERVED`, H4·H6·H7 `VIDEO_UNKNOWN`
- seed 42 전체 계측: `CALIBRATION_PASS`
- 독립 seed 평가: `INDEPENDENT_VALIDATION_PASS`
- 공식 운영진 결과: `OFFICIAL_RESULT_UNMEASURED`

따라서 **Run06 후보는 내부 제출 게이트를 통과했고 제출 3종이 준비됐다.** 다만
`INDEPENDENT_VALIDATION_PASS`를 예선 합격이나 운영진 공식 점수로 표현하지 않는다.

## 제출 파일 3종

| 제출물 | 파일 | 검증 |
|---|---|---|
| 정책 | `policy.pt` | Run06 iter 9900 actor tensor 8/8 일치; SHA-256 `7c3ae684…24a` |
| 환경 | `env.yaml` | Run06 학습 환경 원본; SHA-256 `506a54aa…99d` |
| 기술 개선 리포트 | `TECHNICAL_REPORT.md` | reward·run·평가 한계를 후보와 대조 |

정책 식별자는 `iter=9900`과 checkpoint SHA-256
`8eb06e2b0f590077fe3d20557da3f77d5c7dc34a0507edfa3e4af8df8ff4b636`이다.

## 현재 자체점수 — 교정용 결과

- seed 42, 32 environments, H1~H7 10개 case, 각 1,000 step
- 조기 종료: 0/320 environment-episodes
- 내부 simulation proxy: **66.04/70**
- 문서 자체감사: **27/30**
- 합계 산술값: **93.04/100**

이 값은 다음 이유로 **신뢰도 보정 전 점수**다.

1. 학습과 평가가 모두 seed 42에 묶여 있었다.
2. 평가 명령과 지형이 학습 분포 안에 있다.
3. tracking 변환식 `exp(-(RMSE/0.5)^2)`과 임계값은 운영진 공식식이 아니다.
4. 임계값은 부분 H4·H6·H7 결과를 본 뒤 고정해 seed 42에는 독립적이지 않다.
5. 하나의 checkpoint와 한 seed는 일반화를 입증하지 않는다.

## 독립 검증 완료

- 동결 정책·proxy·threshold로 seed **101·202·303** 평가
- H1~H7 10개 case/seed, 총 30개 case 정상 종료
- 누락 seed 0, 실패 seed 0, 실패 시나리오 0
- 모든 시나리오 최악 survival: 1.0000
- 내부 simulation proxy: **65.73/70**
- 판정: `INDEPENDENT_VALIDATION_PASS`

독립 평가 원문은 `INDEPENDENT_EVAL_REPORT.md`와 `INDEPENDENT_EVAL_REPORT.json`에 보존한다.

## 남은 외부 게이트

팀 대시보드에 `policy.pt`, `env.yaml`, 기술 개선 리포트를 실제 업로드하고 제출 완료 화면을
회수해야 단계 6/6으로 전환할 수 있다. 현재 실제 업로드 여부는 `[미측정]`이다.
