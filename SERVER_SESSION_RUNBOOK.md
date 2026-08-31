# H1 휘발성 서버 세션 런북

> **260831 운영 정정:** 서버 사용시간이 제한되므로 복원만 하려고 서버를 켜지 않는다.
> 로컬에서 실행 목적·스크립트·회수 경로를 모두 확정한 뒤, 서버에서는
> `업로드 1회 → 실행 1줄 → bundle 다운로드`로 끝낸다. 복원은 실행 스크립트 내부의 사전검사다.
> 파일 목록·작업 ID·검증·병합 상태의 정본은 `ARTIFACT_MANAGEMENT.md`다.

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 후보의 H1~H7 실제 행동과 설계 의도 20점·리포트 10점의 영상 증거를 확보한다.
- [현재 단계] **단계 1/6 — H4 정량 기본 행동 게이트.** H4 yaw 추종량이 가장 이른 미완료 증거다.
- [확보] Run06 10,000 iter·model_9900·학습/영상 artifact 정합, 사전등록 수치 게이트 5/5 PASS, H1~H3·H5 시각 PASS.
- [미확보] H4 양방향 yaw 추종량, H6 tracking·termination, H7 밀침 회복시간, 독립 seed.
- [이번 테스트] Run06 정책을 재학습하지 않고 32환경에서 H4·H6·H7의 command↔actual·termination을 기록한다.
- [흐름] Run06 분석 완료 → **고정 evaluator 실행·회수** → 정량 판정 → 최종 문서 → 제출.
- [지금 할 일] 아래 평가 package 한 개를 업로드하고 명령 한 줄만 실행한다.
- [보장하지 않음] 영상 1세트나 단일 seed만으로 공식 survival_rate, 최적 reward, 예선 점수 또는 통과 가능성을 보장하지 않는다.

## 다음 서버 — Run06 H1~H7 전체 자체 점수 평가 (A260831-11)

업로드 파일:

`workspace/training/humanoid/run06_fixed_eval_package.zip`  
SHA-256: `e897fa104f950b6bf511f891e1ec024dd4c3ae2783652a8459bf3bd1b9205551`

서버 `/workspace/training/humanoid/`에 업로드한 뒤 **아래 한 줄만** 실행한다.

```bash
cd /workspace/training/humanoid && echo 'e897fa104f950b6bf511f891e1ec024dd4c3ae2783652a8459bf3bd1b9205551  run06_fixed_eval_package.zip' | sha256sum -c - && unzip -o run06_fixed_eval_package.zip && sed -i 's/\r$//' server_run06_fixed_eval.sh && bash server_run06_fixed_eval.sh
```

예상 시간: 약 8~15분(10개 case, 각 20초 시뮬레이션 + Isaac Lab 시작 시간).

완료 확인: `tmux attach -t run06_fixed_eval`에서 `[DONE] Run06 fixed-policy evaluation complete`.
다운로드할 파일:

- `/workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz`
- `/workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz.sha256`

이 작업은 학습을 하지 않으며 reward를 바꾸지 않는다. H1~H7 중 하나라도 누락되면
`SELF_ASSESSMENT_INCOMPLETE`이고, FULL tar를 받기 전에는 성능 제출 후보로 승급하지 않는다.

## 과거 절차 — Run06 H1~H7 영상 후 종료

로컬 파일 `workspace/training/humanoid/server_run06_videos.sh`를 서버
`/workspace/training/humanoid/`에 업로드한 뒤 아래를 실행한다.

```bash
cd /workspace/training/humanoid
echo '793ca0546d5cea3d0c63e96f61b850404e8d072e59eee6d4ac541c072e59df9f  server_run06_videos.sh' | sha256sum -c -
bash -n server_run06_videos.sh
VIDEO_SUITE=full VIDEO_RESUME=1 bash server_run06_videos.sh
tmux attach -t run06_videos
```

full suite는 H1·H2·H3 좌우·H4 양방향·H5 요철·H6 ±10°·H7 밀침 총 10개를
seed 42, 4 env, 1000 step 고정 조건으로 녹화한다. 핵심 4종이 먼저 끝나면 CORE tar가 생기고,
전체 완료 뒤 FULL tar가 생긴다.

