# H1 휘발성 서버 세션 런북

> **260831 운영 정정:** 서버 사용시간이 제한되므로 복원만 하려고 서버를 켜지 않는다.
> 로컬에서 실행 목적·스크립트·회수 경로를 모두 확정한 뒤, 서버에서는
> `업로드 1회 → 실행 1줄 → bundle 다운로드`로 끝낸다. 복원은 실행 스크립트 내부의 사전검사다.
> 파일 목록·작업 ID·검증·병합 상태의 정본은 `ARTIFACT_MANAGEMENT.md`다.

## 0. 예선 기준 현재 위치

- [예선 목표] 규정 제10조 — 200점 = H1 100 + Go2 100. 로봇 유형별 최고점만 합산하며 **한 라운드에 한 로봇만** 제출한다. 한 기체만 올리면 상한이 100점이다.
- [현재 단계] **Go2 단계 3/6 — 환경 적응 게이트.** H1은 `H1_FROZEN_FOR_SUBMISSION`으로 GPU 배정 0시간.
- [확보] H1 자체예상 92.73/100(시뮬 65.73/70 + 문서 자체감사 27/30), 672 episode 자세 게이트 재검증 통과. Go2 Pilot-01 평지 생존 실측.
- [미확보] **H1 실제 제출 여부 `[미측정]`**, 남은 라운드 수·마감 `[미측정]`, Go2 지형 시나리오 가중 0.60 전량.
- [이번 테스트] G-A012 — 동결 Pilot-01을 재학습 없이 69 case × 3 seed로 자세 게이트 평가하고 시나리오별 영상 7건을 남긴다.
- [흐름] 규정 정본화 완료 → **Go2 측정 실행·회수** → 단일변수 학습 → 재평가 → H1·Go2 각 라운드 제출.
- [지금 할 일] 아래 「Go2 4족 — G-A012」 절의 업로드 1회 + 실행 1줄.
- [보장하지 않음] 자체 proxy는 운영진 evaluator가 아니다. 65.73/70도 공식 점수가 아니다.

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

## Go2 4족 — G-A012 Pilot-01 자세 게이트 전 시나리오 측정 (260903)

> **260901 정정 유지:** `server_run_Go2_videos.sh`는 `LEGACY_INVALID_MAPPING`이며 **실행 금지**다.
> 구형 러너는 H1형 stand/forward/lateral/complex/rough/±10°/push를 쓰지만 Go2 기준은
> G1 전진, G2 전방위, G3 rough, G4 ±20°, G5 10~15cm 계단, G6 push, G7 DR이다.
> 아래 G-A012 패키지가 이 절이 요구하던 정식 evaluator이며, 지금부터는 이것만 쓴다.

**이 작업은 학습을 하지 않는다.** 규정 제8조의 점수는 `생존율 × 추종`인데 Go2 가중의 0.60
(G3 0.20 · G4 0.15 · G5 0.15 · G7 0.10)이 유효한 생존 지표로 측정된 적이 없다. 어느 reward를
돌릴지 정하기 전에 실점 위치를 먼저 확정한다.

### 전 과정

**1단계 — 로컬 준비 (완료됨)**

| 항목 | 값 |
|---|---|
| 업로드 파일 | `C:\dev\Nconnect\workspace\training\quadruped\go2_pilot_v2_baseline.zip` |
| 크기 | 6,461,584 B (27 members) |
| SHA-256 | `200b3ac6dc07b1ab58f3ea201722dcf8a46eb62a8f1f73db69dbb26e81d19671` |
| 사전검증 | `bash -n` PASS · CRLF 없음 · ZIP CRC PASS · manifest 27/27 · 내장 model/env SHA 대조 PASS · contract test PASS |

**2단계 — 서버 업로드**

`go2_pilot_v2_baseline.zip` 하나만 서버 `/workspace/`에 올린다. 공식 트리
`/workspace/training/quadruped/`에는 아무것도 올리지 않는다(제14조 — 원본 유지).

**3단계 — 실행 (한 줄)**

```bash
cd /workspace && echo '200b3ac6dc07b1ab58f3ea201722dcf8a46eb62a8f1f73db69dbb26e81d19671  go2_pilot_v2_baseline.zip' | sha256sum -c - && unzip -o go2_pilot_v2_baseline.zip -d /workspace && bash /workspace/go2_pilot_v2_baseline/server_run_go2_pilot_v2_baseline.sh
```

스크립트가 내부에서 tmux 세션 `go2_pilot_v2_baseline`을 띄우고, 패키지 manifest 대조·중복
실행 차단·정책 SHA 대조를 먼저 수행한다. 실패 시 어느 단계에서 멈췄는지 stdout에 남는다.

**4단계 — 진행 확인**

```bash
tmux attach -t go2_pilot_v2_baseline     # 빠져나올 때 Ctrl-b, d
```

| 단계 | 내용 | 예상 |
|---|---|---|
| PHASE 1/3 | 69 case × seed 101/202/303, 자세 게이트 evaluator | ~55분 |
| PHASE 2/3 | G1~G7 시나리오별 영상 7건 (seed 101) | ~8분 |
| PHASE 3/3 | 단일 ZIP 포장 + SHA | ~2분 |

총 **약 1시간 5분** (측정 단가 28초/case 기준). 예산 25시간의 4.4%.

**5단계 — 완료 확인**

```bash
cat /workspace/_keep/go2_pilot_v2_baseline/RESULT_STATUS.txt   # RESULT_STATE=FULL
cat /workspace/_keep/go2_pilot_v2_baseline/RUNNER_STATUS.txt   # RUNNER_RC=0, TELEMETRY_PILOT_V2=69, VIDEOS_PILOT_V2=7
```

tmux 로그 마지막 줄이 `[DONE] GO2_PILOT_V2_BASELINE_RESULT_READY`여야 한다.

**6단계 — 다운로드 (파일 2개만)**

```text
/workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip
/workspace/_keep/GO2_PILOT_V2_BASELINE_RESULT.zip.sha256
```

`_keep/go2_pilot_v2_baseline/` 폴더 내용물(계측 CSV·로그·영상·정책 사본)은 전부 이 ZIP 안에
있으므로 폴더를 따로 받지 않는다. `.sha256`은 전송 손상 검증에 필요하므로 반드시 함께 받는다.

**7단계 — 로컬 배치**

```text
C:\dev\Nconnect\workspace\_keep\
```

두 파일을 여기에 넣고 완료 보고한다. 이후 분석은 별도 지시 없이 즉시 착수한다
(메모리 `keep-inbox-autostart`).

**8단계 — 다음 결정**

가중치 × 실점이 가장 큰 시나리오 하나가 다음 단일 변수를 정한다. **사전등록이며 결과를 본 뒤
기준을 바꾸지 않는다.**

| 측정 결과 | 1순위 변수 |
|---|---|
| G3/G4/G5에서 생존율 붕괴 | `undesired_contacts` / `termination_penalty` 활성화 (현재 주석) |
| 생존 1.0인데 추종 낮음 | `track_lin_vel_xy_exp` ↑ |
| 지형에서 발 걸림 | `feet_air_time` ↑ |
| 통통 튀며 착지 불안 | `lin_vel_z_l2` 강화 |

이어지는 학습은 3,000~5,000 iter (Go2 실측 3.86초/iter → 3.2~5.4시간) + 재평가 1시간.
누적 5.4~7.5시간 / 25시간.

### 실패 처리

중단·오류 시에도 EXIT trap이 그 시점까지의 결과를 `RESULT_STATE=PARTIAL`로 같은 경로에
포장한다. **PARTIAL도 그대로 다운로드한다** — 69 case 중 일부만으로도 약한 시나리오를
판정할 수 있는 경우가 많고, 실패 로그가 ZIP에 함께 들어간다. 재개는 `GO2_RESUME=1`.

### 서버를 켜기 전 조건

이 절이 실제 한 줄 명령과 다운로드 경로를 담고 있어야 Go2를 위해 서버를 켠다.
260903 기준 위 내용으로 갱신 완료 — **실행 가능 상태**였다.

### 실행 결과 — 완료·회수·서버 종료 승인 (260903 15:34 회수)

| 확인 항목 | 결과 |
|---|---|
| 외부 SHA | `a722e9e740a2818cdce316c6fb901c92f6180a600c06b37da6609a66ed95aa9a` — sidecar와 일치 |
| 상태 | `RESULT_STATE=FULL`, `RUNNER_RC=0` |
| 내용 | telemetry 69/69, 영상 7/7, manifest 448/448 OK, `TRAINING=none` |
| 실행 시간 | 약 29분 (예상 1시간 5분보다 짧음) |
| 서버 잔여물 | 없음 — 학습이 없어 bundle 밖에 남는 산출물이 없다 |

**→ 서버 종료 승인(G-D57).** 결과 요약: worst-case `33.79311/70`, 가중 실점 1위 G3 `12.97`,
2위 G5 `10.50`, 두 시나리오 모두 실점 인자는 생존이다.
분석: `workspace/training/quadruped/reports/GO2_PILOT_V2_BASELINE_RESULT_ANALYSIS_260903.md`.

