# Go2 예선 프로젝트 상태 원장

> 이 문서는 Go2 캠페인의 append-only 정본이다. H1 `PROJECT_STATE.md`의 과거 D23과 완료 상태를
> 삭제하거나 덮어쓰지 않는다. 외부 대시보드 행위는 증거가 없으면 `[미측정]`이다.

## 0. 예선 기준 현재 위치

- [예선 목표] Go2 시뮬레이션 70점, 설계 의도 20점, 리포트 품질 10점의 자체 70점 이상·목표 75점 이상
- [현재 단계] **단계 2/6 — 짧은 학습 pilot**
- [확보] G-A007·G-A009 폐기 근거, G-A009 G1 `VIDEO_OBSERVED`, 고정 engine·G-A010 JSON upload package `ARTIFACT_VERIFIED`
- [미확보] G-A010 checkpoint·tier-1 telemetry·G1 영상, screening 승자, 독립 학습 seed, 200자 제출문, `OFFICIAL_RESULT`
- [이번 테스트] `lin_vel_z_l2 -3→-2`만 바꾼 1,000-iter candidate가 G1을 `+0.05` 개선하고 G2~G7 survival을 유지하는지 판정
- [흐름] engine·JSON 검증 완료 → **G-A010 서버 실행·회수** → tier-1 판정 → 대표평가/독립 seed → 제출
- [지금 할 일] engine ZIP과 G-A010 JSON을 서버 `/workspace/`에 업로드하고 원장의 한 줄 명령 실행
- [보장하지 않음] 단일 seed·내부 proxy·영상만으로 공식 점수, 최적 reward, 예선 통과를 보장하지 않음

## 1. 현재 기준선 식별자

| 항목 | 값 | 상태 |
|---|---|---|
| run ID | `train_260831-Go2_5var_1000` | 확인 |
| 학습 | seed 42, 4096 env, 1,000 iter, best iter 972, 보존 checkpoint `model_999.pt` | 확인 |
| model SHA256 | `c4d78adf3fbd90311e70d2b165370ddded3d5f913e8f128621fa1be45f89af8d` | exported ↔ recovered model_999 일치 |
| env SHA256 | `f5550641c82aeb0a98892b8c74d61d6234d527733061fa3476338bf55b26975d` | exported ↔ recovered params/env 일치 |
| reward source SHA256 | `2b432994609c86dcc42d17c70d3752ce121effa56a1257f67b733b84134d5a37` | 현재 로컬 파일 |
| generic video SHA256 | `5beb7445d5e9814dba4bdcc2ed40bb38765d069d43926ddf45a469c378cc957c` | 존재하나 checkpoint sidecar 없음 |
| recovered tar SHA256 | `3eb3b69711d247d5c2bff9ffdc96bfa6db3f7ce7767226d02545650a502c1b4a` | STATUS/DOWNLOAD_SHA 확인 |
| `policy.pt` | 없음 | ▲ 제출 불가 — 즉시 해소 대상(단계 5에서 생성) |

## 2. 확인된 사실

| ID | 사실 | 근거 |
|---|---|---|
| G-F01 | 강좌의 Go2 배포 기준은 `track=1.0`, `feet=0.01`, `lin_z=-3.0`, `ang_xy=-0.08`, `action=-0.01`이다 | 강좌 14강 974~986 |
| G-F02 | 현재 pilot은 위 기준에서 네 항을 동시에 바꿨고 action_rate는 바꾸지 않았다 | `quadruped_rewards.py`, recovered STATUS |
| G-F03 | report 진단은 최고 reward 18.02@972, terrain 3.94, 학습지형 낙상률 13.8%, std 0.499다 | `exported/report.html` |
| G-F04 | G-F03은 학습 진단값이며 G1~G7 official survival/tracking이 아니다 | 강좌 15강: 정량과 영상 교차 확인, 공식 evaluator 상세 미공개 |
| G-F05 | 제공 가이드의 Go2 G1~G7은 전진·전방위·rough·±20°·10~15cm 계단·push·DR이다 | `workspace/PRELIM_RL_GUID.md:60-70` |
| G-F06 | 기존 Go2 영상 러너는 G1 stand, G2 forward, G3 lateral, G4 complex, G5 rough, G6 ±10°, G7 push로 구성돼 G-F05와 불일치한다 | `server_run_Go2_videos.sh` |
| G-F07 | 현재 env의 tracking std는 0.5, rough noise는 0.01~0.06m, stairs 학습 범위는 0.05~0.23m다 | `exported/env.yaml:215-262,822-833` |
| G-F08 | 현재 env는 base mass를 -1~+3kg으로 randomize하지만 friction은 static 0.8/dynamic 0.6 고정 범위다 | `exported/env.yaml:649-720` |
| G-F09 | 1라운드 제출 계약은 Go2 유형 선택, `policy.pt`, `.yaml`, 기술 개선 리포트 30~200자다. 팀원 누구나 파일 수정·삭제가 가능하고 심사 시작 전까지 자유롭게 수정할 수 있다고 표시된다 | 사용자 제공 대시보드 원문(260901) |
| G-F10 | `model_best_20260831154121.pt`가 존재하지만 연결된 `env_20260831154121.yaml`도 Pilot-01의 튜닝 reward(`1.2/0.2/-2.0/-0.05/-0.01`)다 | 로컬 SHA·env 내용 감사(260901); 배포 기본 control lineage로 사용할 수 없음 |
| G-F11 | pre-pilot source의 배포 기본 reward는 `1.0/0.01/-3.0/-0.08/-0.01`이지만 이 값으로 1,000 iter를 완료한 provenance-valid model·tfevents·env artifact는 로컬에 없다 | `git show 51d76f0^:workspace/training/quadruped/quadruped_rewards.py`; pre-pilot tree와 artifact 감사(260901) |
| G-F12 | Pilot-01은 run 내부에서 reward·episode length·tracking 진단이 개선됐으나 reward 계수가 다른 Default 정책과의 상대 성능은 계산할 수 없다 | Pilot tfevents 100-iter window 분석; 공통 G1~G7 대조군 없음 |

## 3. 결정

| ID | 결정 | 이유 |
|---|---|---|
| G-D01 | Go2를 H1과 분리된 신규 캠페인으로 운영한다 | H1 완료 상태·artifact·점수와 혼합 방지 |
| G-D02 | pilot을 `MULTIVARIABLE_EXPLORATORY_BASELINE`으로 동결한다 | 네 변수 동시 변경으로 개별 인과 귀속 불가 |
| G-D03 | 기존 영상 러너를 `LEGACY_INVALID_MAPPING`으로 분류한다 | 공식/제공 G registry 불일치 |
| G-D04 | 새 학습 전에 pilot을 정확한 G1~G7 evaluator로 측정한다 | 병목은 iteration이 아니라 성능 공백 |
| G-D05 | 자체평가는 survival×tracking, G1~G7 전부, worst-case 방향, 평가 seed 101/202/303으로 운영한다 | 제공 점수 개념·단일 seed 과대해석 방지 |
| G-D06 | 장기학습은 단일변수 screening 승자만 5k→10k→15k로 승급한다 | 강좌의 변인 통제·짧은 실험 후 장기 원칙 |
| G-D07 | 공식 상세가 미공개인 evaluator는 `INTERNAL_PROXY`라고 표기한다 | 공식 재현·공식 점수 오인 방지 |
| G-D08 | 1차 튜닝 기반 초기 순서를 `G-A002 fixed eval → 조건부 control → 최대 감점 축 단일변수 ablation`으로 고정한다 | 성능 공백을 먼저 닫고 불필요한 GPU 학습과 다변수 반복을 방지 |
| G-D09 | **260901 정정:** 향후 실험 계보는 배포 기본값에서 from-scratch로 다시 시작한다. Pilot-01은 resume하지 않고 비교군·가설 출처로 동결한다 | 사용자 결정; 네 변수 동시 변경의 인과 공백을 제거 |
| G-D10 | Default-01 1,000 iter 생성과 Pilot-01 동일 G1~G7 쌍대평가를 조건부가 아닌 첫 의사결정 게이트로 둔다 | “기본 대비 얼마나 좋아졌는가”를 먼저 측정해야 upgrade/restart 판단 가능 |
| G-D11 | Default/Pilot 정책 비교에서 `Train/mean_reward` 절대값을 사용하지 않고 survival·tracking·completion·recovery·영상만 사용한다 | reward 계수가 달라 objective 절대값이 공정한 성능척도가 아님 |
| G-D12 | `GO2_DEFAULT_BASELINE_TEST_PRD.md`를 Go2 기획자가 매 기획·실험·판정에서 참조하고 같은 턴에 갱신하는 살아있는 정본으로 운영한다 | 사용자 결정; 단발 계획의 노후화와 원장 불일치 방지 |
| G-D13 | 사용자 서버 작업은 검증된 단일 업로드 ZIP·한 줄 실행·단일 결과 ZIP 회수로 제공하고, 이후 같은 유형 작업에서도 경로·SHA·명령·완료표식·다운로드·종료 게이트를 자동 안내한다 | 사용자 결정; 반복 요청 제거와 휘발성 서버 회수 누락 방지 |

## 4. 미측정·차단 공백

| ID | 등급 | 공백 | 해소 방법 |
|---|---|---|---|
| G-B01 | 필수(제출요건) | pilot의 G1~G7 survival/tracking | 새 fixed evaluator package |
| G-B02 | 필수(제출요건) | G3/G4/G5/G6/G7 정확한 환경 실현값·사건 로그 | telemetry와 config dump |
| G-B03 | 필수(제출요건) | policy↔checkpoint actor tensor | 선택 checkpoint로 play export 후 tensor 대조 |
| G-B04 | 필수(제출요건) | 정확한 G1~G7 영상 | 새 evaluator와 동일 case/checkpoint 영상 |
| G-B05 | 필수(제출요건) | Go2 200자 제출문 | 최종 env·검증 결과 후 작성·글자수 검사 |
| G-B06 | 조사 | 공식 command/terrain/push/DR/tracking 상세 | 공지 확인 전까지 내부 proxy로 버전 고정 |
| G-B07 | 조사 | 독립 학습 seed 재현성 | 장기 후보가 생긴 뒤 비용 대비 결정 |
| G-B08 | 조사 | provenance-valid 배포 기본 Default-01 checkpoint | 기본 reward·seed 42·4096 env·1,000 iter from-scratch package로 생성·회수 |
| G-B09 | 조사 | Default-01 ↔ Pilot-01 동일 G1~G7 쌍대 비교 | 같은 registry·case·평가 seed·metric·영상으로 paired report 생성 |

## 5. NEXT

테스트 정본은 `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md`다. 첫 구현은
기존 runner 수정이 아니라 **정확한 G1~G7 evaluator와 Default-01 from-scratch package**다.
로컬 package 검증은 완료됐다. 실행 정본은 `go2_default_vs_pilot_v1.zip` SHA
`a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`이며, 다음 행동은 이 ZIP을
서버에 업로드해 한 줄 runner를 실행하는 것이다. 새 reward 학습은 Default/Pilot 쌍대평가 뒤 결정한다.
상세 실행계획은 `.omx/plans/go2-default-baseline-experiment-plan.md`를 따른다.

## 6. 병렬화 근거 경계 — 260901 정정

| ID | 확정 사실 | 근거·한계 |
|---|---|---|
| G-F13 | `--num_envs 4096`은 강좌 13·14강에 실제 제시된 Go2 학습 명령이며 Pilot-01과 Default-01의 통제값이다. 그러나 할당 서버에서 환경 수·동시 프로세스 수를 단계별 벤치마크해 산출한 하드웨어 최대치는 아니다. | `test/13강의. 로봇 학습 하기 · 진화 · NAVER CONNECT ROBOTICS GUIDE BOOK.html:1169,1194,1271`, `test/14강의. 보상 함수 설계와 조정 · 진화 · NAVER CONNECT ROBOTICS GUIDE BOOK.html:963,1018,1069` |
| G-F14 | 보존된 과거 서버 로그는 GPU 1개 `NVIDIA GeForce RTX 5080`, 메모리 `16303 MB`를 기록한다. 이는 과거 실측 자원 식별자이지 현재 세션의 가용 VRAM·GPU 사용률·최적 동시 실행 수를 보장하지 않는다. | `workspace/server_returns/train_260831-06_run05cfg_10000/extracted/train_260831-06_run05cfg_10000/train.log:370206`; 현재 Go2 runner는 시작 시 `nvidia-smi` 정적 정보만 저장하며 사용률 시계열·확장 벤치마크는 미수집 |
| G-F15 | 현재 통합 runner는 학습만 단일 Isaac Lab 프로세스 안에서 4096 env로 벡터화한다. 두 정책, 평가 seed/case, worst-case 영상은 순차 실행하며 다중 GPU 분배가 없다. 따라서 전체 workflow를 "할당 자원의 최대 병렬 처리"라고 표현하지 않는다. | `workspace/training/quadruped/server_run_go2_default_vs_pilot_v1.sh:75-86,231-249,271-272,311-320` |

## 7. 첫 서버 결과 및 복구 판정 — 260901

| ID | 최신 사실 | 근거 |
|---|---|---|
| G-F16 | 첫 서버 실행은 Default-01 학습과 Default G1~G7 telemetry 69/69까지 완료했지만 `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`로 종료했다. Pilot telemetry는 0/69이고 영상은 0/14다. | `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/STATUS.txt`, `INGEST_STATUS.md` |
| G-F17 | 실패 원인은 runner가 Pilot `exported/`를 먼저 삭제하고 그 안의 checkpoint를 복사한 순서 오류이며, 실패 bundle 생성도 서버에 없는 bare `python3`를 호출했다. | 격리된 `launcher.log`; 수정 전 runner 215~221, 264~272행 |
| G-F18 | 수신한 `.sha256`는 0 byte이고 최종 ZIP 본체가 없으므로 FULL 결과의 `ARTIFACT_VERIFIED` 근거가 아니다. 부분 폴더 461파일은 별도 격리·매핑했으며 학습 결과 병합은 하지 않았다. | `workspace/server_returns/DOWNLOAD_MAP.tsv`, `MERGE_RESULT.tsv` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D14 | 서버를 유지하고 `G-A006` hotfix로 `GO2_RESUME=1` 재개한다. Default 학습·69 telemetry는 fingerprint로 재사용하고 Pilot telemetry·비교 보고서·14영상·FULL ZIP만 완성한다. | 재학습 비용을 피하면서 PRD의 동일 evaluator 비교와 필수 회수물을 완성할 수 있음 |
| G-D15 | 최초 package SHA `a95e09...`는 `BUGGY_DO_NOT_REUSE`로 격리한다. 현재 서버는 hotfix SHA `b2fa2d...`, 새 서버는 수정 통합 package SHA `db239f...`를 사용한다. | 같은 오류의 반복 실행 방지 |

**LATEST NEXT:** `/workspace/go2_default_vs_pilot_v1_hotfix.zip`을 업로드하고 `GO2_RESUME=1`로 재개한다. `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`과 유효한 `.sha256`가 로컬에서 검증되기 전에는 서버 종료 불가다.

## 8. FULL 결과 회수 및 서버 종료 판정 — 260901

| ID | 최신 사실 | 근거 |
|---|---|---|
| G-F19 | FULL ZIP과 SHA가 로컬에 도착했고 외부 SHA `af41ccc5...b25b`가 일치한다. package는 `RESULT_STATE=FULL`, `RUNNER_RC=0`, Default/Pilot telemetry 69+69, 영상 7+7을 포함한다. | `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/VERIFICATION_STATUS.md` |
| G-F20 | 내부 manifest는 launcher.log 한 건을 제외한 923건이 일치한다. launcher.log는 manifest 생성 뒤 완료행이 추가된 packaging 순서 문제이며, 외부 ZIP SHA는 일치한다. | 같은 검증 보고서 |
| G-F21 | 내부 proxy는 Default `17.90699/70`, Pilot `41.97990/70`이고 둘 다 `INTERNAL_GATE_FAIL`이다. Pilot은 Default보다 약 `+24.07/70` 높지만 G3~G5·G7 약점이 남는다. 영상은 파일 확보만 끝났고 `VIDEO_UNKNOWN`이다. | paired/self-eval JSON |

