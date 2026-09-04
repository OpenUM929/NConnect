# Go2 예선 캠페인 일정·진행 원장

## 0. 현재 흐름

`Pilot-01·Default-01 쌍대평가 완료 → **단계 2 기본값 단일변수 screening** → 환경 적응 게이트 → 장기 승급 → 최종 평가·문서 → 제출`

## 1. 단계표

| 단계 | 등급 | 작업 | 상태 | 완료 기준 |
|---:|---|---|---|---|
| 0 | 필수(제출요건) | Pilot-01 artifact 정합성 | 완료 | source/env/checkpoint/tfevents/video/policy 계보 |
| 0 | 필수(제출요건) | Go2 G1~G7 registry·평가 package | 로컬 구현·검증 완료 | canonical registry test, Python test, `bash -n`, package SHA |
| 0 | 조사 | Default-01 1,000-iter training package·artifact | 완료 | reward-only diff, seed 42, 4096 env, from-scratch, bundle SHA |
| 1 | 필수(제출요건) | Default-01·Pilot-01 G1~G7 쌍대 fixed eval | 완료 — 두 정책 `INTERNAL_GATE_FAIL` | 정책별 69 telemetry, survival·tracking·영상·paired report |
| 2 | 개선 | 기본값 기반 최대 감점 시나리오 단일변수 1k~5k | **현재 — G-A010 package 검증 완료·서버 실행 대기** | 동일 evaluator에서 목표 G 개선 + 타 G 비열등 |
| 3 | 필수(제출요건) | 선택 후보의 G3 rough·G4 ±20°·G5 10~15cm·G6 push·G7 DR | ▲ 제출 불가 — screening 승자 미확보 | 전 시나리오 survival·tracking·영상 |
| 4 | 개선 | screening 승자 5k→10k→15k | HOLD | 각 승급점에서 비열등 게이트·독립 평가 |
| 5 | 필수(제출요건) | 다중 seed 최종 평가·제출 bundle·200자 리포트 | pending | 자체 최소 70/100·목표 75, lineage, manifest |
| 6 | 필수(제출요건) | Go2 대시보드 제출 | pending | Go2 선택·2파일·30~200자·접수 증거 |

`필수(제출요건)` 행이 막히면 `blocked`로 미루지 않고 `▲ 제출 불가 — 즉시 해소 대상`으로 표시한다.

## 2. 1차 실행 계획 예산

| 순서 | 작업 | 서버/GPU | 사용자가 하는 일 | 재평가 지점 |
|---:|---|---|---|---|
| 1 | evaluator·Default training package 로컬 구현/테스트 | 0 | 없음 | 모든 로컬 검증 PASS |
| 2 | Default-01 from-scratch 학습 | 1,000 iter | zip 업로드·한 줄 실행·bundle 다운로드 | artifact·reward-only diff 검증 |
| 3 | Default-01·Pilot-01 G1~G7 fixed eval + 영상 | 정책 평가 2회; 시간은 smoke 후 실측 | 같은 세션 실행·두 bundle 다운로드 | paired delta와 분기 판정 |
| 4 | 기본값 기반 단일변수 screening | 첫 후보 1,000 iter; 필요 시 3k→5k | package 실행·회수 | primary 개선·타 G 비열등 |
| 5 | 승자 장기학습 | 5k→10k→15k | 각 승급점 회수 | 매 단계 독립평가 |

GPU 시간과 사람 시간을 분리한다. 학습이 돌면 문서·artifact 준비를 병렬 진행한다.

### 2-a. 최소 경로·1차 계획 예산·재평가 지점

| 구분 | 범위 | 다음 단계 승인 조건 |
|---|---|---|
| 최소 경로 | evaluator·Default package → Default-01 1k → Default/Pilot 쌍대평가 | PRD의 restart/promising/inconclusive/shared weakness 중 하나 판정 |
| 1차 계획 예산 | 신규 학습 1회(Default 1k) + 정책 평가 2회 | 기본 대비 Pilot delta와 최대 감점 scenario가 특정됨 |
| 재평가 지점 1 | 두 package 로컬 검증 완료 | 서버 실행 명령 제공 여부 |
| 재평가 지점 2 | Default 학습 bundle 회수 | exact checkpoint 평가 가능 여부 |
| 재평가 지점 3 | 두 정책 G1~G7 결과 | 첫 단일변수 후보 또는 추가 seed 결정 |
| 재평가 지점 4 | screening 1k | 폐기 / 3k~5k 확장 / 독립 학습 seed 재검증 결정 |
| 재평가 지점 5 | 5k·10k·15k 각각 | 다음 iter 승급 또는 직전 verified checkpoint 동결 |