**(리셋, 260905) G-A019는 실행하지 않는다.** 다음 실행 절차는 아래 **G-A020** 절이다.
Pilot-01을 동결 기준선에서 완전히 내리고 Chain-01(재현성 있는 단일변수 검증만 누적한
기준선)로 재출발한다. 이유는 `GO2_PROJECT_STATE.md` §27을 보라 — 요약하면 Pilot-01은
reward 4개를 동시에 바꾸고 seed 하나로 만든, 재현 검증이 한 번도 없었던 정책이었고,
그 위에서 진행한 5회 실험 중 4회가 후퇴(2회는 전 시나리오 붕괴)했다. G-A013~G-A019
절은 완료된 이력으로 남기되 더 이상 비교·채택 대상이 아니다.

## Go2 4족 — G-A020 RESET: Chain-01 기준선 · `lin_vel_z_l2` -3.0 → -2.0 (260905)

**상태: 완료·기각(260905).** 정본 파일은 `workspace\training\quadruped\upload\G-A020\current\`.
**엔진이 v1_3 → v1_4로 바뀐다.** 이전 엔진·이전 사양(G_A013~G_A019)은 전부 SUPERSEDED다.

### 왜 리셋하는가

Pilot-01은 Default-01에서 reward 4개(`track_lin_vel_xy_exp`·`feet_air_time`·
`lin_vel_z_l2`·`ang_vel_xy_l2`)를 동시에 바꾸고 학습 seed 42 하나로 260831에 만든
정책이다. `GO2_REWARD_EVIDENCE_MASTER.md`(260901)는 이미 "학습 seed는 42 하나라
독립 학습 재현성은 미확보" "**control 생성 전까지 Pilot-01이 개선됐다는 표현은
금지**한다"고 명시했다. 그런데 260903 G-D69에서 이 규칙이 재검토 없이 뒤집혀
동결 기준선이 Pilot-01로 전환됐고, control(재현 검증)은 끝내 만들어지지 않았다.
그 위에서 진행한 G-A013~G-A019(5회) 중 4회가 후퇴했고 2회(G-A016·G-A018)는 전
시나리오가 붕괴했다. 유일한 개선(G-A017, +3.71/70)도 시나리오 하나의 생존 후퇴로
기각됐다.

### 왜 Chain-01인가

Pilot-01의 4개 동시 변경 중 2개는 이미 Default-01 위에서 **개별적으로 단일변수
검증**이 끝나 있었다: `track_lin_vel_xy_exp` 1.0→1.2(G-A011, `+3.0902846/70`,
생존 후퇴 0건), `lin_vel_z_l2` -3.0→-2.0(G-A010, `+2.2571599/70`, G7 -0.03125만
허용 내). Pilot-01을 만들 때는 이 검증들을 참고하지 않고 4개를 한꺼번에 바꿨을
뿐이다. Chain-01은 더 깨끗한 결과(G-A011, 생존 후퇴 전혀 없음)를 새 동결 기준선
으로 삼는다 — `track_lin_vel_xy_exp: 1.2`만 바뀌고 나머지는 Default-01 그대로인,
seed 42·1000 iter·단일변수·독립 검증 완료 checkpoint다(model SHA `143871e3…542d4`).

이번 회차(G-A020)는 Chain-01 위에 G-A010의 검증된 `lin_vel_z_l2 -3.0→-2.0`을
얹어, 두 검증된 개선이 **실제로 합쳐지는지**(Pilot-01이 검증 없이 가정했던 바로
그 지점)를 확인한다. H1(2족) 캠페인이 Run02→04→05로 검증된 변경을 하나씩 쌓아
Run06(92.73/100)을 만든 방식과 같은 원칙이다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_4.zip` | 19,135,939 B | `a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0` |
| `G_A020_chain01_lin_vel_z_m2.json` | 3,155 B | `1bc313e5f2879666da81b427cac4355045b1e006caef981f31da914756e7cca2` |

엔진 v1.4는 검증된 v1_3 ZIP에 `baseline/chain01/`(G-A011 checkpoint·env·tier-1
캐시)만 추가한 것이다 — Default-01 소스 체인이 로컬에 없어(`GO2_DEFAULT_VS_PILOT_RESULT.zip`
미보유, 기존에 알려진 문제) 전체 재빌드 대신 이 방식을 썼다. Default-01·Pilot-01
payload는 원본 그대로 손대지 않았다. 추출본 `validate` VALID(`baseline=Chain-01`) ·
`materialize` 후보 `lin_vel_z_l2 -2.0`·기준선 `-3.0`(나머지 5개, `track_lin_vel_xy_exp
1.2` 포함, 동일) · 기준선 checkpoint `143871e3…` 일치 · 계약 테스트 `Ran 50 tests`,
`FAILED (failures=6, errors=7)`(리셋 이전과 동일한 13건의 기존 알려진 실패만, 새 실패
0건)를 확인했다.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0  go2_tuning_engine_v1_4.zip\n1bc313e5f2879666da81b427cac4355045b1e006caef981f31da914756e7cca2  G_A020_chain01_lin_vel_z_m2.json\n' | sha256sum -c --strict - && unzip -oq go2_tuning_engine_v1_4.zip && cd /workspace/go2_tuning_engine_v1_4 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A020_chain01_lin_vel_z_m2.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A020_RUN_GUIDE.txt`에 있다.

### 4. 진행 확인

`tmux attach -t go2_g_a020` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_CHAIN01_LIN_VEL_Z_M2_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_CHAIN01_LIN_VEL_Z_M2_RESULT.zip
/workspace/_keep/GO2_CHAIN01_LIN_VEL_Z_M2_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치
(특히 `lin_vel_z_l2: -2.0`, `track_lin_vel_xy_exp: 1.2` 유지) · 정책 계보를 로컬에서
확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | 두 개선이 합쳐진다 → 이 지점을 Chain-02로 동결 → seed 202·303 대표평가 → 남은 미검증 항(`feet_air_time`·`ang_vel_xy_l2`·`action_rate_l2`·`flat_orientation_l2`)을 여기서부터 재개 |
| FAIL | Chain-01(`track_lin_vel_xy_exp`=1.2만)을 현재까지 가장 신뢰할 수 있는 후보로 보고, 남은 미검증 항을 Chain-01에서부터 재개(이번 조합은 재시도하지 않음) |

### 결과 (260905) — FAIL, 전 시나리오 붕괴

`baseline_points_70=18.610562` → `candidate_points_70=0.428330`(delta `-18.182232`).
G1·G2·G4·G5 생존 -1.0(전멸), G3 -0.84375, G6 -0.9375, G7만 -0.0625(허용 범위).
`RUNNER_RC=0`·`RESULT_STATE=FULL`·엔진/사양 SHA 모두 일치 확인 — 실행 자체는
정상, 결과가 실제로 이렇다. 개별로는 안전했던 두 변경(G-A011·G-A010)이 합쳐지자
정반대로 전멸했다. **Chain-02로 승격하지 않는다.** Chain-01은 그대로 동결 기준선
유지(G-F135, G-D86). 다음은 아래 G-A021.

---

## Go2 4족 — G-A021: Chain-01 기준선 · `ang_vel_xy_l2` -0.08 → -0.05 (260905)

**상태: 완료·기각(260905).** 정본 파일은 `workspace\training\quadruped\upload\G-A021\current\`.
**엔진은 v1_4 그대로**(변경 없음, G-A020과 동일 엔진 재사용).

### 왜 이 다이얼인가

G-A020(Chain-01 + `lin_vel_z_l2` 동시 결합)이 전 시나리오 붕괴로 기각됐다
(위 결과 참조, G-D86). 재발을 막기 위해 이번부터는 **한 번에 하나씩만** 쌓는다
(G-D87). 남은 미검증 4항(`feet_air_time`·`ang_vel_xy_l2`·`action_rate_l2`·
`flat_orientation_l2`) 중, 사족 로봇 reward shaping 문헌에서 `track_lin_vel_xy_exp`
(속도 추종)와 상호작용 위험이 상대적으로 낮다고 알려진 `ang_vel_xy_l2`(몸통 회전
억제)를 먼저 고른다. 후보값 `-0.05`는 Pilot-01이 원래 4개를 동시에 바꿀 때
이 다이얼에 실제로 썼던 값(`-0.08→-0.05`)이다 — 그때는 다른 3개와 함께 바뀌어
개별 효과가 한 번도 분리 측정된 적이 없었다. 이번이 그 값의 첫 단독 검증이다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_4.zip` | 19,135,939 B | `a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0` |
| `G_A021_chain01_ang_vel_xy_m005.json` | 2,882 B | `0177803887af8a9693fafdf9f5f6ec51dd6efcfe54c6e4577e4aa82a5df0e83e` |

