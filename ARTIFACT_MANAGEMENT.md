# NConnect 파일·artifact 운영 정본

> **역할:** 서버 작업의 계획, 파일 목록, 다운로드, 검증, 선택 병합, 작업 이력을 한곳에서 추적한다.  
> **대상:** 메인 팀장, 스케줄러, 기획자, 분석가, 보고서 작성자, 서버 실행 사용자.  
> **갱신 방식:** 작업 시작 전에 행을 만들고, 증거가 생길 때 같은 행의 상태만 전진시킨다. 과거 행은 삭제하지 않는다.  
> **갱신일:** 2026-08-31

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 후보의 H1~H7 실제 행동과 설계 의도 20점·리포트 10점의 영상 증거를 확보한다.
- [현재 단계] **단계 1/6 — H4 정량 기본 행동 게이트.** H4 yaw 추종량이 가장 이른 미완료 증거다.
- [확보] Run06 10,000 iter·model_9900·학습/영상 artifact 정합, 사전등록 수치 게이트 5/5 PASS, H1~H3·H5 시각 PASS.
- [미확보] H4 양방향 yaw 추종량, H6 tracking·termination, H7 밀침 회복시간, 독립 seed.
- [이번 테스트] 추가 학습 없이 Run06 고정 정책의 H4·H6·H7 원시 telemetry를 회수한다.
- [흐름] Run06 분석 완료 → **A260831-08 고정 평가** → 정량 판정 → 최종 문서·제출물 정합 → 제출.
- [지금 할 일] 검증된 평가 ZIP을 서버에 올리고 런북의 한 줄 명령만 실행한다.
- [보장하지 않음] 영상 1세트나 단일 seed만으로 공식 survival_rate, 최적 reward, 예선 점수 또는 통과 가능성을 보장하지 않는다.

## 1. 이 문서가 해결하는 문제

서버는 접속마다 초기화되고, 사용자는 서버 명령 실행과 다운로드를 담당한다. 반면 로컬
`C:\dev\Nconnect\workspace\training`은 과거 run·원장·보고서를 보존하는 정본이다. 서버의
`training` 전체를 로컬에 덮어쓰면 새 run뿐 아니라 업로드 당시의 오래된 문서도 함께 돌아와
로컬 정본을 과거 상태로 되돌릴 수 있다.

따라서 모든 서버 작업은 다음 두 결과를 별도로 관리한다.

1. **필수 run bundle:** 해당 run의 checkpoint·tfevents·로그·설정·상태·해시
2. **보험 snapshot:** 서버 `/workspace/training` 전체 사본. 직접 병합하지 않고 복구·누락 확인에만 사용

## 2. 정본 우선순위

충돌할 때 아래에서 위로 덮지 않는다. 위 항목이 우선한다.

1. 실제 회수 artifact와 검증된 내용(`STATUS.txt`, params YAML, tfevents, checkpoint tensor)
2. 이 문서의 artifact 작업 원장과 파일 변경 원장
3. `PROJECT_STATE.md`의 고정 사실·결정·LATEST NEXT
4. `H1_REWARD_EVIDENCE_MASTER.md`의 reward·run 과학 판정
5. `CAMPAIGN_SCHEDULE.md`의 현재 단계·일정
6. `CAMPAIGN_PLAN.md`의 장기 방향
7. 개별 보고서와 과거 계획

파일 SHA256은 전송 무결성 증거다. `policy.pt` 동일성은 비결정적 직렬화 때문에 checkpoint
iter + `model_best.pt` SHA256과 `torch.jit.load(...).state_dict()` tensor 비교로 판정한다.

## 3. 역할과 기록 책임

| 역할 | 실행 책임 | 반드시 갱신할 곳 |
|---|---|---|
| 사용자 | 서버 시작, 제공 명령 실행, 결과 tar 다운로드 | 외부 실행 결과를 메인 팀장에게 전달. 원장 갱신 책임은 없음 |
| 메인 팀장 | 명령·회수 경로 확정, 검증, 선택 병합, 최종 상태 보고 | 이 문서, `PROJECT_STATE.md`, 관련 계획·보고서 |
| 스케줄러 | 가장 이른 미완료 단계와 필수/개선/조사 등급 관리 | `CAMPAIGN_SCHEDULE.md`, 이 문서 작업 상태 |
| 기획자 | 단일 변수, 통제 변수, 성공/실패/INCONCLUSIVE, 회수물 사전등록 | `experiment_history.csv`, `H1_REWARD_EVIDENCE_MASTER.md` |
| 분석가 | SHA·설정·seed·지표·checkpoint·H1~H7 측정 범위 판정 | 이 문서 검증 결과, reward 마스터, 해당 보고서 |
| 보고서 작성자 | 검증된 run 식별자와 근거만 인용 | `REPORT_*.md`, `TECH_REPORT_H1.md`, evidence index |

## 4. 관리 파일 목록

### 4-a. 운영·판정 정본

| 경로 | 역할 | 갱신 시점 |
|---|---|---|
| `AGENTS.md` | 모든 담당자가 따라야 할 최상위 운영 계약 | 불변 규칙 변경 시 |
| `ARTIFACT_MANAGEMENT.md` | 파일 목록·artifact lifecycle·작업 내역의 단일 진입점 | 모든 서버 작업 전/후 |
| `PROJECT_STATE.md` | 사실(F)·결정(D)·LATEST NEXT 원장 | 새 사실·결정 즉시 |
| `CAMPAIGN_SCHEDULE.md` | 현재 단계·등급·게이트·다음 일정 | 상태 전이 시 |
| `CAMPAIGN_PLAN.md` | 목표·점수축·장기 단계 계획 | 전제·범위 변경 시 |
| `H1_REWARD_EVIDENCE_MASTER.md` | reward 9개와 Run별 과학적 지위 | 새 분석 결과 수용 시 |
| `SERVER_SESSION_RUNBOOK.md` | 서버에서 복사해 실행할 검증된 명령 | 서버 패키지·경로 변경 시 |
| `REPORT_260831.md` | 현재 사용자용 종합 보고 | 캠페인 판정 변경 시 |

### 4-b. 학습·제출 artifact

