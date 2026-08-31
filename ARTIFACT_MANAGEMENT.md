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
| `workspace/training/quadruped/server_run_Go2_videos.sh` | Go2 G1~G7 고정 영상 러너 (H1 벤치마킹) | Quadruped-v0, 10종(G1·G2·G3×2·G4×2·G5·G6×2·G7), SHA `9fb41a14839400f277a616c9e1f010c0f8c4af5fcd8b463784a9e78444ff6c9f` (12,666B, CRLF 0), model SHA `C4D78ADF3FBD90311E70D2B165370DDDED3D5F913E8F128621FA1BE45F89AF8D`, Git Bash `bash -n` PASS; CORE/FULL 2단 패키징, fingerprint, VIDEO_STATUS.tsv 지원 |
| `workspace/training/quadruped/quadruped_rewards.py` | Go2 5변수 pilot 1,000 iter (1.2/0.2/-2/-0.05) | `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05` 반영, `model_best.pt` 6.8M |
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
| `A260831-09` | 260831 | 개선 | Go2 5변수 pilot 1,000 + G1~G7 영상 스위트 | `PLANNED` | Go2 `server_run_Go2_videos.sh` 업로드·`VIDEO_SUITE=full` 실행·FULL tar 2파일 다운로드 | H1 `server_run06_videos.sh` 벤치마킹해 Quadruped-v0 10종 포팅, RUNBOOK에 Go2 절차 추가 | H1 대비 Go2 `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05`, CORE 4종→FULL 10종 동일 구조, model SHA `C4D78ADF…` | 서버 스위트 실행 후 VERIFIED |

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

## 10. 새 작업 기록 템플릿

```markdown
| `A<YYMMDD>-<NN>` | <일시> | 필수(제출요건)/개선/조사 | <RUN_ID/범위> | `PLANNED` | <사용자 실행> | <로컬 작업> | <사전 증거> | <첫 NEXT> |
```

작업 완료 시 새 행을 만들지 않고 같은 작업 ID의 상태와 증거를 전진시킨다. 범위가 달라지거나
새 서버 비용이 생기는 경우에만 새 작업 ID를 만든다. 외부 시스템의 사용자 행동은 로그·파일로
확인되기 전 `[미측정]`으로 두며, 우리가 지시한 사실과 사용자가 실제 수행한 사실을 구분한다.