추출본 `validate` VALID(`baseline=Chain-01`) · `materialize` 후보
`ang_vel_xy_l2 -0.05`·나머지 5개(`track_lin_vel_xy_exp 1.2`·`lin_vel_z_l2 -3.0`
포함) 기준선과 동일 확인 완료.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는
아무것도 올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0  go2_tuning_engine_v1_4.zip\n0177803887af8a9693fafdf9f5f6ec51dd6efcfe54c6e4577e4aa82a5df0e83e  G_A021_chain01_ang_vel_xy_m005.json\n' | sha256sum -c --strict - && rm -rf go2_tuning_engine_v1_4 && unzip -oq go2_tuning_engine_v1_4.zip && cd /workspace/go2_tuning_engine_v1_4 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A021_chain01_ang_vel_xy_m005.json
```

### 4. 진행 확인

`tmux attach -t go2_g_a021` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_CHAIN01_ANG_VEL_XY_M005_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_CHAIN01_ANG_VEL_XY_M005_RESULT.zip
/workspace/_keep/GO2_CHAIN01_ANG_VEL_XY_M005_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치
(특히 `ang_vel_xy_l2: -0.05`, `track_lin_vel_xy_exp: 1.2` 유지) · 정책 계보를 로컬에서
확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | 이 지점을 Chain-02로 동결 → seed 202·303 대표평가 → 남은 미검증 항(`feet_air_time`·`action_rate_l2`·`flat_orientation_l2`)을 여기서부터 재개 |
| FAIL | Chain-01(`track_lin_vel_xy_exp`=1.2만)을 현재까지 가장 신뢰할 수 있는 후보로 유지, 남은 미검증 항을 Chain-01에서부터 재개(이번 값은 재시도하지 않음) |

### 결과 (260905) — FAIL, 부분 후퇴(전멸 아님)

`RUNNER_RC=0`, `RESULT_STATE=FULL`, 자체 `SHA256SUMS.txt` 9/9 통과, 엔진·사양 SHA
둘 다 일치, `env.yaml` 렌더링 확인(`ang_vel_xy_l2: -0.05` 나머지 5개 유지),
`model_best.pt` SHA가 `RUNNER_STATUS.txt`와 일치. `baseline_points_70=18.610562`,
`candidate_points_70=12.002626`, `delta=-6.607936`(게이트 미달). G2~G6 survival
부분 후퇴(-0.156~-0.75, G-A020처럼 -1.0 전멸은 아님), G1 무변화, **G7(DR seed)은
오히려 개선**(survival +0.406). Chain-02로 승격하지 않음, `-0.05`는 이 다이얼에서
재시도하지 않음(G-F137, G-D88). 다음은 아래 G-A022.

---

## Go2 4족 — G-A022: Chain-01 기준선 · `feet_air_time` 0.01 → 0.20 (260905)

**상태: 완료·기각(260905).** 정본 파일은 `workspace\training\quadruped\upload\G-A022\current\`.
**엔진은 v1_4 그대로**(변경 없음, G-A020/G-A021과 동일 엔진 재사용).

### 왜 이 다이얼인가

G-A021(Chain-01 + `ang_vel_xy_l2` -0.05)도 게이트 실패로 기각됐다(위 결과 참조,
G-D88). 사전등록된 분기(G-A021 spec `branch.on_tier1_fail`)에 따라 이 실패한
후보 위가 아니라 **Chain-01 위에서** 다음 미검증 항으로 넘어간다. 남은 3항
(`feet_air_time`·`action_rate_l2`·`flat_orientation_l2`) 중 `feet_air_time`을
고른 이유는, 유일하게 **과거 다른 기준선(Default-01)에서 총점이 실제로 개선된
이력**이 있기 때문이다(G-A007, G-F93: `+3.8656/70`, 실패 사유가 G5 생존 후퇴
단 1건뿐 — 전멸이 아니었음). `action_rate_l2`·`flat_orientation_l2`는 각각
과거 기준선에서 이미 다이얼째 기각/철회된 이력이 있어(G-F127) 우선순위가 낮다.
후보값 `0.20`은 G-A007과 동일값 그대로 재사용 — Chain-01 위에서도 같은 방향이
유지되는지만 새로 확인한다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_4.zip` | 19,135,939 B | `a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0` |
| `G_A022_chain01_feet_air_time_020.json` | 2,967 B | `5bb6ba1d4f90db9882e42e1de119c1f99cdb0c08c076a4c70c85df6d57507ec8` |

추출본 `validate` VALID(`baseline=Chain-01`) · `materialize` 후보
`feet_air_time 0.2`·나머지 5개(`track_lin_vel_xy_exp 1.2`·`lin_vel_z_l2 -3.0`·
`ang_vel_xy_l2 -0.08` 포함) 기준선과 동일 확인 완료.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는
아무것도 올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'a030427748aad4049b3591fd20370f75091fe6365941f92d46e123333e3877c0  go2_tuning_engine_v1_4.zip\n5bb6ba1d4f90db9882e42e1de119c1f99cdb0c08c076a4c70c85df6d57507ec8  G_A022_chain01_feet_air_time_020.json\n' | sha256sum -c --strict - && rm -rf go2_tuning_engine_v1_4 && unzip -oq go2_tuning_engine_v1_4.zip && cd /workspace/go2_tuning_engine_v1_4 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A022_chain01_feet_air_time_020.json
```

### 4. 진행 확인

`tmux attach -t go2_g_a022` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_CHAIN01_FEET_AIR_TIME_020_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_CHAIN01_FEET_AIR_TIME_020_RESULT.zip
/workspace/_keep/GO2_CHAIN01_FEET_AIR_TIME_020_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치
(특히 `feet_air_time: 0.2`, `track_lin_vel_xy_exp: 1.2` 유지) · 정책 계보를 로컬에서
확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | 이 지점을 Chain-02로 동결 → seed 202·303 대표평가 → 남은 미검증 항(`action_rate_l2`·`flat_orientation_l2`)을 여기서부터 재개 |
| FAIL | Chain-01(`track_lin_vel_xy_exp`=1.2만)을 현재까지 가장 신뢰할 수 있는 후보로 유지, 남은 미검증 항을 Chain-01에서부터 재개(이번 값은 재시도하지 않음) |

### 결과 (260905) — FAIL, G-A020에 가까운 전면 후퇴

외부 SHA·엔진/사양 SHA·`SHA256SUMS.txt` 9/9·`env.yaml` 가중치(`feet_air_time
weight=0.2`, 나머지 5개 Chain-01과 동일)·`model_best.pt` SHA 전부 로컬 검증
통과. `baseline_points_70=18.610562` → `candidate_points_70=4.883013`
(`delta=-13.727549`). G1~G6 전부 생존 후퇴 `0.10` 초과(G1·G2·G4·G5 `-1.0`,
G3 `-0.84375`, G6 `-0.28125`) — G-A021(부분 후퇴)보다 나쁘고 G-A020(전멸)에
가깝다. G7만 `-0.0625`로 허용 범위 내. Default-01 위에서 유일하게 총점을
개선했던 값(G-A007, `+3.8656/70`)이 Chain-01 위에서는 최악에 가까운 붕괴를
냈다. 상세는 `GO2_PROJECT_STATE.md` G-F138/G-D89.

**→ 기각. Chain-02로 승격하지 않는다.** Chain-01 위 개별 스태킹 3/3
(G-A020·G-A021·G-A022)이 전부 실패했고, 남은 두 항(`action_rate_l2`·
`flat_orientation_l2`)은 각각 다이얼째 이미 완전히 소진돼(G-F127) 새로 시도할
코히런트한 값이 없다 — **이 두 항은 Chain-01 위에서도 시도하지 않는다.**
단일변수 보상 스태킹 탐색은 여기서 종료한다(G-D89). 다음은 아래 **G-A023**
절 — Chain-01 자체를 학습 없이 69-case·3seed로 실측해 처음으로 진짜 대표
점수를 확보한다.

---

## Go2 4족 — G-A023: Chain-01 자체 69-case·3seed 실측 (학습 없음, 260905)

**상태: 완료·중대 발견(260905).** Chain-01의 실제 69-case×3seed 점수는
`2.307745/70`(worst-case 집계) — G1·G2·G3·G4·G5·G7 6개 시나리오 전부
`survival_proxy=0.0`(3 seed 전부 동일). 이는 여태 tier-1이 써 온 evaluator와
다른 evaluator(`posture_gate_v2`, schema_version 2)로 나온 결과다: 같은
checkpoint·같은 케이스를 구버전 evaluator(schema_version 1, termination-only)로
채점하면 survival=1.0으로 나온다 — Chain-01 계보 전체(G-A011·13·18·20·21·22)의
tier-1 엔진(fix2, SHA `a030427748…`)이 구버전 `go2_eval_telemetry.py`를 얼려서
쓰고 있었기 때문이다. Default-01은 같은 posture_gate_v2로 이미 실측돼 있고
(`17.90699/70`, 7개 시나리오 전부 생존) — Chain-01과의 유일한 차이인
`track_lin_vel_xy_exp 1.0→1.2`가 실제로는 posture 붕괴를 일으킨 변경이었다.
상세는 `GO2_PROJECT_STATE.md` §28(G-F139-141, G-D91-93). **동결 기준선을
Default-01로 되돌린다. 다음 작업은 tuning engine의 evaluator를 최신
`go2_eval_telemetry.py`로 재빌드하는 것 — 그 전까지 서버 작업 보류.**

<details><summary>이전 절차 기록 (참고용, 더 이상 실행하지 않음)</summary>

정본 파일은 `workspace\training\quadruped\upload\G-A023\current\`.
**패키지가 새로 바뀐다** — 기존 `go2_tuning_engine_v1_4`(JSON 스펙 기반 학습+tier-1
게이트 엔진)이 아니라, G-A012가 Pilot-01에 썼던 것과 같은 "학습 없음, frozen
checkpoint 실측 전용" 패키지다. `tools/build_go2_chain01_baseline_package.py` +
`server_run_go2_chain01_baseline.sh`로 새로 빌드했다(G-A012 스크립트에서 이름만
`pilot`→`chain01`로 교체, 로직은 동일).

### 왜 이 작업인가

Chain-01(G-A011, `track_lin_vel_xy_exp` 1.0→1.2 단독)은 지금까지 seed 101
tier-1 프록시 점수(`+3.0902846/70`, 생존 후퇴 0건)만 있다 — 지정 시나리오
절만으로 조기 종료됐기 때문에(G-F92) 대표 seed(202·303)·69-case·
`posture_gate_v2` 평가를 받은 적이 한 번도 없다. Chain-01 위에 얹은 3개
개별 보상 스태킹(G-A020·21·22)이 전부 실패했고 남은 두 항도 소진돼(G-D89)
더 시도할 단일변수가 없는 지금, Chain-01 자체의 진짜 점수를 확보하는 것이
다음으로 정보가치가 가장 높다. 학습이 없으므로 제출 후보에 아무 위험도
없다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_chain01_baseline.zip` | 6,455,643 B | `51bac58e0126b2a1468acd893ab55851908109afdd027799a73ce4ba00907e8c` |