| 경로/패턴 | 내용 | 병합 규칙 |
|---|---|---|
| `workspace/server_returns/<RUN_ID>/` | 서버 다운로드 최초 격리 위치 | 원본 보존, 여기서 직접 수정 금지 |
| `workspace/training/humanoid/logs/rsl_rl/humanoid/<run>/` | checkpoint, tfevents, params | 검증된 새 run 디렉터리만 추가 |
| `workspace/training/humanoid/reports/experiment_history.csv` | 실험 사전등록·결과 이력 | 기존 행 삭제 금지, Run06은 bundle 판정 후 갱신 |
| `workspace/training/humanoid/reports/*_add.md` | run별 분석 보고 | 대응 run 식별자와 근거 필수 |
| `workspace/training/humanoid/reports/EVIDENCE_INDEX_S0.md` | H1~H7 영상·근거 색인 | 최종 후보 평가 후 갱신 |
| `workspace/training/humanoid/exported/model_best.pt` | 현재 export 기준 checkpoint | 명시적 승급 결정 전 교체 금지 |
| `workspace/training/humanoid/exported/env.yaml` | 제출 환경 설정 | 채택 checkpoint와 일치 검증 후 교체 |
| `workspace/training/humanoid/exported/policy.pt` | 제출 정책 | checkpoint tensor 동일성 확인 후 교체 |
| `workspace/training/humanoid/humanoid_rewards.py` | 현재 보상 소스 | 사전등록된 단일 변경만 허용 |
| `workspace/training/humanoid/run06_server_package.zip` | 현재 서버 패키지 | SHA256 `1478e6a20d068dcbecd64ef648f1e3d1a7d5adf6e24dd6907d95b0430e8eaf86` |
| `workspace/training/humanoid/server_run06_videos.sh` | Run06 H1~H7 고정 영상 러너 | SHA256 `793ca0546d5cea3d0c63e96f61b850404e8d072e59eee6d4ac541c072e59df9f`, CRLF 0, Git Bash `bash -n` PASS; terrain seed 오류 제거·resume·3종 지형 preflight 지원 |
| `workspace/training/humanoid/run06_fixed_eval_package.zip` | Run06 H4·H6·H7 정량 평가 업로드 package | SHA256 `bf90f1943d36f5538da6aa861eab655a6fd28c2c244c4a544bc26282e05aac93`, 14 members, ZIP CRC PASS, Run06 model_9900 내장 |
| `workspace/training/humanoid/server_run06_fixed_eval.sh` | 학습 없는 32환경 고정 evaluator 러너 | CRLF 0, Git Bash `bash -n` PASS, H4 좌우·H6 ±10°·H7 push 원시 CSV 회수 |
| `workspace/training/quadruped/server_run_Go2_videos.sh` | **LEGACY_INVALID_MAPPING — 실행·G1~G7 판정 금지** | H1형 G1 stand/G2 forward/G3 lateral/G4 complex/G5 rough/G6 ±10°/G7 push로, 제공 Go2 registry와 불일치. 역사 보존만 하며 신규 evaluator가 대체해야 함 |
| `workspace/training/quadruped/quadruped_rewards.py` | Go2 실질 4변수 동시 변경 pilot 1,000 iter | `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05`; action -0.01은 불변. `MULTIVARIABLE_EXPLORATORY_BASELINE`, 개별 인과효과 미측정 |
| `workspace/training/quadruped/config/go2_self_eval_registry.json` | Go2 G1~G7 canonical 내부평가 registry | G1 forward·G2 omni·G3 rough·G4 ±20°·G5 10~15cm stairs·G6 push·G7 DR, weight sum 1.0 |
| `tools/verify_download_artifact.py` | 서버 다운로드 정형 검증기 | 외부/내부 SHA, 안전한 tar 경로, 시나리오 수, model SHA를 JSON으로 판정 |
| `.codex/agents/artifact-verifier.md` | 저비용 artifact 검증 역할 | `explore`/`gpt-5.6-luna` 전용, 의미 판정·병합·서버 종료 권한 없음 |
| `workspace/server_returns/train_260831-06_run05cfg_10000/` | Run06 검증 격리본 | bundle SHA·내부 18/18·snapshot tar 검증 완료, 아직 training 미병합 |

## 5. 서버 artifact lifecycle

```text
PLANNED → RUNNING → RECEIVED → VERIFIED → MERGED → ANALYZED → REPORTED → SUBMISSION_READY
               ↘ FAILED / INCONCLUSIVE / BLOCKED
```

| 상태 | 완료 기준 |
|---|---|
| `PLANNED` | 목적·변수·seed·iter·시간·중단점·회수물·다음 분기 기록 |
| `RUNNING` | 사용자 제공 서버 출력으로 실행 시작 확인. 실제 iter는 로그 전까지 미측정 |
| `RECEIVED` | 원본 tar가 `workspace/server_returns/<RUN_ID>/`에 있고 파일 SHA 기록 |
| `VERIFIED` | tar SHA, `TRAIN_RC`, source hash, params, seed, checkpoint, tfevents 확인 |
| `MERGED` | 병합 전/후 목록과 대상 경로 기록, 기존 정본 비파괴 확인 |
| `ANALYZED` | 사전 기준으로 `INTERNAL_GATE_PASS/FAIL/INCONCLUSIVE`와 H1~H7 측정 범위 판정 |
| `REPORTED` | reward 마스터·상태·일정·보고서가 같은 판정으로 동기화 |
| `SUBMISSION_READY` | 최종 `policy.pt`·`env.yaml`·리포트 일치와 H1~H7 증거 확인 |

## 6. 회수·병합 불변식

1. 서버 `training` 전체 다운로드는 허용하지만 **보험 snapshot**으로만 취급한다.
2. 로컬 `workspace/training`에 전체 압축을 직접 해제하거나 폴더를 통째로 덮어쓰지 않는다.
3. `/workspace/_keep/<RUN_ID>_DOWNLOAD.tar.gz`를 별도 다운로드하거나 snapshot 전 `training/_server_returns/<RUN_ID>/`로 복사한다.
4. 원본 tar는 `workspace/server_returns/<RUN_ID>/original/`에 보존하고, 분석용 해제본은 `extracted/`에 둔다.
5. 검증 전 `exported/model_best.pt`, `env.yaml`, `policy.pt`, 보고서, 원장을 교체하지 않는다.
6. 병합 전 `MERGE_PLAN.tsv`, 병합 후 `MERGE_RESULT.tsv`와 `LOCAL_SHA256SUMS.txt`를 남긴다.
7. 같은 이름의 파일은 자동 overwrite하지 않는다. 내용 비교 후 `add / replace / keep-local / conflict`를 명시한다.
8. 서버 snapshot에만 있고 필수 bundle에 없는 파일은 누락 원인을 확인한 뒤 별도 판정한다.

## 7. Run별 필수 회수 파일

| 분류 | 필수 파일/검사 |
|---|---|
| 실행 상태 | `STATUS.txt`, `TRAIN_RC`, `RUN_ID`, `MAX_ITERS`, 시작·종료 시각 |
| 무결성 | 다운로드 tar SHA256, 내부 `SHA256SUMS.txt`, source hash |
| 학습 설정 | `params/agent.yaml`, `params/env.yaml`, seed, num_envs, max_iterations |
| 곡선 | TensorBoard tfevents, `train.log` |
| 모델 | 3k/5k/10k milestone과 마지막 checkpoint |
| 소스 | `train.py`, `humanoid_rewards.py`, `h1_task/*.py`, restore 결과 |
| 제출 후보 | `model_best.pt`, `env.yaml`; `policy.pt`는 별도 export·tensor 검증 전 제출 후보 아님 |
| 분석 | Run05 대비 xy/yaw, episode length, base_contact, mean_std, H1~H7 직접/미측정 표 |