```text
/workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz
/workspace/_keep/train_260831-06_run05cfg_10000_VIDEOS_FULL.tar.gz.sha256
```

`[DONE] Run06 video suite=full` 확인과 두 파일 다운로드 뒤에만 서버를 종료한다.

## Go2 4족 — G1~G7 영상 스위트 (H1 벤치마킹)

H1 `server_run06_videos.sh`를 벤치마킹해 Go2용으로 포팅한 `server_run_Go2_videos.sh`를 사용한다. 동일 구조(CORE 4종→FULL 10종 2단 패키징, fingerprint, VIDEO_STATUS.tsv, preflight)로 동작한다.

로컬 파일 `workspace/training/quadruped/server_run_Go2_videos.sh`를 서버 `/workspace/training/quadruped/`에 업로드한 뒤 아래를 실행한다.

```bash
cd /workspace/training/quadruped
sha256sum server_run_Go2_videos.sh
bash -n server_run_Go2_videos.sh
VIDEO_SUITE=full VIDEO_RESUME=1 bash server_run_Go2_videos.sh
tmux attach -t run_Go2_videos
```

Go2 스위트는 H1과 동일하게 **G1 제자리(0,0,0)·G2 전진(0.75,0,0)·G3 좌우(±0.3)·G4 복합 양방향(0.5,±0.15,±0.5)·G5 요철(random_rough 2~10cm)·G6 경사 ±10°(0.17632698)·G7 밀침(0.5 m/s)** 총 10개를 seed 42, 4 env, 1000 step 고정 조건으로 녹화한다. 핵심 4종(G1·G2·G4·G7)이 먼저 끝나면 CORE tar가 생기고, 전체 완료 뒤 FULL tar가 생긴다.

```text
/workspace/_keep/train_260831-Go2_5var_1000_VIDEOS_FULL.tar.gz
/workspace/_keep/train_260831-Go2_5var_1000_VIDEOS_FULL.tar.gz.sha256
```

`[DONE] Go2 video suite=full` 확인과 두 파일 다운로드 뒤에만 서버를 종료한다. H1과 동일한 검증(`VIDEO_STATUS.tsv` 10/10, `*.artifacts.sha256` PASS)을 적용한다.

## 현재 Run06 완료·전체 회수

**전체 `training` 폴더 다운로드 자체는 좋다. 다만 로컬 정본에 즉시 덮어쓰지 않는다.**
서버는 업로드 당시의 문서·스크립트 사본과 새 학습 결과가 섞여 있으므로, 통째로 덮어쓰면
로컬에서 그 뒤 갱신한 원장·보고서·실험 이력을 과거 버전으로 되돌릴 수 있다. 또한 최종
Run06 bundle은 `/workspace/_keep` 아래에 있어 `training`만 내려받으면 빠진다.

Run06이 끝난 뒤 서버에서 다음 한 블록만 실행한다.

```bash
set -e
RUN_ID=train_260831-06_run05cfg_10000
KEEP=/workspace/_keep/$RUN_ID

grep -q '\[DONE\] DOWNLOAD=' "$KEEP/launcher.log"
grep '\[DONE\] DOWNLOAD=' "$KEEP/launcher.log"
cat "$KEEP/STATUS.txt"
cat "$KEEP/DOWNLOAD_SHA256.txt"

mkdir -p /workspace/training/_server_returns/$RUN_ID
cp -a "/workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz" \
  "$KEEP/DOWNLOAD_SHA256.txt" "$KEEP/STATUS.txt" \
  /workspace/training/_server_returns/$RUN_ID/

tar -C /workspace -czf "/workspace/training_${RUN_ID}_snapshot.tar.gz" training
sha256sum "/workspace/training_${RUN_ID}_snapshot.tar.gz"
echo "[DOWNLOAD-1] /workspace/_keep/${RUN_ID}_DOWNLOAD.tar.gz"
echo "[DOWNLOAD-2] /workspace/training_${RUN_ID}_snapshot.tar.gz"
```

권장 회수는 두 파일이다.

1. **필수·작은 파일:** `/workspace/_keep/train_260831-06_run05cfg_10000_DOWNLOAD.tar.gz`
2. **보험·전체 snapshot:** `/workspace/training_train_260831-06_run05cfg_10000_snapshot.tar.gz`

로컬에서는 전체 snapshot을 다음처럼 격리한다.