빌드 검증: `bash -n` PASS · CRLF 0 바이트 · ZIP CRC PASS · manifest 27/27 ·
내장 `chain01/exported/model_best.pt` SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`
· `chain01/exported/env.yaml` SHA `2ba9a1e11b52792c7ee7a76c9891a98d5f2d7d56c058f1182410f773bac5aa71`
— 둘 다 Chain-01 등록값과 일치. 소스는 `workspace/_keep/go2_track_lin_vel_120_v1/training/`
(G-A011 서버 회수본)에서 그대로 가져왔다.

### 2. 업로드

`go2_chain01_baseline.zip` 하나만 `/workspace/` 직속에 올린다. 정본 트리
`/workspace/training/quadruped/`에는 아무것도 올리지 않는다(제14조).

### 3. 실행 한 줄

```bash
cd /workspace && printf '51bac58e0126b2a1468acd893ab55851908109afdd027799a73ce4ba00907e8c  go2_chain01_baseline.zip\n' | sha256sum -c --strict - && unzip -oq go2_chain01_baseline.zip && bash /workspace/go2_chain01_baseline/server_run_go2_chain01_baseline.sh
```

### 4. 진행 확인

```bash
tmux attach -t go2_chain01_baseline     # 분리: Ctrl-b, d
```

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/3 | 69 case × seed 101/202/303, 자세 게이트 evaluator | ~55분 |
| PHASE 2/3 | G1~G7 시나리오별 영상 7건 (seed 101) | ~8분 |
| PHASE 3/3 | 단일 ZIP 포장 + SHA | ~2분 |

총 **약 1시간 5분**. 학습이 없어 GPU 시간이 실제로는 더 짧게 나올 수 있다
(G-A012 실측: 예상 1시간 5분 대비 실제 약 29분).

### 5. 완료 확인

```bash
cat /workspace/_keep/go2_chain01_baseline/RESULT_STATUS.txt   # RESULT_STATE=FULL
cat /workspace/_keep/go2_chain01_baseline/RUNNER_STATUS.txt   # RUNNER_RC=0, TELEMETRY_CHAIN01=69, VIDEOS_CHAIN01=7
```

tmux 로그 마지막 줄이 `[DONE] GO2_CHAIN01_BASELINE_RESULT_READY`여야 한다.

### 6. 다운로드 (파일 2개)

```
/workspace/_keep/GO2_CHAIN01_BASELINE_RESULT.zip
/workspace/_keep/GO2_CHAIN01_BASELINE_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 두 파일을 넣는다. 이후 분석은 별도 지시
없이 즉시 착수한다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE=FULL`/`RUNNER_RC=0` · telemetry 69/69 · 영상 7/7 ·
`TRAINING=none` · `CHAIN01_MODEL_SHA=143871e3…` 일치를 로컬에서 확인해야
종료 여부를 답한다.

### 9. 다음 결정

이 결과가 Chain-01의 진짜 `/70` 점수다. 가중 실점(생존×추종 후퇴)이 가장 큰
시나리오가 있으면 그것이 제출 전 마지막으로 검토할 후보를 알려주지만, 이미
G-A020·21·22가 실패했고 남은 두 항이 소진된 상태이므로 **이 결과 자체가
사전등록상 다음 단일변수를 자동으로 정하지는 않는다** — 새 변수는 이 결과를
본 뒤 별도로 정당화해야 한다.

</details>

---

## Go2 4족 — G-A010 (재측정) · `lin_vel_z_l2` -3.0 → -2.0, engine v1.4/posture_gate_v2 (260905~260906)

**상태: 완료 — FAIL(최종 기각). 재실행 대상 아님.**

G-A010은 260902에 engine v1.1로 **실제로 실행됐고 결과가 있었다**(가중 총점
`+2.2571599/70`, "생존 후퇴 0건") — 그러나 그 evaluator는 `schema_version:1`
(termination-only, posture_gate_v2 이전)로 확인됐고, Chain-01(G-A011~22)이 같은
세대 evaluator로 잘못 통과됐던 것과 동일한 맹점을 공유한다(`GO2_PROJECT_STATE.md`
G-F146, 정정 이력 포함). 260905에 engine을 posture_gate_v2 포함 v1.4로 재빌드하고
(계약 테스트 16/16 통과, G-F144·G-F145) 같은 spec을 그 엔진 대상으로 재검증해
**재측정**(신규 실험 아님)으로 재게시했다(G-F146, G-D96·G-D97).

**260906 재측정 결과: `INTERNAL_EARLY_KILL_FAIL`.** `baseline_points_70=17.132070`→
`candidate_points_70=9.499548`(`-7.632522/70`), G1~G6 survival 전부 `-0.1` 초과
회귀(G4·G5 최악 `-0.65625`/`-0.6875`), G1 tracking 개선은 사실상 없었다(`-0.00055`).
G1 raw case: `terminated_env_count:0`(v1 기준 "전원 생존")인데 `fallen_env_count:13/32`,
`survival_proxy_v1:1.0` vs `survival_proxy_v2:0.59375` — G-A011의 `track_lin_vel_xy_exp`
사례(G-F141)와 동일 패턴 재현. **`lin_vel_z_l2`는 `-3.0`으로 최종 확정, 다이얼 닫힘**
(G-D99). 상세: `GO2_PROJECT_STATE.md` §31(G-F147~150, G-D99·G-D100),
`GO2_REWARD_EVIDENCE_MASTER.md` §15·§17-d. 아티팩트: `workspace/_keep/go2_g_a010_lin_vel_z_m2_v2_260906/`.

**다음 실험은 G-A024다** — 아래 섹션 참조.

---

## Go2 4족 — G-A024 · `ang_vel_xy_l2` -0.08 → -0.15, engine v1.4/posture_gate_v2 (260906)

**상태: 완료 — FAIL(최종 기각, G-A010보다 더 심함). 재실행 대상 아님.**

G-A010(안정화 벌점 완화 방향)이 전 시나리오급 survival 붕괴로 기각됐으므로(위 섹션),
사전등록 분기가 지목했던 "ang_vel_xy_l2 -0.08→-0.05"(같은 완화 방향)는 쓰지 않고
**반대 방향(벌점 강화, -0.08→-0.15)**을 썼다(Pilot-01 위 G-D75 값을 Default-01에 적용,
ID는 Chain-01의 "G-A011"과 충돌 회피용 G-A024).

**결과: `INTERNAL_EARLY_KILL_FAIL`.** `candidate_points_70=0.0`(완전 붕괴), delta
`-17.13/70`. **G1~G7 전 시나리오(7/7)** survival `-0.1` 초과 회귀(G1·G2·G4·G5는 `-1.0`
완전 전멸). G1 raw: `fallen_env_count:32/32`(전원 낙상), `height_rel_mean:0.144`(임계
`0.18` 미달). 학습 자체는 수치적으로 안정(mean reward 11.9~12.9, 발산 없음) — 정책이
새 reward를 잘 최적화해서 낮게 웅크려 거의 안 움직이는 국소최적해로 수렴한 전형적
reward hacking. `-0.08` 유지, 다이얼 닫힘. 상세: `GO2_PROJECT_STATE.md` §32
(G-F151~153, G-D101). 아티팩트: `workspace/_keep/go2_g_a024_ang_vel_xy_m015/`.

**패턴 확정:** Default-01 위 posture_gate_v2 실측 단일변수 3건(`track_lin_vel_xy_exp`
강화·`lin_vel_z_l2` 완화·`ang_vel_xy_l2` 강화) 전부 실패 — 방향 불문. 다음은 G-A025.

---

## Go2 4족 — G-A025 · `flat_orientation_l2` 0.0 → -1.0 (G-A013 재측정), engine v1.4/posture_gate_v2 (260906)

**상태: 업로드 대기 — 다음에 실행할 것.**

이것은 재측정이다, 신규 실험이 아니다. `flat_orientation_l2 0.0→-1.0`은 G-A013(260903)이
이미 Default-01 위에서 시험해 `-1.4278/70`(G2·G4·G5·G6 후퇴)로 기각됐지만, 그 실행의
`RUNNER_STATUS.txt`(`ENGINE_VERSION=1.1.0`)와 tier1 case summary(`schema_version:1`)를
직접 열람해 확인한 결과 posture_gate_v2 이전의 termination-only evaluator였다 — G-A010의
260902 원본 결과와 같은 세대의 신뢰 불가 도구다. 다른 두 안정화 항(간접 유도)이 둘 다
실패한 뒤, 몸통 기울기를 직접 벌점화하는 이 항을 posture_gate_v2로 다시 잰다.

**위험 고지:** 지형과 무관하게 "평평한" 자세를 요구하므로 경사(G4)·계단(G5)에서 필요한
기울임 자체를 벌줄 수 있다 — G4/G5 survival을 특히 주의 깊게 본다. 실패 시 사전등록된
다음 분기는 reward 무변경 대조군(seed 42, 1000 iter from-scratch, reward 6개 전부
Default-01 그대로)으로 재학습 자체의 변동성부터 분리 측정하는 것이다(G-D103) — 4연패가
되면 reward 값이 아니라 재학습 절차 자체를 의심해야 한다.

### 업로드 2파일

`workspace/training/quadruped/upload/G-A025/current/`
  1. `go2_tuning_engine_v1_4.zip` — SHA `81c3bccef543eae116732a3965f6ad5fee692431243eb0ec00615acab2243b37`
  2. `G_A025_flat_orientation_m1.json` — SHA `fddddfd12f5487b04811bb0e3bf02b7ef38f5f6687f85e5b0f62f04b96b8f70f`

상세 실행 절차·모니터링·다운로드·서버 종료 관문은 같은 폴더의
`GO2_G_A025_RUN_GUIDE.txt`를 그대로 따른다(서버 종료 전 `RUNNER_STATUS.txt`의
`ENGINE_ARCHIVE_SHA256`이 위 engine SHA와 일치하는지 반드시 확인).

---

## Go2 4족 — G-A019 Pilot-01 기준선 · `track_lin_vel_xy_exp` 1.2 → 1.3 (260905)

**상태: 업로드 대기.** 정본 파일은 `workspace\training\quadruped\upload\G-A019\current\`.

### 왜 `action_rate_l2`를 다른 방향으로 다시 시도하지 않는가

G-A018(`action_rate_l2` −0.01 → −0.008)은 총점 `−44.3986/70`으로 기각됐다.
G1~G7 **전 시나리오**의 생존이 동시에 0.10 넘게 후퇴했다 — 규모는 G-A016과
비슷하지만 메커니즘은 다르다. iteration 단위로 학습 로그를 재확인한 결과
`track_lin_vel_xy_exp` 보상은 iter 100→1000 동안 꾸준히 올라 최종 `0.56`에
도달했다(episode 길이 900~1000/1000 유지) — **학습 자체는 정상**이다. 실패는
평가 에피소드 안에서 일어난다: `forward_fast`는 t=0.6s까지 정상 보행하다가
t=1.0~2.0s 사이 약 1.4초에 걸쳐 부드럽게(`cmd_vx` 일정, 급변 트리거 없음) 붕괴해
`height≈0.10`·`speed≈0.01`로 얼어붙고 남은 18초 넘게 재개되지 않는다.
`slope_plus_20`도 같은 타이밍이고, `dr_seed_101`은 정지 자세가 웅크림(~0.10m)과
직립(~0.44m)으로 이분화된다. 즉 "학습을 못 배웠다"가 아니라 **"배운 보행 리듬이
에피소드 안에서 지속되지 못하고 붕괴한다"**는 실패다. 강화 방향(`−0.01→−0.012`)
재탐색으로 이 붕괴를 피할 근거가 없어 다이얼째 기각한다.

### 왜 이 변수·이 값인가

참가자 파일이 명시한 6개 reward 항이 이제 전부 막혔다: `feet_air_time`(상한 확정),
`ang_vel_xy_l2`(다이얼째 기각), `flat_orientation_l2`(부호 반대로 철회),
`lin_vel_z_l2`(방향 기확정), `action_rate_l2`(다이얼째 기각), 그리고
`track_lin_vel_xy_exp` — 이 항만 유일하게 총점을 실제로 올렸다(G-A017,
46.49124→50.19916, `+3.70792/70`). 실패 원인은 G4(경사) 생존의 단독 후퇴
(`1.0→0.78125`, `-0.21875`)였다.

G-A019는 새 다이얼이 아니라 **이 유일한 개선 신호의 크기를 절반(+0.2→+0.1)으로
줄인 재탐색**이다. 1.2(Pilot-01 자체, G4 생존 1.0·추종 0.5533)와 1.4(G-A017, G4
생존 0.78125·추종 0.7286) 사이는 한 번도 측정된 적이 없어 후퇴가 선형인지 문턱형인지
모른다. 이 지점을 확인하지 않고 포기하면 유일한 개선 신호를 검증 없이 버리는 셈이다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_3.zip` | 12,781,997 B | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| `G_A019_pilot_track_lin_vel_xy_130.json` | 3,241 B | `643b36c9572520038ebf4467534590a961becffc25fcc9a39088b394f8305e17` |