### 7-a. 학습 후 영상 필요성 판정·종료 게이트

학습 작업에는 학습 artifact와 행동 영상 artifact를 별도 상태로 둔다. 학습 bundle이
`VERIFIED`여도 영상이 필요한 run의 행동 평가는 `PENDING`이며 `ANALYZED`로 승급하지 않는다.

| 판정 | 적용 조건 | 종료 전 필수 조치 |
|---|---|---|
| `VIDEO_REQUIRED` | 새 reward/env/policy/checkpoint, 장기 학습, 후보 채택·폐기, H1~H7·survival·tracking 주장 | 고정 evaluator 영상 생성 → 로그·policy/checkpoint 식별자 포함 tar 생성 → tar와 `.sha256` 로컬 다운로드 확인 |
| `VIDEO_CONDITIONAL` | 학습 결과나 이상 징후에 따라 추가 시나리오가 달라짐 | 기본 CORE 영상을 확보하고 종료 직후 재판정; 추가 영상 필요 시 같은 세션에서 FULL로 확장 |
| `VIDEO_NOT_REQUIRED` | checkpoint 없는 smoke test 또는 동일 tensor·동일 evaluator 영상이 이미 검증됨 | 예외 근거와 대체 영상 경로·정책 식별자 기록 |
| `VIDEO_REQUIRED_NOT_ACQUIRED` | 필수 영상 생성/패키징/다운로드 실패 | 실패 로그와 재현 checkpoint·source·config 회수; 평가 완료 금지; 다음 세션 첫 작업으로 이관 |

**서버 종료 가능 조건:** 영상 판정이 기록되고, `VIDEO_REQUIRED`이면 영상 tar와 SHA가 로컬에
도착했으며 파일 존재·외부 SHA 일치까지 확인돼야 한다. 내부 파일 수·정책 대응 검증은
`RECEIVED → VERIFIED` 단계에서 수행한다. 영상이 없는 학습은 성능상 실패가 아니라
**행동 평가 미완료**다.

영상 사전등록에는 `RUN_ID / checkpoint iter+SHA / suite(CORE·FULL) / H1~H7 매핑 / seed /
num_envs / video_length / 명령 고정값 / 예상 파일 수 / 서버 경로 / 로컬 회수 경로 / 실패 시
부분 bundle 경로`를 모두 적는다.

## 8. Artifact 작업 원장 — append-only

| 작업 ID | 일시 | 등급 | RUN_ID/범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|---|
| `A260831-01` | 260831 | 조사 | 서버 회수 정책 | `REPORTED` | 없음 | 전체 snapshot 격리·선택 병합 규칙 확정 | 이 문서, `AGENTS.md`, `SERVER_SESSION_RUNBOOK.md`, 담당 지침 3종 | 완료 — 후속 작업은 이 규칙 유지 |
| `A260831-02` | 260831 | 개선 | `train_260831-06_run05cfg_10000` | `ANALYZED` | Run06 10k 자연 완료·두 tar 다운로드 | 종료·bundle·설정·곡선 검증 | `TRAIN_RC=0`, model_9900, `INTERNAL_GATE_PASS` 5/5 | Run06 동결 기준선 유지 |
| `A260831-03` | 260831 | 필수(제출요건) | Run06 필수 bundle 회수 | `VERIFIED` | 필수 bundle·전체 snapshot 다운로드 | `server_returns/<RUN_ID>/` 격리, tar·SHA·내부 18/18 검증 | `INGEST_STATUS.md`, `FILE_MANIFEST.tsv`, `LOCAL_SHA256SUMS.txt`, `MERGE_PLAN.tsv` | 원본 보존, 분석 전 병합 금지 |
| `A260831-04` | 260831 | 조사 | Run06 분석·선택 병합 | `ANALYZED` | 없음 | Run05 대비 Run06 마지막500 곡선·영상 분석 | xy·yaw·episode·base_contact·std 개선; 영상 증거 계층 정정 | 제출 후보 문서에 한계 반영 |
| `A260831-05` | 260831 | 필수(제출요건) | Run06 H1~H7 고정 영상 10종 | `VERIFIED` | resume 완료·FULL tar와 SHA 다운로드 | FULL 원본 격리·외부/내부 SHA·시나리오·model 대응 검증 | verifier PASS, 내부 47/47, video 10, policy 10, model SHA `8eb06e2…b636` | 서버 종료; A260831-04 영상·곡선 분석 시작 |
| `A260831-07` | 260831 | 개선 | 저비용 다운로드 검증 역할 | `VERIFIED` | 없음 | Luna용 read-only agent와 결정론적 검증 CLI 작성 | `artifact-verifier.md`, `verify_download_artifact.py`, Run06 FULL PASS JSON | 메인 팀장이 입력 계약·최종 의미 판정 유지 |
| `A260831-08` | 260831 | 필수(제출요건) | Run06 H4·H6·H7 고정 정량 평가 | `ANALYZED` | ZIP 업로드·한 줄 실행·FULL tar 다운로드 | 원본 telemetry 회수·로컬 보고서 재생성 | H4 yaw, H6 양방향, H7 회복 내부 측정 양호; threshold·공식 결과 없음 | 제출 후보의 보조 근거로만 사용 |
| `A260831-10` | 260831 | 개선 | 판정 지침·후속 학습 방향 | `REPORTED` | 없음 | 증거 4계층, TTL 우선 보고, 단일변수 screening·승급 규칙 확정 | `AGENTS.md`, 마스터 §9, 일정·상태·제출 리포트 동기화; candidate manifest 검증 | 공식 결과 대기 계획 철회; A260831-11로 자체 점수 확보 |
| `A260831-11` | 260831 | 필수(제출요건) | Run06 H1~H7 전체 자체 점수 | `PLANNED` | 다음 서버 접속에서 평가 전용 ZIP 업로드·한 줄 실행·FULL tar와 SHA 다운로드 | H1~H7 10 case 20초 telemetry, 내부 proxy v1 scorecard, package SHA `e897fa10…05551` | `run06_fixed_eval_package.zip`, `FIXED_EVAL_REPORT.json/md`; 학습 없음 | 회수 후 70점 게이트 판정, 최대 감점 시나리오만 screening |
| `A260831-09` | 260831 | 조사 | Go2 pilot·구형 영상 스위트 | `INCONCLUSIVE` | 실행 금지 | 제공 Go2 registry와 구형 runner 매핑 대조 | pilot artifact는 존재하나 구형 runner는 `LEGACY_INVALID_MAPPING`; G1~G7 미측정 | `G-A002` 신규 evaluator로 대체 |
| `G-A001` | 260901 | 조사 | Go2 운영체계·자체평가 재설계 | `REPORTED` | 없음 | 별도 원장·전용 역할 4종·canonical registry·protocol·handoff·validator 작성 | `GO2_*`, `.codex/agents/go2-*`, `validate_go2_campaign.py` | 새 세션에서 G-A002 evaluator 구현 |
| `G-A002` | 260901 | 필수(제출요건) | Pilot-01 정확한 G1~G7 평가 package | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | telemetry/report/lineage/worst-case video runner와 package builder/test 구현 완료 | package 로컬 검증 완료; 서버 결과는 `[미측정]` | `G-A005` package로 실행 |
| `G-A003` | 260901 | 조사 | Pilot-01 기반 초기 캠페인 계획 | `REPORTED` | 없음 | frozen artifact·control 유효성 감사, 평가→조건부 control→단일변수 ablation→승급 계획 작성 | `.omx/plans/go2-post-pilot-initial-work-plan.md`, G-F10·G-D08, 일정·reward 원장 동기화 | `G-A002` evaluator/package 구현 |
| `G-A004` | 260901 | 조사 | Default-01 1,000 iter + Pilot-01 쌍대 G1~G7 평가 | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | Default test PRD·상세계획·통합 runner 구현 완료 | Default 결과는 `[미측정]`; `VIDEO_REQUIRED`: 정책별 worst-case G1~G7 7개, seed 101/202/303 중 정량 최악 seed, 500 steps, 결과 ZIP `evaluation/<policy>/videos/` | `G-A005` 실행 → 정책별 69 telemetry·7 영상 회수 |
| `G-A005` | 260901 | 필수(제출요건) | Go2 Default-vs-Pilot 단일 실행·회수 package | `VERIFIED` | `/workspace/go2_default_vs_pilot_v1.zip` 업로드 후 검증된 한 줄 실행 | deterministic ZIP build, reward-only default staging, embedded Pilot SHA, manifest, runner syntax·contract test | `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`; 28 members; ZIP CRC·manifest·CRLF·Git Bash `bash -n` 검증 | 서버 실행 후 `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`과 SHA 회수 |

