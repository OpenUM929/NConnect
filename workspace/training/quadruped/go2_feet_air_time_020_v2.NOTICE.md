# go2_feet_air_time_020_v2 — 손상 구간 주의 (ZIP 바깥 고지)

**대상**: `go2_feet_air_time_020_v2.zip` 안의
`go2_feet_air_time_020_v1/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` **§9 PARTIAL** 절.

> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).**
> 원문을 복원·삭제하지 않는다. 확인한 정상 기록: `go2_feet_air_time_020_v2.VERIFICATION.md`
> (v2 원인·수정·패키지 SHA·검증, 정상 영문). PARTIAL 결과 수치는
> `GO2_REWARD_EVIDENCE_MASTER.md` §10에 있으나 그 절도 손상 구간의 재구성 기록이다(원문 아님).

## 이 고지가 ZIP 바깥에 있는 이유 (2026-09-19, 결함 X-1)

위 경고는 한때 **ZIP 안의 PRD 에 직접 추가돼 있었다.** 의도는 옳았으나 그 편집이 발행된 회차
산출물의 바이트를 바꿨다:

| | HEAD | 편집 후 |
|---|---|---|
| 바이트 | 34298008 | 34298254 |
| sha256 | `cc43ac30…5c34e` | `ce53c262…dd9b` |

그리고 바깥 `.sha256` 도 함께 갱신돼 **현재 파일과 기록이 일치했다** — 그래서 체크섬 검사가
이 변경을 잡지 못했다. 항목 수는 95개로 같았고 추가·삭제도 없었으며 바뀐 파일은
`GO2_FEET_AIR_TIME_020_SCREENING_PRD.md` 와 `PACKAGE_SHA256SUMS.txt` 둘뿐이었다. 조작이
아니라 주의 표시였지만, **얼어붙은 산출물에 주석을 다는 것이 불변 릴리스 규칙이 막으려던 바로
그 일이다.** 표시가 정당하면 그것은 산출물 밖에 둔다 — 이 파일이 그 자리다.

2026-09-19 에 ZIP 과 `.sha256` 을 HEAD 로 되돌렸고, 발행 ZIP 의 바이트가 HEAD 와 달라지면
`tools/test_go2_published_release_contract.py` 가 실패한다. 되돌리기 전 파일은 세션
스크래치패드에 보존했다.

결함 기록: `reports/GO2_DEFECT_LEDGER.md` 의 `X-1`.