현재 provenance-valid 배포 기본 control checkpoint는 없다. `model_best_20260831154121.pt`의 paired env도
Pilot-01 튜닝 reward이므로 control로 쓰지 않는다. 따라서 Default-01 1,000 iter 생성은 조건부가 아니라
쌍대 비교의 **필수 기준**이다. 이후 실험은 Default-01 계보에서 one-at-a-time으로 진행한다.

테스트 계약: `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md`.
상세 실행·case·분기 계약: `.omx/plans/go2-default-baseline-experiment-plan.md`.

## 3. 실행 승인 게이트

- 신규 학습은 `go2-test-planner`의 12항 사전등록 없이는 `HOLD`다.
- 45분 이상 작업은 정보가치, 더 짧은 대안, 조기중단, bundle이 없으면 `HOLD`다.
- 서버는 package SHA·CRLF·syntax·완료표식·다운로드 경로 검증 전 켜지 않는다.
- 학습 후 필수 영상·telemetry·bundle이 로컬 검증되기 전 서버 종료 판정을 내리지 않는다.
- 현재 `server_run_Go2_videos.sh`는 `LEGACY_INVALID_MAPPING`; 실행 일정에서 제외한다.

## 4. 자체 점수 게이트

| 축 | 배점 | 내부 완료 기준 |
|---|---:|---|
| simulation proxy | 70 | G1~G7 전부, survival≥.95, tracking≥.70, weighted proxy≥.70 |
| 설계 의도 자체감사 | 20 | 문제·변경·가설·env·실제 행동·한계 일치 |
| 리포트 품질 자체감사 | 10 | 30~200자, 명료성, 사실·추론 분리, 근거 run 특정 |
| 총 자체예상 | 100 | 최소 70, 운영 목표 75 이상 |

내부 점수는 공식 점수·통과선이 아니다.

## 5. 진행 원장

| no | 일자 | 항목 | state | 산출물·근거 |
|---:|---|---|---|---|
| 1 | 260901 | 별도 Go2 캠페인 사용자 승인 | done | 사용자 요청 |
| 2 | 260901 | Pilot-01 model/env/tar hash 대조 | done | `GO2_PROJECT_STATE.md` §1 |
| 3 | 260901 | 강좌·가이드 G1~G7 재설계 | done | canonical JSON·evaluation protocol |
| 4 | 260901 | legacy runner 매핑 오류 격리 | done | `LEGACY_INVALID_MAPPING` |
| 5 | 260901 | Go2 전용 역할 4종 생성 | done | `.codex/agents/go2-*.md` |
| 6 | 260901 | 새 세션 handoff 작성 | done | `reports/NEW_SESSION_HANDOFF.md` |
| 7 | 다음 세션 | evaluator 구현·package 테스트 | pending | 로컬 검증 결과 |
| 8 | 260901 | 1차 튜닝 기반 초기 작업계획 확정 | done | `G-A003`, `.omx/plans/go2-post-pilot-initial-work-plan.md`, G-D08 |
| 9 | 260901 | 기본값 재시작·쌍대평가 PRD 및 상세계획 확정 | done | `G-A004`, `GO2_DEFAULT_BASELINE_TEST_PRD.md`, 새 실행계획, G-D09~G-D11 |
| 10 | 260901 | PRD 지속 참조·동일 턴 갱신 계약 | done | PRD §10, G-D12, Go2 기획·평가·보고 역할 지침 |
| 11 | 260901 | 단일 업로드·실행·결과 ZIP package 구현·검증 | done | `go2_default_vs_pilot_v1.zip`, SHA `a95e09c4…2356`, Python tests, Git Bash `bash -n`, ZIP CRC·manifest |

## 6. 사용자 결정