엔진은 G-A015~G-A018에서 실제로 실행된 것과 **바이트 동일**하다. 추출본 `validate`
VALID · `materialize` 후보 `1.3`/기준선 `1.2`(나머지 5개 동일) · 기준선 checkpoint
`c4d78adf…` 일치 · 계약 테스트 `Ran 50 tests`, `FAILED (failures=6, errors=7)`(13건
전부 기존에 알려진 실패, G-A019 관련 실패 0건)를 확인했다. 상세:
`workspace/training/quadruped/G_A019.VERIFICATION.md`.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a  go2_tuning_engine_v1_3.zip\n643b36c9572520038ebf4467534590a961becffc25fcc9a39088b394f8305e17  G_A019_pilot_track_lin_vel_xy_130.json\n' | sha256sum -c --strict - && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A019_pilot_track_lin_vel_xy_130.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A019_RUN_GUIDE.txt`에 있다.

### 4. 진행 확인

`tmux attach -t go2_g_a019` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_PILOT_TRACK_LIN_VEL_XY_130_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_PILOT_TRACK_LIN_VEL_XY_130_RESULT.zip
/workspace/_keep/GO2_PILOT_TRACK_LIN_VEL_XY_130_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치
(특히 `track_lin_vel_xy_exp: 1.3`, 나머지 5개는 Pilot-01 값) · 정책 계보를 로컬에서
확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | seed 202·303 대표평가 → 69-case `posture_gate_v2` 재평가 → Pilot-01 `33.79311/70`과 비교. 통과 시 최선두 제출 후보 |
| FAIL (총점 Δ < +1.0/70, 어떤 시나리오도 생존 후퇴 > 0.10 없음) | 참가자 파일 안의 단일 변수 실험 완전 소진 — 동결 Pilot-01을 제출 후보로 보고 |
| FAIL (G4 생존 후퇴 > 0.10, 이번에도) | `track_lin_vel_xy_exp` 1.2 최종 상한 확정. 참가자 파일 안의 단일 변수 실험 완전 소진 |

---

## Go2 4족 — G-A018 Pilot-01 기준선 · `action_rate_l2` −0.01 → −0.008 (260904)

**상태: 업로드 대기.** 정본 파일은 `workspace\training\quadruped\upload\G-A018\current\`.

### 왜 `track_lin_vel_xy_exp`를 더 밀지 않는가

G-A017(`track_lin_vel_xy_exp` 1.2 → 1.4)은 총점이 실제로 개선됐다 —
기준 `46.49124/70` → 후보 `50.19916/70`(`+3.70792`). Pilot-01 동결 뒤 처음으로 총점이
오른 회차다. 그런데도 기각됐다 — 발화한 게이트는 `G4_survival_regressed_over_0.1`
하나뿐이다. G4(경사 ±20°)의 생존이 `1.0 → 0.78125`(`−0.21875`)로 후퇴 상한(0.10)의
두 배를 넘었다. 같은 시나리오에서 추종은 `0.5533 → 0.7286`(`+0.1752`)로 크게
좋아졌지만, 참가자 파일 자신이 경고한 대로("너무 높이면 험지/장애물서 자세 무너짐")
생존이 무너졌다. 사전등록 분기는 G3·G5를 취약 후보로 지목했지만 실제로 걸린 곳은
G4였다 — 그래도 규칙("임의 시나리오 생존 후퇴 > 0.10")은 그대로 적용된다. §19-b
(생존 절 우선)에 따라 총점 개선과 무관하게 **다이얼을 완전히 기각**하고, `1.2 → 1.3`
축소 재탐색은 하지 않는다 — 그 경로는 "총점 후퇴 + 생존 후퇴 없음" 전용 조건이었고
이번엔 정반대 패턴이었다.

### 왜 이 변수인가

참가자 파일이 명시한 6개 reward 항 중 5개가 이제 막혔다: `feet_air_time`(상한 0.20
확정), `ang_vel_xy_l2`(다이얼째 기각), `flat_orientation_l2`(부호 반대로 철회),
`lin_vel_z_l2`(방향 기확정), `track_lin_vel_xy_exp`(다이얼째 기각). **남은 미검증
항은 `action_rate_l2` 하나뿐**이며, 이번 회차는 참가자 파일 안에서 시도할 수 있는
마지막 단일 변수다.

−0.008은 참가자 파일의 권장 구간(`−0.02 ~ −0.005`) 안이며, 현재값(−0.01) 대비 20%
완화로 G-A011·G-A017이 지켜온 "작은 폭" 규율과 같은 크기다. 방향은 페널티 완화
(관절 반응 민첩화) — 실점 1·2순위 G3(거친 지형)·G5(계단)가 자세 회복에 빠른 관절
반응을 필요로 할 수 있다는 가설이다. 이 항은 참가자 파일이 어느 방향으로도 "⚠️"
경고를 달지 않은 유일한 항이라 위험 신호가 가장 약하지만, 그만큼 사전 근거도 없다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_3.zip` | 12,781,997 B | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| `G_A018_pilot_action_rate_m008.json` | 3,000 B | `7844cbe1f8f81f83116252922ac2921bbf261baab6661d0e2160e2b6d1945567` |

