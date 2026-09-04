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

**LATEST NEXT:** `workspace\training\quadruped\upload\G-A015\current\` 2파일 업로드 → 실행 →
`workspace\_keep`로 회수. 절차 정본은 `SERVER_SESSION_RUNBOOK.md`의 **G-A015** 절.