| ID | 결정 | 이유 |
|---|---|---|
| G-D16 | G-A006을 `ARTIFACT_VERIFIED`로 승급하고 서버 종료를 허용한다. | 필수 ZIP·SHA·telemetry·영상이 로컬에 있으며 재현에 필요한 artifact를 회수함 |
| G-D17 | 성능 결론은 Pilot의 Default 대비 개선과 `INTERNAL_GATE_FAIL`을 동시에 유지하고, 영상 관찰·정식 분석 전 reward 업그레이드를 시작하지 않는다. | 내부 proxy 개선이 공식 결과나 전체 시나리오 통과를 뜻하지 않음 |

**LATEST NEXT:** 서버를 종료한다. 로컬에서는 FULL ZIP을 격리 보존한 채 영상 14개 관찰과 Default-vs-Pilot 상세 분석을 수행하고 living PRD를 갱신한다.

## 9. Default-vs-Pilot 상세 분석·영상 판정 — 260901

### 9-a. 확인된 사실

| ID | 사실 | 근거 |
|---|---|---|
| G-F22 | 동일 evaluator에서 Pilot은 Default보다 `+24.07291/70` 높고 평가 seed 101·202·303 모두 양의 delta다 | paired report JSON, 분석 보고서 §2~3 |
| G-F23 | Pilot은 G1·G2·G6 `INTERNAL_SCENARIO_PASS`, G3·G4·G5·G7 `INTERNAL_SCENARIO_FAIL`이다 | Pilot self-eval JSON |
| G-F24 | Pilot은 G3 survival `-.15625`, G4 `-.03125`, G5 `-.125`로 사전 비열등 허용치 `-.02`를 위반했다 | paired report JSON, PRD §5-c |
| G-F25 | Pilot 최대 내부 감점은 G5 `8.12/70`, 다음은 G3 `7.84/70`이며 G5의 약한 인수는 tracking/completion이다 | weight×(1-proxy) 재계산 |
| G-F26 | 14개 MP4에서 각 12프레임을 균등 추출해 직접 관찰했다. 평지 이동·push 회복 개선과 rough/stairs 불안정이 정량과 일치한다 | `reports/evidence/go2_default_vs_pilot_260901/VIDEO_OBSERVATION.md` |
| G-F27 | artifact 로그가 덮는 최초 학습 시작~FULL 완료 창은 약 2시간 8분으로 추정 1.5~3시간 안이다. 서버 생성~종료 전체 과금 시간은 `[미측정]`이며, 최초 runner 오류가 불필요한 진단·재개 시간을 추가했다 | launcher timestamp, PRD §11·§13 |

### 9-b. 결정

| ID | 결정 | 근거 |
|---|---|---|
| G-D18 | Default 성능으로 전면 회귀하지 않는다. Pilot은 성능 상한·가설 출처로 보존한다 | Default 전 G 실패, Pilot G1·G2·G6 통과 및 +24.07/70 |
| G-D19 | Pilot checkpoint는 resume하지 않는다. 후속 인과 실험은 Default-01 계보에서 from-scratch·one-at-a-time으로 수행한다 | 네 reward 동시변경 인과 공백 |
| G-D20 | PRD 최종 분기는 `SHARED_WEAKNESS_FOUND`로 확정한다 | 두 정책 공통 실패 G3·G4·G5·G7과 Pilot survival 회귀 |
| G-D21 | 첫 사전등록 후보는 Default `feet_air_time .01→.2` 단일 변경 1,000 iter다 | 최대 감점 G5, 약한 tracking/completion, 강좌의 발 들기 직접 연결성 |
| G-D22 | 현재 단계는 3/6 환경 적응 게이트다. 새 서버 실행은 단일변수 사전등록·회수 package 검증 전 `HOLD`다 | 단계 0~2 증거 완료, G3·G4·G5·G7 미달 |

**SUPERSEDED NEXT (completed by §10):** `feet_air_time .01→.2` 단일변수 1,000-iter screening의 기준 policy·유지값·G1~G7 성공/실패·조기중단·영상·telemetry·bundle을 사전등록하고 실행 package를 로컬 검증한다.

## 10. `feet_air_time=0.20` 단일변수 package 확정 — 260901

### 10-a. 확인된 사실

| ID | 사실 | 근거 |
|---|---|---|
| G-F28 | Default-01의 재현 식별자는 checkpoint iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`, env SHA `4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c`다 | G-A006 FULL result의 training model/env와 default identity |
| G-F29 | 다음 candidate는 Default reward에서 `feet_air_time 0.01→0.20`만 바꾸며 `track_lin=1.0`, `lin_vel_z=-3.0`, `ang_vel_xy=-0.08`, `action_rate=-0.01`을 유지한다 | G-A007 builder AST contract test |
| G-F30 | G-A007 package는 21 members, SHA `36170b858d64ac3fd5d8d61a38d5eeff8e0c8cc986cbda182b85004fb5dd3a3f`로 deterministic rebuild·CRC·safe path·내부 manifest·CRLF 0·`bash -n`·contract 5/5를 통과했다 | `go2_feet_air_time_020_v1.VERIFICATION.md` |
| G-F31 | Default 학습·69-case 평가를 반복하지 않고 검증된 Default self-eval report를 고정 입력으로 포함한다. candidate만 1k 학습·69-case·7영상을 실행한다 | builder baseline provenance, runner phase contract |
| G-F32 | 이전 artifact의 부분별 실측은 1k 학습 약 65분, 정책 하나 69-case 약 22분, 영상 7개 약 4분이다. 이번 실행 창은 시작·packaging 여유 포함 약 1시간 35분~2시간으로 추정한다 | G-A006 ZIP entry timestamp 분석, screening PRD §7 |

### 10-b. 결정

| ID | 결정 | 근거 |
|---|---|---|
| G-D23 | G-A007 사전등록을 승인한다. 정량 승급은 G5 proxy `+0.03`, G5 survival `≥-0.02`, 전 G survival `≥-0.02`, tracking `≥-0.05`, seed delta `≥-0.02`를 모두 요구한다 | 최대 감점 G5와 사전 비열등 계약 |
| G-D24 | 정량 조건 충족만으로 `INTERNAL_SCREEN_QUANTITATIVE_PASS_VIDEO_REVIEW_PENDING`이며, 7영상 `VIDEO_OBSERVED` 전에는 승급하지 않는다 | 학습 종료 후 영상 증거 게이트 |
| G-D25 | 단일 GPU에서 학습·평가 case를 순차 실행하고 4,096 env 내부 벡터 병렬화만 사용한다. 하드웨어 최대 병렬 처리라고 주장하지 않는다 | 강좌 예제값·Default 실측은 있으나 확장 benchmark 없음 |
| G-D26 | package 검증이 완료됐으므로 새 서버 실행 `HOLD`를 해제한다. 실행 결과는 사용자 로그·회수 ZIP 전까지 `[미측정]`이다 | G-F30, 외부 실행 증거 경계 |

**LATEST NEXT:** `workspace/training/quadruped/go2_feet_air_time_020_v1.zip`을 서버 `/workspace/`에 업로드하고 검증된 한 줄 명령을 실행한다. 완료 뒤 `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`과 `.sha256`을 `workspace/_keep/`에 내려받는다. 두 파일의 로컬 검증 전에는 서버를 종료하지 않는다.

## 11. G-A007 PARTIAL ??? evaluator v2 ? 260901

### 11-a. ??? ??

| ID | ?? | ?? |
|---|---|---|
| G-F33 | candidate ??? `TRAIN_RC=0`?? model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`? ???? | PARTIAL ZIP `training/TRAIN_STATUS.txt`, `model_best.pt` |
| G-F34 | ??? `PARTIAL`, `RUNNER_RC=5`, telemetry 8/69, video 0/7?? G2 `combined_yaw_left`, seed 101 startup?? segmentation fault? ???? | PARTIAL `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `launcher.log` |
| G-F35 | v1 telemetry? fixed horizon?? hard process exit? ??? upstream Isaac Lab? `env.close()`? `simulation_app.close()` ??? ???? | v1 `go2_eval_telemetry.py`; Isaac Lab v2.3.1 upstream play L163-189 |
| G-F36 | v2 package? hard-exit AST call 0, graceful stop, case/video 3? bounded retry, stable launcher snapshot? ???? | `go2_feet_air_time_020_v2.VERIFICATION.md` |
| G-F37 | v2 ZIP SHA? `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`?? deterministic build?CRC?manifest 94/94?contract 6/6?`bash -n`? ???? | G-A008 verification |

### 11-b. ??

| ID | ?? | ?? |
|---|---|---|
| G-D27 | v1 runner ?? ???? `BUGGY_DO_NOT_REUSE`? ???? | hard exit? fail-fast ??? ????? ?? failure surface? ??? |
| G-D28 | reward? checkpoint? ??? ?? G-A008 v2? ??? ???? | ??? ?? ???? ??? ?? ?? ? evaluator startup?? ??? |
| G-D29 | v2 ?? ?? ? ??? `INTERNAL_GATE_INCONCLUSIVE`, ??? `VIDEO_UNKNOWN`, ?? ??? `OFFICIAL_RESULT_UNMEASURED`? | telemetry 8/69?video 0/7 |

**LATEST NEXT:** ?? v1 ??? v2? ??? ???? ???. v1 ???? ??? ??? ? `go2_feet_air_time_020_v2.zip`?? package ??? ???? `GO2_RESUME=1`? ?? checkpoint? case fingerprint? ?????. ???? ????.


## 12. 69-case 출처 감사와 H1·Go2 공통 승급 규칙 — 260902

### 12-a. 확인된 사실

| ID | 사실 | 근거 |
|---|---|---|
| G-F38 | 강좌·제공 가이드가 직접 정한 것은 Go2 G1~G7의 시나리오 범주·지형·가중치이며, `69-case`라는 총개수는 강좌 요구사항이 아니다. | `workspace/PRELIM_RL_GUID.md:60-70`, `go2_self_eval_registry.json` `source` |
| G-F39 | 69건은 내부 설계가 정한 G1 3, G2 7, G3 2, G4 2, G5 4, G6 4 case를 seed 101·202·303으로 반복한 66건과 G7 fixed seed 3건의 합이다. | `workspace/training/quadruped/config/go2_self_eval_registry.json` |
| G-F40 | case 격자, seed 101·202·303, 내부 임계값, 영상·worst-case 집계는 공식 evaluator의 공개 계약이 아니라 불확실성을 줄이기 위한 내부 설계다. | registry `official_unknowns`, `origin_audit` |
| G-F41 | 현재 G-A007은 내부 v1 proxy `21.77/70`이며, G7 중복과 G5 진행도 계산 결함 때문에 full-suite 승급 근거로 사용할 수 없다. | G-A007 결과 분석; G3/G7 동일 `steps.csv`, `go2_eval_telemetry.py` 진행도 감사 |

### 12-b. 결정

| ID | 결정 | 근거 |
|---|---|---|
| G-D30 | H1·Go2 모두 `조기중단 → 대표 평가 → 기체별 전체 평가` 3단계 비용 게이트를 사용한다. | 실패 후보에 전체 평가 비용을 쓰지 않기 위함 |
| G-D31 | 대표 평가는 각 기체 H1~H7/G1~G7에서 유효한 대표 case 1개씩을 seed 101·202·303으로 실행한다. | 시나리오 커버리지와 seed 안정성을 21건으로 먼저 확인 |
| G-D32 | 기체별 전체 평가 승급은 대표 평가 `시뮬레이션 proxy ≥60/70`, 모든 시나리오 survival proxy ≥0.95, tracking proxy ≥0.70, 3 seed 정상 완료, 필수 영상 중 치명적 이상 0건을 동시에 요구한다. | 사용자 결정 260902; 점수와 안정성을 분리하지 않음 |
| G-D33 | 승급 뒤에는 H1은 H1 전용 30-case, Go2는 evaluator를 수리한 뒤 Go2 전용 69-case를 실행한다. Go2 69-case를 H1에 복사하지 않는다. | 기체별 시나리오·동역학·registry가 다름 |
| G-D34 | G-A007은 `INTERNAL_SCREEN_FAIL`로 폐기하며 추가 장기학습·전체평가를 하지 않는다. 새 Go2 서버 실행 전 G5 진행도와 G7 DR evaluator를 먼저 수리한다. | 21.77/70 < 60/70, 계단 정체, evaluator 결함 |

**LATEST NEXT:** 로컬에서 Go2 G5 진행도를 per-env body-frame 적분으로 수정하고 G7을 G3와 다른 실제 DR 조건으로 만든 뒤, 6~8건 조기중단 및 21건 대표 평가가 동작하는 package test를 통과시킨다. 새 서버 학습은 그 전까지 `HOLD — evaluator 수리 전`이다.

## 13. G-A009 다음 단일변수 확정·evaluator 보정 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F42 | G-A007 `feet_air_time=0.20`은 G1 proxy `0.003553`으로 Default `0.003619`을 살리지 못했고, 보정 계단 순진행도 Default 약 `0.336m` 대비 약 `0.049m`였다. | G-A007 69 telemetry 재적분 |
| G-F43 | Pilot의 G1 proxy는 `0.892505`로 Default보다 크게 높았으며, Pilot의 남은 미분리 변경 중 G1에 가장 직접적인 항은 `track_lin_vel_xy_exp 1.0→1.2`다. | Default/Pilot paired report, reward source |
| G-F44 | G5 진행도 v2는 world spawn 위치가 아니라 env별 body-frame command 투영 속도를 적분한 뒤 중앙값을 사용한다. | `go2_eval_telemetry.py`, evaluator contract test |
| G-F45 | G7 v2는 `NCRC_EVAL_DR=1`에서 마찰·반발·base mass·joint reset 범위를 변경하며 G3와 다른 실행 fingerprint를 가진다. 이 범위는 내부 stress test이며 공식 evaluator 값이 아니다. | `go2_task/env_cfg.py`, G-A009 runner/tests |
| G-F46 | G-A009 package는 46 members, CRC·safe path·manifest 45/45, tests 9/9, `bash -n`, CRLF 0, deterministic SHA를 통과했다. | `go2_track_lin_vel_120_v1.VERIFICATION.md` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D35 | 다음 Go2 학습은 Default-01 from-scratch 계보에서 `track_lin_vel_xy_exp 1.0→1.2`만 바꾼 1,000 iter G-A009로 실행한다. | Pilot의 G1 개선 인과를 가장 먼저 분리하고 G-A007 과대 feet-air 후보를 반복하지 않음 |
| G-D36 | 유지값은 `feet_air_time=0.01`, `lin_vel_z_l2=-3.0`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`; seed 42, 4096 env를 고정한다. | 단일변수 인과 계약 |
| G-D37 | G-A009은 candidate 7 case + Default repaired-G7 1 case에서 조기중단하고, `INTERNAL_EARLY_KILL_PASS`일 때만 candidate 21 case로 확장한다. 69-case는 자동 실행하지 않는다. | 서버 비용 최소화와 60/70 승급 정책 |
| G-D38 | G-A009 결과 ZIP·SHA·필수 영상·telemetry·lineage를 로컬 검증하기 전 서버 종료 판정을 내리지 않는다. | 휘발성 서버 회수·영상 게이트 |