## 9. 파일 변경 원장 — append-only

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260831 | `A260831-01` | `ARTIFACT_MANAGEMENT.md` | 중앙 파일 목록·artifact lifecycle·작업 원장 신설 | 필수 절·표·링크 검사 |
| 260831 | `A260831-01` | `AGENTS.md` | 서버 snapshot 비덮어쓰기와 중앙 문서 선조회 규칙 | 규칙 중복·마커 확인 |
| 260831 | `A260831-01` | `SERVER_SESSION_RUNBOOK.md` | Run06 완료 후 필수 bundle·보험 snapshot 회수 명령 | package SHA 일치·shell 명령 정적 검토 |
| 260831 | `A260831-01` | `PROJECT_STATE.md` | F48~F51, D39~D42, LATEST NEXT 기록 | append-only 확인 |
| 260831 | `A260831-01` | `CAMPAIGN_PLAN.md`, `CAMPAIGN_SCHEDULE.md`, `REPORT_260831.md` | 현재 단계 2/6 및 Run06 자연 완료·격리 회수 동기화 | 첫 화면 8항목 검사 |
| 260831 | `A260831-01` | `.codex/agents/*.md` | 기획·일정·분석·보고 시 중앙 운영 문서와 작업 원장 참조 | 3개 담당 지침 검색 |
| 260831 | `A260831-03` | `workspace/server_returns/train_260831-06_run05cfg_10000/` | 원본 bundle·snapshot 격리, tar 해제본, manifest·merge plan·수신 기록 작성 | bundle SHA 일치, tar 2종 PASS, 내부 checksum 18/18 PASS |
| 260831 | `A260831-05` | `workspace/training/humanoid/server_run06_videos.sh` | H1~H7 10종 고정 명령 영상·로그·policy를 CORE/FULL tar로 회수하는 러너 신설 | 8,155 B, CRLF 0, Git Bash `bash -n` PASS |
| 260831 | `A260831-06` | `AGENTS.md`, `ARTIFACT_MANAGEMENT.md`, `SERVER_SESSION_RUNBOOK.md`, `.codex/agents/*.md` | 학습 전·후 영상 필요성 재판정과 영상 다운로드 전 서버 종료 금지 게이트 신설 | 중앙 규칙·역할별 체크리스트·종료 보고 필드 대조 |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/`, `server_run06_videos.sh` | CORE/PARTIAL 원본 격리·검증 및 H5 terrain seed 타입 오류 제거·resume 기능 추가 | 외부 SHA 2종 PASS, tar 2종 PASS, 내부 36/36 PASS, model SHA 일치, Git Bash `bash -n` PASS |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/` | FULL tar·SHA 격리, 해제본·검증 JSON 보존 | tar SHA `c80f972c…9be`, 내부 47/47 PASS, video/policy 10/10, model SHA 일치 |
| 260831 | `A260831-07` | `.codex/agents/artifact-verifier.md`, `tools/verify_download_artifact.py` | 저비용 정형 다운로드 검증 역할·JSON 검증기 신설 | Run06 FULL 입력에서 rc=0, status PASS |
| 260831 | `A260831-08` | `eval_telemetry.py`, `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `run06_fixed_eval_package.zip`, `tools/test_fixed_eval_contract.py` | 기존 play 경로에 opt-in step telemetry를 추가하고 Run06 model_9900 고정 평가 package 생성 | unittest 5/5, Python compile, Git Bash `bash -n`, ZIP CRC·14 members·내장 model SHA PASS |
| 260831 | `A260831-09` | `SERVER_SESSION_RUNBOOK.md` | Go2 G1~G7 영상 스위트 절차 추가 — H1 `server_run06_videos.sh` 벤치마킹 문단 신설 | H1 10종 구조·CORE/FULL·fingerprint·검증 동일 명시, Go2 10종 매핑·명령 인자 대조 |
| 260831 | `A260831-09` | `workspace/training/quadruped/server_run_Go2_videos.sh` | H1 `server_run06_videos.sh`(8,155B) 벤치마킹해 Quadruped-v0 10종 포팅 — G1·G2·G3×2·G4×2·G5·G6×2·G7, seed 42·4 env·1000 step | CRLF 0, model SHA `C4D78ADF…`, Quadruped-v0 task 전환·G시나리오 매핑 확인 |
| 260831 | `A260831-09` | `workspace/training/quadruped/quadruped_rewards.py` | 이미지 5변수 반영 — `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05` (실질 4개 변경) | `grep` 4/4 일치, `report.html` 4/4 주황 점, Python AST PASS |
| 260831 | `A260831-10` | `AGENTS.md`, `.codex/agents/prelim-campaign-manager.md`, `.codex/agents/humanoid-test-planner.md`, `.codex/agents/humanoid-report-writer.md` | artifact·영상·내부 gate·공식 결과 분리, 서버 TTL 우선 답변, 학습 승인 규칙 추가 | 필수 제목·용어 검색, `git diff --check` |
| 260831 | `A260831-10` | `H1_REWARD_EVIDENCE_MASTER.md`, `CAMPAIGN_SCHEDULE.md`, `PROJECT_STATE.md`, `experiment_history.csv` | Run06 단계 5/6 동기화, 공식 산식과 내부 proxy 경계 정정, 후속 screening 순서 확정 | H1~H7 증거 행렬·F69~F70/D56~D58·현재 단계 대조 |
| 260831 | `A260831-10` | `workspace/submission_candidates/h1_run06_model9900/`, `workspace/training/humanoid/exported/TECHNICAL_REPORT.md`, `workspace/training/humanoid/reports/TECH_REPORT_H1_RUN06_FINAL.md` | 제출 리포트 판정 용어·공식 산식 출처 정정 및 3개 사본 동기화 | report SHA 동일, candidate `SHA256SUMS.txt` 5/5 일치; policy/env/model hash 불변 |
| 260831 | `A260831-11` | `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `RUN06_FIXED_EVAL_README.txt`, `tools/test_fixed_eval_contract.py` | H4·H6·H7 부분 평가를 H1~H7 10 case 전체 20초 평가로 확장하고 내부 시뮬 proxy /70 게이트 추가 | unittest 8/8, compile, Git Bash `bash -n`, ZIP 14 members·SHA `e897fa10…05551` |
| 260831 | `A260831-11` | `AGENTS.md`, 담당 agent 3종, 마스터·일정·상태 원장 | 부분 PASS 점수 제외, 공식 결과 대기 철회, 총 자체예상 70/100 최소·75/100 목표 규칙 | `SELF_ASSESSMENT_INCOMPLETE`, threshold, NEXT 문구 대조 |
| 260831 | `A260831-11` | `SELF_ASSESSMENT_RUBRIC.md`, 제출 후보 리포트 3개 사본·manifest | 문서 자체감사 27/30 고정, 부분 평가를 성능 승급에서 제외 | report 3개 SHA 동기화, candidate manifest 6/6 PASS |
| 260901 | `G-A003` | `.omx/plans/go2-post-pilot-initial-work-plan.md`, `GO2_PROJECT_STATE.md`, `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`, `ARTIFACT_MANAGEMENT.md` | 1차 튜닝 이후 평가 우선 초기계획, 유효 control 부재, 최소 경로·예산·재평가점 기록 | `validate_go2_campaign.py` PASS, `git diff --check` PASS |
| 260901 | `G-A004` | `GO2_DEFAULT_BASELINE_TEST_PRD.md`, `.omx/plans/go2-default-baseline-experiment-plan.md`, Go2 상태·일정·reward·handoff, `ARTIFACT_MANAGEMENT.md` | 조건부 control 계획을 Default-01 필수 생성·Pilot 쌍대평가·기본값 one-at-a-time 계보로 정정 | `validate_go2_campaign.py`, 문서 계약 검사, `git diff --check` |
| 260901 | `G-A004` | Default test PRD·상세계획, Go2 역할 지침 5종, 상태·일정 | PRD를 매 기획 턴 참조·동일 턴 갱신하는 living contract로 승격하고 `PRD_CHANGE`·`LEDGER_SYNC` 게이트 추가 | `validate_go2_campaign.py`, PRD lifecycle 계약 검사, `git diff --check` |
| 260901 | `G-A005` | Go2 evaluator·lineage·통합 runner·builder·tests·README, `play.py`, `train.py`, `go2_task/env_cfg.py` | Default 1k와 Default/Pilot 69-case·worst-video 평가를 단일 업로드/명령/결과 ZIP 구조로 구현 | Python compile·5 unit tests, Git Bash `bash -n`, CRLF 0, ZIP CRC·safe paths·27-file internal manifest, Pilot SHA, reward-only 4-line diff |
| 260901 | `G-A005` | Go2 PRD·상태·일정·상세계획·AGENTS·handoff·planner brief | G-D13 사용자 실행 package 자동 제공 계약과 실제 경로·SHA·완료표식·회수 게이트 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 10. 새 작업 기록 템플릿

