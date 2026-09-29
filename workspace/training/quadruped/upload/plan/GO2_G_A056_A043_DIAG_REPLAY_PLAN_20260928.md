# G-A056 계획 — A043 진단 재생 (학습 없음 · 보상 변경 없음, 2026-09-28)

- **상태: 발행 v2(ARTIFACT_VERIFIED) = 현재 실행본(Codex 2026-09-29 실행 권고, 추가 제작·재분석 없음), 사용자 서버 실행 승인 대기.** 서버 실행은 사용자 결정이며 승인 전에는 시작하지 않는다.
  - 실행 ZIP: `upload/G-A056/current/GO2_G_A056_a043_diag_replay_v2.zip`
  - SHA256: `6f82da12d56ca511f0748dd897ff7c8152aae034dc64950d08a6fa10ed19c17e`
  - v1(`7d4d6fe7…8398`)은 실행 전에 대체했고 history에 보존했다. 관절 텐서 하나가 없을 때 관절 이름까지 자리표시자로 바뀌던 결함을 로컬 관문이 찾았다.
- 요청:
  - Codex 2026-09-28 「승인 요청용 준비 지시」
  - 같은 날 「제작·검증 지시」 1~5. 관절 채널 포함은 Codex가 설계 선택으로 확정했다.
- 선행 분석: `reports/GO2_A043_TILT_ONSET_20260928.md`
  - 기록: "일부 험지 사건에서 기울기 증가보다 앞선 옆 속도 변화가 관측됨"
  - 남은 질문: 그 속도 변화가 어떻게 발생했는가, 지지·자세 회복은 왜 실패했는가
- G-A054는 기각된 제안이 쓴 이름이라 건너뛰었다. G-A055는 보류 상태를 유지한다.
- A052 발행물과 모듈(`go2_eval_diag.py`, 래퍼, 러너, 빌더, 검증기, 판독기)은 수정하지 않았다.
  - A052 빌더 `--check`: REBUILD_IDENTICAL `828c18cd…`
- 배포 학습 코드(train/play/task/reward)는 수정하지 않는다.

## 0. 예선 기준 현재 위치
- [예선 목표] 시뮬레이션 70점. G3 험지(가중 0.20)와 G2 복합 우회전에서 A043이 넘어지는 과정의 원인 단서를 찾는다.
- [현재 단계] 2/6 — 원인 분석(보상 후보 선정 전).
- [확보] 실행 ZIP v2, 로컬 관문 통과(§9), A043 정책·평가 식별자 대조.
- [미확보] 서버 재생 결과. 실물 Isaac Lab 실행은 아직 없다.
- [이번 테스트] 같은 정책·같은 조건 재생에 읽기 전용 채널과 로봇 지정 영상을 붙인다. 판정과 변수 선택은 하지 않는다.
- [흐름] 사건표 → 계획·발행(완료) → **서버 실행 승인(현재)** → 재생·회수 → 로컬 검증·판독 → Codex가 방향 판단
- [지금 할 일] 사용자: 서버 실행 여부를 결정한다. 실행하면 ZIP 하나를 올리고 안내문 한 줄을 실행한다.
- [보장하지 않음]
  - 이번 진단이 다루는 것은 선택한 두 case의 원인 단서다.
  - 다른 seed, 밀침, 계단, 보상 개선 효과는 검증하지 않는다.
  - 한 정책, 학습 seed 42 한 경로다. 시간 순서는 인과가 아니다.

## 1. A052 재사용 범위와 변경

### 1-1. 그대로 재사용 [확인]
- 평가기 `353614…0d84`(schema 6). A043 평가 identity의 evaluator_sha256과 같다.
- plain/diag 루트 구조와 "평가기 먼저, 진단은 step 기록 뒤" 래퍼 순서
- 센서 `_data` 읽기, `contact_fresh`·`contact_age_s`
- 판독기의 축 A 함수(`go2_diag_replay_readout.window_readout`·`calibrate`)를 import해서 그대로 쓴다.

