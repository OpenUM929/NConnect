# G-A052 계획 — A048 진단 재생 (학습 없음 · 보상 변경 없음, 2026-09-28)

요청: Codex `upload/plan/GO2_FAILURE_DATA_REQUEST_CODEX_20260928.md` §5, 2026-09-28 검토(“세 case 진단 재생을 준비할 가치가 있다”).
1단계 결과: `reports/GO2_FAILURE_DATA_FINDINGS_20260928.md`. 작업 ID `GO2-FAILURE-DATA-20260928`, 회차 `G-A052`.
A051 재개가 아니다. 변수를 고르지 않는다. 판독 결과는 Codex에 돌려준다.

**v2 (2026-09-28, Codex 검토 반영). v1(SHA `09973af1…465f`)은 실행 전에 대체했다.** 고친 것 세 가지:
- 판독기가 접촉 결측을 '지지 발 0개'로 읽었다. 결측과 실제 0개를 분리했고, 비교에 필요한 한쪽이 결측이면 unknown이다.
- 회수 검증기 종료코드 0이 필수 파일 완결을 보장하지 않았다. 필수 파일·SHA 목록 포함·진단 키 완결을 검사하고, artifact와 채널 확보를 나눴다(종료코드 0/3/1).
- 접촉 버퍼가 그 step에 갱신됐는지 기록하지 않았다. 행마다 `contact_fresh`·`contact_age_s`를 남긴다.

## 0. 예선 기준 현재 위치
- [예선 목표] 시뮬레이션 70점. G3 험지 옆걸음 전복·가라앉음과 G5 계단 실패에서 무엇이 먼저 무너지는지 재서, 후보 방향의 상대 지지를 가른다.
- [현재 단계] 2/6 — 다음 보상 후보 선정 전 진단.
- [확보] A048 iter 900 정책·env·평가기 원본, 1단계 사건표, 세 case의 원 명령줄(G-A048 launcher.log).
- [미확보] 몸통 roll·pitch 각속도, 발 위치·접촉·체공시간, action, 보상 항 값.
- [이번 테스트] 같은 정책을 같은 조건으로 다시 굴리며 위 채널을 함께 기록한다. 판정 없음.
- [흐름] 1단계 사건표 → **G-A052 재생(서버 약 15분)** → 로컬 회수 검증·판독 → Codex가 후보 방향 판단
- [지금 할 일] 사용자: 서버 실행 여부 결정. 실행하면 `upload/G-A052/current/` ZIP 하나를 올리고 안내문의 한 줄을 실행한다.
- [보장하지 않음] 한 정책·한 학습 seed·세 case다. 관측된 선후는 인과가 아니다. 점수를 재지 않는다.

## 1. 범위
| 번호 | 루트 | case | 평가 seed | 목적 |
|---|---|---|---|---|
| 1 | plain | rough_lateral | 202 | 평가기만. 저장본과의 재현 확인 |
| 2 | diag | rough_lateral | 202 | 전복 7대·낮은 자세 1대(env 23), 같은 재생의 생존 24대 |
| 3 | diag | stairs_10_down(실제 오르기) | 101 | 발-모서리 관계, 계단 영상 판독과 같은 seed |
| 4 | diag | stairs_15_down(실제 오르기) | 101 | 같음 |

- 정책: G-A048 iter 900 — model `984e6149…5ad7`, env `a19077a9…3a35`(평가 `identity.json`과 대조).
- 소스: G-A048 실행 ZIP `candidate/` 바이트 그대로(train.py 제외). 평가기 `353614…0d84`(schema 6).
- 명령: 네 실행 모두 G-A048 러너가 낸 play.py 명령과 글자 단위로 같다(관문 `B_Runner.test_2`).
- 추가 seed는 넣지 않는다. 계획 §5-4의 “case당 1개까지”는 이번 결과에서 사건이 없을 때 따로 판단한다.