- 260901: 4족보행을 별도 캠페인으로 시작한다.
- 260901: H1과 같은 방식으로 자체평가와 튜닝 과정 증거를 쌓는다.
- 260901: 현재 1차 튜닝 결과를 기준선으로 활용한다.
- 260901: 준비 작업 완료 후 새 세션에서 실행한다.
- 260901: 1라운드 제출은 Go2 선택 + `policy.pt` + `.yaml` + 기술 개선 리포트 30~200자다.
- 260901: 1차 튜닝 이후에는 새 reward 값을 먼저 정하지 않고, Pilot-01 G1~G7 fixed eval 결과로 초기 실험 순서를 결정한다.
- 260901: 향후 실험은 튜닝 전 배포 기본값에서 from-scratch로 다시 시작한다. Pilot-01은 resume하지 않고 비교군·가설 출처로 보존한다.
- 260901: Default-01 1,000 iter와 Pilot-01의 동일 G1~G7 쌍대평가를 첫 의사결정 게이트로 수행한다.
- 260901: 기획자는 Default Baseline 테스트 PRD를 매 기획·실험·판정에서 계속 참조하고, 새 결정·artifact·결과가 생긴 같은 턴에 PRD와 관련 원장을 갱신한다.
- 260901: 사용자 서버 작업에는 검증된 ZIP 경로·SHA·한 줄 실행·완료 표식·단일 결과 ZIP·종료 게이트를 다음부터 별도 요구 없이 자동 제공한다.

## 7. 실행 갱신 — `G-A006` 부분 결과 복구

| 순서 | 등급 | 작업 | 상태 | 완료 기준 |
|---:|---|---|---|---|
| 1 | 필수(제출요건) | 부분 결과 격리·manifest·다운로드 매핑 | 완료 | 461파일 보존, `DOWNLOAD_MAP.tsv`, `LOCAL_SHA256SUMS.txt`, merge 미실행 |
| 2 | 필수(제출요건) | 현재 서버에 hotfix 업로드·resume | 실행 대기 | `[STARTED] ... resume=1`, 기존 Default 69건 재사용 |
| 3 | 필수(제출요건) | Pilot 69 telemetry·정책별 7영상·비교 보고서 생성 | 실행 대기 | `RUNNER_RC=0`, telemetry 69×2, 영상 7×2 |
| 4 | 필수(제출요건) | FULL ZIP·SHA 로컬 회수 및 검증 | ▲ 제출 불가 — 즉시 해소 대상 | ZIP 존재, 외부 SHA 일치, CRC·내부 manifest·lineage·case count 확인 |
| 5 | 조사 | Default 대비 Pilot 분석과 restart/upgrade 결정 | HOLD — 평가 미완료 | PRD §6 분기 판정 및 reward master 갱신 |

현재 서버 종료 게이트는 **불가**다. `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`과 유효한 `.sha256`를 `workspace/_keep/`에 내려받은 뒤 로컬 검증해야 해제한다.

## 8. FULL 분석 이후 일정 갱신 — 260901

| 순서 | 등급 | 작업 | 상태 | 다음 게이트 |
|---:|---|---|---|---|
| 1 | 필수(제출요건) | FULL ZIP·SHA·69×2 telemetry·14영상 검증 | 완료 | `ARTIFACT_VERIFIED` |
| 2 | 필수(제출요건) | 14영상 직접 관찰·G1~G7 증거표 | 완료 | `VIDEO_OBSERVED` |
| 3 | 조사 | Default 대비 Pilot 예상/실제·분기 분석 | 완료 | `SHARED_WEAKNESS_FOUND`, 보고서 발행 |
| 4 | 개선 | `feet_air_time .01→.2` 단일변수 1k 사전등록·package | 완료 | ZIP SHA `f7da2c5e…af49`, contract 5/5, manifest·`bash -n` |
| 5 | 개선 | 단일변수 1k 서버 screening | **현재 — 실행 가능, 외부 결과 미측정** | G5 개선 + 전 G 비열등 + 영상 |

서버 종료 게이트는 **가능**으로 정정됐다. 다음 package 검증 전에는 새 서버를 켜지 않는다. artifact 로그가 덮는 실행 창은 약 2시간 8분이지만 서버 생성~종료 전체 과금 시간은 `[미측정]`이며, 최초 runner 오류가 만든 불필요한 진단·재개 비용을 후속 시간 예산에 포함한다.

## 9. G-A007 실행 일정 — 260901

| 순서 | 등급 | 작업 | 상태 | 다음 게이트 |
|---:|---|---|---|---|
| 1 | 개선 | 단일변수 PRD·승급/실패/INCONCLUSIVE 기준 사전등록 | 완료 | PRD와 reward/state/artifact 원장 일치 |
| 2 | 개선 | candidate-only runner·reporter·package 구현 | 완료 | Default report 고정 재사용, 69 telemetry·7영상·lineage |
| 3 | 개선 | ZIP/SHA/manifest/CRLF/`bash -n`/contract 검증 | 완료 | SHA `f7da2c5e…af49`, 21 members, tests 5/5 |
| 4 | 개선 | 서버 업로드·한 줄 실행 | **사용자 실행 대기** | `[STARTED] go2_feet_air_time_020_v1 resume=0` |
| 5 | 개선 | FULL 결과 ZIP·SHA 다운로드 | pending | `RUNNER_RC=0`, telemetry 69, video 7, lineage |
| 6 | 개선 | 격리·검증·영상 관찰·내부 판정 | pending | 승급 후보 / 실패 / INCONCLUSIVE 중 하나 |