### 1-2. 새 파일 (A052 파일은 사본만 만들고 고치지 않음)
- 계측: `go2_eval_diag_v2.py`(v1 사본 + 관절 묶음), `go2_eval_telemetry_diag_wrapper_v2.py`
- 카메라 계측: `go2_eval_camera_probe.py`, `go2_eval_telemetry_camera_wrapper.py`
- 러너: `server_run_go2_a043_diag_replay.sh`
- 빌더: `tools/build_go2_a043_diag_replay_package.py`
- 검증기: `tools/verify_go2_a043_diag_replay_harvest.py`
- 판독기: `tools/go2_a043_diag_readout.py`
- 관문: `tools/test_go2_g_a056_diag_contract.py`

### 1-3. 소스와 정책 [확인]
- 소스
  - A043 캠페인 ZIP `68480a13…da45` 안 staged ZIP `9b0b0d3a…fb03`의 `candidate/`. train.py는 뺀다.
  - A048 candidate와는 `quadruped_rewards.py` 하나만 다르다.
- 정책: A043 `model_iter900.pt` `4d923681…bd6b`, env `9af8f18a…a06d`
  - `CHECKPOINT_PIN.txt`와 평가 `identity.json`에서 둘 다 대조했다.
- 결과 패키저 `package_go2_result.py`는 A043·A048 것이 바이트 단위로 같다.

## 2. API 확인 — Isaac Lab v2.3.1 원문 [확인]
원문은 `raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.1/...`에서 받아 줄 번호로 대조했다. 서버는 Isaac Sim 5.1이다.

**관절 채널** (`source/isaaclab/isaaclab/assets/articulation/articulation_data.py`)
- `joint_pos`·`joint_vel` (L726·L735)
  - property다. 버퍼가 sim 시각보다 오래됐을 때만 PhysX view를 읽는다. 쓰기는 없다.
- `computed_torque` (L315): "actuator model 출력, clipping 전"
- `applied_torque` (L323): "clipping 뒤 시뮬레이션에 넣은 값"
- `joint_effort_limits` (L367), `joint_pos_limits`, `soft_joint_pos_limits` (L374)

**값이 기록되는 시점** (`articulation.py`)
- `_apply_actuator_model` (L1836~1869)이 `computed_torque`·`applied_torque`를 채운다.
- 이 함수는 `write_data_to_sim` (L184)에서 물리 substep마다 불린다.
- 따라서 기록 행에는 그 step의 **마지막 substep 값만** 남는다.

**Go2 액추에이터** (`isaaclab_assets/robots/unitree.py` L170~177)
- `DCMotorCfg`: effort_limit 23.5, saturation_effort 23.5, velocity_limit 30, stiffness 25, damping 0.5
- DC 모터 clip(`actuator_pd.py` L292~305)은 관절 속도에 따라 한계가 바뀐다.
  - 그래서 토크가 23.5 N·m에 가깝다는 것만으로는 포화라고 할 수 없다.
  - **계산 토크와 적용 토크가 다른 행이 기록된 clip이다.**
  - 앞 substep의 clip은 보이지 않는다(판독 한계).
- 배포 `go2_task/env_cfg.py`에는 액추에이터를 덮어쓰는 줄이 없다.

**viewer.env_index 적용 경로**
- `ViewerCfg` (`envs/common.py`): `env_index: int = 0` (L50), `cam_prim_path = "/OmniverseKit_Persp"` (L29)
- `hydra.py` L91: `env_cfg.from_dict(...)`가 설정 객체를 만든 **뒤에** 명령줄 override를 적용한다.
  - 배포 env_cfg `__post_init__`는 viewer의 origin_type·asset_name·eye·lookat만 정하므로(L84~88) `env.viewer.env_index=<k>`가 살아남는다.
- `viewport_camera_controller.py`
  - asset_root 모드는 렌더 때마다 `root_pos_w[cfg.env_index]`를 원점으로 잡는다(L164).
  - 그다음 `sim.set_camera_view(원점+eye, 원점+lookat)`로 `/OmniverseKit_Persp`를 옮긴다(L219, `simulation_context.py` L390).