```markdown
| `A<YYMMDD>-<NN>` | <일시> | 필수(제출요건)/개선/조사 | <RUN_ID/범위> | `PLANNED` | <사용자 실행> | <로컬 작업> | <사전 증거> | <첫 NEXT> |
```

작업 완료 시 새 행을 만들지 않고 같은 작업 ID의 상태와 증거를 전진시킨다. 범위가 달라지거나
새 서버 비용이 생기는 경우에만 새 작업 ID를 만든다. 외부 시스템의 사용자 행동은 로그·파일로
확인되기 전 `[미측정]`으로 두며, 우리가 지시한 사실과 사용자가 실제 수행한 사실을 구분한다.

### A260831-11 상태 전이 — 260901

- 상태: `PLANNED → RECEIVED → VERIFIED → ANALYZED`
- 원본: `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz`
- 외부 SHA-256: `4e552b2caea4f9a33475bf7a93bc35a383c9aa9b79a42e308b002c01674b860f`
- 검증: 안전 경로 0, 내부 69/69, case 10/10, `RUNNER_RC=0`, model SHA 일치
- 분석: 66.0414/70, `CALIBRATION_PASS / GENERALIZATION_UNVERIFIED`

### A260901-01 — 독립 multi-seed 검증

| 항목 | 값 |
|---|---|
| 등급 | 필수(제출요건) |
| 상태 | `SUBMISSION_READY` |
| 정책 | Run06 model_9900, SHA `8eb06e2…b636` 동결 |
| seeds | 101, 202, 303 사전등록 |
| 범위 | seed별 H1~H7 10 case, 32 env, 1,000 step |
| 판정 | 시나리오별 최악 seed, 세 seed 모두 통과 |
| 영상 | `VIDEO_NOT_REQUIRED` — 동일 checkpoint 영상 10종 VERIFIED, 이번 작업은 seed telemetry |
| 패키지 | `workspace/training/humanoid/run06_independent_eval_package.zip` |
| package SHA-256 | `ed235d67f2f2f4decb2fec71cc1d2664a45f2304b928dff5d20d9be343f584d2` |
| 예상 서버 시간 | 15~25분, 학습 없음 |
| 필수 회수 | `..._INDEPENDENT_EVAL_FULL.tar.gz`와 `.sha256` |
| 결과 | 외부 SHA 일치, 내부 189/189, 30/30 case, 실패 seed·시나리오 0, 65.73/70 |
| 후보 | `workspace/submission_candidates/h1_run06_model9900/UPLOAD_READY/` 3종, manifest 3/3 |
| NEXT | 팀 대시보드 업로드·접수 증거 회수 |

## 11. Go2 partial 수신 및 복구 — `G-A006` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 확보 | 미확보 / NEXT |
|---|---|---|---|---|---|
| `G-A006` | 필수(제출요건) | Default-vs-Pilot 결과 회수·복구 | `RECEIVED` | Default 학습 artifact, Default telemetry 69/69, 부분 결과 461파일 | Pilot telemetry 0/69, 영상 0/14, 비교 보고서, FULL ZIP 및 유효 SHA. 서버 종료 불가; hotfix resume 후 재회수 |