## 2. 계측 — 읽기만 한다
- 모듈 `go2_eval_diag.py`. play.py가 부르는 평가기 이름 자리에 래퍼(`go2_eval_telemetry_diag_wrapper.py` → diag 루트의 `go2_eval_telemetry.py`)를 둔다.
- 래퍼는 원 평가기(`go2_eval_telemetry_v6.py`, 바이트 동일)를 먼저 설치한 뒤, 평가기의 step 기록이 끝난 다음 진단 기록을 붙인다. action과 step 결과는 그대로 넘긴다.
- 기록 채널(Isaac Lab v2.3.1 이름, 서버 Isaac Sim 5.1):
  - 몸통 선속도·각속도(몸통 좌표), projected gravity xyz, 자세 쿼터니언, 몸통 높이
  - 네 발 위치·속도(world)
  - 접촉: 순간 힘, 이력 최대 힘, 접촉 시간, 체공 시간, 직전 체공 시간, first contact(센서 정의 그대로 재계산), base 접촉 힘
  - 발 아래 지형(파생): 높이 스캐너 광선 중 발에 가장 가까운 것의 z, 발 반경 15 cm 안 최고 z, 가장 가까운 광선까지 거리
  - action, 이전 action
  - 보상 항별 가중값(초당, `RewardManager._step_reward`)과 가중치
- 금지한 것:
  - 시뮬레이션 쓰기, manager `compute()` 추가 호출
  - 센서 lazy update 유발. 접촉은 `.data`가 아니라 `_data`를 읽는다. 가짜 센서에서 `.data` 접근이 실패하는 관문 `A_Recorder`로 막는다.
- `_data`를 읽으면 갱신을 일으키지 않을 뿐, 값이 최신이라는 증명은 아니다. 그래서 행마다 센서 자신의 표시로 갱신 여부를 적는다. `contact_fresh` = 낡음 표시 없음이고 마지막 갱신 시각이 현재 센서 시각이다. `contact_age_s` = 둘의 차.
  - 이 과제에서는 base_contact 종료와 feet_air_time 보상이 매 step 마지막 물리 substep 뒤에 `.data`를 읽어 버퍼를 갱신한다(Isaac Lab v2.3.1 `sensor_base.py`, `manager_based_rl_env.py`).
  - 그 step에 reset된 env는 센서 reset이 낡음으로 표시하므로 0이 정상이다.
  - reset 행이 아닌데 0이면 그 행의 접촉은 쓰지 않는다.
- 시각 한계: Isaac Lab은 한 step 안에서 보상·종료 → 종료 env reset → 관측 순서로 돈다. 그 step에 종료된 env의 로봇·센서 값은 reset 뒤 상태다. steps.csv와 같다.
- 한 채널 묶음이 실패하면 멈추지 않는다. `diag_meta.json`의 `unavailable`에 이유를 적고 빈 칸으로 둔다(`DIAG_PARTIAL`).
- 규정: 배포 train/play/task/reward 파일은 바이트 그대로다. 서버에 도구를 설치하지 않고 외부 연결도 없다. 계측은 학습 경로 밖에서 저장 정책을 읽기만 한다(R-6-3). 제출물 생성과 무관하다.

## 3. 재현·개입 확인
- plain ↔ G-A048 저장본(seed 202 rough_lateral): 같으면 이번 재생의 env_id가 1단계 사건표의 로봇과 같다.
- diag ↔ plain(같은 세션): 같으면 저장된 채널·정밀도에서 차이가 발견되지 않았다는 뜻이다. 모든 내부 상태에 개입이 없었다는 증명은 아니다(검증기 표기 `NO_DIFFERENCE_IN_STORED_CHANNELS`).
- 계단 두 case는 diag ↔ 저장본만 있다. 다르면 계측 영향과 재현 실패를 가를 수 없으니, 그 case는 새 표본으로 읽는다.
- 재현이 되지 않아도 실패가 아니다. 판독은 그 재생의 steps.csv로 사건을 다시 고르므로 자기 완결적이다. 다만 1단계 env 번호와 잇지 않는다.

## 4. 사전 고정 판독 정의 (결과 전, 문턱 아닌 분석 편의값)
생성 `tools/go2_diag_replay_readout.py`. 사건 선택은 1단계와 같은 자세 게이트를 이 재생의 steps.csv에 적용한다.