- 영상 프레임은 `ManagerBasedRLEnv.render()`가 같은 prim의 render product에서 읽는다(`manager_based_rl_env.py` L286~293).

## 3. 범위 [확인, 기존 사건표]
- 두 case 모두 평가 seed 202
  - 험지 옆걸음: 낙상 11 / 선후 판독 가능 6
  - 복합 우회전: 낙상 9 / 선후 판독 가능 8
  - 세 seed 가운데 판독 가능한 사건이 가장 많다.
- 실행
  - plain·diag × 두 case = play 4회
  - 영상 4회: 험지 env 5·11, 우회전 env 3·16. 결과 전에 사건표로 고정했다.
- 명령
  - 네 평가 명령은 A043 `launcher.log`가 낸 명령과 글자 단위로 같다(관문 B_Runner.test_2).
  - 영상 명령은 그 명령의 `--headless` 뒤에 `--video --video_length 1000 --enable_cameras`, 끝에 `env.viewer.env_index=<k>`만 더한 것이다.
- 첫 episode만 분석한다(§5).

## 4. 사건 대응과 영상 대응 — 분리해 검증한다

**telemetry**
- plain ↔ A043 저장본이 같을 때만 기존 사건표의 onset을 붙인다(`stored_table_env_match=1`).
- 다르면 붙이지 않고 새 재생 표본으로 판독한다.
- 같은 seed·env 번호만으로 같은 사건이라고 하지 않는다.

**카메라**
- steps.csv가 일치하는 것과 별개로, 카메라가 지정 env를 실제로 찍었는지 `camera.csv`로 확인한다.
- 매 step 기록하는 값:
  - `cfg.env_index`
  - 컨트롤러 `viewer_origin`
  - 녹화 prim `/OmniverseKit_Persp`의 world 위치(USD `ComputeLocalToWorldTransform`, 읽기만)
  - prim − eye로 되짚은 원점과 대상 로봇 몸통의 수평 거리
  - 가장 가까운 env, 다른 로봇까지 거리
- **판정(사전 고정)**
  - 평가 대상 행: step ≥ 10이고, 그 행과 앞 행에서 대상 env가 reset되지 않은 행
  - 통과 행: `cfg.env_index`가 지정값이고, 되짚은 원점과 대상 몸통의 거리가 그 행 또는 앞 행 기준 ≤ 0.10 m
  - **설명 정정(2026-09-29, Codex 확인):** 검사하는 것은 카메라와 로봇 사이의 직접 거리가 아니다. 카메라 prim 위치에서 eye 오프셋(배포 설정 (−4, −4, 4) m, `camera_meta.json`의 `default_cam_eye`)을 빼서 되짚은 추정 원점과, 대상 로봇 몸통 사이의 **수평(xy) 거리**다. 구현(`go2_eval_camera_probe.py`, `verify_go2_a043_diag_replay_harvest.camera_check`)은 처음부터 이 방식이다. 앞선 보고의 "카메라 위치와 로봇 위치가 0.10 m 안"이라는 표현이 부정확했다. ZIP 재발행은 없다.
  - 통과 행이 95% 이상이면 CAMERA_ON_TARGET이다.
  - 카메라는 렌더 때 갱신되고 계측은 step 안에서 읽으므로 한 step 늦을 수 있다. 그래서 앞 행도 허용한다.
- **영상 판정**
  - `VIDEO_ENV_MATCHED`: 카메라가 대상을 따라갔고, 영상 실행 steps.csv가 plain과 같다. 영상 속 로봇이 diag 재생의 같은 env다.
  - `VIDEO_ENV_OWN_RUN_ONLY`: 카메라는 따라갔지만 steps.csv가 다르다. 영상은 자기 실행의 steps.csv에만 대응한다.
  - `VIDEO_CAMERA_UNVERIFIED`: 카메라 계측이 없거나 따라가지 않았다.
  - `VIDEO_NOT_ACQUIRED`: 파일·식별자·프레임 수(995~1001)가 맞지 않는다.
    - 프레임 기준은 기존 A043 영상에서 쟀다: 500 step → 499프레임, 50 fps.
