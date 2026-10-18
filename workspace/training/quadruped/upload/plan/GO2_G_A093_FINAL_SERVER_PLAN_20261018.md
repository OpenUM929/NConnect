# G-A093 계획 — 공식 서버 최종 제출 학습 5,000회 (2026-10-18)

## 0. 예선 기준 현재 위치
- **[예선 목표]** 시뮬레이션 70점 축과 제출 3종(`policy.pt`·`env.yaml`·기술 개선 리포트)이다. 이번 학습의 정책이 제출물이 된다.
- **[현재 단계]** 4/6 단계적 장기 학습이다. 패키지 두 판을 준비했다. G-A092 판독 뒤 한 판을 공식 서버에서 실행한다.
- **[확보]** G-A083 보상 PC2 iter 2400 57.59/70. 서버에서 이미 시험한 5,000회 실행 틀(G-A079 v3)이 있다.
- **[미확보]** G-A092 결과, 공식 서버 학습 정책과 그 69 case 평가, 리포트 500자.
- **[흐름]** G-A092 판독 → 판 선택 → **공식 서버 5,000회 + 평가(tmux, 무인)** → 도착 후 결과 ZIP 회수·판독 → 제출
- **[지금 할 일]** G-A092 판독 결과에 맞는 ZIP을 서버 `/workspace/`에 올리고 §3의 한 줄을 실행한다.
- **[보장하지 않음]** PC2 iter 2400 점수가 서버 5,000회 정책의 점수를 보장하지 않는다. 공식 점수가 아니다.

## 1. 사용자 결정
- "제출용 파일은 직접 학습을 해야", "강좌 배포의 최대 횟수로 이번 테스트 결과를 획득 후에 진행".
- "결과에 따라 개선이 있으면 개선안으로 그렇지 않으면 기본안으로 최종 공식서버에서 학습할 수 있게 세팅 준비해줘."
- 학습 횟수: 강좌가 "본격 학습"으로 명시한 값은 5,000이다(13강 "5000(본격 학습)"). 배포 `agent_cfg.py`의 기본값도 5,000이다. 근거는 `reports/GO2_LECTURE_REWARD_REFERENCE.md` §9.

## 2. 판 선택 규칙 (G-A092 판독 뒤)
| 판 | 보상 | 고르는 조건 |
|---|---|---|
| `GO2_G_A093_FINAL_FEET0P05_5000_v1` (개선안) | G-A083 + feet_air_time 0.05 | G-A092 신버전 > 57.59, 보호 기준 유지 |
| `GO2_G_A093_FINAL_A083_5000_v1` (기본안) | G-A083 | 그 밖의 경우 |

- **공통 보상:** track_lin 2.0, track_ang 0.75, lin_vel_z −3, ang_vel_xy −0.05, action_rate −0.01, flat −0.225.
- **학습 조건:** seed 42, 4096 env, 처음부터 5,000회.

## 3. 서버 실행
```bash
cd /workspace && sha256sum -c <ZIP>.sha256 && unzip -oq <ZIP> -d /workspace && ISAACLAB_SH=/workspace/IsaacLab/isaaclab.sh bash /workspace/<slug>/run_point.sh --only <key>
```
- **판별 값:**
  - 개선안: slug `go2_g_a093_final_feet0p05_5000`, key `final_a092_feet0p05`
  - 기본안: slug `go2_g_a093_final_a083_5000`, key `final_a083`
- **웹을 닫아도 되는 때:** `[STARTED] … in tmux` 줄이 나오면 닫아도 된다. 학습은 계속된다.
- **진행 확인:** `tmux attach -t <slug>`로 들어간다. 나올 때는 Ctrl+b 다음 d.
- **예상 시간:**
  - 끝까지 가면 학습 약 4시간 35분 + 평가 약 1시간 30분 = 약 6시간이다.
  - 2,600 근처에서 발산하면 약 2시간 20분 + 1시간 30분이다.
  - 학습 속도는 A078 서버 로그의 3.29초/iter로 추정했다.
- **회수:** `/workspace/_keep/<RESULT>.zip`과 `.sha256`
- **제출 파일 위치 (결과 ZIP 안):**
  - `evaluation/candidate/policy.pt`: 평가한 checkpoint에서 play.py가 export한 파일
  - `training/env.yaml`
  - `exported/report.html`

## 4. 위험과 대비
- **발산:** 이 계열의 seed 42 공식 서버 실행은 두 번 다 3,000 전에 발산했다.
  - G-A077: 2584, 두 번 비트 단위로 같았다.
  - G-A079: 2836.
  - PC2 G-A091도 2594에서 발산했다.
  - 발산하면 학습을 잇지 않는다. 발산 직전 checkpoint(대략 2500~2700)를 평가한다. 기록은 `training/EVAL_CHECKPOINT_OVERRIDE.txt`에 남는다.
- **평가 중 Isaac Sim 충돌:** G-A079 v3는 평가 61/69에서 충돌해 평가를 잃었다. 이번 판은 case와 영상을 각각 최대 3번 다시 시도한다. 기록은 `logs/EVAL_RETRIES.txt`에 남는다.
- **서버 중단:** 같은 한 줄을 다시 실행하면 거울 사본 중 가장 새 checkpoint에서 이어 학습한다.
- **R-6:** 배포 train.py, play.py, go2_task는 바이트 단위로 같다. 바뀐 것은 보상 값, 우리 러너, 설정뿐이다.

## 5. 결과 판독 (도착 후)
- **점수:** 69 case로 신버전과 과거 버전 점수를 낸다. 보호 기준은 G-A083 계획 §5와 같다.
- **대조군:** 패키지 안의 대조군은 G-A077 서버 정책(iter 2400)이다. 참고용일 뿐이다. 비교의 중심은 G-A083 57.59와 G-A092다.
- **제출:** 판독 뒤 사용자가 정한다. 자동 제출은 없다.

## 6. 패키지
- **빌더:** `tools/build_go2_g_a093_final_server_package.py`. G-A079 v3 빌더 위에서 보상·설정·재시도만 바꿨다.
- **시험:** `tools/test_go2_g_a093_final_server_package.py`. 두 판 정적 검사와, 가짜 Isaac Lab으로 도는 종단 시험(충돌 재시도, 발산 대체 평가)이다.
- **위치:** `upload/G-A093/current/` 두 ZIP과 `.sha256`.