엔진은 G-A015~G-A017에서 실제로 실행된 것과 **바이트 동일**하다(결정론적 빌드).
추출본 `validate` VALID · `materialize` 후보 `−0.008`/기준선 `−0.01`(나머지 5개 동일) ·
기준선 checkpoint `c4d78adf…` 일치 · 계약 테스트 `Ran 50 tests`,
`FAILED (failures=6, errors=7)`(13건 전부 기존에 알려진 실패, G-A018 관련 실패 0건)를
확인했다. 상세: `workspace/training/quadruped/G_A018.VERIFICATION.md`.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a  go2_tuning_engine_v1_3.zip\n7844cbe1f8f81f83116252922ac2921bbf261baab6661d0e2160e2b6d1945567  G_A018_pilot_action_rate_m008.json\n' | sha256sum -c --strict - && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A018_pilot_action_rate_m008.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A018_RUN_GUIDE.txt`에 있다.

### 4. 진행 확인

`tmux attach -t go2_g_a018` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_PILOT_ACTION_RATE_M008_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_PILOT_ACTION_RATE_M008_RESULT.zip
/workspace/_keep/GO2_PILOT_ACTION_RATE_M008_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치
(특히 `action_rate_l2: -0.008`, 나머지 5개는 Pilot-01 값) · 정책 계보를 로컬에서
확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | seed 202·303 대표평가 → 69-case `posture_gate_v2` 재평가 → Pilot-01 `33.79311/70`과 비교 |
| FAIL (총점 Δ < +1.0/70, 어떤 시나리오도 생존 후퇴 > 0.10 없음) | −0.008이 과했다(다리 떨림) → `−0.01 → −0.012`(강화 방향), 같은 기준선·seed |
| FAIL (임의 시나리오 생존 후퇴 > 0.10) | 이 다이얼도 기각. 참가자 파일 안의 단일 변수 실험 소진 — 이미 확정된 다이얼의 세분화 재탐색으로 전환 |

---

## Go2 4족 — G-A017 Pilot-01 기준선 · `track_lin_vel_xy_exp` 1.2 → 1.4 (260904)

**상태: 업로드 대기.** 정본 파일은 `workspace\training\quadruped\upload\G-A017\current\`.

### 왜 `ang_vel_xy_l2`를 다시 시도하지 않는가

G-A016(`ang_vel_xy_l2` −0.05 → −0.15)은 총점 `−45.1155/70`으로 기각됐다. G-A015보다
심각하다 — G1~G7 **전 시나리오**의 생존이 동시에 0.10 넘게 후퇴했다. 학습 로그를
직접 추적한 결과 물리적 원인은 "넘어짐"이 아니라 **학습 극초반(iter ~100~150)에
고착된 전역 동결**이다. `track_lin_vel_xy_exp` 보상은 iter 150 근처 0.24에 도달한 뒤
남은 850 iteration 내내 전혀 개선되지 않고 정체했고, 실제 평가 시계열에서는 명령
속도 1.2m/s에 대해 처음 1초 안에 몸통 높이가 0.40m→0.18m로 주저앉고 이후 999
스텝 내내 속도 0에 가깝게 제자리에서 웅크린 채 고정됐다(`proj_grav_z`는 −0.999에서
서서히 −0.81로 안정되어 쓰러진 것은 아님을 확인). 사족 보행의 정상 트로트는 몸통
롤·피치 각속도를 필연적으로 만들어내므로, `ang_vel_xy_l2`를 3배로 올리자 "안 움직여서
각속도 자체를 없애는" 국소최적해가 트래킹 보상의 초반 그레이디언트보다 더 매력적인
선택지가 됐다. 사전등록 §19-d 3행(G5 생존 후퇴 `0.71875` > 0.10)에 따라 **이 다이얼은
완전히 기각**하고 다음 실점 순위로 이동한다. 크기를 줄여 재시도할 문제가 아니다 —
붕괴가 iter 150 안에 이미 고착됐으므로 더 작은 폭도 같은 함정에 빠질 위험이 있다.

### 왜 이 변수인가

가중 실점 순위(Pilot-01 69-case 기준)는 G3 `12.97` > G5 `10.50` > G4 `4.95` >
G7 `3.61` > G2 `2.60` > G1 `1.13` > G6 `0.45`(/70)다. 1순위(`feet_air_time`)는 상한
확정, 2순위(`ang_vel_xy_l2`)는 다이얼째 기각됐으므로 3순위 **G4(경사 ±20°)**로
이동한다.

G4는 다른 시나리오와 실점 성격이 다르다 — Pilot-01 기준선에서 G4의 생존은 이미
`1.0`(만점)이고 실점은 전부 추종(`tracking_proxy 0.5533`)에서 온다. 남은 6개 reward
항 중 이 지표를 직접 만들어내는 항은 `track_lin_vel_xy_exp` 하나뿐이다. 나머지는
모두 막혀 있다: `feet_air_time`(상한 확정), `ang_vel_xy_l2`(다이얼 기각),
`flat_orientation_l2`(G-A013에서 부호 반대 확인, 철회), `lin_vel_z_l2`(G-A010이
방향을 이미 확정). 1.4는 참가자 파일의 권장 구간 `0.5 ~ 2.0` 안이며, G-A011이 이미
같은 방향으로 한 단계(`1.0 → 1.2`) 검증해 생존 후퇴 0건을 확인한 전례와 같은 폭
(+0.2)만 다시 민다 — G-A015·G-A016이 보여준 "큰 배수 도약 → 파국적 붕괴" 패턴을
반복하지 않기 위함이다. 다만 참가자 파일 자신이 "너무 높이면 험지/장애물서 자세
무너짐"이라고 경고한 항이므로, 이미 여유가 적은 G3(`0.8125`)·G5(`0.71875`)·
G7(`0.9375`) 생존이 0.10 넘게 후퇴하는지가 이번 회차의 핵심 관찰 지표다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_3.zip` | 12,781,997 B | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| `G_A017_pilot_track_lin_vel_xy_140.json` | 2,978 B | `824753950d00bcddd9c4647b641a6b0f37632ecafc7064fd5d65bab68ee5f0b4` |

엔진은 G-A015·G-A016에서 실제로 실행된 것과 **바이트 동일**하다(결정론적 빌드).
추출본 `validate` VALID · `materialize` 후보 `1.4`/기준선 `1.2`(나머지 5개 동일) ·
기준선 checkpoint `c4d78adf…` 일치를 확인했다. 상세:
`workspace/training/quadruped/G_A017.VERIFICATION.md`.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a  go2_tuning_engine_v1_3.zip\n824753950d00bcddd9c4647b641a6b0f37632ecafc7064fd5d65bab68ee5f0b4  G_A017_pilot_track_lin_vel_xy_140.json\n' | sha256sum -c --strict - && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A017_pilot_track_lin_vel_xy_140.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A017_RUN_GUIDE.txt`에 있다.

### 4. 진행 확인

`tmux attach -t go2_g_a017` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip
/workspace/_keep/GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

## Go2 4족 — G-A016 Pilot-01 기준선 · `ang_vel_xy_l2` −0.05 → −0.15 (260904)