- **한계** [확인]
  - 험지 case는 지형 칸이 4개이고 로봇이 32대라 한 칸에 약 8대가 있다.
  - 다른 로봇이 화면에 함께 보일 수 있으므로 0.30 m 안에 다른 로봇이 있던 행의 비율을 기록한다.
  - 기존 4 env 영상에서는 칸마다 로봇이 한 대였다.
  - 프레임과 step 사이에는 ±1프레임(0.02 s)의 대응 불확실성이 있다.

## 5. 사전 고정 판독 정의 (결과 전 · 분석 편의값 · 문턱 아님)
- **첫 episode**
  - 로봇마다 첫 terminated/truncated 행에서 자르고 그 행도 뺀다. 그 행의 로봇·센서 값은 reset 뒤 상태다.
  - 낙상 규칙은 평가기와 같다. 0.5 s 유예 뒤 proj_grav_z > −0.5 또는 height_rel < 0.18이 0.5 s 이어지거나, 그 전에 몸통 접촉으로 종료되면 낙상이다.
  - C-39(fall_channel이 reset 뒤 자료를 읽던 결함)는 이 판독에서 생기지 않는다.
  - 관문 D.test_10은 첫 episode 뒤 행을 전부 999로 바꿔도 판독이 같음을 확인한다.
- **onset**
  - 낙상 이전에 기울기가 18°를 마지막으로 위로 넘은 시각이다.
  - A052의 −0.95 교차는 약 18.2°이므로 같은 뜻이다.
- **판독 창:** W = [onset − 1.0 s, onset).
- **축 A** (A052와 같은 함수·같은 값 일곱 개)
  - 비교: 회전 t_rot 대 접촉 변화 t_contact = min(t_slip, t_support)
  - 생존 기준 R·S·D: 같은 재생 생존 로봇의 첫 episode 유효 행 p95
  - 결측은 unknown이다.
- **t_vy_full**
  - 대상: 명령 방향 옆 속도 초과량(actual_vy − cmd_vy, 0.1 s 이동평균)
  - 정의: 이 값이 자기 정상 보행 창 평균 + 2σ를 넘은 상태가 onset까지 끊김 없이 이어진 구간의 시작. onset 전 3 s 안에서만 찾는다.
  - 정상 보행 창: 2 s ~ min(8 s, onset − 1.5 s)
  - 정상 보행 창이 20행 미만이면 무효이고 축 B는 unknown이다.
  - 기울어짐 시작 분석과 같은 코드(`go2_a043_tilt_onset.lead_lag`)를 쓴다.
- **t_vy_w** = max(t_vy_full, W 시작)
  - W보다 먼저 시작했으면 `vy_departure_before_window=1`로 표시한다.
- **축 B** (새 축, 값 일곱 개)
  - 비교: t_vy_w 대 t_contact(W 안)
  - 값: lateral_first / contact_first / simultaneous / lateral_only / contact_only / not_observed / unknown
  - 차이 ≤ 0.04 s이면 simultaneous다.
  - 둘 다 W 시작에서 잡히면 simultaneous다. 창 밖의 선후는 이 판독이 가르지 않는다.
  - 어느 한쪽이 무효(정상 보행 창 부족, 접촉 결측·낡은 버퍼, 기준 없음)이면 unknown이다.
- **t_act**
  - 정의: W 안에서 |a − a_prev|(12차원 L2)가 같은 재생 생존 로봇 첫 episode 유효 행의 p95를 2행 이상 넘은 첫 시각
  - W 안에 action 결측 행이 있으면 무효다(`act_invalid_reason`).
  - `t_act_minus_t_vy`는 숫자로만 남긴다.
  - **action 변화가 먼저라는 값을 '정책이 가속을 일으켰다'로 판정하지 않는다.**
