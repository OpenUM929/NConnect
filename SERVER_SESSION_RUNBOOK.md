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

다음 실행 절차는 아래 **G-A015** 절이다. G-A013 절은 완료(`ARTIFACT_VERIFIED`, 가설 기각)이며 이력으로 남긴다.

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