## 14. 범용 튜닝 엔진 전환 결정 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F47 | G-A009 ZIP의 소스 생성·압축·검증은 로컬 작업이므로 서버 GPU 학습시간을 늘리지 않는다. 현재 ZIP은 그대로 실행 가능하다. | package build/test는 `C:\dev\Nconnect`에서 완료; 서버 명령 미실행 |
| G-F48 | reward 값만 달라질 때 runner·builder·reporter를 복제하면 서버 비용보다 유지보수 비용·검증 반복·결함 재발 위험이 커진다. | G-A005~G-A009 package 계보 |
| G-F49 | 재현성에는 매 run의 source snapshot이 필요하지만, 이는 안정된 엔진이 실행 시 자동 복사하면 되며 실험마다 새 소스를 생성할 필요는 없다. | artifact source·manifest 계약 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D39 | G-A009은 이미 검증된 현 package로 실행하며 재포장 때문에 실행을 지연하지 않는다. | 재포장은 이번 서버 runtime을 줄이지 않고 새 결함 위험만 추가 |
| G-D40 | G-A010부터 `고정 engine ZIP + experiment.json` 구조를 사용한다. reward·seed·iter·env 수·평가 tier·case·영상·output contract는 JSON으로 주입한다. | 값 변경과 실행 기능 분리 |
| G-D41 | engine source는 evaluator 또는 schema 동작이 바뀔 때만 version bump·재검증한다. reward 값만 바뀌면 engine ZIP을 재생성하지 않는다. | 불필요한 소스·검증 반복 제거 |
| G-D42 | 결과 ZIP은 `engine_version`, engine SHA, experiment JSON 원문·SHA, 실제 env.yaml, model/policy lineage와 telemetry를 자동 포함한다. | JSON 오입력과 실행 artifact의 대응 보존 |

## 15. G-A009 회수·조기중단 판정 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F50 | G-A009 결과는 `RESULT_STATE=FULL`, `RUNNER_RC=0`, `TRAIN_RC=0`이며 outer SHA·CRC·manifest 125/125·필수 case·영상·lineage가 모두 검증됐다. | `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/VERIFICATION.json` |
| G-F51 | candidate model 식별자는 iter 900, SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`이며 policy actor tensor 8/8이 checkpoint와 일치한다. | result `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json` |
| G-F52 | tier 1 candidate는 `20.62741/70`, repaired baseline은 `17.53712/70`이지만 목표 G1 delta가 `-0.0000663`으로 사전 기준 `+0.05`에 미달했다. | `reports/TIER1_DECISION.json` |
| G-F53 | G-A009은 runner 사전등록 분기상 `INTERNAL_EARLY_KILL_FAIL`; candidate G1·G2·G3·G4·G5·G7은 내부 시나리오 기준 미달이고 G6만 내부 시나리오 기준을 충족했다. | candidate `SELF_EVAL_REPORT.json` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D43 | 필수 회수물 누락이 없으므로 G-A009 서버는 종료한다. | 휘발성 서버 종료 게이트 충족 |
| G-D44 | `track_lin_vel_xy_exp=1.20` 후보는 대표 3-seed·69-case·장기학습으로 승급하지 않는다. | 주목적 G1 개선 실패와 `INTERNAL_EARLY_KILL_FAIL` |
| G-D45 | 다음 학습값은 G-A009 결과와 남은 Pilot 단일변수를 대조한 뒤 고정 engine+JSON 계획으로 확정한다. | 실패 후보 반복과 실험별 소스 재생성 방지 |

## 16. G-A009 분석·영상 판독·다음 값 확정 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F54 | G-A009 총 proxy 증분 `+3.09028/70` 중 G6 기여가 `+2.41007/70`(`77.99%`)이며 목표 G1 기여는 `-0.00070/70`이다. | `TIER1_DECISION.json`, scenario weight 재계산 |
| G-F55 | G1 영상 499 frames·50 fps·9.98초를 직접 판독했으며 네 환경 모두 전진 명령 대비 시작 격자 부근에 머물렀다. | G1 MP4·contact sheet, video SHA `9d811701…c6cdb` |
| G-F56 | 학습 best reward `16.2977@900`과 training-terrain base-contact `6.52%`는 고정 G1 점수가 아니며, G1 evaluator 평균속도는 `0.02748 m/s`, RMSE는 `1.18714`다. | `candidate_training.log`, candidate `SELF_EVAL_REPORT.json` |
| G-F57 | G-A009 후보의 내부 최대 감점은 G1 `10.46/70`, 다음 G5 `10.16`, G3 `9.49`다. | `weight×(1-proxy)×70` 재계산 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D46 | G-A009을 `ANALYZED/REPORTED`, G1 `VIDEO_OBSERVED`, 최종 `INTERNAL_EARLY_KILL_FAIL`로 닫는다. | artifact·정량·영상 증거 계층 완결 |
| G-D47 | G-A010은 Default-01 from-scratch에서 `lin_vel_z_l2 -3.0→-2.0`만 바꾼 1,000 iter로 한다. | feet-air·track-linear 단독 실패 뒤 남은 미분리 항 중 강좌 1k 전진 관찰 근거와 G1/G3/G5 정보가치가 가장 큼 |
| G-D48 | G-A010이 G1 `+0.05` 기준을 실패하면 G-A011 `ang_vel_xy_l2 -0.08→-0.05` 단독으로 간다. 둘 다 실패한 뒤에만 상호작용 실험을 검토한다. | 단일변수 인과 우선, Pilot 4변수 조합 즉시 반복 금지 |
| G-D49 | 새 서버 실행 전 고정 engine ZIP과 G-A010 `experiment.json`을 로컬에서 schema·contract·CRLF·`bash -n`·결과 contract까지 검증한다. | 서버는 실행·회수에만 사용하고 실험별 소스 재생성을 제거 |

## 17. G-A010 고정 engine·JSON 실행 준비 완료 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F58 | `go2_tuning_engine_v1.zip`은 6,415,805 bytes, 34 members, SHA `4489bef429a38a145763b5af8c4d55081c0a10f501a9b552194f111116f98a5a`이며 deterministic rebuild 2/2·CRC·manifest 33/33·unsafe path 0을 통과했다. | `go2_tuning_engine_v1.VERIFICATION.md` |
| G-F59 | G-A010 spec SHA는 `fa0bb3b749aa4412cb5023807cc895db08f416e626730ee34477c516bc6ec425`이며 Default reward/model/env 고정과 `lin_vel_z_l2 -3→-2` 단일 변경을 validator·contract가 확인했다. | `G_A010_lin_vel_z_m2.json`, contract 14/14 |
| G-F60 | engine ZIP에는 G-A010 spec이 없으며, 추출된 engine만으로 별도 JSON을 읽어 candidate/default source·registry·baseline을 materialize할 수 있다. | extracted-engine self-contained test |
| G-F61 | runner는 FULL/PARTIAL 모두 engine/spec identity, training artifact, 완료 telemetry, G1 영상, policy lineage를 단일 결과 ZIP과 SHA companion으로 자동 패키징한다. | generic runner 정적 계약·`bash -n` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D50 | G-A010은 고정 engine ZIP과 별도 JSON 두 파일만 업로드하고 검증된 한 줄 명령으로 실행한다. | 실험별 소스 복제 제거와 사용자 서버 작업 최소화 |
| G-D51 | 결과 회수 경로는 `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256`로 고정한다. | 한 번의 다운로드 묶음과 종료 게이트 자동화 |
| G-D52 | 확인 자원은 단일 RTX 5080 16,303MiB뿐이므로 4096-env 학습은 하나만 실행한다. | 동시 2개 학습의 peak VRAM 근거 없음 |

**LATEST NEXT:** engine ZIP과 G-A010 JSON을 서버 `/workspace/`에 업로드해 한 줄 실행한다. 완료 뒤 결과 ZIP 2종을 로컬 `workspace/_keep/`에 회수하고 artifact·영상·tier-1을 검증한다.

## 18. G-A010 최초 server preflight 실패와 v1.1 복구 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F62 | engine v1.0은 서버에 없는 bare `python3`를 line 17에서 호출해 즉시 종료됐고 `KEEP_DIR_NAME` 오류는 그 연쇄 결과다. tmux·training 시작 출력은 없어 iteration 소비 0이다. | 사용자 제공 원본 shell 출력 |
| G-F63 | v1.1은 모든 config Python 호출을 `/workspace/IsaacLab/isaaclab.sh -p`로 전환했다. | runner source·contract |
| G-F64 | v1.1 engine SHA는 `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`, colocated spec SHA는 `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`다. | local SHA·verification report |

| ID | 결정 | 이유 |
|---|---|---|
| G-D53 | v1.0은 `BUGGY_DO_NOT_REUSE`; v1.1만 서버에 다시 올린다. | 검증된 서버 환경 불일치 제거 |
| G-D54 | engine ZIP과 spec JSON은 로컬 `workspace/training/quadruped/upload/<EXPERIMENT_ID>/current/` 한 폴더에 함께 둔다. | 사용자 이동 비용 최소화와 현재본 오선택 방지 |

**LATEST NEXT:** `upload/G-A010/current/`의 v1.1 ZIP과 JSON을 `/workspace/`에 업로드하고 v1.1 한 줄 명령을 실행한다.

## 19. Go2 업로드 폴더·release 이력 체계 확정 — 260902

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F65 | G-A010 사용자 업로드 파일은 `workspace/training/quadruped/upload/G-A010/current/`에 함께 배치됐고 원본과 SHA가 일치한다. | `UPLOAD_MANIFEST.json`, copy 후 SHA 검증 |
| G-F66 | v1.1 release snapshot은 `upload/G-A010/history/20260902_engine-v1.1/`에 보존된다. | history directory·manifest |
| G-F67 | ledger는 v1.0을 `WITHDRAWN_BUGGY_DO_NOT_REUSE`, v1.1을 `ACTIVE_ARTIFACT_VERIFIED`로 분리한다. | `upload/G-A010/UPLOAD_HISTORY.tsv` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D55 | 이후 Go2 서버 입력은 quadruped 루트가 아니라 `upload/<EXPERIMENT_ID>/current/`에서만 사용자에게 안내한다. | 현재본·폐기본 혼동과 파일 이동 비용 방지 |
| G-D56 | release 발행은 `tools/publish_go2_upload_bundle.py`로 current/history/SHA/ledger를 함께 갱신한다. | 반복 가능한 이력관리와 복사 무결성 보장 |

**LATEST NEXT:** `workspace/training/quadruped/upload/G-A010/current/`에서 ZIP과 JSON 두 파일을 `/workspace/`에 업로드한 뒤 `GO2_G_A010_RUN_GUIDE.txt`의 v1.1 명령을 실행한다.

## 20. G-A012 동결 Pilot-01 자세 게이트 69-case 기준선 회수·분석 — 260903

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F68 | `GO2_PILOT_V2_BASELINE_RESULT.zip` 외부 SHA `a722e9e740a2818cdce316c6fb901c92f6180a600c06b37da6609a66ed95aa9a`가 서버 sidecar와 일치하고 manifest 448/448이 OK다. | 로컬 `sha256sum -c` |
| G-F69 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 69/69, 영상 7/7, `TRAINING=none`, `EVALUATOR=posture_gate_v2`. | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt` |
| G-F70 | 동결 Pilot-01의 내부 simulation proxy는 worst-case 집계 `33.79311/70`(fraction `0.482759`), 평균 집계 `45.03099/70`이며 `INTERNAL_GATE_FAIL`이다. | `go2_fixed_eval_report.build_policy`, `reports/evidence/go2_pilot_v2_baseline_260903/` |
| G-F71 | 가중 실점 순위는 G3 `12.97` > G5 `10.50` > G4 `4.95` > G7 `3.61` > G2 `2.60` > G1 `1.13` > G6 `0.45`(/70)다. | 같은 report |
| G-F72 | 블록별로 평지(가중 0.40) `23.82/28`, 지형(가중 0.60) `9.97/42`다. | 같은 report |
| G-F73 | G3·G5 실점의 지배 인자는 생존이다. `rough_lateral` 최대 23/32 낙상, `stairs_15_down` 32/32 전량 낙상이며 tracking은 G3에서 `0.78~0.80`으로 유지된다. | per-case 표 |
| G-F74 | G4는 낙상하지 않고(survival `.97~1.00`) 오르막 20초 진행이 `1.86~2.35m`에 그치는 추종 실점이다. | per-case 표 |
| G-F75 | **`dr_seed_*`의 `steps.csv`가 같은 seed의 `rough_forward`와 SHA-256까지 동일하다. G7은 독립 측정이 아니다.** | seed 101 `f9e76807…`, 202 `df1f7589…`, 303 `f262778a…` |
| G-F76 | 실행 비용은 로그 타임스탬프 `06:01:11Z→06:30:04Z` 약 29분이며 eval 순수 wall 합계는 1,391초다. | `launcher.log`, 69개 `summary.json` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D57 | G-A012를 `ARTIFACT_VERIFIED`로 확정하고 서버 종료를 승인한다. | FULL·RC=0·manifest 448/448·69/69·7/7, 서버에만 있는 산출물 없음(`TRAINING=none`) |
| G-D58 | 사전등록(§15-c)에 따라 다음 단일 변수는 **생존을 직접 겨냥하는 reward 한 항**이다. 가중 실점 1·2위(G3·G5)의 실점 인자가 모두 생존이기 때문이다. | 사후 재협상 없는 사전등록 규칙 |
| G-D59 | 실행 전 `undesired_contacts`·`termination_penalty`의 env 정의 여부를 10-iter smoke test로 먼저 확인한다. | 주석이 미정의 가능성을 명시; 학습 시간 낭비 방지 |
| G-D60 | G7 수치는 결함 수정 전까지 G3와 별개 증거로 인용하지 않는다. 다음 evaluator에서 DR case를 수정한다. | G-F75 `AUDIT_FINDING` |

**LATEST NEXT:** (§21에서 갱신됨)

## 21. G-A013 생존 다이얼 확정과 tuning engine v1.2 — 260903

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F77 | **Go2 env에는 `undesired_contacts`가 `null`(비활성)이고 `termination_penalty` 항은 존재하지 않는다.** 계획이 지목했던 생존 레버 두 개는 실재하지 않는다. | 서버 학습 산출 `.../2026-09-01_19-18-17/params/env.yaml`의 `rewards:` 전체 덤프 |
| G-F78 | 같은 env.yaml의 reward 항은 11개이고 그중 `flat_orientation_l2`(weight `0.0`)와 `dof_pos_limits`(weight `0.0`)만 정의돼 있으면서 미사용이다. | 같은 파일 |
| G-F79 | G-A010은 가중 총점 `+2.26/70`(17.54→19.79), G3 survival `+0.094`, G6 survival `+0.344`를 얻고도 `target_G1_improvement_below_0.05` 한 가지 이유로 조기 종료됐다. | `workspace/_keep/go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json` |
| G-F80 | Go2 1,000 iter 학습의 실측 비용은 `3.48초/iter`, 총 `00:59:11`이다. | G-A010 `launcher.log` rsl_rl 최종 요약 |
| G-F81 | tuning engine v1.2(engine_version `1.1.0`)를 빌드했다. SHA `9e79a9dff6a9f6a7636692df7780634f0d1ffe47372ef703e8c86c8fbdeb640e`, 6,419,244 B, 34 members, 내부 manifest 33/33. | `go2_tuning_engine_v1_2.VERIFICATION.md` |
| G-F82 | G-A013 experiment JSON SHA `2e255c1e18165f2be7e17f09893503262a1c846998d12f20cb7ddbd9273cecb2`. 추출본에서 `validate` VALID, `materialize` 결과가 candidate `-1.0`·default `0.0`. | 로컬 추출 후 실행 |
| G-F83 | `tools/` 계약 테스트 44/44 통과. 구 builder 3종은 template의 6번째 키 추가로 실패했으나 동일값(`0.0`) 키를 추가해 복구했고, 완료된 실험의 학습 조건은 변하지 않는다. | `python -m unittest discover -s tools` |
| G-F84 | 업로드 정본은 `upload/G-A013/current/`에 발행됐고 4개 파일 SHA가 전부 OK다. release는 `history/20260903_engine-v1.2/`에 불변 보존된다. | `publish_go2_upload_bundle.py`, `sha256sum -c` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D61 | **G-D59를 대체한다.** 10-iter smoke test를 실행하지 않는다. 두 항의 부재는 이미 서버 `env.yaml`로 실측됐으므로 서버 시간을 쓸 이유가 없다. | G-F77 — 측정이 이미 존재한다 |
| G-D62 | 단계 C의 단일 변수를 `flat_orientation_l2` `0.0 → -1.0`으로 확정한다. | G-F77·G-F78 — 실재하면서 미사용인 유일한 자세·생존 다이얼. G-D58(생존 항)의 유일한 실행 가능 후보 |
| G-D63 | tier-1 게이트 목표를 G1 고정에서 실험별 지정(G1~G7)으로 바꾸고 G-A013은 G3를 목표로 한다. | G-F79 — 목표 고정이 총점을 올린 후보를 잘못 죽였다 |
| G-D64 | 엔진 archive를 `v1_2`로 개명한다. 구 `v1_1`은 `SUPERSEDED_DO_NOT_REUSE`이며 버전 교차 업로드는 validate 단계에서 즉시 실패한다. | 학습 시작 전 실패가 학습 후 오염보다 싸다 |
| G-D65 | `quadruped_rewards.py`에 `flat_orientation_l2`를 활성 키(⑥)로 올린다. 파일 안내가 "줄 추가/삭제/주석 자유"를 명시하므로 규정 제2조 5항 위반이 아니며, 값은 default와 같은 `0.0`으로 둔다. | 렌더러가 주석이 아닌 실제 키를 요구; 기본값 동일이라 기존 실험 재현성 유지 |