**상태: 업로드 대기.** 정본 파일은 `workspace\training\quadruped\upload\G-A016\current\`.

### 왜 `feet_air_time`을 더 밀지 않는가

G-A015(`feet_air_time` 0.20 → 0.35)는 총점 `−30.1219/70`으로 기각됐다. 실패 방식은
"조금 못하다"가 아니라 **보행 자체의 붕괴**다. 후보의 몸통은 넘어지지 않는다
(`proj_grav_z` 평균 −0.964, 기울어진 프레임 0.0%). 대신 **주저앉는다** — 지면 대비
몸통 높이 평균 0.183 m(기준선 0.303 m), 0.20 m 미만 프레임이 72.5%(기준선 2.8%),
속도는 절반(0.121 vs 0.246). 공중 체류 시간에 큰 보상을 걸면 정책은 몸을 낮추고
다리를 오래 들고 있는 느린 걸음으로 수렴하며, `posture_gate_v2`는 이를 정확히 낙상으로
집계한다. 계단에서는 32개 env 중 31개가 base contact로 종료됐고 전진 거리는
5.70 m → 1.89 m로 줄었다. 사전등록 §18-e의 "생존 후퇴 > 0.10" 분기에 따라
**0.20을 `feet_air_time`의 상한으로 확정**하고 다음 실점 순위로 이동한다.

### 왜 이 변수인가

사전등록 §18-e의 두 분기(총점 후퇴 / 생존 후퇴)가 동시에 발화했다. **생존 절이
우선한다** — 더 좁고 구체적인 조건이며, 그 증거가 명확하기 때문이다(G1 −0.969,
G4 −1.000, G3·G7 −0.813, G5 −0.719). 따라서 "0.20~0.35 사이 재탐색(0.28)"은
실행하지 않고 다음 실점 순위인 **G5(계단, `10.50/70`)**로 넘어간다.

G5의 실점 인자는 생존이고, 계단 낙상의 물리적 시작점은 몸통의 pitch·roll 진동이다.
④ `ang_vel_xy_l2`는 정확히 그 각속도에 벌점을 매기는 유일한 다이얼이며, Pilot-01
기준선에서 **한 번도 측정된 적이 없고** 지금까지의 어떤 측정 결과와도 모순되지 않는다.
(③ `lin_vel_z_l2`를 −2.0 → −2.5로 되돌리는 안은 G-A010의 실측 `+2.2572/70`과 방향이
반대라 제외했다.) −0.15는 참가자 파일이 명시한 권장 구간 `-0.3 ~ -0.02` 안이다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_3.zip` | 12,781,997 B | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| `G_A016_pilot_ang_vel_xy_m015.json` | 2,633 B | `0eadb9a7a72dbbaaf3618faf7e07482ba0309054bc3bfaa9fccc149882e11f76` |

엔진은 G-A015에서 실제로 실행된 것과 **바이트 동일**하다(결정론적 빌드). 이번 회차의
새 검증 대상은 실험 사양뿐이며, 추출본 `validate` VALID · `materialize` 후보 `−0.15`/
기준선 `−0.05`(나머지 5개 동일) · 기준선 checkpoint `c4d78adf…` 일치 · 계약 테스트
50/50 OK를 확인했다. 상세: `workspace/training/quadruped/G_A016.VERIFICATION.md`.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a  go2_tuning_engine_v1_3.zip\n0eadb9a7a72dbbaaf3618faf7e07482ba0309054bc3bfaa9fccc149882e11f76  G_A016_pilot_ang_vel_xy_m015.json\n' | sha256sum -c - && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A016_pilot_ang_vel_xy_m015.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A016_RUN_GUIDE.txt`에 있다.

### 4. 진행 확인

`tmux attach -t go2_g_a016` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분.

### 5. 완료 확인