- **관절** (W 안, 기록만)
  - 적용 토크/effort 한계의 최댓값
  - 계산 토크 ≠ 적용 토크(|차| > 1e-4 N·m)인 행 수. 마지막 substep만 기록된다.
  - soft 관절 한계 0.05 rad 안에 든 행 수
- **생존 대조**
  - 같은 case 생존 로봇의, onset 중앙값 앞 1 s 창이다.
  - 비교군일 뿐 인과 대조군이 아니다. 지형과 보행 위상이 통제되지 않았다.
- **자동 처방은 없다.** 판독기는 값을 고르지 않는다.

## 6. A052에서 확인된 계측 시간 해상도와 한계
- 기록 주기는 0.02 s(50 Hz)다. 같은 행 안의 선후는 볼 수 없다.
- 접촉 센서는 update_period 0.005 s, history 3, 문턱 1 N이다.
- `contact_time > 0`은 하중 지지의 증명이 아니다.
- world 발 속도는 접촉점 미끄럼과 같지 않다.
- 발밑 지형 높이 채널은 창 안 변화가 약 2~4 mm라 해상도가 부족하다.
- 0.04 s보다 작은 선후는 simultaneous로 묶인다.

## 7. 시간 — 25~35분은 추정이고, 45분은 계획 예산이다
- **실측**
  - A052 러너 1분 57초. play 한 번 27~31 s.
  - A043 영상(4 env, 500 step)은 첫 실행 약 67 s, 이후 약 12 s였다.
  - A052의 서버 세션 전체 시간은 기록되지 않았다 [모름].
- **추정**
  - 서버 준비: 5~10분
  - 평가 play 4회: 2~3분
  - 영상 4회: 4~8분. 32 env·1000 step 카메라 실행은 잰 적이 없다.
  - 패키징: 1분 이내
  - 다운로드: 5~10분. ZIP 6.5 MB 업로드, 결과는 추정 60~90 MB.
  - 로컬 검증: 5~10분. 영상 프레임 디코딩을 포함한다.
- **서버 켜진 시간: 추정 25~35분, 계획 예산 45분.** "case당 30초"는 play 한 번의 벽시계이지 전체 작업 시간이 아니다.
- 이번 세션 전체 시간을 남기기 위해 러너가 `meta/RUN_TIMES.txt`에 시작·끝 시각을 적는다.

## 8. 필수 회수물과 종료 조건
- **결과 ZIP 하나:** `/workspace/_keep/GO2_G_A056_RESULT.zip` + `.sha256`
- **SERVER SHUTDOWN GATE:** `python -B tools/verify_go2_a043_diag_replay_harvest.py <내려받은 ZIP>`
  - 폴더를 주면 zip이 검사되지 않으므로 종료 불가(3)다.
- 검증기가 따로 내는 판정 네 가지:
  - zip: sidecar SHA, 안전한 경로
  - artifact: 필수 파일, SHA 목록, 식별자, 키
  - channels: 필수 묶음 7개(관절 포함), 필수 열, 접촉 갱신
    - 채널이 실패한 뒤에도 재생이 계속된 것은 회수 안전장치일 뿐, 채널 확보가 아니다.
  - video: 영상 네 개

| 종료코드 | shutdown | 서버 |
|---|---|---|
| 0 | OK | 네 판정 모두 통과(영상 네 개 모두 MATCHED 또는 OWN_RUN_ONLY). 끈다. |
| 3 | EXCEPTION_DECISION_REQUIRED | zip·artifact 통과, 채널 또는 영상 미완료. 끄지 않고 같은 서버에서 복구할 수 있는지 판단한다. 복구할 수 없으면 `exception_evidence`로 진단 데이터·checkpoint 식별 정보·실패 로그가 받은 ZIP 안에 있는지 확인한다. 그다음 ARTIFACT_MANAGEMENT.md G-A056에 미완료 항목·사유·받은 것·unknown으로 남을 질문을 적고 끈다. `collection=PARTIAL_NOT_COMPLETE`이며 '회수 완결'·'진단 성공'으로 쓰지 않는다. |
| 1 | DO_NOT_SHUTDOWN | zip SHA 또는 artifact 실패. 끄지 않고 다시 회수한다. |