**LATEST NEXT:** `workspace/training/quadruped/upload/G-A013/current/`의 두 파일을 `/workspace/`에 올리고 `SERVER_SESSION_RUNBOOK.md` G-A013 절 3단계의 한 줄을 실행한다. 결과 ZIP과 `.sha256`을 `workspace/_keep`에 내려놓으면 지시 없이 분석에 착수한다.

## 22. G-A013 결과 회수·분석과 게이트 결함 발견 — 260903

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F85 | `GO2_FLAT_ORIENTATION_M1_RESULT.zip` 외부 SHA `cb3c93352c241bfd963a0bcf3ff722dae7ee0db0faff1f9322e0717d4ed6cec5`가 서버 sidecar와 일치하고 ZIP CRC 무결, 내부 manifest 128/128 OK다. | 로컬 `sha256sum -c`, `unzip -t` |
| G-F86 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 후보 7/7·기준 7/7, 영상 1/1(`G1_forward_fast_seed_101.mp4` 1,678,333 B), 정책 계보 `ACTOR_TENSORS_MATCH`(8/8). | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json` |
| G-F87 | 단일 변수는 실제로 적용됐다. 서버 `training/env.yaml`에 `flat_orientation_l2: weight -1.0`이 기록됐고 후보 model SHA는 `676cc1cb…b12e1c`다. | `training/env.yaml:884-887`, `evaluation/candidate/identity.json` |
| G-F88 | `train.py` 리포트의 "보상 변화: (기본값과 동일)" 줄은 참가자 리포트가 6번째 키를 모르기 때문이며, IsaacLab에 전달된 가중치와 무관하다. | `logs/candidate_training.log` vs `training/env.yaml` |
| G-F89 | G-A013 판정은 `INTERNAL_EARLY_KILL_FAIL`, 총점 `−1.4277880975157924/70`(기준 `17.13207`, 후보 `15.70428`)이다. | `reports/TIER1_DECISION.json` |
| G-F90 | 시나리오별 생존 Δ는 G3 `+0.15625`, G7 `+0.25`, G2 `−0.1875`, G6 `−0.125`, G4 `−0.3125`, G5 `−0.3125`다. 부호가 지형 조건에 따라 갈린다. | 같은 파일 |
| G-F91 | G-A013은 **지정 시나리오 목표(G3 proxy Δ `+0.0608` > `0.05`)를 통과한 유일한 실험**이면서 총점은 유일하게 후퇴한 실험이다. | 같은 파일 |
| G-F92 | 반대로 총점을 올린 두 실험은 지정 시나리오 절만으로 조기 종료됐다. G-A011 `track_lin_vel_xy_exp` 1.0→1.2는 `+3.0902846/70`에 생존 후퇴 0건, G-A010 `lin_vel_z_l2` −3.0→−2.0은 `+2.2571599/70`에 G7 `−0.03125`(허용 내)뿐이다. | `go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json`, `go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json` |
| G-F93 | `feet_air_time` 0.01→0.20은 69-case·3seed 스위트에서 `+3.8656/70`(기준 `17.9070`, 후보 `21.7726`)이며 모든 시나리오의 생존 Δ ≥ `−0.02`, 추종 Δ ≥ `−0.05`, seed Δ ≥ `−0.02`다. 탈락 사유는 `g5_proxy_delta_at_least_plus_0_03` 하나뿐이다. | `go2_feet_air_time_020_v1/reports/GO2_FEET_AIR_TIME_020_SCREENING_REPORT.md` |
| G-F94 | 엔진 v1.3(`engine_version 1.2.0`) SHA-256 `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a`, 12,781,997 B, 50 멤버, 내부 manifest 49/49 OK. | `tools/build_go2_tuning_engine.py`, `go2_tuning_engine_v1_3.VERIFICATION.md` |
| G-F95 | G-A015 실험 사양 `G_A015_pilot_feet_air_time_035.json` SHA-256 `f2ac4d7fb68da95ec982c708f95664a31ec46af8d38d7a9721dbc29c8c8ca693`, 2,579 B. 추출본에서 `validate` VALID(`baseline=Pilot-01`), `materialize` candidate `feet_air_time 0.35`·기준선 `0.2`, 나머지 5개 동일. | 로컬 end-to-end 검증 |
| G-F96 | 엔진 ZIP은 두 동결 기준선의 checkpoint·env·seed 101 tier-1 증거를 모두 싣는다. Pilot-01 쪽은 7/7 case가 `VERIFIED_G_A012`로 캐시돼 기준선 재평가 비용이 0이다. | `baseline/pilot/`, `baseline/default/` |
| G-F97 | 계약 테스트 47/47 OK. Default-01 기준 실험도 같은 엔진에서 여전히 materialize 된다(회귀 없음). | `python -m unittest discover -s tools` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D66 | G-A013을 `ARTIFACT_VERIFIED`로 확정하고 서버 종료를 승인한다. 가설(`flat_orientation_l2` 강화가 생존을 올린다)은 **기각**한다. | FULL·RC=0·manifest 128/128·telemetry 7/7·영상 1/1, 서버에만 있는 산출물 없음 |
| G-D67 | 사전등록된 후속 **G-A014(`flat_orientation_l2` −2.0)를 취소**한다. | 실패 방식이 과소가 아니라 부호 오류다(G-F90). +20° 경사·계단에서는 몸통이 지형을 따라 기울어야 하는데 이 항이 정확히 그것에 벌점을 매긴다. 해로운 방향으로 가중치를 두 배로 미는 실행은 근거가 없다 |
| G-D68 | tier-1 게이트를 **가중 총점 기준**으로 교체한다(`min_total_points_delta` 필수·양수, `target_scenario`는 관측값으로 강등, 판정 `schema_version` 3). | 측정된 4건 전부에서 고정 시나리오 절과 목적함수의 부호가 반대였다(G-F91·G-F92). 규정이 채점하는 값은 가중 총점이다. 생존 가드는 유지해 G-A013 형태를 계속 차단한다 |
| G-D69 | 동결 기준선을 **Pilot-01로 전환**한다. 엔진은 Default-01·Pilot-01 둘 다 싣고 실험이 선택한다. | 같은 69-case 스위트에서 Default-01 `17.90697/70` vs Pilot-01 `33.79311/70`(G-F70). Default-01 기준 스크리닝은 제출할 일이 없는 정책을 최적화한다. 과거 실험과의 비교 가능성보다 실제 제출 후보 개선이 우선이다 |
| G-D70 | 다음 단일 변수는 **`feet_air_time` 0.20 → 0.35**(G-A015)다. | 사전등록 §15-c의 출력은 G3(`12.97/70`)이고 G3·G5 실점 인자는 모두 생존이다. `feet_air_time`은 험지와 계단에 동시에 작용하는 유일한 다이얼이며, 측정된 곡선이 있는 유일한 변수다(G-F93) |
| G-D71 | `quadruped_rewards.py`는 Pilot-01 설정 정본이다. 로컬에서 이 파일의 값을 Default로 되돌리지 않는다. | 260903에 검증 중 `feet_air_time`을 0.2→0.01로 잘못 되돌려 `test_default_staging_changes_only_four_pilot_lines`가 실패했다. 엔진은 이 파일을 템플릿으로 렌더하므로 파일 값이 실행에 영향을 주지는 않으나, Pilot-01 정본으로서의 의미가 훼손된다 |

**(마감)** G-A015는 실행·회수·검증 완료. 후속은 §23.

## 23. G-A015 결과 회수·분석과 `feet_air_time` 상한 확정 — 260904

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F98 | `GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip` 외부 SHA `8d8bb89b85ab4428ae499d19bb334528e787cd7ca28b24da2825edb389ce4a7f`가 서버 sidecar와 일치하고 ZIP CRC 무결, 내부 manifest 128/128 OK다. | 로컬 `sha256sum -c`, `unzip -t` |
| G-F99 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 후보 7/7·기준 7/7, 영상 1/1(`G1_forward_fast_seed_101.mp4` 2,205,383 B), 정책 계보 `ACTOR_TENSORS_MATCH`(8/8). 서버가 기록한 `ENGINE_ARCHIVE_SHA256`·`EXPERIMENT_SHA256`은 업로드본과 동일하다. | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json` |
| G-F100 | 단일 변수는 실제로 적용됐다. 서버 `training/env.yaml`에 `feet_air_time: weight 0.35`, 나머지 5개는 Pilot-01 값(1.2 / −2.0 / −0.05 / −0.01 / 0.0) 그대로다. 후보 model SHA `994562a1…a6c909`. | `training/env.yaml:854-887`, `evaluation/candidate/identity.json` |
| G-F101 | 기준선 arm은 동결 Pilot-01(`c4d78adf…f89af8d`)이고 tier-1 7 case 중 6개가 `SOURCE=VERIFIED_G_A012` 캐시, `dr_seed_101`만 신규 실행이다. tier-1(seed 101) 기준선 총점은 `46.49124/70`. | `evaluation/baseline_tier1/cases/*/STATUS.txt`, `reports/TIER1_DECISION.json` |
| G-F102 | G-A015 판정은 `INTERNAL_EARLY_KILL_FAIL`, 총점 `−30.121932/70`(기준 `46.49124`, 후보 `16.36931`)이다. 발화한 게이트는 총점 절과 G1·G3·G4·G5·G7 생존 절 다섯이다. | `reports/TIER1_DECISION.json` |
| G-F103 | 후보의 시나리오별 생존은 G2 `1.000`, G6 `0.938`, G7 `0.125`, G1 `0.031`, G3·G4·G5 `0.000`이다. 평지·저속만 살아남고 속도·험지·경사·계단은 전멸이다. | `evaluation/candidate/SELF_EVAL_REPORT.md` |
| G-F104 | 실패 방식은 전복이 아니라 **주저앉음**이다. 후보 `dr_seed_101`의 `proj_grav_z` 평균 −0.964(기울어진 프레임 0.0%)인데 `height_rel` 평균 0.183 m(기준선 0.303 m), 0.20 m 미만 프레임 72.5%(기준선 2.8%), 속도 0.121(기준선 0.246)이다. | 양쪽 `steps.csv` 32,000행 집계 |
| G-F105 | 7개 case 전부에서 같은 서명이 나온다. `height_rel` 평균은 `slope_plus_20` 0.154 ~ `push_pos_x` 0.347이고, `proj_grav_z`는 모든 case에서 −0.87 이하로 몸통은 수평을 유지한다. | 후보 case별 `steps.csv` |
| G-F106 | 계단(G5)에서 후보는 32 env 중 **31개가 base contact로 종료**됐고(기준선 2개) 전진 거리는 `5.696 m → 1.888 m`다. | `cases/seed_101/stairs_15_up/summary.json` 양쪽 |
| G-F107 | 엔진 1.2.0의 가중 총점 게이트는 설계대로 작동했다. 파국적 후보를 tier-1(약 1시간)에서 죽였고 seed 202·303 대표평가를 실행하지 않았다. | `evaluation/candidate/cases/`에 seed_101만 존재 |
| G-F108 | G-A016 사양 `G_A016_pilot_ang_vel_xy_m015.json` SHA-256 `0eadb9a7a72dbbaaf3618faf7e07482ba0309054bc3bfaa9fccc149882e11f76`, 2,633 B. 추출본에서 `validate` VALID(`baseline=Pilot-01`), `materialize` 후보 `ang_vel_xy_l2 −0.15`·기준선 `−0.05`, 나머지 5개 동일. | 로컬 end-to-end 검증 |
| G-F109 | 엔진 ZIP은 재빌드해도 `dfbe47ae…877b1a`로 동일하다. G-A016은 G-A015와 **바이트 동일한 엔진**을 쓴다. | 계약 테스트가 재빌드 후 출력한 SHA |
| G-F110a | 표기 결함(무해): 기준선 arm의 `evaluation/baseline_tier1/identity.json`은 Pilot-01을 쓸 때도 `"policy":"default"`로 적힌다. 런타임 디렉터리 이름이 arm 고정(`default`/`candidate`)이기 때문이다. 실제 정체는 같은 파일의 `model_sha256`이 `c4d78adf…f89af8d`(Pilot-01)로 못박아 증명한다. | `evaluation/baseline_tier1/identity.json`, `meta/ENGINE_METADATA.json` |
| G-F110 | 계약 테스트 50/50 OK. G-A015의 실측 7시나리오 수치를 게이트에 재생하는 회귀 테스트가 추가됐다. | `python -m unittest discover -s tools` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D72 | G-A015를 `ARTIFACT_VERIFIED`로 확정하고 **서버 종료를 승인**한다. 가설(`feet_air_time` 0.35가 험지·계단 생존을 올린다)은 **기각**한다. | FULL·RC=0·manifest 128/128·telemetry 7/7·영상 1/1, 서버에만 있는 산출물 없음 |
| G-D73 | **`feet_air_time`의 상한을 0.20으로 확정**한다. 0.28 재탐색은 실행하지 않는다. | 사전등록 §18-e의 두 분기가 동시 발화했고, 더 좁고 구체적인 **생존 절이 우선**한다. 실패가 −1 수준의 후퇴가 아니라 보행 붕괴(G4 생존 −1.000)이므로 0.20~0.35 구간을 더 쪼갤 근거가 없다 |
| G-D74 | 분기 충돌 시 **생존 절 > 총점 절** 우선 규칙을 캠페인 표준으로 못박는다. | 두 절이 동시에 발화할 수 있다는 사실이 G-A015에서 처음 드러났다. 사후에 유리한 분기를 고르는 것을 막으려면 우선순위를 문서에 남겨야 한다 |
| G-D75 | 다음 단일 변수는 **`ang_vel_xy_l2` −0.05 → −0.15**(G-A016)다. 기준선은 동결 Pilot-01 그대로. | 실점 2순위 G5(`10.50/70`)의 인자는 생존이고, 계단 낙상은 몸통 pitch·roll 진동에서 시작한다. ④는 그 각속도에 직접 벌점을 매기는 유일한 다이얼이며 Pilot-01에서 미측정이고 기존 측정과 모순되지 않는다. ③ `lin_vel_z_l2` −2.5 안은 G-A010 실측(`+2.2572/70`)과 방향이 반대라 제외 |
| G-D76 | 엔진은 v1.3(`1.2.0`)을 **그대로 재사용**한다. | 게이트는 이번 회차에서 설계대로 작동했다(G-F107). 결과 해석을 위해 엔진을 손댈 이유가 없고, 바이트 동일 재사용은 회차 간 비교 가능성을 지킨다 |