- 최소 경로: 1k candidate 1회 → 69-case·7영상 → 판정.
- 1차 계획 예산: 이전 artifact 실측 기준 약 1시간 35분~2시간 실행 창.
- 재평가 지점: 결과 ZIP 로컬 검증과 7영상 관찰이 모두 끝난 시점.
- 승급 시에도 즉시 장기 학습하지 않고 독립 학습 seed를 먼저 수행한다.

## 10. G-A008 evaluator ?? ?? ? 260901

| ?? | ?? | ?? | ?? | ?? ?? |
|---:|---|---|---|---|
| 1 | ??(????) | PARTIAL ?????? ?? ?? | ?? | hard exit ? cleanup ?? ? ?? startup crash failure surface ?? |
| 2 | ??(????) | graceful close?bounded retry?stable manifest ?? | ?? | hard-exit 0, retry 3?, launcher snapshot |
| 3 | ??(????) | v2 package ?? | ?? | SHA `73c6ba1f?8dbc`, manifest 94/94, tests 6/6, `bash -n` |
| 4 | ??(????) | v1? ?? ?? ?? v2 resume | ?? ?? `[???]` | training skip, ?? case skip, graceful ?? ?? |
| 5 | ?? | FULL ?? ???????? ?? | HOLD ? ?? ?? ?? | telemetry 69, video 7, lineage, ?? gate ?? |

v1 ?? ???? ???? ????. ????? ????? ?? ?? candidate ??? ????.


## 11. 260902 저비용 3단계 평가 일정

| 순서 | 등급 | 작업 | 상태 | 승급/종료 기준 |
|---:|---|---|---|---|
| 1 | 필수(제출요건) | G5 per-env 진행도와 G7 실제 DR 조건 수리·회귀 테스트 | **현재** | 초기 위치 독립 진행도, G3/G7 조건 fingerprint 불일치 |
| 2 | 조사 | 조기중단 6~8 case·seed 101·표적 영상 1개 | pending | 명백한 회귀면 후보 종료; 아니면 대표 평가 |
| 3 | 개선 | G1~G7 대표 7 case × seed 3 = 21 case | pending | proxy ≥60/70 + 전 G survival ≥.95 + tracking ≥.70 + 3 seed 정상 + 영상 치명 이상 0 |
| 4 | 필수(제출요건) | 승급 후보만 Go2 전용 전체 69-case·필수 영상 | pending | 단계 3 조건 충족 후보만 실행 |
| 5 | 필수(제출요건) | H1에는 동일 승급 개념과 H1 전용 전체 30-case 적용 | policy fixed | Go2 69-case를 H1에 복사하지 않음 |

- 최소 경로: 6~8 case에서 실패 시 즉시 종료.
- 1차 계획 예산: 조기중단 통과 후보만 21 case까지 사용.
- 재평가 지점: 대표 평가가 60/70과 안정성 조건을 모두 충족한 시점.
- 전체 평가 예산: 승급 후보만 H1 30-case 또는 Go2 69-case를 사용.
- G-A007: `INTERNAL_SCREEN_FAIL`; 장기학습·추가 전체평가 없음.

## 12. G-A009 실행 일정 — 260902

| 순서 | 등급 | 작업 | 상태 | 종료/승급 기준 |
|---:|---|---|---|---|
| 1 | 필수(제출요건) | G5 env별 진행도·G7 독립 DR evaluator 보정과 회귀 테스트 | 완료 | evaluator tests 3/3, G3/G7 mode 분리 |
| 2 | 개선 | `track_lin_vel_xy_exp 1.0→1.2` only, 1,000 iter | 완료 — `TRAIN_RC=0`, result `ARTIFACT_VERIFIED` | artifact·source·diff 회수 완료 |
| 3 | 조사 | candidate/baseline 각 7 case 조기중단 평가, 필수 영상 1개 | 완료 — `INTERNAL_EARLY_KILL_FAIL`, G1 `VIDEO_OBSERVED` | G1 delta `-0.0000663`로 `+0.05` 기준 미달 |
| 4 | 개선 | 조기중단 통과 시 candidate 21-case 대표평가 | 미실행 — 승급 금지 | 60/70, 전 G survival≥.95·tracking≥.70, 3 seed 완결 |
| 5 | 필수(제출요건) | Go2 전용 69-case 전체평가 | HOLD — 대표평가 승급 전 실행 금지 | 대표평가 승급·영상 이상 0건 뒤 별도 package |