```text
C:\dev\Nconnect\workspace\server_returns\train_260831-06_run05cfg_10000\
```

그 뒤 SHA256·`STATUS.txt`·`TRAIN_RC`·source hash·tfevents·checkpoint를 검증하고,
검증된 **새 run 산출물만** `workspace/training/humanoid`에 병합한다. 기존 폴더 삭제나
전체 덮어쓰기는 금지한다.

## 다음 서버 접속 — Run 06 장기 수렴

- 목적: **서기 재튜닝이 아니다.** Run 05 보상 설정을 고정하고 10,000 또는 15,000 iter까지
  수렴시켜 직진·회전·생존 지표가 개선되는지 확인한다.
- 다음 서버 세션 준비물: CRLF를 제거해 다시 만든 `run06_server_package.zip` 하나
  (6,655,075 B, SHA-256 `1478e6a20d068dcbecd64ef648f1e3d1a7d5adf6e24dd6907d95b0430e8eaf86`). 현재 실행 중인 Run06에는 재업로드하지 않는다.
- 기본 선택: 사용 가능 시간이 2시간 20분 이상이면 10,000 iter, 3시간 20분 이상이면 15,000 iter.
- 완료 후: `/workspace/_keep/train_260831-06_run05cfg_<iter>_DOWNLOAD.tar.gz`를 내려받는다.

```bash
set -e
cd /workspace/training/humanoid
echo '1478e6a20d068dcbecd64ef648f1e3d1a7d5adf6e24dd6907d95b0430e8eaf86  run06_server_package.zip' | sha256sum -c -
if command -v unzip >/dev/null 2>&1; then unzip -o run06_server_package.zip; else python -m zipfile -e run06_server_package.zip .; fi
MAX_ITERS=10000 bash server_run06_long.sh
tmux attach -t run06_10000
```

15,000 iter를 확보할 시간이 있으면 마지막 두 줄의 `10000`만 `15000`으로 바꾼다.

## 0. 운영 불변식

- 대회 서버는 **접속마다 초기화되는 휘발성 실행환경**이다.
- 지속 정본은 `C:\dev\Nconnect\workspace\training`이다.
- 서버 run은 `업로드 → 검증 → 복원 → 실행 → bundle 생성 → 다운로드 → 로컬 검증`까지 끝나야 `done`이다.
- 서버에 과거 파일이 없다는 사실로 과거 실행 여부를 판단하지 않는다.
- **새 서버 명령보다 로컬 기존 데이터 조회가 먼저다.** `C:\dev\Nconnect\workspace\training`의
  log·tfevents·checkpoint·영상·보고서가 동일 질문에 이미 답하면 재실행하지 않는다.

### 로컬 정본 현재 인벤토리 (260831)

- `workspace/training/humanoid`: 190파일 · 466,878,876B
- tfevents 5 · checkpoint `.pt` 34 · 영상 `.mp4` 37 · 원문 `.log` 22
- Run 01~05와 Run 05 bootstrap·평가 영상·보고서가 보존돼 있다.

## 1. 세션 시작 — Run 05 복원

먼저 로컬 파일을 서버 `/workspace/training/humanoid/`에 업로드한다.

```text
C:\dev\Nconnect\workspace\training\humanoid\bootstrap_run05.zip
```

로컬 정본 식별자:

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `bootstrap_run05.zip` | 6,606,766 B | `3ceafae142c9bdda378c9e1ebc08eb7dd576e66980603f0c61587a3a0ad03073` |
| `_bootstrap/restore.sh` | 1,717 B | `c8b125b22f5951a3447844460323c252bdaa6878651377f1a364939072d67f96` |
| `_bootstrap/exported/model_best.pt` | 7,151,477 B | `2775a61e5294f37ec99a1454cdf200b2b0d9cd233022f68c6f293715690e9abc` |
| `_bootstrap/exported/env.yaml` | 34,741 B | `b5950a5a2066a3fe0d4298bed8ae0a3c558a6bc6aba605e1af39cd6dd66f24b3` |
| `_bootstrap/humanoid_rewards.py` | 9,482 B | `f6592b6bcf6632159da656b80a2954f04212b81925384a5c545125874bd59e81` |

업로드 후 실행:

```bash
cd /workspace/training/humanoid || exit 1

EXPECTED=3ceafae142c9bdda378c9e1ebc08eb7dd576e66980603f0c61587a3a0ad03073
ACTUAL=$(sha256sum bootstrap_run05.zip | awk '{print $1}')
echo "bootstrap_zip=$ACTUAL"
[ "$ACTUAL" = "$EXPECTED" ] || { echo '[FAIL] bootstrap zip hash'; exit 1; }

if command -v unzip >/dev/null 2>&1; then
  unzip -o bootstrap_run05.zip
else
  python -m zipfile -e bootstrap_run05.zip .
fi

sha256sum _bootstrap/restore.sh \
  _bootstrap/exported/model_best.pt \
  _bootstrap/exported/env.yaml \
  _bootstrap/humanoid_rewards.py

bash _bootstrap/restore.sh

echo '=== restored rewards ==='
grep -nE 'track_lin_vel_xy_exp|track_ang_vel_z_exp|feet_air_time|termination_penalty|flat_orientation_l2' humanoid_rewards.py
```

`restore.sh`의 모든 `[OK]`와 마지막 `[DONE]`이 필요하다. 복원은 `policy.pt`를 갱신하지 않는다.
학습·평가 후 `play.py`로 새로 export하고 checkpoint 가중치와 대조하기 전에는 제출하지 않는다.

## 2. 실행 중 보존 규칙

- run마다 고유 RUN_ID와 tmux 이름을 쓴다.
- 진단 run은 `NO_AUTO_SUBMIT=1`을 명시한다.
- `/workspace/_keep/<RUN_ID>/`에 log·checkpoint·설정·해시를 보존한다.
- 학습을 동시에 두 개 돌리지 않는다.
- finalize 전에 필요한 `model_*.pt`를 `_keep`으로 복사한다.

## 3. 세션 종료 — 다운로드 bundle 필수

아래 항목이 bundle에 없으면 run을 `done`으로 올리지 않는다.

- 학습 stdout log
- tfevents와 `params/*.yaml`
- `model_best.pt`와 보존 checkpoint
- `env.yaml`
- `policy.pt`·영상(play를 실행한 경우)
- RUN_ID·checkpoint iter·SHA-256 목록

### 3-a. 학습 후 영상 판정 — 서버 종료 전 필수

학습이 끝나면 다음 순서를 건너뛰지 않는다.

1. `ARTIFACT_MANAGEMENT.md` 작업 ID의 영상 판정(`VIDEO_REQUIRED / VIDEO_CONDITIONAL / VIDEO_NOT_REQUIRED`)을 확인한다.
2. 실제 최종 checkpoint iter·SHA와 사전등록 값이 같은지 확인하고, 다르면 영상 대상을 최종 checkpoint로 갱신한다.
3. reward/env/policy/checkpoint가 바뀌었거나 H1~H7·survival·tracking을 판정할 run이면 영상을 생성한다.
4. 영상 tar와 `.sha256`를 다운로드하고 로컬 파일 존재와 외부 SHA 일치를 확인한다.
5. 아래 종료 보고 5행이 채워진 뒤에만 서버 종료를 안내한다.

```text
영상 판정: VIDEO_REQUIRED | VIDEO_CONDITIONAL | VIDEO_NOT_REQUIRED
생성 결과: <suite, mp4 수, 로그 수, policy/checkpoint 식별자>
다운로드 결과: <서버 tar·sha 경로 → 로컬 경로>
로컬 검증 상태: <파일 존재, 외부 SHA PASS; 내부 검증은 PENDING/VERIFIED>
미측정 H1~H7: <남은 항목 또는 없음>
```

영상이 필수인데 생성이 실패하면 실패 로그와 checkpoint·source·config를 묶어 회수하고
`VIDEO_REQUIRED_NOT_ACQUIRED`로 종료한다. 이는 서버를 영원히 켜 두라는 뜻이 아니라,
**평가 미완료와 다음 세션의 영상 복구 작업을 명시한 뒤 재현 자산을 잃지 말라**는 뜻이다.

bundle을 PC로 내려받은 뒤 `C:\dev\Nconnect\workspace\training\humanoid`에 반영하고,
로컬 해시·가중치·로그 종료코드를 검증한다. 서버 화면만 보고 완료로 기록하지 않는다.