**LATEST NEXT:** `workspace\training\quadruped\upload\G-A016\current\` 2파일 업로드 → 실행 →
`workspace\_keep`로 회수. 절차 정본은 `SERVER_SESSION_RUNBOOK.md`의 **G-A016** 절.

**(마감)** G-A016은 실행·회수·검증 완료. 후속은 §24.

## 24. G-A016 결과 회수·분석과 G-A017 준비 — 260904

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F111 | `GO2_PILOT_ANG_VEL_XY_M015_RESULT.zip` 외부 SHA `84f483a6ba04fc0536ea22fbe824add29cedf49c367c77b7801e52db76de1844`가 서버 sidecar와 일치하고 ZIP CRC 무결, 내부 manifest 128/128 OK다. | 로컬 `sha256sum -c`, `zipfile.testzip` |
| G-F112 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 후보 7/7·기준 7/7, 영상 1/1(`G1_forward_fast_seed_101.mp4` 1,834,069 B), 정책 계보 `ACTOR_TENSORS_MATCH`(8/8). `training/env.yaml`은 `ang_vel_xy_l2 -0.15`만 바뀌고 나머지 5개(`feet_air_time 0.2`, `lin_vel_z_l2 -2.0` 포함)는 Pilot-01 값 그대로다 — 단일 변수 원칙 유지 확인. | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json`, `training/env.yaml` |
| G-F113 | G-A016 판정은 `INTERNAL_EARLY_KILL_FAIL`, 총점 `−45.115544/70`(기준 `46.49124`, 후보 `1.37570`)이다. G1~G7 **전 시나리오**의 생존이 0.10 넘게 후퇴했다(G1 `−1.000`, G2 `−1.000`, G3 `−0.8125`, G4 `−1.000`, G5 `−0.71875`, G6 `−0.78125`, G7 `−0.90625`). G-A015보다 넓고 심각하다. | `reports/TIER1_DECISION.json` |
| G-F114 | 실패 방식은 전복이 아니라 **학습 극초반(iter ~100~150)에 고착된 전역 동결**이다. 학습 로그에서 `track_lin_vel_xy_exp`는 iter 150 근처 `0.24`에서 정체해 남은 850 iteration 동안 개선되지 않았고, `ang_vel_xy_l2` 페널티는 `−0.54→−0.07`로 계속 줄었다. 평가 시계열(`forward_fast`, 명령 vx 1.2m/s)은 t=0.02s `height_rel 0.398`에서 t=1.02s `0.177`로 반토막, 이후 999 스텝 내내 `height_rel≈0.12~0.13`·`speed_xy≈0` 고정, `proj_grav_z`는 `−0.999→−0.81`로 서서히 안정(쓰러짐 아님)이다. | `logs/candidate_training.log`, `evaluation/candidate/cases/seed_101/forward_fast/steps.csv` |
| G-F115 | G-A017 사양 `G_A017_pilot_track_lin_vel_xy_140.json` SHA-256 `824753950d00bcddd9c4647b641a6b0f37632ecafc7064fd5d65bab68ee5f0b4`, 2,978 B. 추출본에서 `validate` VALID(`baseline=Pilot-01`), `materialize` 후보 `track_lin_vel_xy_exp 1.4`·기준선 `1.2`, 나머지 5개 동일. | 로컬 end-to-end 검증 |
| G-F116 | 엔진은 재빌드해도 `dfbe47ae…877b1a`로 동일하다. G-A017은 G-A015·G-A016과 **바이트 동일한 엔진**을 쓴다. 계약 테스트 실행 시 이번 사양 추가와 무관한 기존 실패(대형 원본 파일 미보유로 인한 재빌드 테스트, G-F94 이후 알려진 상태) 6/7건만 재현되고 엔진·게이트 계약은 전부 통과한다. | `python -m unittest discover -s tools` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D77 | `ang_vel_xy_l2` 다이얼을 **완전히 기각**한다. 더 작은 폭(예: −0.10) 재탐색은 실행하지 않는다. | 사전등록 §19-d 3행(G5 생존 후퇴 `0.71875` > 0.10) 발화. 붕괴가 iter 150 안에 이미 고착됐다는 근거(G-F114)로 볼 때 더 작은 폭도 같은 국소최적해 함정에 빠질 위험이 크고, §19-d 2행(생존 후퇴 허용 내) 조건은 발화하지 않았다 |
| G-D78 | 다음 단일 변수는 **`track_lin_vel_xy_exp` 1.2 → 1.4**(G-A017)다. 기준선은 동결 Pilot-01 그대로, 엔진은 v1.3(1.2.0) 바이트 동일 재사용. | 실점 3순위 G4(경사, `4.95/70`)의 실점 인자는 순수 추종(`tracking_proxy 0.5533`, 생존은 이미 `1.0`)이다. 남은 미검증 reward 항은 `track_lin_vel_xy_exp`·`action_rate_l2` 뿐이고, G4 실점과 직접 연결되는 것은 전자뿐이다. `+0.2`는 G-A011이 이미 안전을 확인한 것과 같은 폭으로, G-A015·G-A016의 "3배 도약" 패턴을 반복하지 않는다 |

**LATEST NEXT:** `workspace\training\quadruped\upload\G-A017\current\` 2파일 업로드 →
실행 → `workspace\_keep`로 회수. 절차 정본은 `SERVER_SESSION_RUNBOOK.md`의 **G-A017** 절.

**(마감)** G-A017은 실행·회수·검증 완료. 후속은 §25.

## 25. G-A017 결과 회수·분석과 G-A018 준비 — 260904

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F117 | `GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip` 외부 SHA `7b056d0e7f36e421ebbddd79b117be8a5d75dc309c7ad8a8dbe6d8066cf521ab`가 서버 sidecar와 일치, ZIP CRC 무결(129 멤버 OK). | 로컬 `hashlib.sha256`, `zipfile.testzip` |
| G-F118 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 후보 7/7·기준 7/7, 영상 1/1(`G1_forward_fast_seed_101.mp4`), 정책 계보 `ACTOR_TENSORS_MATCH`(8/8). `training/env.yaml`은 `track_lin_vel_xy_exp 1.4`만 바뀌고 나머지 5개(`feet_air_time 0.2`, `lin_vel_z_l2 -2.0`, `ang_vel_xy_l2 -0.05` 포함)는 Pilot-01 값 그대로다. | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json`, `training/reward_only.diff` |
| G-F119 | G-A017 판정은 `INTERNAL_EARLY_KILL_FAIL`이지만 총점은 실제로 개선됐다: 기준 `46.49124/70` → 후보 `50.19916/70`(`+3.70792`). Pilot-01 동결 뒤 처음으로 총점이 오른 회차다. 발화한 게이트는 `G4_survival_regressed_over_0.1` 하나뿐이다. | `reports/TIER1_DECISION.json` |
| G-F120 | G4의 생존은 `1.0 → 0.78125`(`-0.21875`)로 후퇴 상한(0.10)의 두 배를 넘었다. 같은 시나리오에서 추종은 `0.5533 → 0.7286`(`+0.1752`, 요구 임계 0.70 육박)로 크게 개선됐다. 나머지 6개 시나리오는 생존이 유지되거나 개선됐다(G3 survival `+0.09375`, G7 survival `+0.0625`). | `reports/TIER1_DECISION.json` scenario_deltas, `evaluation/candidate,baseline_tier1/SELF_EVAL_REPORT.json` |
| G-F121 | 사전등록 분기(24-e)는 G3·G5를 취약 후보로 지목했지만 실제 후퇴는 G4에서 발생했다. 규칙 자체("임의 시나리오 생존 후퇴 > 0.10")는 특정 시나리오 예측이 빗나가도 그대로 적용된다. | 24-e 분기표 vs 실측 |
| G-F122 | G-A018 사양 `G_A018_pilot_action_rate_m008.json` SHA-256 `7844cbe1f8f81f83116252922ac2921bbf261baab6661d0e2160e2b6d1945567`, 3,000 B. 추출본에서 `validate` VALID(`baseline=Pilot-01`), `materialize` 후보 `action_rate_l2 -0.008`·기준선 `-0.01`, 나머지 5개 동일. 계약 테스트 `Ran 50 tests`, `FAILED (failures=6, errors=7)` — 13건 전부 기존에 알려진 실패(대형 원본 파일 미보유, G-F94 이후 상태)이며 G-A018 관련 실패는 0건. | 로컬 end-to-end 검증, `python -m unittest discover -s tools` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D79 | `track_lin_vel_xy_exp` 다이얼을 **완전히 기각**한다. 총점이 개선됐어도 `1.2 → 1.3` 축소 재탐색은 하지 않는다. | §19-b(생존 절 우선)와 24-e 분기표 3행(임의 시나리오 생존 후퇴 > 0.10 → 다이얼 기각) 발화. 축소 재탐색 경로는 "총점 후퇴 + 생존 후퇴 없음" 전용 조건이었고 이번엔 정반대 패턴이라 조건 자체가 다르다 |
| G-D80 | 다음 단일 변수는 **`action_rate_l2` −0.01 → −0.008**(G-A018)이며, 참가자 파일 안에서 시도 가능한 **마지막** 단일 변수다. 기준선은 동결 Pilot-01로 복귀. | `feet_air_time`·`ang_vel_xy_l2`·`flat_orientation_l2`·`lin_vel_z_l2`·`track_lin_vel_xy_exp` 5개 항이 모두 막혔다(상한 확정 2건, 다이얼째 기각 2건, 방향 기확정 1건). 참가자 파일에서 방향 경고("⚠️")가 없는 유일한 항이라 위험 신호가 가장 약하다 |