- 최소 경로: 학습 1회 + 평가 8회 + 영상 1개에서 회귀 시 자동 종료.
- 1차 계획 예산: 조기통과 때만 candidate 평가 14회를 더해 총 21회로 확장.
- 재평가 지점: 결과 ZIP의 `TIER1_DECISION.json` 또는 `REPRESENTATIVE_DECISION.json` 회수 직후.
- 예상 실행 창: 기존 1,000-iter 약 1시간을 기준으로 조기종료 약 1시간 5분~1시간 20분, 대표평가 확장 약 1시간 15분~1시간 35분. 서버 과금시간은 보장하지 않는다.

## 13. 범용 engine·JSON 전환 일정 — 260902

| 순서 | 등급 | 작업 | 상태 | 완료 기준 |
|---:|---|---|---|---|
| 1 | 개선 | 이미 검증된 G-A009 package 실행 | 완료 — FULL ZIP·SHA 검증 | 결과 ZIP·SHA 회수 |
| 2 | 조사 | G-A009 결과 분석과 다음 값 결정 | 완료 — G1 `VIDEO_OBSERVED`, G-A010 `lin_vel_z_l2 -3→-2` | 보고서·reward/state 원장 일치 |
| 3 | 개선 | 고정 engine v1.1 hotfix | 완료 — upload package `ARTIFACT_VERIFIED` | v1.0 `BUGGY_DO_NOT_REUSE`; v1.1 SHA `e8f8b3cd…b7cd`, IsaacLab Python launcher, contract 8/8 |
| 4 | 개선 | `experiment.json` schema와 G-A009 호환 fixture·G-A010 입력 작성 | 완료 | spec SHA `fa0bb3b7…c425`, Default identity·단일변경·gate·영상·output 검증 |
| 5 | 개선 | G-A010부터 engine 재사용·JSON만 교체 | 완료 — 실행 준비 | G-A010 spec은 engine에 미포함, extracted-engine materialization 통과 |
| 6 | 필수(운영) | `quadruped/upload/<ID>/current` + immutable history + ledger | 완료 — G-A010 발행 | current/history SHA 일치, v1.0 폐기·v1.1 활성 상태 분리 |

- 현재 G-A009을 다시 포장하지 않는다. 이미 발생한 로컬 제작비용은 회수할 수 없고, 재포장은 서버 실행시간을 줄이지 않는다.
- 범용화 후에도 휘발성 새 서버에는 같은 고정 engine ZIP을 업로드해야 하지만, 실험별로 다시 생성·검증하지 않는다.

## 14. G-A009 분석 후 최소 경로 — 260902

| 순서 | 등급 | 작업 | 상태 | 재평가/종료 기준 |
|---:|---|---|---|---|
| 1 | 조사 | G-A009 Default 대비·예상 대비·영상 분석 | 완료 | G1 목표 실패, G6 기여 77.99%, `INTERNAL_EARLY_KILL_FAIL` |
| 2 | 개선 | 고정 engine + G-A010 `experiment.json` 로컬 구현·검증 | 완료 | engine SHA 고정, JSON 단일 변경, contract 14/14 |
| 3 | 개선 | G-A010 `lin_vel_z_l2 -3→-2` only, 1,000 iter | **현재 — 사용자 서버 실행 대기** | G1 `+0.05`, survival 회귀 `≤0.10`; 실패 시 즉시 결과 ZIP |
| 4 | 조사 | G-A010 tier-1 7-case·G1 영상 | pending | 조기통과 때만 21-case; 실패 시 G-A011 |
| 5 | 개선 | G-A011 `ang_vel_xy_l2 -.08→-.05` only | 조건부 | G-A010 실패 때만 실행 |

- 최소 경로: G-A010 1회 학습 + tier-1 7-case + 영상 1개.
- 1차 계획 예산: G-A010 조기통과 때만 seed 202·303의 14 case를 추가한다.
- 재평가 지점: G-A010 결과 ZIP의 조기판정 회수 직후.
- 서버 병렬화: 확인된 자원은 RTX 5080 1장·16,303MiB뿐이며 peak VRAM telemetry는 없다. 따라서 4096-env 학습 2개 동시는 사실근거가 부족해 승인하지 않고 후보는 순차 실행한다. 학습 중 CPU 기반 package·문서 작업만 병렬화한다.