**기준 시각 T와 창**
- 기울기 먼저 사건: proj_grav_z가 −0.95를 마지막으로 넘은 시각
- 높이 먼저 사건: 첫 자세 불량 시각
- 그 밖: 첫 자세 불량, 없으면 종료 직전 행
- 창은 [T − 1.0 s, T).

**같은 재생의 생존 로봇으로 정하는 기준** (재생마다 다시 계산, `CALIBRATION.json`)
- R: |ω_xy|의 p95
- S: 지지 중 발 수평 속도의 p95
- D: 지지 발 ≤ 1 연속 구간 길이의 p95

**창 안의 시작 시각**
- 회전 `t_rot`: |ω_xy| > R가 3행(0.06 s) 이상 이어진 첫 구간
- 미끄러짐 `t_slip`: 지지 중 발 수평 속도 > S가 2행 이상. 어느 발인지도 적는다.
- 지지 부족 `t_support`: 지지 발 ≤ 1 구간이 D보다 길어진 첫 시각
- 접촉 변화 `t_contact` = min(t_slip, t_support)

**판정 값 일곱 개** — 이 밖의 값을 쓰지 않는다
- rotation_first: 회전이 접촉 변화보다 0.04 s 넘게 먼저
- contact_first: 접촉 변화가 회전보다 0.04 s 넘게 먼저
- simultaneous: 차이 0.04 s 이하
- rotation_only / contact_only: 한쪽만 나타남
- not_observed: 둘 다 나타나지 않음
- unknown: 채널 결측

**유효성** (v2)
- 회전은 창 모든 행에 |ω_xy|가 있어야 잰다.
- 접촉 변화는 창 모든 행에 네 발 접촉 시간·발 속도가 있고 `contact_fresh = 1`이어야 잰다.
- 결측은 0 지지로 세지 않는다. 기준 계산(R·S·D)도 유효 행만 쓴다.
- 한쪽이라도 무효면 판정은 unknown이다. 회전 쪽 관측(`rotation_valid`·`t_rot`·`omega_xy_max`)은 따로 남긴다. 무효 사유는 `rotation_invalid_reason`·`contact_invalid_reason`에 적는다.

**함께 적는 것**
- 발별 0.1 s 칸 접촉 순서(어느 발이 언제 떨어졌나), 평균 지지 발 수, |ω_xy| 최댓값, action 변화량 평균, 창 평균 보상 항 값
- 계단 보조(파생): 지지 중 발 수평 속도 < 0.05, 그리고 발 주변 15 cm 안 최고 지형 − 발 높이 > 0.04인 첫 시각(`high_terrain_near_stopped_stance_foot_derived_t`). 주변 높은 지형과 멈춘 지지 발의 조합일 뿐 단 모서리 충돌의 증거가 아니다.
- 생존 대조: 같은 case 생존 로봇의, 낙상 T 중앙값 앞 1초 창. 같은 시각이지 같은 지형·상황의 대조가 아니다.

**자동 처방 없음.** Codex 결정표를 따른다(“회전 먼저면 회전 벌점을 G3에 한해 재비교, 계단 위험 그대로 / 접촉 변화 먼저면 접촉·보행 방향 우선”). 판독기는 값을 고르지 않는다. 정상 보행에서도 발은 교대로 떨어지므로, 지지 부족은 생존 로봇 분포보다 길 때만 센다.

## 5. 비용·회수
- **시간:** play.py 4회. G-A048 스위트는 69 case가 09:51→10:22(launcher.log)로 case당 기동 포함 약 0.5분이었다. 진단 CSV 쓰기 부담은 잰 적이 없다. 실행 15분 이내로 보고, 서버 세션은 30분으로 잡는다.
- **용량:** 진단 CSV는 case당 32,000행 × 약 110열이다. gzip 전 약 40 MB로 추정하며, 결과 ZIP은 수십 MB로 본다(추정).
- **영상:** 찍지 않는다(NOT_RECORDED). 이번 진단은 수치 계측으로 제한한다.
  - 녹화기는 별도 4 env 재생의 한 대만 따라간다. 이 32 env 재생과 같은 조건이 아니고, env_id와 묶을 수도 없다.
  - 발이 단 모서리의 어디에 닿았는지 같은 충돌 형상은 미확정으로 남긴다.