**LATEST NEXT:** `workspace\training\quadruped\upload\G-A018\current\` 2파일 업로드 →
실행 → `workspace\_keep`로 회수. 절차 정본은 `SERVER_SESSION_RUNBOOK.md`의 **G-A018** 절.

**(마감)** G-A018은 실행·회수·검증 완료. 후속은 §26.

## 26. G-A018 결과 회수·분석과 참가자 파일 6개 항 소진 확정 — 260905

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F123 | `GO2_PILOT_ACTION_RATE_M008_RESULT.zip` 외부 SHA `814d48ed5a36bd92ef64a319da3111a2fb58a857410ffe48ed8fc8eb63da728a`가 서버 sidecar와 일치, ZIP CRC 무결(129 멤버 OK). | 로컬 `hashlib.sha256`, `zipfile.testzip` |
| G-F124 | `RESULT_STATE=FULL`, `RUNNER_RC=0`, telemetry 후보 7/7·기준 7/7, 영상 1/1, 정책 계보 `ACTOR_TENSORS_MATCH`(8/8). `training/env.yaml`은 `action_rate_l2 -0.008`만 바뀌고 나머지 5개는 Pilot-01 값 그대로다. | `RESULT_STATUS.txt`, `RUNNER_STATUS.txt`, `POLICY_LINEAGE.json`, `training/reward_only.diff` |
| G-F125 | G-A018 판정은 `INTERNAL_EARLY_KILL_FAIL`, 총점 `-44.398639/70`(기준 `46.49124`, 후보 `2.09260`). G1~G7 전 시나리오의 생존이 0.10 넘게 후퇴했다(G-A016과 같은 규모의 전면 붕괴). | `reports/TIER1_DECISION.json` |
| G-F126 | **(260905 정정)** 최초 분석은 G-A016과 "같은 서명"이라고 기록했으나 iteration 단위로 재확인한 결과 메커니즘이 다르다. G-A016은 학습 자체가 iter ~150에서 고착돼 걷기를 배우지 못했다(850 iter 무개선). G-A018은 학습이 정상이다 — `track_lin_vel_xy_exp`가 iter 100→1000 동안 꾸준히 올라 최종 `0.56`(episode 길이 900~1000/1000 유지). 실패는 평가 에피소드 **안에서** 일어난다: `forward_fast`(32 env 평균)는 t=0.6s까지 정상 보행(`height 0.331`·`speed 0.237`)하다가 t=1.0~2.0s 사이 약 1.4초에 걸쳐 부드럽게(급변 트리거 없이, `cmd_vx` 전 구간 `1.2` 일정) 붕괴해 `height≈0.10`·`speed≈0.01`로 얼어붙고 남은 18초 넘게 재개되지 않는다. `slope_plus_20`도 같은 타이밍. `dr_seed_101`은 정지 자세가 이분화(웅크림 `~0.10m` vs 직립 `~0.44m`)된다. 공통점은 "학습을 못했다"가 아니라 "학습한 보행 리듬이 에피소드 안에서 지속되지 못하고 붕괴한다"는 것 — G-A016과 구별되는 별개의 실패 양상이다. | iteration별 `logs/candidate_training.log` 재분석, 7개 case `steps.csv` 시계열 |
| G-F127 | 참가자 파일이 명시한 6개 reward 항이 전부 소진됐다: `feet_air_time`(상한 확정)·`ang_vel_xy_l2`(다이얼째 기각)·`flat_orientation_l2`(부호 반대로 철회)·`lin_vel_z_l2`(방향 기확정)·`track_lin_vel_xy_exp`(1.4에서 기각, 단 유일하게 총점 개선)·`action_rate_l2`(다이얼째 기각). 새 미검증 항은 없다. | §26-c 종합 |
| G-F128 | G-A019 사양 `G_A019_pilot_track_lin_vel_xy_130.json` SHA-256 `643b36c9572520038ebf4467534590a961becffc25fcc9a39088b394f8305e17`, 3,241 B. 추출본에서 `validate` VALID(`baseline=Pilot-01`), `materialize` 후보 `track_lin_vel_xy_exp 1.3`·기준선 `1.2`, 나머지 5개 동일. 계약 테스트 `Ran 50 tests`, `FAILED (failures=6, errors=7)` — 13건 전부 기존에 알려진 실패, G-A019 관련 실패 0건. | 로컬 end-to-end 검증 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D81 | `action_rate_l2` 다이얼을 **완전히 기각**한다. 강화 방향(`-0.01→-0.012`) 재탐색은 하지 않는다. | 25-d 분기표 3행(임의 시나리오 생존 후퇴 > 0.10, 실제로는 7개 전부) 발화. 붕괴가 전 시나리오·동일 서명(G-F126)으로 나타나 방향을 반대로 돌려도 같은 함정을 피할 근거가 없다 |
| G-D82 | 다음 단일 변수는 **`track_lin_vel_xy_exp` 1.2 → 1.3**(G-A019)이며, 새 다이얼이 아니라 **유일하게 총점을 개선한 항의 크기를 절반으로 줄인 재탐색**이다. 기준선은 동결 Pilot-01 그대로. | 참가자 파일 6개 항이 전부 소진됐다(G-F127). `track_lin_vel_xy_exp`만 총점 개선(+3.71/70)을 낸 적이 있고, 그 실패는 G4 생존 단독 후퇴였다 — 크기를 줄이면 문턱 아래로 들어올 수 있다는 가설을 검증하지 않고 포기하는 것은 유일한 개선 신호를 버리는 것과 같다 |

**LATEST NEXT:** `workspace\training\quadruped\upload\G-A019\current\` 2파일 업로드 →
실행 → `workspace\_keep`로 회수. 절차 정본은 `SERVER_SESSION_RUNBOOK.md`의 **G-A019** 절.

**(리셋, 260905)** G-A019는 실행하지 않는다. 후속은 §27.

## 27. 캠페인 리셋 — Pilot-01 폐기, Chain-01로 재출발 — 260905

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F129 | Pilot-01은 Default-01에서 reward 4개(`track_lin_vel_xy_exp`·`feet_air_time`·`lin_vel_z_l2`·`ang_vel_xy_l2`)를 동시에 바꾸고 학습 seed 42 하나로 260831에 만든 정책이다. `GO2_REWARD_EVIDENCE_MASTER.md`(260901)는 이미 "학습 seed는 42 하나라 독립 학습 재현성은 미확보" "control 생성 전까지 Pilot-01이 개선됐다는 표현은 금지"라고 명시했다. | `GO2_REWARD_EVIDENCE_MASTER.md` L65, L77-82 |
| G-F130 | 260903 G-D69에서 이 규칙이 재검토 없이 뒤집혀 동결 기준선이 Pilot-01로 전환됐다. control(재현 검증)은 끝내 생성되지 않았다. 이후 G-A013~G-A019(5회 실행) 중 4회 후퇴, 2회(G-A016·G-A018) 전 시나리오 붕괴. 유일한 개선(G-A017 +3.71/70)도 시나리오 하나의 생존 후퇴로 기각됐다. | §19-26, 사용자 지시 260905 |
| G-F131 | Pilot-01의 4개 동시 변경 중 2개는 이미 Default-01 위에서 개별 단일변수 검증이 끝나 있었다: `track_lin_vel_xy_exp` 1.0→1.2(G-A011, `+3.0902846/70`, 생존 후퇴 0건), `lin_vel_z_l2` -3.0→-2.0(G-A010, `+2.2571599/70`, G7 -0.03125만 허용 내). 두 검증은 각각 독립적으로 이뤄졌을 뿐, 함께 적용됐을 때의 안전성은 한 번도 측정되지 않았다. | `go2_track_lin_vel_120_v1/reports/TIER1_DECISION.json`, `go2_g_a010_lin_vel_z_m2/reports/TIER1_DECISION.json` |
| G-F132 | Chain-01을 G-A011의 검증된 checkpoint(model SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`, env SHA `2ba9a1e11b52792c7ee7a76c9891a98d5f2d7d56c058f1182410f773bac5aa71`)로 등록했다. `go2_tuning_config.py`의 `FROZEN_BASELINES`에 추가하고 `ENGINE_VERSION`을 1.2.0→1.3.0으로, `tools/build_go2_tuning_engine.py`의 baseline payload에 `baseline/chain01/`을 추가해 엔진을 v1.4(SHA `a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0`, 66 members)로 재빌드했다. Default-01 소스 체인이 로컬에 없어(`GO2_DEFAULT_VS_PILOT_RESULT.zip` 미보유, G-F94 계열 기존 문제) 전체 재빌드 대신 검증된 v1_3 ZIP을 그대로 읽어 Chain-01 baseline만 추가하는 방식으로 만들었다 — Default-01·Pilot-01 payload는 손대지 않았다. | `go2_tuning_config.py`, `tools/build_go2_tuning_engine.py`, 로컬 rebuild 스크립트 |
| G-F133 | G-A020 사양 `G_A020_chain01_lin_vel_z_m2.json` SHA-256 `1bc313e5f2879666da81b427cac4355045b1e006caef981f31da914756e7cca2`, 3,155 B. 추출한 v1.4 엔진으로 `validate` VALID(`baseline=Chain-01`) · `materialize` 후보 `lin_vel_z_l2 -2.0`·기준선 `-3.0`(나머지 5개, `track_lin_vel_xy_exp 1.2` 포함, 동일) · 기준선 checkpoint `143871e3…` 일치 · `baseline_seed` 캐시 7/7 확인. 계약 테스트는 `go2_tuning_config.py`의 `ENGINE_VERSION` 변경으로 `test_go2_tuning_engine_contract.py`의 두 fixture(G-A015·G-A016 재검증)가 일시적으로 `engine_version mismatch`로 깨졌으나, 히스토리 spec 파일(SHA로 이미 원장에 기록됨)을 고치는 대신 테스트가 fixture 로드시 `engine_version`을 현재 값으로 패치하도록 수정해 해결했다. 이후 `Ran 50 tests`, `FAILED (failures=6, errors=7)` — 리셋 이전과 동일한 13건의 기존 알려진 실패만 남고 새 실패 0건. | 로컬 end-to-end 검증, `python -m unittest discover -s tools` |
| G-F134 | fix1 엔진(`ebb8b5d4…`) 업로드 후 서버 실행이 `server_run_go2_tuning_engine_v1.sh: line 3: set: pipefail: invalid option name`로 즉시 죽었다. `od -An -tx1`로 원인 확인: v1.4 재빌드 때 로컬 디스크에서 새로 읽어 넣은 `server_run_go2_tuning_engine_v1.sh`·`go2_tuning_config.py` 두 파일이 그 시점 로컬 사본에 CRLF(`\r\n`)가 섞여 있었고, `set -euo pipefail\r`을 Linux bash가 `pipefail`이 아닌 알 수 없는 옵션으로 거부했다. (`grep -c $'\r'`는 이 MSYS 환경에서 CR을 못 잡아 오검출 0을 반환 — `od` byte dump로만 확정 가능했다.) 학습은 line 3에서 즉시 종료돼 iteration 소비 0, GPU 낭비 없음. 두 파일 CR 제거(`sed -i 's/\r$//'`) 후 `bash -n`·`ast.parse`·엔진 재조립·`validate`+`materialize` end-to-end 재검증 통과. fix2 엔진 SHA `a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0`, 19,135,939 B, 66 members(개수 불변) — `upload/G-A020/current`에 재게시, fix1은 `history/`에 보존. | 사용자 재현 보고(260905), `od -An -tx1` 직접 검증 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D83 | **Pilot-01을 동결 기준선에서 완전히 내린다.** 향후 어떤 실험도 Pilot-01과 비교·채택하지 않는다. | 재현성 미확인 상태로 260903에 채택된 것 자체가 260901 자체 규칙 위반이었고, 그 위에서 반복된 실패가 이를 뒷받침한다(G-F129, G-F130) |
| G-D84 | 새 동결 기준선은 **Chain-01**(`track_lin_vel_xy_exp`=1.2만, Default-01 대비 개별 검증 완료)이다. | 참가자 파일 6개 항 중 유일하게 "단일변수·독립 검증·생존 후퇴 0건"을 모두 만족하는 항이 이것뿐이다(G-F131) |
| G-D85 | 다음 실험(G-A020)은 Chain-01 위에 G-A010의 검증된 `lin_vel_z_l2 -3.0→-2.0`을 얹어 **두 검증된 개선의 합성 안전성**을 확인한다. PASS 시 이 지점을 Chain-02로 동결하고 남은 4개 미검증 항(`feet_air_time`·`ang_vel_xy_l2`·`action_rate_l2`·`flat_orientation_l2`)을 여기서부터 재개한다. | H1 캠페인이 검증된 변경을 하나씩 누적해(Run02→04→05) 최종 후보(Run06, 92.73/100)를 만든 방식과 동일 원칙(`H1_REWARD_EVIDENCE_MASTER.md` §3) |

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F135 | G-A020 실행 완료(260905, `RUNNER_RC=0`, `RESULT_STATE=FULL`). fix2 엔진 사용 확인(`RUNNER_STATUS.txt`의 `ENGINE_ARCHIVE_SHA256=a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0`, `EXPERIMENT_SHA256=1bc313e5f2879666da81b427cac4355045b1e006caef981f31da914756e7cca2` 둘 다 사양과 일치). `training/env.yaml`에서 `track_lin_vel_xy_exp weight=1.2`·`lin_vel_z_l2 weight=-2.0` 렌더링 확인(사양대로). **결과: 전 시나리오 생존 붕괴.** `baseline_points_70=18.610562`, `candidate_points_70=0.428330`, `delta=-18.182232`. G1·G2·G4·G5 survival ≈ -1.0(전멸), G3 -0.84375, G6 -0.9375, G7만 -0.0625(허용 범위 내). `status=INTERNAL_EARLY_KILL_FAIL`, `official_result=OFFICIAL_RESULT_UNMEASURED`. 개별로는 각각 안전했던 두 변경(G-A011 `+3.09/70`, G-A010 `+2.26/70`, 둘 다 생존 후퇴 0건)이 함께 학습되자 정반대로 전멸을 냈다 — G-F131에서 예고한 "합쳐졌을 때의 안전성은 한 번도 측정되지 않았다"는 위험이 실제로 발현된 사례. | `go2_g_a020_chain01_lin_vel_z_m2/RUNNER_STATUS.txt`, `reports/TIER1_DECISION.json`, `training/env.yaml` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D86 | G-A020 조합(Chain-01 + `lin_vel_z_l2 -2.0`)을 **완전히 기각**한다. Chain-02로 승격하지 않는다. 동결 기준선은 여전히 **Chain-01**(`track_lin_vel_xy_exp=1.2` 단독)이다. 두 검증된 개선을 "합치면 더 좋아질 것"이라는 가정 자체를 다음 실험에서 전제로 삼지 않는다. | 전 시나리오 생존 붕괴(G-F135)로 최소 통과 기준(생존 후퇴 ≤0.1) 정반대 방향으로 위배 — 재탐색으로 구제할 여지가 없다(G-D81과 동일 패턴: 전 시나리오·동일 방향 붕괴) |
| G-D87 | 다음 실험은 Chain-01 위에 **미검증 4항 중 하나만** 개별로 얹는다(`feet_air_time`·`ang_vel_xy_l2`·`action_rate_l2`·`flat_orientation_l2` 중 택1, 동시 결합 금지). 어떤 항을 먼저 할지는 후속 턴에서 확정한다. | G-A020의 실패가 "동시 결합"에서 왔을 가능성이 높으므로, 이후로는 한 번에 하나씩만 쌓아 실패 시 원인 특정이 가능하게 한다(H1 원칙 재확인) |

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F136 | G-A021 사양 `G_A021_chain01_ang_vel_xy_m005.json`(SHA `0177803887af8a9693fafdf9f5f6ec51dd6efcfe54c6e4577e4aa82a5df0e83e`, 2,882 B) 준비 완료. Chain-01 위에 `ang_vel_xy_l2` -0.08→-0.05 단독 변경(G-D87의 4항 중 택1). 후보값 -0.05는 Pilot-01이 4개 동시 변경 때 이 다이얼에 실제로 썼던 값 — 그때는 다른 3개와 동시에 바뀌어 개별 효과가 한 번도 분리 측정되지 않았다. 엔진은 v1_4(fix2) 그대로 재사용, 변경 없음. `validate` VALID·`materialize` 후보 `ang_vel_xy_l2 -0.05`·나머지 5개(`track_lin_vel_xy_exp 1.2`·`lin_vel_z_l2 -3.0` 포함) 기준선과 동일 확인. | `config/experiments/G_A021_chain01_ang_vel_xy_m005.json`, 로컬 validate/materialize 검증 |

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F137 | G-A021 실행 완료(260905, `RUNNER_RC=0`, `RESULT_STATE=FULL`, `SHA256SUMS.txt` 9/9 자체 검증 통과). 엔진·사양 SHA 둘 다 일치(`ENGINE_ARCHIVE_SHA256=a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0`, `EXPERIMENT_SHA256=0177803887af8a9693fafdf9f5f6ec51dd6efcfe54c6e4577e4aa82a5df0e83e`). `training/env.yaml` 렌더링 확인(`ang_vel_xy_l2 weight=-0.05`, 나머지 5개 `track_lin_vel_xy_exp 1.2`·`lin_vel_z_l2 -3.0` 포함 기준선과 동일). `model_best.pt` SHA `414a4fd1...` 가 `RUNNER_STATUS.txt`의 `CANDIDATE_MODEL_SHA`와 일치. **결과: 게이트 재실패, 그러나 G-A020과 질적으로 다르다.** `baseline_points_70=18.610562`, `candidate_points_70=12.002626`, `delta=-6.607936`(`min_total_points_delta≥1.0` 미달). survival 후퇴는 G2 -0.75·G3 -0.375·G4 -0.59375·G5 -0.59375·G6 -0.15625로 전멸이 아니라 부분 후퇴이며, G1은 무변화(-0.0004), **G7(DR seed)은 오히려 개선**(survival +0.40625, proxy +0.1545) — 도메인 무작위화 조건에서만 이 완화가 도움이 됐다. `status=INTERNAL_EARLY_KILL_FAIL`, `official_result=OFFICIAL_RESULT_UNMEASURED`. | `go2_g_a021_chain01_ang_vel_xy_m005/RUNNER_STATUS.txt`, `reports/TIER1_DECISION.json`, `training/env.yaml`, `SHA256SUMS.txt` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D88 | G-A021(Chain-01 + `ang_vel_xy_l2 -0.05`)을 **기각**한다. Chain-02로 승격하지 않는다. 동결 기준선은 여전히 **Chain-01**이다. 이 값(-0.05)은 이 다이얼에서 재시도하지 않는다. 다음 실험은 사전등록된 분기(G-A021 spec `branch.on_tier1_fail`)에 따라 **이 실패한 후보 위가 아니라 Chain-01 위에서** 남은 미검증 항 중 `feet_air_time`을 개별로 얹는다(G-A022). 후보값은 `0.01→0.20`으로, Default-01 위에서 이미 측정된 값(G-A007, G-F93: `+3.8656/70`, 실패 사유가 G5 생존 후퇴 단 1건뿐 — 전멸이 아니었음)과 동일하게 맞춰 재사용해, Chain-01 위에서 같은 방향이 유지되는지만 새로 확인한다. | G-A021의 총점 delta가 음수이고 5개 시나리오 생존이 후퇴해 최소 통과 기준 미달(G-F137). `action_rate_l2`·`flat_orientation_l2`는 과거 다른 기준선에서 이미 다이얼째 기각/철회된 이력이 있어(G-F127) 상대적으로 우선순위가 낮고, `feet_air_time`은 유일하게 과거 기준선에서 총점이 실제로 개선된 이력이 있는 항이라 다음 순번으로 택한다 |

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F138 | G-A022 실행 완료(260905, `RUNNER_RC=0`, `RESULT_STATE=FULL`, `SHA256SUMS.txt` 자체 검증 통과). 엔진·사양 SHA 둘 다 일치(`ENGINE_ARCHIVE_SHA256=a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0`, `EXPERIMENT_SHA256=5bb6ba1d4f90db9882e42e1de119c1f99cdb0c08c076a4c70c85df6d57507ec8`). `training/env.yaml` 렌더링 확인(`feet_air_time weight=0.2`, 나머지 5개 `track_lin_vel_xy_exp 1.2`·`lin_vel_z_l2 -3.0`·`ang_vel_xy_l2 -0.08`·`action_rate_l2 -0.01`·`flat_orientation_l2 0.0` 포함 Chain-01 기준선과 동일). `model_best.pt` SHA `92c08d90...` 가 `RUNNER_STATUS.txt`의 `CANDIDATE_MODEL_SHA`와 일치. **결과: 게이트 재실패, G-A021보다 더 나쁘고 G-A020에 가깝다.** `baseline_points_70=18.610562`, `candidate_points_70=4.883013`, `delta=-13.727549`. G1~G6 전부 생존 후퇴 0.10 초과(G1 -1.0·G2 -1.0·G3 -0.84375·G4 -1.0·G5 -1.0·G6 -0.28125) — 사실상 전멸에 가깝다. G7만 -0.0625로 허용 범위 내. Default-01 위에서 유일하게 총점을 개선했던 값(G-A007, +3.8656/70)이 Chain-01 위에서는 G-A020(전멸)에 근접한 붕괴를 낸 것 — 세 다이얼(lin_vel_z_l2·ang_vel_xy_l2·feet_air_time) 개별 스택이 전부 실패했고, 가장 강한 사전 근거를 가졌던 항조차 예외가 아니었다. | `go2_g_a022_chain01_feet_air_time_020/RUNNER_STATUS.txt`, `reports/TIER1_DECISION.json`, `training/env.yaml`, `SHA256SUMS.txt` |