## 15. 규정집 대조 후 Go2 정책 결정 (260903)

### 15-a. 규정이 바꾼 전제 3개

1. **제10조 — 로봇 유형별 최고점 합산, 한 로봇만 제출하면 100점 상한.**
   "H1이냐 Go2냐"는 잘못된 질문이었다. 두 기체를 모두 제출해야 200점이 열린다.
   H1은 이미 자체예상 92.73/100 정책이 있으므로 **H1 GPU 예산은 0시간**이고
   (`H1_REWARD_EVIDENCE_MASTER.md` §12-e), 잔여 25시간은 전부 Go2 몫이다.
2. **제8조 — 생존율 = "넘어지지 않고 완주한 비율".** 260902까지의 evaluator는
   종료 이벤트만 셌다. 이 문구가 자세 게이트 수정의 **규정상 근거**다. 내부 판단이 아니다.
3. **제7조 — "사족(Go2)의 단차 등반은 요구되지 않는다", G5는 계단 10~15cm.**
   `terrain_levels ≥ 7.0`을 성능 목표로 사전등록한 것은 **규정에 없는 목표**였다.
   G-A011(5,000 iter)의 판정 기준을 이 근거로 **철회**한다.

### 15-b. 가중치 구조가 지시하는 것

| 블록 | 시나리오 | 합계 가중 | 현재 v2 측정 상태 |
|---|---|---:|---|
| 평지 | G1 0.15 + G2 0.15 + G6 0.10 | **0.40** | Pilot-01 재채점 완료 (1.000 / 1.000 / 0.969) |
| 지형 | G3 0.20 + G4 0.15 + G5 0.15 + G7 0.10 | **0.60** | **전부 미측정** |

**점수의 60%가 한 번도 유효한 지표로 측정된 적이 없다.** 어느 시나리오가 몇 점을
잃고 있는지 모르는 상태에서 5시간짜리 학습을 거는 것은, 캠페인이 이미 5.81시간을
들여 저지른 실수(무너진 기준선 위의 단일변수 비교)의 반복이다.

### 15-c. 결정

**G-A012 — 학습하지 않는다. 먼저 측정한다.**

| 단계 | 내용 | GPU | 산출 |
|---|---|---:|---|
| 0 | **H1 제출** (policy.pt + env.yaml + 리포트) | **0h** | 규정 제10조상 최대 기대이득 행동 |
| **A** | **동결 Pilot-01, 69 case × 3 seed, 자세 게이트 + 시나리오별 영상 7건** | **~1.1h** | **최초의 진짜 G1~G7 점수표** |
| B | A의 최대 가중 실점 시나리오가 다음 단일 변수를 **결정한다** | 0h | 사전등록 완료, 사후 재협상 없음 |
| C | 단일 변수 학습 3,000~5,000 iter + 69 case 재평가 | ~4.3~6.4h | 후보 정책 |
| 예비 | C 실패 시 2차 시도 | ~6h | |
| | **소계** | **~11.4~13.5h / 25h** | 여유 11.5h 이상 |

- **A는 학습이 없으므로 제출 후보를 손상시킬 수 없다.** 25시간 중 4.4%로
  나머지 96%를 어디에 쓸지가 결정된다.
- **사전등록 판정(고정):** A의 시나리오별 `가중 실점 = (1 − survival_v2 × tracking_proxy) × weight × 70`
  중 **최댓값 하나**가 C의 단일 변수를 결정한다. 다른 선택 규칙은 인정하지 않는다.
  terrain curriculum level은 목표가 아니며 진척 지표로만 기록한다.
- **영상은 지표를 반증할 수 있다.** 계단 위 플랫폼에 멈춰 선 정책은 숫자상 생존·추종
  양호로 읽힌다. 영상과 숫자가 충돌하면 `AUDIT_INCONCLUSIVE`이며 숫자를 의심한다.

### 15-d. 아직 쓰지 않은 레버 — 생존 reward가 비활성이다

`quadruped_rewards.py`에서 다음 두 항이 **주석 처리되어 있다**:

```
# "undesired_contacts":  -1.0,   # 배/무릎 닿음 패널티
# "termination_penalty": -200.0, # 넘어짐 벌점
```

규정 제8조의 생존율은 tracking에 **곱해지는** 인수인데, 생존을 직접 겨냥하는 두 reward가
꺼진 채로 캠페인 5.81시간이 `feet_air_time`·`track_lin_vel_xy`·`lin_vel_z` 같은
**이동 다이얼**에만 쓰였다. 주석은 "Go2 기본값엔 미정의일 수 있음 → skip 경고 가능"이라고
적고 있으므로 **존재 여부부터 확인해야 한다.** 이 확인은 10 iter smoke test(수 분)로 끝난다.
단계 B의 유력 후보이며, A의 점수표가 생존 쪽 실점을 지목하면 1순위가 된다.