- 서버 원본: `/workspace/_keep/go2_default_vs_pilot_v1/`
- 최초 로컬 inbox: `workspace/_keep/go2_default_vs_pilot_v1/`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/`
- 부분 결과: `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`, 519,957,865 bytes
- 로컬 directory manifest SHA-256: `2b7867626065552ee1fe1a73a07a79a8ac577cb3ef0a03e481b6b0607e00b8a4`
- 수신한 `GO2_DEFAULT_VS_PILOT_RESULT.zip.sha256`는 0 byte라 무결성 증거로 사용할 수 없다.
- 원인: Default 평가 후 Pilot의 `exported/`를 삭제한 뒤 같은 경로에서 checkpoint를 복사했고, 실패 packaging이 서버에 없는 bare `python3`를 호출했다.
- 현재 서버용 hotfix: `workspace/training/quadruped/go2_default_vs_pilot_v1_hotfix.zip`, SHA-256 `b2fa2d57aee9ab55ea9765171d8230c8aeac8c38bbe46285548c864b4eee2d39`.
- 새 서버용 수정 통합 package: `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA-256 `db239f77fe3336209ecb8d4f38478c1fc1dd605fbf5c0351e95a9ba1b7e74cfd`.
- 폐기된 최초 package는 격리 원본에 `go2_default_vs_pilot_v1_buggy.zip`으로 보존했다. SHA-256 `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`이며 다시 실행하지 않는다.
- 다운로드 매핑 정본: `workspace/server_returns/DOWNLOAD_MAP.tsv`.
- 병합: `NOT_PERFORMED`; FULL 결과 검증 전 `workspace/training/quadruped`에 run 결과를 병합하지 않는다.

### G-A006 FULL 회수 검증 — 260901

- 상태: `RECEIVED → VERIFIED`
- 회수물: `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` 및 `.sha256`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/`
- 외부 SHA-256: `af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b` 일치
- package: 925 entries, unsafe path 0, `RESULT_STATE=FULL`, `RUNNER_RC=0`
- 필수 telemetry: Default 69/69, Pilot 69/69
- 필수 영상: Default 7/7, Pilot 7/7, 14개 모두 non-empty; 관찰 판정은 `VIDEO_UNKNOWN`
- 내부 manifest: launcher.log 1건만 packaging 종료행 후첨으로 불일치, 나머지 923건 일치·누락 0
- 판정: `ARTIFACT_VERIFIED`; 서버 종료 가능. 병합은 `NOT_PERFORMED`, 다음 상태는 `ANALYZED`.
- 상세: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/VERIFICATION_STATUS.md`

### G-A006 선택 병합·분석·보고 — 260901

- 상태: `VERIFIED → MERGED → ANALYZED → REPORTED`
- 선택 병합: paired/self-eval JSON·MD 4개와 14개 영상 contact sheet만 `workspace/training/quadruped/reports/evidence/go2_default_vs_pilot_260901/`에 추가했다.
- 원본 MP4·FULL ZIP은 `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/`에서 보존하며 로컬 training 정본에 통째로 덮어쓰지 않았다.
- 병합 증거: `MERGE_PLAN.tsv`, `MERGE_RESULT.tsv`, `LOCAL_SHA256SUMS.txt`; 18개 대상 모두 `OK`.
- 영상 판정: 각 MP4의 3%~97% 구간 12프레임 직접 관찰, `VIDEO_OBSERVED`; 연속 gait timing·foot contact는 미측정.
- 분석: Default `17.90699/70`, Pilot `41.97990/70`, delta `+24.07291/70`; 둘 다 `INTERNAL_GATE_FAIL`; 분기 `SHARED_WEAKNESS_FOUND`.
- 보고서: `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.
- NEXT: Default 계보 `feet_air_time .01→.2` 단일변수 1,000-iter screening을 별도 작업 ID로 사전등록한다.

## 12. Go2 단일변수 screening package — `G-A007` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A007` | 개선 | Default 계보 `feet_air_time 0.01→0.20` only, 1,000 iter | package `VERIFIED` / result `RECEIVED(PARTIAL)` | 학습 완료, evaluator 8건 뒤 Isaac Sim crash; 재개 실행 표식은 아직 `[미측정]` | PARTIAL ZIP·SHA 격리, CRC·safe path·training artifact·8 telemetry 확인 | result SHA `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5` | 동일 서버에서 `GO2_RESUME=1`; FULL ZIP·SHA 재회수 전 서버 종료 불가 |

### 사전등록된 artifact·영상 계약

- RUN_ID: `train_260901-Go2_feet_air_time_020_1000`
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `feet_air_time 0.01→0.20`; 나머지 네 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1~G7 정량 worst-case 각 1개, 총 7개, 평가 seed 101/202/303 중 worst seed, 4 env, 500 steps, 약 10초.
- Default 영상은 `VIDEO_NOT_REQUIRED`: 동일 Default-01 tensor·동일 registry/evaluator의 7영상이 G-A006에서 `ARTIFACT_VERIFIED`·`VIDEO_OBSERVED`; `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/default/`을 재사용한다.
- telemetry: candidate 69건, G1~G7 survival·tracking·G5 completion·G6 recovery·G7 실현값.
- 필수 정책 증거: `model_best.pt`, `env.yaml`, `policy.pt`, `POLICY_LINEAGE.json`, source·diff·log·checkpoint·tfevents·params.
- 실패 회수: `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`이 `PARTIAL`로 만들어져 가능한 checkpoint·source·config·launcher log를 보존한다.
- 정상 회수: 같은 결과 ZIP이 `FULL`, `RUNNER_RC=0`, telemetry 69, video 7을 포함해야 한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 위 두 파일 로컬 도착·외부 SHA 일치·ZIP CRC·내부 manifest·69 telemetry·7영상·lineage 확인 전 종료 불가.

### 로컬 검증 증거

- 사전등록 PRD: `workspace/training/quadruped/reports/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`.
- package: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip`.
- package SHA companion: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip.sha256`.
- 상세 검증: `workspace/training/quadruped/go2_feet_air_time_020_v1.VERIFICATION.md`.
- 검증: deterministic rebuild SHA 일치, ZIP CRC·safe path, 내부 manifest 94/94, 단일 reward diff, frozen baseline 69/69·identity, Python compile, contract 5/5, CRLF 0, Git Bash `bash -n`.
- 예상 실행 창: 이전 artifact 실측을 기준으로 1시간 35분~2시간. 전체 서버 과금 시간은 보장하지 않는다.

### PARTIAL 결과 회수 — 260901