- 영상 실패는 러너를 멈추지 않는다. `video/VIDEO_STATUS.txt`와 로그에 남는다.
- 평가 실행이 실패하면 러너가 멈추고, 있는 것을 묶는다(`INCOMPLETE_CRASH`).
- 학습 report: 비해당(학습 없음).

## 9. 로컬 검증 결과 (2026-09-28)
- 관문 `tools/test_go2_g_a056_diag_contract.py` 23개 통과. 패키지 테스트는 v2 발행 뒤 다시 돌려 통과했다. 확인한 것:
  - 계측 v2: 관절 열·meta 기록, 관절 텐서 결측 시 `unavailable`과 `DIAG_PARTIAL`, 텐서 불변, 센서 `.data` 비접근
  - 카메라 계측: 대상 추적, 컨트롤러·prim 없음 → `unavailable`
  - 래퍼 두 개의 호출 순서
  - 러너 `bash -n`·LF, 평가 명령 4개가 A043 launcher.log와 글자 단위로 같음, 영상 명령은 추가 인자만 다름
  - 패키지: 재빌드 바이트 동일, 내부 SHA, A043 소스 바이트 동일, 평가기·정책 SHA, train.py 없음
  - A052 보존: A052 발행 ZIP이 여전히 바이트 동일로 재빌드되고, A052 모듈이 A052 ZIP 안의 바이트와 같음
  - 가짜 회수물(저장 A043 steps.csv + 가짜 채널 + 999프레임 mp4)로 확인한 경로:
    - 정상 ZIP → 0/OK, 영상 네 개 MATCHED
    - 폴더 입력 → 3(ZIP_NOT_CHECKED)
    - sidecar 불일치 → 1
    - 필수 파일 결측·SHA 목록 누락 → 1
    - 관절 묶음 unavailable → 3, PARTIAL_NOT_COMPLETE, exception_evidence
    - reset 아닌 행의 관절 NaN → 3
    - reset 행 빈칸 → 0
    - 재현 불일치(plain ≠ 저장본) → 기존 사건표를 붙이지 않고, 영상은 OWN_RUN_ONLY
    - 영상 파일 결측 → 3(NOT_ACQUIRED, 사유 기록)
    - 카메라가 대상에서 0.5 m 떨어짐 → 3(CAMERA_UNVERIFIED)
    - 프레임 400 → NOT_ACQUIRED
  - 판독기: 사건 수가 기존 사건표와 같음(험지 11, 우회전 9), 축 A·B 값 집합, 첫 episode 뒤 행 오염에 불변, 결측 → unknown
- 한계
  - Isaac Lab 실물에서 돌려 보지 못했다.
  - 카메라 prim 읽기(USD)와 32 env 카메라 실행의 결정성은 실물에서만 확인된다.
  - 실패하면 해당 영상이 `VIDEO_CAMERA_UNVERIFIED` 또는 `NOT_ACQUIRED`로 남고, 진단 채널 회수에는 영향이 없다.

## 10. 결과별 다음 행동 (자동 없음)
- 판독 순서(Codex 2026-09-29): 관측 → 원인 설명 가능 범위 → 강좌 예측(`reports/GO2_LECTURE_REWARD_REFERENCE.md`) → 기존 반례(`reports/GO2_REWARD_TRIAL_REFERENCE.md`).
- 사건별 축 A·B 값, `t_act_minus_t_vy`, 관절 기록, 생존 대조, 영상 대응을 Codex에 돌려준다. 보상 방향과 폭은 이번 판독이 정하지 않는다.
- 대부분 not_observed 또는 unknown이면 이 표본으로 가르지 못했다고 쓴다. 추가 seed는 자동으로 돌리지 않는다.
- G-A055는 보류 상태를 유지한다.