| ID | 결정 | 이유 |
|---|---|---|
| G-D89 | G-A022(Chain-01 + `feet_air_time 0.20`)을 **기각**한다. Chain-02로 승격하지 않는다. **남은 두 항(`action_rate_l2`·`flat_orientation_l2`)은 Chain-01 위에서 시도하지 않는다** — 단일변수 보상 스태킹 탐색을 여기서 종료한다. 동결 기준선은 Chain-01 그대로다. | (1) G-F127이 이미 260905 리셋 이전에 확정한 사실: 이 두 항은 각각 다이얼째 완전히 소진됐다 — `action_rate_l2`는 유일하게 시도된 값(-0.008, 완화 방향)이 전 시나리오 붕괴로 다이얼째 기각(G-D81)됐고 반대 방향(강화)도 "같은 함정을 피할 근거가 없다"는 이유로 재탐색이 명시적으로 배제됐다. `flat_orientation_l2`는 유일하게 시도된 방향(0.0→-1.0)이 실패(G-D66)했고 후속 강화(-2.0)는 "실패가 부호/메커니즘 오류이지 크기 부족이 아니다"라는 이유로 취소(G-D67)됐다 — 참가자 파일이 명시한 "↑ 키우면 안 넘어짐" 방향 자체가 +20°/계단 지형에서 필요한 지형 추종 기울임을 정확히 벌점 매겨 구조적으로 막혀 있다. 즉 두 항 모두 코히런트한 방향이 전부 이미 죽어 있어 새로 시도할 값이 없다. (2) Chain-01 위 개별 스태킹 3/3(G-A020·G-A021·G-A022)이 전부 실패했고, 그중 유일하게 양의 사전 근거를 가졌던 `feet_air_time`조차 가장 심한 후퇴 중 하나를 냈다 — 남은 두 항은 애초에 음의 사전 근거만 가지고 있어 기대값이 이보다 낮다. 이미 실패가 확정된 값을 Chain-01 위에서 재확인하는 것은 새 정보 없이 예산만 소모한다. | G-F127, G-D81, G-D66, G-D67, G-F138 |
| G-D90 | 다음 작업은 새 보상 실험이 아니라 **Chain-01 자체의 실측**이다. Chain-01(G-A011)은 지금까지 seed 101 tier-1 프록시 점수(`+3.0902846/70`, 생존 후퇴 0건)만 있고 대표 seed(202·303)·69-case·posture_gate_v2 평가를 받은 적이 없다 — G-A011이 지정 시나리오 절만으로 조기 종료됐기 때문이다(G-F92). G-A012가 Pilot-01에 썼던 것과 같은 방식(학습 없이 frozen checkpoint를 69-case×3seed·영상 7종으로 측정)을 Chain-01용으로 새로 만든다(G-A023, work id, `tools/build_go2_chain01_baseline_package.py`+`server_run_go2_chain01_baseline.sh`, G-A012 스크립트에서 이름만 교체). 로컬에서 `bash -n`·CRLF 0·zip CRC·manifest 27/27·내장 model/env SHA 대조(`143871e3…`/`2ba9a1e1…`) 전부 통과했다. | G-F92(G-A011이 tier-1 프록시만 있음), G-A012 선례(`SERVER_SESSION_RUNBOOK.md` §"G-A012"), 예산 효율(학습 없음, 이미 실패 확정된 다이얼 재확인보다 정보가치 높음) |

**LATEST NEXT:** (§28에서 갱신됨)

## 28. G-A023 결과 회수 — Chain-01 실측 붕괴 발견과 evaluator 버전 불일치 확정 — 260905

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F139 | G-A023 실행 완료(260905, `RUNNER_RC=0`, `RESULT_STATE=FULL`, 외부 SHA·`SHA256SUMS.txt` 자체 검증 통과, telemetry 69/69·영상 7/7·`TRAINING=none`·`CHAIN01_MODEL_SHA` 일치). `go2_fixed_eval_report.build_policy()`로 직접 채점한 결과 **Chain-01의 실제 69-case×3seed 점수는 `2.307745/70`**(worst-case 집계)이며, G1·G2·G3·G4·G5·G7 6개 시나리오 전부 `survival_proxy=0.0`(3개 seed 전부 동일 패턴, 특정 seed의 우연이 아님) — 전진(느림·보통·빠름)·경사(±20°)·계단(4종)·대각선 이동·편측 yaw 전부 붕괴. 생존하는 것은 후진·좌우 이동·회전(`survival≈1.0`)과 push(부분)뿐이다. | `go2_chain01_baseline_result_extract/`, `go2_fixed_eval_report.build_policy()` 직접 실행, 로컬 SHA/manifest 검증 |
| G-F140 | 이 결과는 지금까지 Chain-01 계보 전체(G-A011·13·18·20·21·22)의 tier-1 스크리닝이 써 온 `survival_proxy`와 **다른 evaluator**로 나왔다. `go2_g_a022_chain01_feet_air_time_020/evaluation/baseline_tier1/.../forward_fast/summary.json`은 `schema_version:1`이고 `survival_proxy:1.0`(termination-only — 물리 시뮬레이션이 강제 종료됐는지만 본다)인 반면, 같은 checkpoint·같은 forward_fast 케이스를 이번 G-A023(`schema_version:2`, `EVALUATOR=posture_gate_v2`)로 채점하면 `survival_proxy_v1:1.0`은 동일하게 남아있지만 `survival_proxy_v2:0.0`(`height_rel_mean=0.1427` `<` `height_rel_min_m=0.18` 기준 미달, 즉 쓰러지진 않았지만 기준 이하로 웅크린 채 회복하지 못함)이 새로 계산되고, 최종 `survival_proxy` 필드는 v2 값을 채택한다. `tracking_xy_rmse`(1.18714 vs 1.18714, 완전 일치) 등 물리 궤적 자체는 두 결과가 동일하다 — 같은 rollout을 두 개의 다른 채점 규칙으로 읽은 것이다. 코드(`go2_eval_telemetry.py`, git 커밋 `f229e06` 하나에 v1/v2 로직이 함께 들어있다)는 `posture_measured`가 참이면 항상 v2를 계산하므로, tier-1이 v1만 낸 이유는 실행 시점 분기가 아니라 **엔진 아카이브(fix2, SHA `a030427748…`)가 이 커밋 이전의 구버전 `go2_eval_telemetry.py`를 그대로 얼려서 담고 있기 때문**이다. G-A011~G-A022 전체가 이 엔진 하나로 실행됐다(G-F132, G-F134). | `evaluation/baseline_tier1/cases/seed_101/forward_fast/summary.json`(schema_version 1), `evaluation/chain01/cases/seed_101/forward_fast/summary.json`(schema_version 2), `go2_eval_telemetry.py` L159·L349-379, `git log -p` |
| G-F141 | `GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.json`(G-A012, 같은 posture_gate_v2 evaluator, G-F69)에서 Default-01의 실측을 다시 읽으면 **G1(forward_fast) survival_proxy=1.0**이고 7개 시나리오 전부 survival이 0.625~1.0으로 하나도 붕괴하지 않는다(총점 `17.90699/70`, 이미 알려진 값과 일치). Chain-01과 Default-01의 유일한 차이는 `track_lin_vel_xy_exp` 1.0→1.2뿐이다(G-F131). 즉 이 한 값 변경이, tier-1(v1 evaluator)에서는 `+3.09/70`의 "안전한 개선"으로 보였지만 실제로는 posture_gate_v2 기준 **survival을 6/7 시나리오에서 전멸시키는 회귀**였다 — 정책이 tracking 보상을 더 쫓도록 압박받자 낮게 웅크린 채로 버티는 전략에 빠졌고, termination-only 게이트는 이를 전혀 잡아내지 못했다. | `GO2_DEFAULT_VS_PILOT_PAIRED_REPORT.json` per_scenario.G1-G7.default, G-F131 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D91 | **Chain-01을 동결 기준선에서 즉시 내린다.** Chain-01 자체를 최종 후보로도, 향후 어떤 실험의 기준선으로도 쓰지 않는다. | 실측(G-F139) 결과 6/7 시나리오 survival 전멸(`2.307745/70`) — Chain-01은 애초에 Default-01보다 나은 정책이 아니라, tier-1의 낡은 evaluator가 놓친 심각한 posture 회귀였다(G-F140, G-F141) |
| G-D92 | **동결 기준선을 Default-01로 되돌린다.** Default-01은 이미 posture_gate_v2로 실측된 유일한 정책이다(`17.90699/70`, 7개 시나리오 전부 생존, G-F141). G-A011~G-A022에서 나온 모든 "단일변수 검증 결과"(track_lin_vel_xy_exp·lin_vel_z_l2·ang_vel_xy_l2·feet_air_time 각각의 tier-1 PASS/FAIL 판정)는 termination-only(v1) evaluator로 내려진 것이라 **survival 결론은 신뢰하지 않는다** — tracking/속도 방향성 신호만 참고 가능하다. `track_lin_vel_xy_exp 1.0→1.2`는 이제 "검증된 안전한 개선"이 아니라 "posture_gate_v2 기준 실패가 확인된 변경"으로 재분류한다. | G-F139-141; H1 캠페인과 동일 원칙 — 신뢰할 수 없는 게이트로 승인된 누적 변경 위에 계속 쌓지 않는다 |
| G-D93 | 다음 작업은 새 보상 실험이 아니라 **tuning engine의 evaluator를 현재 `go2_eval_telemetry.py`(posture_gate_v2 포함, 커밋 `f229e06`)로 재빌드하는 것**이다. 이 작업이 끝나기 전에는 어떤 신규 tier-1 결과도 survival 기준으로 신뢰하지 않는다. 재빌드·로컬 계약 테스트 통과 후에만 Default-01 위 새 단일변수 실험을 재개한다. | G-F140 — 엔진이 구버전 evaluator를 얼린 채로 있는 한 같은 맹점이 다음 실험에도 그대로 반복된다 |

**LATEST NEXT:** 로컬에서 tuning engine을 posture_gate_v2 포함 최신 `go2_eval_telemetry.py`로 재빌드하고 계약 테스트를 통과시킨다. 서버 작업은 그 전까지 보류.

## 29. PRD 감사·엔진 재빌드 진행 상황 (260905)

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F142 | living PRD `workspace/training/quadruped/reports/GO2_DEFAULT_BASELINE_TEST_PRD.md`는 v1(Default-01 vs Pilot-01 쌍대 비교) 범위에서 멈춰 있고, Chain-01 계보 전체(G-A009~G-A023, 이 문서 §18~28)는 이 PRD를 갱신하지 않고 진행됐다. `Chain-01`이라는 문자열이 PRD 본문에 0회 등장한다. G-D12("Go2 기획자가 매 기획·실험·판정에서 참조하고 같은 턴에 갱신하는 살아있는 정본으로 운영한다")는 사실상 G-A009 시점부터 지켜지지 않았고, `GO2_PROJECT_STATE.md`가 실질적 living ledger 역할을 대신 수행해 왔다 | `GO2_DEFAULT_BASELINE_TEST_PRD.md` 전문 grep(`Chain-01` 0건), 본 문서 §18-28 |
| G-F143 | G-D93 엔진 재빌드는 **부분 진행 상태**다. `tools/build_go2_tuning_engine.py`는 이미 로컬에서 output을 `go2_tuning_engine_v1_4.zip`으로 바꾸고 `go2_eval_telemetry.py`를 현재 워크스페이스 파일에서 직접 읽도록 돼 있다(수정 전부터 그랬음 — `source_files()`가 항상 라이브 경로를 읽는다). 디스크의 `go2_tuning_engine_v1_4.zip`(19,135,939 B, uncommitted)을 직접 열어 확인한 결과 내부 `go2_eval_telemetry.py`의 SHA(`f8ed1d014478865055d7b10a2e2bf6c238b7c41564b686f66cfd76271169f8c1`)가 현재 워크스페이스 파일과 완전히 일치 — **posture_gate_v2가 이미 임베드돼 있다.** 그러나 `python -m unittest tools/test_go2_tuning_engine_contract.py`는 16개 중 3개 실패하며, 실패 원인은 evaluator가 아니라 **Default-01 소스 zip `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/GO2_DEFAULT_VS_PILOT_RESULT.zip`이 로컬에 없는 기존 결손**(주석에 이미 "Default-01 소스 체인이 로컬에 없어"로 기록된 G-F94 계열 문제)이다. `workspace/_keep/go2_default_vs_pilot_v1/training/model_best.pt`가 기대 SHA(`99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`)와 일치하는 압축 해제본으로 존재하지만, 같은 디렉터리의 `env.yaml`은 기대 SHA `4d1d294b63dafeceb223fb48226cbe6a533157bc54f97ce486f644bd1bda262c`가 아니라 `a39c77dc9f45a9ebcff4363e389288ba1e2cf1a38def04a8b05c4337b6fd83ea`를 낸다(내용까지 같은지는 미확인 — 재직렬화로 인한 무해한 바이트 차이일 수도, 실제 config drift일 수도 있다. 추측하지 않는다) | `zipfile` 직접 열람(`go2_tuning_engine_v1_4.zip:source_template/go2_eval_telemetry.py`), `python -m unittest` 출력, `sha256sum` 직접 실행 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D94 | **이 living PRD를 v1 범위(Default-01 vs Pilot-01)로 공식 종료한다.** 파일에 종료 note만 추가하고 Chain-01 이후 이력을 소급 기입하지 않는다. 앞으로 Go2의 유일한 living 정본은 `GO2_PROJECT_STATE.md`다 — 같은 역할의 문서 두 개를 동시에 운영하지 않는다 | G-F142. Chain-01이 이미 폐기됐고(G-D91) 새 PRD 버전을 소급 작성하는 것은 정보가치 없는 서류 작업이다 |
| G-D95 | 엔진 v1_4는 `ENGINE_REBUILD_PARTIAL — EVALUATOR_FIXED / BASELINE_PAYLOAD_UNVERIFIED`로 기록한다. posture_gate_v2 임베드는 확인됐으므로 evaluator 문제 자체는 해결됐다고 봐도 되지만, 계약 테스트 3건이 실패하는 한 이 엔진을 서버에 올리지 않는다. 다음 로컬 작업은 `env.yaml` SHA 불일치의 원인(재직렬화 vs 실제 drift)을 확인해 3개 실패 테스트를 통과시키는 것이며, G-D93의 "재빌드·계약 테스트 통과 전 서버 작업 보류"는 그대로 유지한다 | G-F143 — evaluator는 고쳤지만 빌드 재현성이 아직 증명되지 않았다 |

**LATEST NEXT:** `env.yaml` SHA 불일치 원인을 확인하고 `tools/test_go2_tuning_engine_contract.py` 16/16을 통과시킨 뒤 `go2_tuning_engine_v1_4.zip`을 커밋한다. 그 전까지 서버 작업은 보류(G-D93 유지).