- 로컬 원본 보존: `workspace/server_returns/go2_feet_air_time_020_v1_partial_260901/original/`.
- 외부 SHA: `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, companion과 일치.
- ZIP: 96 members, CRC 정상, unsafe path 0, `RESULT_STATE=PARTIAL`, `RUNNER_RC=5`.
- 학습: `TRAIN_RC=0`, seed 42, 4096 env, 1,000 iter; candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`.
- 평가: telemetry 8/69, candidate video 0/7, `POLICY_LINEAGE.json` 미생성. 따라서 `ARTIFACT_VERIFIED` 미달, `VIDEO_UNKNOWN`, `INTERNAL_GATE_INCONCLUSIVE`, `OFFICIAL_RESULT_UNMEASURED`.
- 실패점: `G2/combined_yaw_left`, eval seed 101 시작 시 Isaac Sim startup segmentation fault; 이미 완료된 8건은 fingerprint로 재사용 가능하다.
- 내부 manifest: 95건 중 94건 일치, `launcher.log` 1건은 manifest 생성 뒤 tee가 계속 기록하는 기존 packaging 순서 문제로 불일치. 외부 ZIP SHA와 CRC는 일치하지만 FULL 결과에서 다시 감사한다.
- 고정 검사 도구 `tools/verify_download_artifact.py`는 tar/gzip 전용이라 ZIP 입력을 `ESCALATE`했다. 메인 루프가 ZIP CRC·safe path·manifest·count를 직접 검증했다.
- 재개 명령: `cd /workspace/go2_feet_air_time_020_v1 && GO2_RESUME=1 bash server_run_go2_feet_air_time_020_v1.sh`.
- 서버 종료 게이트: FULL 결과 ZIP·SHA를 다시 내려받아 telemetry 69·video 7·lineage·policy와 무결성을 로컬 검증하기 전까지 **종료 불가**.

### 파일 변경 원장 추가

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260901 | `G-A007` | screening PRD·runner·reporter·builder·tests·README·ZIP | Default report 재사용 + candidate 1회 학습/69-case/7영상/단일 결과 ZIP 구현 | deterministic SHA, ZIP CRC·manifest, compile, tests 5/5, `bash -n`, CRLF 0 |
| 260901 | `G-A007` | Go2 PRD·상태·일정·reward master·planner brief·AGENTS | 단계 3 현재 위치, 사전 gate, package 경로·실행·회수·종료 조건 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 13. Go2 evaluator graceful-shutdown hotfix ? `G-A008` (260901)

| ?? ID | ?? | ?? | ?? | ??? ?? | ?? ?? | ?????? | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A008` | ??(????) | G-A007 candidate ??? ?? evaluator ?????? ?? ?? | `VERIFIED` | v1 ?? ?? `[???]`; v2 ?? ?? ?? ?? | PARTIAL ?? ??, graceful stop, bounded retry, stable manifest, deterministic package | `go2_feet_air_time_020_v2.zip`, SHA `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`, tests 6/6 | ?? v1 ??? ?? ?? ??; v2? completed case?checkpoint ??? ?? |

### ????? ??

- `BUGGY_DO_NOT_REUSE`: v1 telemetry? hard process exit ??? retry ?? runner.
- ?? ??: v1? 8 case ?? ? ?? Isaac startup? `XOpenDisplay` ?? segmentation fault? ?? ??? ????.
- ?? ?? ??? ??: ?? horizon?? `env.step()` ???? ????? ?? ??? upstream `env.close()`?`simulation_app.close()`? ????.
- v2: hard-exit AST call 0, `simulation_app.is_running()` false? ?? loop exit, case/video ?? 3? bounded retry, ?? case fingerprint ???.
- manifest ??: active `launcher.log`? ???? immutable `launcher.snapshot.log`? package??.
- ??: deterministic SHA, ZIP CRC, safe path, manifest 94/94, Python compile, contract 6/6, Git Bash `bash -n`.
- ??: NVIDIA Kit ?? segmentation fault ??? ???? ???? ???. v2? ?? cleanup? ???? transient startup failure? ?? ??? ?? ???? ??? ??.

### ?? ?? ??

| ?? | ?? ID | ?? | ?? ?? | ?? |
|---|---|---|---|---|
| 260901 | `G-A008` | `go2_eval_telemetry.py`, runner, result packager | hard exit ??, graceful close, bounded retry, live-log manifest race ?? | compile, contract 6/6, AST hard-exit 0, `bash -n` |
| 260901 | `G-A008` | builder, v2 README, v2 ZIP, verification | ??? ?? ?? ?? resume hotfix package | SHA `73c6ba1f?8dbc`, deterministic rebuild, CRC, manifest 94/94 |

## 14. Go2 feet_air_time 0.20 FULL 재수신 — `G-A007` (260901)

- 등급: `개선`
- lifecycle: `RECEIVED`
- 로컬 inbox: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`
- 수신 시각: 2026-09-01 20:53 KST
- 파일 크기: 207,738,612 bytes
- 외부 ZIP SHA-256: `ec45628bae08092f7d671ea5c4cc409d9a247bde80e5bd4214d13b191239effc` (companion 일치)
- 1차 비파괴 검사: ZIP CRC 정상, unsafe path 0, `RESULT_STATE=FULL`, 69개 case `EVAL_RC=0`, 영상 7개, `policy.pt`·`POLICY_LINEAGE.json`·`model_best.pt`·`env.yaml` 존재.
- 격리 예정 경로: `workspace/server_returns/go2_feet_air_time_020_v1_full_260901/`
- NEXT: 격리 추출 → 내부 manifest/정책 lineage/69 telemetry/7 영상 검증 → 선택 병합·분석·원장 갱신.

## 15. Go2 track-linear 단일변수 screening — `G-A009` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A009` | 개선 | Default 계보 `track_lin_vel_xy_exp 1.0→1.2` only, 1,000 iter + 저비용 단계평가 | `REPORTED` | ZIP 업로드·한 줄 실행·결과 ZIP 2종 다운로드 완료 | 격리·무결성·정량 비교·G1 영상 판독·원장 갱신 완료 | result SHA `d9d84f68…61c3`, manifest 125/125, candidate/baseline 7/7, G1 `VIDEO_OBSERVED`, 분석 보고서 | G-A010 engine+JSON 로컬 준비 |

### 사전등록 artifact·영상 계약