- **학습 report:** 비해당(학습 없음). A048 원 report는 로컬 `_keep/go2_g_a048_…/exported/report.html`을 참조한다.
- **회수 필수:** 결과 ZIP·.sha256 한 벌. 그 안에 다음이 들어 있어야 한다.
  - 네 실행의 steps.csv·summary.json·STATUS
  - diag 세 case의 diag.csv.gz·diag_meta.json·DIAG_STATUS
  - meta/identity.json·RUN_TIMES.txt·REPRO_STATUS.txt, logs/, launcher.snapshot.log, SHA256SUMS.txt
- **종료 게이트:** 실행 안내 §5. 로컬 `tools/verify_go2_diag_replay_harvest.py`가 판정 두 개를 따로 낸다: artifact(필수 파일·SHA 목록 포함·식별자·진단 키 완결)와 channels(필수 채널 묶음·필수 열·접촉 갱신).
  - 종료코드 0: 둘 다 통과. 끈다.
  - 종료코드 3: artifact는 통과, 필수 채널 미확보. 켠 채로 복구 가능성을 판단한다. 복구할 수 없으면 예외 종료 결정을 ARTIFACT_MANAGEMENT.md의 G-A052 항목에 남긴 뒤 끈다(결측 채널·case, 사유, 부분 회수분, unknown으로 남을 질문).
  - 종료코드 1: artifact 실패. 끄지 않는다. 다시 회수한다.

## 6. 결과별 다음 행동 (자동 없음)
- ARTIFACT_VERIFIED: 판독기 실행 → 사건별 판정 값 일곱 개와 생존 대조를 Codex에 반환한다. 후보 방향·폭은 Codex가 정한다.
- diag 채널 일부 UNAVAILABLE: 남은 채널만 판독하고, 빠진 채널이 가르던 질문은 `unknown`으로 둔다. 같은 서버에서 원인을 고칠 수 있으면 그 case만 다시 잰다.
- 사건 not_observed가 대부분: 이 표본에서는 가르지 못했다고 쓴다. 추가 seed는 Codex 판단으로 넘기며, 자동 반복하지 않는다.

## 7. 로컬 검증 (발행 전)
- 관문 `tools/test_go2_g_a052_diag_contract.py`:
  - 가짜 env로 계측(열·행·센서 `.data` 비접근·텐서 불변·first contact 정의·채널 실패 기록)
  - 래퍼 호출 순서
  - 러너 `bash -n`·LF, G-A048 명령과 글자 단위 동일
  - 패키지 재빌드 동일·내부 SHA·A048 소스 바이트 동일
  - 가짜 회수물에서 검증기와 판독기 실행. 검증기는 통과, 변조 거부, SHA 목록 누락, 필수 파일 결측, 진단 키 중복, 채널 결측·낡은 버퍼(종료코드 3)를 모두 확인했다.
  - 검증기 필수 열(2026-09-28 보완, ZIP 불변): 판독기가 읽는 열 전부를 네 발 모두에 대해 본다. reset이 아닌 행의 빈칸·NaN·Infinity는 건수와 첫 위치를 기록하고 종료코드 3이다. RR_contact_time 전체 결측, 한 행 결측(위치 기록), 비유한 값(inf·nan·-Infinity)은 3, reset 행의 빈칸은 0임을 확인했다. diag_meta의 reward_weights에 등록된 보상 항 열이 하나라도 없으면 3이다(열 하나 삭제 회귀 포함).
  - 판독기 결측 회귀: Codex 재현 입력 두 개(접촉 전부 결측 + 회전 있음, 같은 결측 + 지지 기준 존재)가 unknown이 되고, 회전 관측은 보존되는지 확인했다.
- 한계: Isaac Lab 실물에서 돌려 보지 못했다. 속성 이름은 v2.3.1 원문과 대조했다(서버는 Isaac Sim 5.1). 실물에서 이름이 다르면 그 묶음은 `unavailable`로 남고 재생은 계속된다.