`[DONE] GO2_PILOT_ANG_VEL_XY_M015_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_PILOT_ANG_VEL_XY_M015_RESULT.zip
/workspace/_keep/GO2_PILOT_ANG_VEL_XY_M015_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 외부 SHA · ZIP CRC · 내부 manifest ·
`RESULT_STATE`/`RUNNER_RC` · telemetry 7/7 · G1 영상 · `training/env.yaml`의 가중치 ·
정책 계보를 로컬에서 확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | seed 202·303 대표평가 → 69-case `posture_gate_v2` 재평가 → Pilot-01 `33.79311/70`과 비교 |
| FAIL (총점 Δ < +1.0/70, 생존 후퇴는 허용 내) | −0.15가 과했다 → 다음 단일 변수는 `−0.05 → −0.10`, 같은 기준선·seed |
| FAIL (G5 생존 후퇴 > 0.10) | 이 다이얼을 기각하고 다음 실점 순위(G4 경사)로 이동 |

---

## Go2 4족 — G-A015 Pilot-01 기준선 · `feet_air_time` 0.20 → 0.35 (260903)

**상태: 업로드 대기.** 정본 파일은 `workspace\training\quadruped\upload\G-A015\current\`.

### 왜 기준선을 Pilot-01로 바꾸는가

같은 69-case `posture_gate_v2` 스위트에서 Default-01은 `17.90697/70`, 동결 Pilot-01은
`33.79311/70`이다(G-F70). 지금까지의 단일 변수 스크리닝(G-A010·G-A011·G-A013)은 전부
Default-01 기준이었고, 이는 **제출할 일이 없는 정책을 최적화**한다. 엔진 v1.3은 두 동결
기준선을 모두 싣고 실험이 `baseline.name`으로 선택한다. 비교 가능성을 잃는 대가보다
실제 제출 후보를 개선하는 이득이 크다.

### 왜 이 변수인가

사전등록(§15-c)은 A(=G-A012 Pilot-01 69-case)의 가중 실점 최댓값 하나가 단일 변수를
결정한다고 못박았다. 순위는 G3 `12.97` > G5 `10.50` > G4 `4.95` > G7 `3.61` > G2 `2.60`
> G1 `1.13` > G6 `0.45`(/70)이고, 1·2위 실점 인자는 모두 생존이다(`rough_lateral` 최대
23/32 낙상, `stairs_15_down` 32/32 낙상). `feet_air_time`은 발 들기 높이를 올려 험지(G3)와
계단(G5)에 동시에 작용하는 유일한 다이얼이며, **측정된 곡선이 있는 유일한 변수**다 —
0.01 → 0.20이 같은 스위트에서 `+3.8656/70`, 어떤 시나리오도 생존이 후퇴하지 않았다.
이번 실행은 그 곡선의 세 번째 점이다.

### 왜 사전등록된 G-A014를 실행하지 않는가

G-A013(`flat_orientation_l2` 0.0 → −1.0)은 `−1.4278/70`으로 기각됐다. 실패 방식이
**과소가 아니라 부호 오류**다: G3 생존 `+0.156`·G7 `+0.250`인 반면 G4 `−0.313`,
G5 `−0.313`, G2 `−0.188`, G6 `−0.125`. +20° 경사와 계단에서는 몸통이 지형을 따라
기울어야 하는데 이 항은 정확히 그것에 벌점을 매긴다. G-A014(`−2.0`)는 해로운 방향으로
가중치를 두 배로 미는 것이므로 **취소**하고, 취소 사실과 근거를 기록으로 남긴다.

### 1. 로컬 준비 (완료)

| 파일 | 크기 | SHA-256 |
|---|---:|---|
| `go2_tuning_engine_v1_3.zip` | 12,781,997 B | `dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a` |
| `G_A015_pilot_feet_air_time_035.json` | 2,347 B | `f2ac4d7fb68da95ec982c708f95664a31ec46af8d38d7a9721dbc29c8c8ca693` |

검증 완료: ZIP CRC 무결 · 내부 manifest 49/49 · 실험 사양 미내장 · `.sh` CRLF 0 ·
추출본 `validate` VALID(`baseline=Pilot-01`) · `materialize` candidate `0.35`/기준선 `0.2`
(나머지 5개 동일) · 기준선 checkpoint `c4d78adf…` 및 env `f5550641…` 일치 ·
캐시된 tier-1 case 7/7(`VERIFIED_G_A012`) · Default-01 경로 회귀 통과 · 계약 테스트 47/47.
상세: `workspace/training/quadruped/go2_tuning_engine_v1_3.VERIFICATION.md`.

### 2. 업로드

두 파일을 `/workspace/` 직속에 올린다. `/workspace/training/quadruped/`에는 아무것도
올리지 않는다(예선 규정 제14조 — 서버는 초기 설정 그대로 사용).

### 3. 실행 한 줄

```bash
cd /workspace && printf 'dfbe47aecb5584ad07583caea726d23a372764b22e12962e0cbd76b268877b1a  go2_tuning_engine_v1_3.zip\n f2ac4d7fb68da95ec982c708f95664a31ec46af8d38d7a9721dbc29c8c8ca693  G_A015_pilot_feet_air_time_035.json\n' | sha256sum -c - && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A015_pilot_feet_air_time_035.json
```

정본 명령은 `workspace/training/quadruped/GO2_G_A015_RUN_GUIDE.txt`에 있다(줄바꿈 이스케이프 포함).

### 4. 진행 확인

`tmux attach -t go2_g_a015` (분리는 `Ctrl-b`, `d`).

| 단계 | 내용 | 예상 |
|---|---|---:|
| PHASE 1/4 | 1,000 iter 학습 | 약 59분 (G-A010 실측 3.48초/iter) |
| PHASE 2/4 | tier-1 게이트 + G1 영상 | 약 5분 |
| PHASE 3/4 | seed 202·303 (tier-1 통과 시에만) | 약 5분 |
| PHASE 4/4 | 포장 | 약 2분 |

조기 종료 약 1시간 6분, 대표평가까지 약 1시간 11분. 기준선 7개 case가 모두 캐시되어
있으므로 기준선 재평가 시간은 들지 않는다.

### 5. 완료 확인

`[DONE] GO2_PILOT_FEET_AIR_TIME_035_RESULT_READY`.
`DECISION=INTERNAL_EARLY_KILL_FAIL`은 **정상 종료**다 — 후보에 대한 판정이지 실행 실패가
아니며 `RUNNER_RC=0`·`RESULT_STATE=FULL`로 전량 포장된다. 어느 쪽이든 회수한다.

### 6. 다운로드 2파일

```
/workspace/_keep/GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip
/workspace/_keep/GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip.sha256
```

### 7. 로컬 배치

`C:\dev\Nconnect\workspace\_keep\`에 그대로 둔다. 정본 트리
`workspace\training\quadruped`는 검증을 통과한 산출물만 병합하며 전체 덮어쓰기는 금지다.

### 8. 서버 종료 관문

DONE 표시만으로 끄지 않는다. 두 파일을 받은 뒤 외부 SHA·ZIP CRC·내부 manifest·
`RESULT_STATE`/`RUNNER_RC`/`TRAIN_RC`·telemetry·G1 영상·model/env/source·정책 계보를
로컬에서 확인해야 종료 여부를 답한다.

### 9. 사전등록 분기

| tier-1 판정 | 다음 |
|---|---|
| PASS | seed 202·303 대표평가 → 69-case `posture_gate_v2` 재평가 → Pilot-01 `33.79311/70`과 비교 |
| FAIL (총점 Δ < +1.0/70) | `feet_air_time` 곡선이 0.20~0.35 사이에서 꺾인 것 → 다음 단일 변수는 `0.20 → 0.28`, 같은 Pilot-01 기준선·seed |
| FAIL (생존 후퇴 > 0.10) | 발 들기가 안정성을 깨는 지점 → 0.20을 상한으로 확정하고 다음 실점 순위(G5 계단)로 이동 |

---

## Go2 4족 — G-A013 `flat_orientation_l2` 단일 변수 학습 (260903)

**왜 이 변수인가 (사전등록 규칙의 출력).** G-A012의 가중 실점 1위는 G3 `12.97/70`,
2위는 G5 `10.50/70`이고 두 시나리오 모두 실점 인자가 생존이다. 계획(§15-d)이 지목했던
`undesired_contacts`·`termination_penalty`는 **서버 `env.yaml` 실측 결과 존재하지 않는다** —
전자는 `undesired_contacts: null`(비활성), 후자는 항 자체가 없다. 10-iter smoke test는
이 실측으로 대체돼 불필요하다. 실재하면서 아직 손대지 않은 자세·생존 다이얼은
`flat_orientation_l2`(현재 weight `0.0`) 하나뿐이며, 이것이 단계 C의 단일 변수다.

**게이트 목표도 함께 고친다.** G-A010은 가중 총점 `+2.26/70`, G3 survival `+0.094`를 얻고도
tier-1 목표가 G1로 고정돼 있어 `target_G1_improvement_below_0.05` 하나로 조기 종료됐다.
엔진 v1.2는 `target_scenario`를 G1~G7 중에서 고르게 하고, G-A013은 **G3**를 목표로 둔다.

### 전 과정

**1단계 — 로컬 준비 (완료됨)**

| 항목 | 값 |
|---|---|
| 업로드 파일 ① | `C:\dev\Nconnect\workspace\training\quadruped\upload\G-A013\current\go2_tuning_engine_v1_2.zip` |
| 크기 / members | 6,419,244 B / 34 |
| SHA-256 | `9e79a9dff6a9f6a7636692df7780634f0d1ffe47372ef703e8c86c8fbdeb640e` |
| 업로드 파일 ② | `C:\dev\Nconnect\workspace\training\quadruped\upload\G-A013\current\G_A013_flat_orientation_m1.json` |
| 크기 | 2,292 B |
| SHA-256 | `2e255c1e18165f2be7e17f09893503262a1c846998d12f20cb7ddbd9273cecb2` |
| 단일 변경 | `flat_orientation_l2` `0.0 → -1.0` (나머지 5개는 Default-01 고정값) |
| 학습 조건 | from scratch, seed 42, 4096 env, 1,000 iter |
| 사전검증 | ZIP CRC OK · manifest 33/33 · `bash -n` PASS · CRLF 0 · 추출본 `validate` VALID · `materialize` candidate `-1.0`/default `0.0` · 계약 테스트 44/44 |

검증 기록: `workspace/training/quadruped/go2_tuning_engine_v1_2.VERIFICATION.md`
업로드 정본(G-D55·G-D56): `workspace/training/quadruped/upload/G-A013/current/` — 이 폴더의
`CURRENT_UPLOAD.txt`·`GO2_G_A013_RUN_GUIDE.txt`가 같은 SHA와 같은 한 줄 명령을 담고 있고,
release는 `history/20260903_engine-v1.2/`에 불변 보존된다.

**2단계 — 서버 업로드**

위 두 파일만 `/workspace/`에 올린다. 공식 트리 `/workspace/training/quadruped/`에는
아무것도 올리지 않는다(제14조 — 원본 유지). 구 엔진 `go2_tuning_engine_v1_1.zip`은
`SUPERSEDED_DO_NOT_REUSE`이며, 잘못 올려도 `engine_version` 불일치로 학습 전에 죽는다.

**3단계 — 실행 (한 줄)**

```bash
cd /workspace && printf '9e79a9dff6a9f6a7636692df7780634f0d1ffe47372ef703e8c86c8fbdeb640e  go2_tuning_engine_v1_2.zip\n2e255c1e18165f2be7e17f09893503262a1c846998d12f20cb7ddbd9273cecb2  G_A013_flat_orientation_m1.json\n' | sha256sum -c - && unzip -oq go2_tuning_engine_v1_2.zip && cd /workspace/go2_tuning_engine_v1_2 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A013_flat_orientation_m1.json
```

실행 전에 스크립트가 스스로 experiment JSON 검증 · 패키지 manifest 대조 · 학습/play 중복
프로세스 차단 · tmux 세션 중복 차단을 수행한다. 실패하면 어디서 멈췄는지 stdout에 남는다.

**4단계 — 진행 확인**

```bash
tmux attach -t go2_g_a013     # 빠져나올 때 Ctrl-b, d
```

| 단계 | 내용 | 예상 |
|---|---|---|
| PHASE 1/4 | 1,000 iter 학습 (G-A010 실측 3.48초/iter) | **59분** |
| PHASE 2/4 | tier-1 조기 종료 판정: 후보 7 case + baseline DR 1 case + G1 영상 | ~5분 |
| PHASE 3/4 | tier-1 통과 시에만 seed 202·303 추가 (14 case) | ~5분 |
| PHASE 4/4 | 단일 ZIP 포장 + SHA | ~2분 |

조기 종료 시 **약 1시간 6분**, 대표평가까지 가면 **약 1시간 11분**. 예산 25시간의 4.4~4.7%.

**5단계 — 완료 확인**

```bash
cat /workspace/_keep/go2_g_a013_flat_orientation_m1/RESULT_STATUS.txt   # RESULT_STATE=FULL
cat /workspace/_keep/go2_g_a013_flat_orientation_m1/RUNNER_STATUS.txt   # RUNNER_RC=0, DECISION=...
```

tmux 마지막 줄이 `[DONE] GO2_FLAT_ORIENTATION_M1_RESULT_READY`여야 한다.
`DECISION`이 `INTERNAL_EARLY_KILL_FAIL`이어도 **정상 종료**다 — 판정이 실패인 것이지
실행이 실패한 것이 아니다. 그 경우에도 `RUNNER_RC=0`, `RESULT_STATE=FULL`이다.

**6단계 — 다운로드 (파일 2개만)**

```text
/workspace/_keep/GO2_FLAT_ORIENTATION_M1_RESULT.zip
/workspace/_keep/GO2_FLAT_ORIENTATION_M1_RESULT.zip.sha256
```

**7단계 — 로컬 배치**

```text
C:\dev\Nconnect\workspace\_keep\
```

두 파일을 여기에 넣고 완료 보고한다. 분석은 별도 지시 없이 즉시 착수한다
(메모리 `keep-inbox-autostart`).

**8단계 — 다음 결정 (사전등록 — 결과를 본 뒤 바꾸지 않는다)**

| G-A013 결과 | 다음 |
|---|---|
| tier-1 PASS (G3 proxy `+0.05` 이상, 총점 비회귀, 어느 G도 survival `-0.10` 초과 회귀 없음) | seed 202·303까지 자동 진행 → 통과 시 69-case `posture_gate_v2` 재평가 |
| tier-1 FAIL이지만 G3 survival 상승 | G-A014 = `flat_orientation_l2 0.0 → -2.0` only (같은 baseline·seed) |
| tier-1 FAIL이고 G3 survival 무변화·하락 | 자세 다이얼 기각. G-A014 = `lin_vel_z_l2 -3.0 → -5.0` only (지면 밀착 강화) |

어느 경로든 **한 번에 한 항만** 바꾼다. 두 항 동시 변경은 인과 귀속이 불가능해
리포트의 설계 의도(20점)를 스스로 무너뜨린다.

### 서버를 켜기 전 조건

이 절의 1~7단계가 실제 파일·SHA·한 줄 명령·다운로드 경로를 담고 있어야 켠다.
260903 기준 **충족 — 실행 가능 상태다.**

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