### 15-e. 철회 항목

- **G-A011(`go2_terrain_5k_v1.zip`, 5,000 iter, 6h40m) — `WITHDRAWN_PRE_LAUNCH`.**
  실행되지 않았으므로 GPU 소비 0. 철회 사유는 판정 기준(`terrain_levels ≥ 7.0`)이
  규정 제7조와 불일치하고, 0.60 가중의 실점 위치를 모르는 상태에서 단일 변수를
  "학습 길이"로 고정했기 때문이다. 패키지 파일은 근거 보존을 위해 남긴다.

## 16. G-A012 결과와 단계 B 확정 (260903)

**A 실행 결과:** 동결 Pilot-01, 69 case × 3 seed, `posture_gate_v2`.
worst-case `33.79311/70`, 평균 `45.03099/70`, 비용 약 29분.
상세: `workspace/training/quadruped/reports/GO2_PILOT_V2_BASELINE_RESULT_ANALYSIS_260903.md`.

| 블록 | 가중 | 획득 | 실점 |
|---|---:|---:|---:|
| 평지 G1+G2+G6 | 0.40 | 23.82/28 | 4.18 |
| 지형 G3+G4+G5+G7 | 0.60 | 9.97/42 | 32.03 |

**단계 B 확정 — 사전등록 규칙의 유일한 출력.** 가중 실점 최댓값은 G3 `12.97/70`,
2위는 G5 `10.50/70`이며 **두 시나리오의 실점 인자는 모두 생존**이다
(`rough_lateral` 최대 23/32 낙상, `stairs_15_down` 32/32 낙상, G3 tracking은 `0.78~0.80` 유지).
따라서 §15-d가 지목한 **생존 reward 한 항**이 단계 C의 단일 변수다.
`undesired_contacts`·`termination_penalty`의 정의 여부를 10-iter smoke test로 먼저 확인한다.

**C 판정 기준(고정):** G3 worst survival `.0938 → ≥ .50`, G5 worst survival `> 0`,
G1·G2·G6 각 proxy 회귀 `≤ .05`, 총 worst-case proxy `> 33.79311/70`.

**측정 결함:** `dr_seed_*` telemetry가 `rough_forward`와 SHA까지 동일하다.
G7은 독립 측정이 아니며 다음 evaluator에서 수정한다(`AUDIT_FINDING`, G-F75).

## 17. 단계 C 확정 — G-A013 `flat_orientation_l2` (260903)

**smoke test는 취소한다.** §16이 요구한 "`undesired_contacts`·`termination_penalty` 정의 여부"는
서버 학습 산출 `env.yaml`에 이미 기록돼 있었다. 실측 결과 `undesired_contacts: null`이고
`termination_penalty`는 항 자체가 없다. **두 레버 모두 사용 불가**이므로 10 iter를 쓸 이유가 없다.

**단일 변수:** `flat_orientation_l2` `0.0 → -1.0`. 11개 reward 중 정의돼 있으면서 한 번도 쓰지
않은 자세 항이고, 기울어짐(중력 xy 성분)에 직접 벌점을 주므로 G-D58이 요구한 "생존을 겨냥하는
한 항"의 유일한 실행 가능 후보다.

| 항목 | 값 |
|---|---|
| work id | G-A013 |
| baseline | Default-01 iter 800 (나머지 5개 weight 고정) |
| 학습 | from scratch, seed 42, 4096 env, 1,000 iter |
| tier-1 목표 | **G3** proxy `+0.05` 이상 |
| 비용 | 조기 종료 약 1시간 6분 / 대표평가까지 약 1시간 11분 |
| 업로드 | `upload/G-A013/current/` 두 파일 |

**게이트 목표 수정(G-D63).** G-A010은 총점 `+2.26/70`과 G3 survival `+0.094`를 얻고도 목표가
G1에 고정돼 조기 종료됐다. 목표 시나리오는 사전등록 규칙이 지목한 시나리오여야 한다.
이 수정은 G-A013 **실행 전에** 확정했고, 결과를 본 뒤 다시 바꾸지 않는다.