- RUN_ID: `train_260902-Go2_track_lin_vel_120_1000`.
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `track_lin_vel_xy_exp 1.0→1.2`; 나머지 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1 forward-fast seed 101, 4 env, 500 step, 1개.
- telemetry: 조기중단 candidate 7 + baseline 7; 조기통과 때 candidate 21 + baseline 7.
- 결과 ZIP: `/workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 실패도 `PARTIAL` ZIP으로 checkpoint·source·config·log·완료 case를 자동 보존한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 두 파일 로컬 도착·외부 SHA·ZIP CRC·manifest·예상 case 수·영상 1·policy lineage를 검증하기 전 종료 판정 금지.

### package 검증

- 경로: `workspace/training/quadruped/go2_track_lin_vel_120_v1.zip`.
- SHA-256: `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`.
- 6,467,257 bytes, 46 members, CRC OK, unsafe path 0, manifest 45/45.
- deterministic rebuild SHA 동일, Python compile, contract 9/9, Git Bash `bash -n`, CRLF 0.
- evaluator: G5 per-env body-velocity integral v2, G7 `NCRC_EVAL_DR=1`, 공식 등가성 주장 없음.

### result 회수·종료 게이트 검증

- 수신 파일: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 격리 원본: `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/original/`.
- 외부 ZIP SHA-256: `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`; companion 일치.
- package: 126 members, CRC 정상, unsafe path 0, 내부 manifest 125/125 일치, `RESULT_STATE=FULL`, `RUNNER_RC=0`, `TRAIN_RC=0`.
- 학습물: model SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`, `model_900.pt`, `env.yaml`, tfevents, params, source, reward diff 확인.
- 평가물: candidate/baseline telemetry 7/7, candidate G1 영상 1/1(1,932,776 bytes), `POLICY_LINEAGE=ACTOR_TENSORS_MATCH` 8/8.
- 증거 계층: `ARTIFACT_VERIFIED`, G1 `VIDEO_OBSERVED`, runner decision `INTERNAL_EARLY_KILL_FAIL`, `OFFICIAL_RESULT_UNMEASURED`.
- 종료 판정: 필수 회수물 누락 0; 서버 종료 가능. 상세 검증은 격리 경로의 `VERIFICATION.json`, `INGEST_STATUS.md`, `LOCAL_SHA256SUMS.txt`에 보존.

### result 분석·영상 증거 보존

- 분석 보고서: `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`.
- 찾기 쉬운 영상: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/videos/G1_forward_fast_seed_101.mp4`.
- contact sheet: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/contact_sheets/G1_forward_fast_seed_101_contact_sheet.jpg`.
- 영상 원본↔복사본 SHA-256: `9d81170136efebbcfb1e708a36b438900365a1da47a32d1cc25a83ba303c6cdb`, 일치.
- 정량 CSV: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/G_A009_COMPARISON.csv`.
- 기계판독 요약·해시: 같은 폴더의 `ANALYSIS_SUMMARY.json`, `SHA256SUMS.txt`.
- 최종 계층: `ARTIFACT_VERIFIED`; G1 `VIDEO_OBSERVED`; G-A009 `INTERNAL_EARLY_KILL_FAIL`; `OFFICIAL_RESULT_UNMEASURED`.

## 16. Go2 `lin_vel_z_l2` 단일변수 screening — `G-A010` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A010` | 개선 | Default 계보 `lin_vel_z_l2 -3.0→-2.0` only, 1,000 iter + tier-1 조기평가 | `PLANNED` | `upload/G-A010/current`의 engine ZIP·JSON 업로드 후 한 줄 실행 | 고정 engine v1.1·JSON·PRD·run guide·contract 검증 완료 | engine SHA `e8f8b3cd…b7cd`, spec SHA `e59dcb93…f8c9`, 34 members, manifest 33/33, tests 8/8, `bash -n` | 서버 실행 → 결과 ZIP 2종 회수 |

- 기준 policy: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `lin_vel_z_l2 -3.0→-2.0`.
- 고정 reward: `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 고정 학습: from-scratch, seed 42, 4096 env, 1,000 iter.
- `VIDEO_REQUIRED`: candidate G1 `forward_fast`, seed 101, 4 env, 500 step, 1개. 학습 종료 뒤 이상 징후가 있으면 추가 시나리오를 재판정한다.
- 조기평가: candidate G1~G7 대표 7-case, repaired-v2 baseline과 paired 비교. G1 proxy `+0.05` 미만 또는 어느 G survival `-0.10` 초과 하락이면 즉시 종료·회수한다.
- 대표평가·69-case·장기학습은 tier-1 조기통과 전 금지한다.
- 현재 upload engine ZIP: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA-256 `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 현재 upload JSON: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA-256 `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 검증: deterministic rebuild, ZIP CRC, unsafe path 0, manifest 33/33, extracted-engine materialization, contract 8/8, Python compile, CRLF 0, Git Bash `bash -n`.
- 서버 한 줄 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.
- 완료 표식: `[DONE] GO2_LIN_VEL_Z_M2_RESULT_READY`.
- 결과 ZIP: `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256`; 성공·실패 모두 가능한 artifact를 단일 ZIP으로 자동 묶는다.
- 실행 지침: `workspace/training/quadruped/upload/G-A010/current/GO2_G_A010_RUN_GUIDE.txt`; package 상세: 같은 폴더의 `go2_tuning_engine_v1_1.VERIFICATION.md`.
- 현재 계층: upload package만 `ARTIFACT_VERIFIED`; 외부 실행·checkpoint·telemetry·영상은 `[미측정]`, `OFFICIAL_RESULT_UNMEASURED`.

## 17. G-A010 server-preflight Python launcher hotfix — `G-A012` (260902)

- 최초 engine v1.0은 bare `python3`를 호출해 서버에서 `command not found`로 종료됐다. tmux·학습은 시작되지 않아 iteration 소비는 0이다.
- v1.0 SHA `4489bef4…8a5a`는 `BUGGY_DO_NOT_REUSE`다.
- hotfix engine: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 같은 폴더의 spec: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 수정: validate·shell-env·materialize를 모두 `/workspace/IsaacLab/isaaclab.sh -p`로 실행하고 bare `python3` 의존을 제거했다.
- 검증: ZIP 34 members, CRC, unsafe 0, manifest 33/33, contract 8/8, extracted materialization, compile, CRLF 0, `bash -n`.
- 새 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.

## 18. Go2 업로드 staging·이력 체계 — `G-A013` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A013` | 필수(운영) | Go2 서버 입력의 단일 업로드 진입점과 버전 이력 | `REPORTED` | `upload/<ID>/current`에서 지시된 두 파일만 선택 | current/history 분리·SHA copy 검증·append-only ledger 자동화 | `upload/README.md`, `G-A010/UPLOAD_HISTORY.tsv`, `tools/publish_go2_upload_bundle.py` | 이후 모든 Go2 실행 package를 동일 체계로 publish |

- 사용자 업로드 진입점은 `workspace/training/quadruped/upload/<EXPERIMENT_ID>/current/`로 고정한다.
- `history/<RELEASE_ID>/`는 release snapshot이며 과거 파일을 현재 사용본으로 승격하지 않는다.
- `UPLOAD_HISTORY.tsv`는 v1.0 `WITHDRAWN_BUGGY_DO_NOT_REUSE`와 v1.1 `ACTIVE_ARTIFACT_VERIFIED`를 분리 기록한다.
- publisher는 원본과 current/history 복사본 SHA를 비교하고, 같은 release identity는 ledger에 중복 추가하지 않는다.