## 30. 엔진 재빌드 완료·G-A010 업로드 재등록 (260905)

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F144 | G-F143의 `env.yaml` SHA 불일치 원인을 확인했다 — **내용 동일, 재직렬화로 인한 바이트 차이**다. `_keep/go2_default_vs_pilot_v1/training/env.yaml`을 직접 열어 6개 reward 가중치(`track_lin_vel_xy_exp=1.0`·`feet_air_time=0.01`·`lin_vel_z_l2=-3.0`·`ang_vel_xy_l2=-0.08`·`action_rate_l2=-0.01`·`flat_orientation_l2=0.0`, `std=0.5`)가 Default-01 배포 기본값과 정확히 일치함을 확인했다. Pilot-01 쪽(`_keep/go2_pilot_v2_baseline/policy/pilot_env.yaml`)도 같은 방식으로 확인(`1.2/0.2/-2.0/-0.05/-0.01/0.0`, model SHA `c4d78adf…` byte-identical). 두 로더(`tools/build_go2_track_lin_vel_120_package.py`, `tools/build_go2_tuning_engine.py`)와 `go2_tuning_config.py`의 `FROZEN_BASELINES` 상수를 압축 해제본 경로·재직렬화 SHA로 갱신했다 | 직접 `sha256sum`·YAML grep 대조, AGENTS.md "해시 불일치는 내용 불일치의 증거가 아니다" 원칙과 동일 근거 |
| G-F145 | `python -m unittest tools/test_go2_tuning_engine_contract.py` **16/16 전부 통과**. 남은 2건은 evaluator나 baseline payload가 아니라 테스트 픽스처 자체(`G_A016`/`G_A015` spec의 `engine_version`·`env_sha256`이 1.2.0/구버전 그대로 고정된 것)가 원인이었다 — 픽스처 파일을 수정하지 않고 테스트 안에서 임시 패치본을 만들어 검증했다(기존 `setUpClass` 방식과 동일 철학). 엔진은 클린 상태에서 재현 가능하게 빌드되며 최종 SHA는 `81c3bccef543eae116732a3965f6ad5fee692431243eb0ec00615acab2243b37`(66 members), 내부 `go2_eval_telemetry.py` SHA `f8ed1d01…`가 현재 워크스페이스와 일치(posture_gate_v2 포함) | `python -m unittest` 16/16 OK 직접 실행, `python tools/build_go2_tuning_engine.py` 재실행으로 동일 SHA 재현 확인 |
| G-F146 | **정정(260906) — G-F146 원문의 "한 번도 실행된 적 없이"는 오류였다.** G-A010은 260902에 engine v1.1(SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`)로 **실제로 학습·평가까지 완료됐다**(G-F79·G-F80, `workspace/_keep/go2_g_a010_lin_vel_z_m2/`에 launcher.log·RUNNER_STATUS.txt·TIER1_DECISION.json 실물 존재, 1,000 iter 00:59:11 실측 GPU 시간 소비). 직접 재확인: 그 결과의 `evaluation/baseline_tier1/.../forward_fast/summary.json`은 `schema_version:1`이고 `RUNNER_STATUS.txt`의 `ENGINE_ARCHIVE_SHA256`도 `e8f8b3cde9…`로, G-D92가 신뢰 불가로 규정한 termination-only(v1) evaluator와 정확히 같은 세대다 — G-D92 본문은 "G-A011~G-A022"만 명시했지만 posture_gate_v2(commit `f229e06`)가 애초에 이보다 나중에 생겼으므로 260902에 실행된 G-A010도 논리적으로 같은 맹점 안에 있다. 즉 재실행 사유는 "실행 안 함"이 아니라 **"실행은 했지만 측정 도구(구버전 evaluator + 폐기된 target-scenario-only gate, G-D68로 대체됨) 자체가 신뢰 불가"**다. 스키마 필드(`engine_version` 1.0.1→1.3.0, `baseline.env_sha256`, `flat_orientation_l2` 키, `min_total_points_delta` gate)를 엔진 v1.4 대상으로 갱신해 `load_and_validate()`·`materialize_runtime()` 통과를 확인한 것은 원문 그대로 유효하다 | `workspace/_keep/go2_g_a010_lin_vel_z_m2/evaluation/baseline_tier1/cases/seed_101/forward_fast/summary.json`, 같은 디렉터리 `RUNNER_STATUS.txt`, `go2_tuning_config.py` 직접 실행 검증 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D96 | **G-D95의 `ENGINE_REBUILD_PARTIAL`을 `ENGINE_REBUILD_VERIFIED`로 승격한다.** G-D93(엔진을 posture_gate_v2로 재빌드하고 계약 테스트를 통과시키기 전 서버 작업 보류)이 완전히 충족됐다 — 서버 작업 보류를 해제한다 | G-F144, G-F145 |
| G-D97 | **다음 서버 실행은 G-A010의 재측정이다**(같은 변수·같은 baseline, 새 ID를 발급하지 않는다 — G-D98 참조). `tools/publish_go2_upload_bundle.py`로 `upload/G-A010/current/`에 engine v1.4 + 갱신된 spec + 새 RUN_GUIDE를 재등록했다(release `20260905_lin_vel_z_m2_engine_v1_4_r2`, engine SHA `81c3bccef5…`, spec SHA `2910450db9…`) | G-F146; 문헌 근거(R-Sci-1)와 G1이 최대 실점 시나리오라는 진단(GO2_REWARD_EVIDENCE_MASTER.md §17-b)이 이미 사전등록돼 있음. **260902 결과(총점 `+2.2571599/70`, G1 개선 미달로 조기종료)는 폐기가 아니라 "방향성 참고, survival 결론 불신"으로 강등** — 새 결과가 나오면 이 값과 나란히 비교해 posture_gate_v2가 같은 변경을 다르게 평가하는지 직접 확인한다(G-A011의 `track_lin_vel_xy_exp` 사례처럼 v1-안전이 v2-위험으로 뒤집힐 수 있음, G-F141) |
| G-D98 | **넘버링 일관성 규칙(260906 신설): 같은 experiment ID를 다른 엔진·gate로 재측정할 때는 ID를 재사용하되, 모든 언급에 "(재측정, 최초 실행 260902, engine v1.1→v1.4)"를 명시한다.** 새 개입에는 항상 다음 미사용 ID(현재 최대 G-A023 다음은 G-A024)를 쓴다. | 사용자 지적(260906) — ID가 시간순으로 왔다갔다 하면 "이미 한 것 아니냐"는 혼동이 생긴다. 재사용/재측정과 신규 실험을 텍스트로 항상 구분해 이 혼동을 원천 차단한다 |

**LATEST NEXT:** (§31에서 갱신됨)

## 31. G-A010 재측정 회수 — posture_gate_v2로 재실측하니 전멸 확인 — 260906

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F147 | `GO2_LIN_VEL_Z_M2_RESULT.zip` 다운로드본 검증 전부 통과: 외부 SHA `0c404c98d8…` 일치, zip CRC 이상 없음, 내부 `SHA256SUMS.txt` 128개 전부 `sha256sum -c` OK, `RUNNER_STATUS.txt`의 `ENGINE_ARCHIVE_SHA256=81c3bccef543eae116732a3965f6ad5fee692431243eb0ec00615acab2243b37`·`EXPERIMENT_SHA256=2910450db9e107875410a80ed1d947d80cced0e31e67b1734f544e300374861d` 둘 다 사양과 일치(엔진이 v1.4임을 서버 산출물 자체가 증명), baseline `identity.json`의 `model_sha256`이 Default-01 고정값(`99ceeaa1a3a1ebee…`)과 일치, candidate `POLICY_LINEAGE.json`이 actor tensor 8/8 매치, G1 필수 영상(`G1_forward_fast_seed_101.mp4`, 유효 MP4 magic bytes) 존재. `RUNNER_RC=0`·`TRAIN_RC=0`. | 로컬 압축 해제·`sha256sum -c`·`unzip -t`·직접 파일 열람 |
| G-F148 | **결과: `INTERNAL_EARLY_KILL_FAIL`.** `TIER1_DECISION.json`: `baseline_points_70=17.132070`, `candidate_points_70=9.499548`, delta `-7.632522`(`min_total_points_delta≥1.0` 대실패). G1~G6 survival 전부 `-0.1` 초과 회귀(G1 `-0.40625`, G2 `-0.65625`, G3 `-0.25`, G4 `-0.65625`, G5 `-0.6875`, G6 `-0.1875`), G7만 `-0.09375`로 허용 범위 내. 목표였던 G1 tracking 개선은 사실상 없었다(`tracking delta -0.00055`, 속도는 그대로인데 survival만 무너짐). | `go2_g_a010_lin_vel_z_m2_v2_260906/.../reports/TIER1_DECISION.json` |
| G-F149 | 붕괴 메커니즘을 G1 raw case에서 직접 확인: `terminated_env_count:0`(구버전 v1 기준으론 "생존 100%"로 보임, `survival_proxy_v1:1.0`)이지만 `fallen_env_count:13/32`, `height_rel_mean:0.261`(임계 `0.18` 위에 있지만 중앙값·평균이 위태롭게 낮음), `height_rel_p10:0.103`(하위 10%는 임계 미달), 결과 `survival_proxy_v2:0.59375`. **G-A011의 `track_lin_vel_xy_exp` 사례(G-F141)와 정확히 같은 패턴** — 종료(termination)는 안 됐지만 자세가 무너진 채 회복 못 함을 v1 evaluator는 전혀 못 잡아낸다. | `evaluation/candidate/SELF_EVAL_REPORT.json` G1 case raw 블록 |
| G-F150 | 260902 v1 측정값(`+2.2571599/70`, "생존 후퇴 0건")과 260906 v2 측정값(`-7.632522/70`, 6개 시나리오 생존 붕괴)은 **같은 checkpoint·같은 reward 변경에 대해 정반대 결론**이다. `lin_vel_z_l2` 페널티를 줄이면(`-3.0→-2.0`, 덜 벌준다) 정책은 속도를 더 내는 대신 낮게 웅크려 불안정해지는 쪽으로 붕괴했다 — 페널티 완화가 "속도 상한 해제"가 아니라 "안정화 제약 제거"로 작용한 것으로 해석한다(사후 해석, 추가 검증 없이 확정 아님). | G-F148, G-F150 비교 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D99 | **`lin_vel_z_l2 -3.0→-2.0`은 최종 기각한다. Default-01의 `-3.0`을 그대로 유지한다.** 이 다이얼은 문헌 근거 우선순위 1위였지만 posture_gate_v2 실측에서 전 시나리오급 생존 붕괴로 확정됐다 — G-A020(Chain-01 위 결합)과 무관하게 Default-01 위 단독으로도 이미 불량임이 증명됐다. | G-F148, G-F149 — R-2 생존 정의 기준 명백한 회귀, 방향성 가설도 기각(tracking 개선 없음) |
| G-D100 | **정정: 다음 단일변수는 `ang_vel_xy_l2 -0.08→-0.15`(원안 `-0.05`가 아니라 반대 방향인 강화)로 확정하고, ID는 G-A011이 아니라 G-A024로 발급한다.** 원래 spec의 `branch.on_tier1_fail`이 "G-A011: -0.08→-0.05"를 지목했으나 그건 G-A010과 같은 "완화" 방향이라 채택하지 않았다(G-F148 참조 — 완화 방향은 이미 두 번 실패). ID는 이미 Chain-01의 `track_lin_vel_xy_exp` 실험에 쓰였다(G-F131) — 그대로 쓰면 번호 충돌·재사용 혼동이 발생해 G-D98 규칙에 따라 다음 미사용 번호를 발급했다. | G-D98; G-D75(Pilot-01 위 사전등록됐던 강화 방향 값 `-0.15`를 Default-01에 적용) |

**LATEST NEXT:** (§32에서 갱신됨)

## 32. G-A024 결과 회수 — 강화 방향도 전멸, 3전 3패 확정 — 260906

| ID | 확정 사실 | 근거 |
|---|---|---|
| G-F151 | `GO2_ANG_VEL_XY_M015_RESULT.zip` 검증 전부 통과: 외부 SHA `d501e442c3…` 일치, zip CRC 이상 없음, 내부 manifest 128/128 `sha256sum -c` OK, `ENGINE_ARCHIVE_SHA256=81c3bccef543…`·`EXPERIMENT_SHA256=8cdc7a24f9…` 둘 다 사양과 일치, `training/env.yaml`에 `ang_vel_xy_l2 weight=-0.15` 렌더링 확인. `RUNNER_RC=0`·`TRAIN_RC=0`. | 로컬 압축 해제·`sha256sum -c`·`unzip -t`·직접 파일 열람 |
| G-F152 | **결과: `INTERNAL_EARLY_KILL_FAIL`, G-A010보다 더 심하다.** `candidate_points_70=0.0`(완전 붕괴), delta `-17.132070/70`. **G1~G7 전 시나리오(7/7)** survival `-0.1` 초과 회귀 — G1·G2·G4·G5는 `-1.0`(완전 전멸), G3 `-0.75`, G6·G7 `-0.65625`. G1 raw: `fallen_env_count:32/32`(전원 낙상), `height_rel_mean:0.144`(임계 `0.18` 미달), `upright_recovered_events:0/128`(복구는 됐지만 하나도 직립 자세로 못 돌아옴), `survival_proxy_v1:1.0` vs `survival_proxy_v2:0.0`. 학습 자체는 수치적으로 안정됐다(`launcher.snapshot.log` 말미 mean reward 11.9~12.9, NaN·발산 없음) — 즉 이건 학습 실패가 아니라 **정책이 새 reward를 잘 최적화해서 낮게 웅크려 거의 움직이지 않는 안정적 국소최적해로 수렴한, 전형적 reward hacking**이다. | `go2_g_a024_ang_vel_xy_m015/reports/TIER1_DECISION.json`, `evaluation/candidate/SELF_EVAL_REPORT.json` G1 raw, `launcher.snapshot.log` |
| G-F153 | Default-01 위에서 posture_gate_v2로 실측된 단일변수 실험은 이제 3건이고 **3건 전부 전면 실패**다: G-A011류 `track_lin_vel_xy_exp` 강화(6/7 붕괴, 원 캠페인), G-A010 `lin_vel_z_l2` 완화(6/7 붕괴), G-A024 `ang_vel_xy_l2` 강화(7/7 붕괴, 방향 반대인데도 더 나쁨). 완화·강화 양방향, 서로 다른 두 안정화 항 모두 실패했다는 것은 방향의 문제가 아니라 **Default-01의 현재 6개 reward 가중치 조합이 이미 안정성-추종 트레이드오프의 얇은 균형점에 있다**는 뜻이다. | G-F141, G-F148, G-F152 비교 |

| ID | 결정 | 이유 |
|---|---|---|
| G-D101 | **`ang_vel_xy_l2 -0.08→-0.15`도 최종 기각한다. `-0.08` 유지.** 강화 방향도 안전하지 않다 — 오히려 더 나쁘다. | G-F152 |
| G-D102 | **정정(발행 전 자체 재확인) — `flat_orientation_l2`는 "한 번도 시도 안 됨"이 아니라 이미 한 번 시도돼 기각됐다.** `G-A013`(260903)이 정확히 이 항을 Default-01 위에서 `0.0→-1.0`으로 시험해 `-1.4278/70`(G2·G4·G5·G6 총점·생존 후퇴)로 조기종료됐다. 그런데 직접 재확인한 결과 그 실행의 `RUNNER_STATUS.txt`는 `ENGINE_VERSION=1.1.0`, evaluator `schema_version:1`(termination-only) — **G-A010의 260902 원본 결과와 완전히 같은 세대의 신뢰 불가 evaluator**다. 즉 이 항은 "미검증"이 아니라 "검증됐지만 그 검증 도구가 이제 신뢰 불가로 판명된" 상태이고, 다음 단일변수(G-A025)는 새 실험이 아니라 **G-A013의 재측정**이다 — 같은 값(`0.0→-1.0`)을 그대로 posture_gate_v2로 다시 잰다. G-A010이 v1에서 "안전"→v2에서 "붕괴"로 뒤집혔던 것과 반대로, 이 항은 v1에서 "회귀"였던 것이 v2에서는 오히려 개선으로 뒤집힐 가능성이 있다(직접 자세 벌점이므로 termination-only 관점에서는 tracking 손실로만 보였을 수 있음). **위험 고지:** 지형과 무관하게 "평평한" 자세를 요구하므로 경사(G4)·계단(G5)에서는 필요한 기울임 자체를 벌줄 수 있다 — G4/G5 survival을 특히 주의 깊게 본다. | `workspace/_keep/go2_g_a013_flat_orientation_m1/RUNNER_STATUS.txt`, 같은 디렉터리 tier1 case summary.json(`schema_version:1`) 직접 재확인 |
| G-D103 | **G-A025도 실패하면 reward 다이얼 탐색을 중단하고 무변경(no-op) 대조군을 먼저 돌린다** — Default-01과 완전히 같은 6개 reward로 seed 42, 1,000 iter를 재학습해 "reward를 안 바꿔도 1,000-iter from-scratch 재학습 자체가 이 정도로 불안정한가"를 분리 측정한다. 4전 4패가 되면 reward 값 문제가 아니라 재학습 절차(커리큘럼·seed·800→1000 iter 차이) 자체를 의심해야 한다. | G-F153의 "3전 3패가 방향이 아니라 균형점 문제"라는 해석이 맞다면, 그 다음 의심 대상은 재학습 절차 자체다 — 과학적 성실성 상 reward 가설을 계속 소모하기 전에 더 단순한 대안 설명(학습 변동성)을 배제해야 한다 |

**LATEST NEXT:** `flat_orientation_l2 0.0→-1.0`(G-A013의 재측정, 새 값 아님)을 Default-01 위에서 G-A025로 준비한다(engine v1.4, 나머지 5개 항 불변, G4/G5 survival 특별 주시). spec 검증 후 `upload/G-A025/`에 게시하고 서버 실행을 안내한다.