**C 판정 기준은 §16 그대로 유지한다** — G3 worst survival `.0938 → ≥ .50`, G5 worst survival `> 0`,
G1·G2·G6 각 proxy 회귀 `≤ .05`, 총 worst-case proxy `> 33.79311/70`.
단 이 기준은 69-case 재평가에 적용되며, G-A013의 tier-1/대표평가는 7-case 선별 게이트다.

**다음 분기(사전등록):** tier-1 PASS → seed 202·303 자동 진행 → 통과 시 69-case 재평가.
tier-1 FAIL이지만 G3 survival 상승 → G-A014 `flat_orientation_l2 0.0 → -2.0` only.
tier-1 FAIL이고 G3 survival 무변화·하락 → 자세 다이얼 기각, G-A014 `lin_vel_z_l2 -3.0 → -5.0` only.

## 18. 단계 C 종료와 단계 D 확정 — 260903

### 18-a. 단계 C 결과: 가설 기각

G-A013(`flat_orientation_l2` 0.0 → −1.0)은 총점 `−1.4278/70`으로 기각됐다. §17이 사전등록한
후속 G-A014(`−2.0`)는 **취소**한다. 취소 근거는 사후 재협상이 아니라 측정된 실패 방식이다:
G-A014의 전제는 "효과가 약해서 실패했다"인데, 실측된 실패는 부호 오류다(G3 생존 `+0.156`
대 G4 `−0.313`·G5 `−0.313`). 경사·계단에서 몸통은 지형을 따라 기울어야 하므로 이 항을 더
강하게 미는 것은 1·2위 실점 시나리오를 악화시킨다. **취소 사실과 근거를 실행 전에 기록한다.**

### 18-b. 게이트 개정 — 실행 전 선언

tier-1 조기 종료 게이트를 시나리오 고정에서 **가중 총점**으로 바꾼다(엔진 1.2.0).

| 실험 | 총점 Δ/70 | 허용 초과 생존 후퇴 | 구 게이트 판정 |
|---|---:|---|---|
| G-A011 `track_lin_vel_xy_exp` 1.0→1.2 | +3.0903 | 없음 | FAIL (G1 고정 목표) |
| G-A010 `lin_vel_z_l2` −3.0→−2.0 | +2.2572 | 없음 | FAIL (G1 고정 목표) |
| G-A013 `flat_orientation_l2` 0.0→−1.0 | −1.4278 | G2·G4·G5·G6 | 목표(G3)는 **통과** |

4건 전부에서 고정 시나리오 절과 목적함수의 부호가 반대다. 규정이 채점하는 값은
`Σ(weight × 생존율 × 추종 점수)`이므로 게이트도 같은 값을 본다. 생존 가드
(`max_survival_regression = 0.10`)는 그대로 두어 총점만 올리고 생존을 무너뜨리는 후보를
계속 차단한다. **이 개정은 G-A015 실행 전에 확정한다.**

### 18-c. 기준선 전환 — 실행 전 선언

동결 기준선을 Default-01(`17.90697/70`)에서 **Pilot-01(`33.79311/70`)**로 바꾼다. 근거는
같은 69-case `posture_gate_v2` 측정치이며, Default-01 기준 스크리닝은 제출 후보가 아닌
정책을 최적화한다. 이로써 G-A010·G-A011·G-A013의 수치는 Pilot-01 기준 신규 결과와 직접
비교할 수 없다. 이 손실은 감수한다.

### 18-d. 단계 D 단일 변수: `feet_air_time` 0.20 → 0.35

사전등록 §15-c는 A(=G-A012 Pilot-01 69-case)의 가중 실점 최댓값 하나가 단일 변수를 결정한다고
못박았다. 순위는 G3 `12.97` > G5 `10.50` > G4 `4.95` > G7 `3.61` > G2 `2.60` > G1 `1.13` >
G6 `0.45`(/70)이고 1·2위 실점 인자는 모두 생존이다. `feet_air_time`은 발 들기 높이를 올려
G3와 G5에 동시에 작용하는 유일한 다이얼이며, 측정된 곡선이 있는 유일한 변수다
(0.01 → 0.20이 같은 스위트에서 `+3.8656/70`, 생존 후퇴 0건).

### 18-e. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | seed 202·303 → 69-case 재평가 → Pilot-01 `33.79311/70`과 비교 |
| FAIL (총점 Δ < +1.0/70) | 곡선이 0.20~0.35 사이에서 꺾인 것 → `0.20 → 0.28`, 같은 기준선·seed |
| FAIL (생존 후퇴 > 0.10) | 0.20을 상한으로 확정하고 다음 실점 순위(G5 계단)로 이동 |

다른 선택 규칙은 인정하지 않는다.
