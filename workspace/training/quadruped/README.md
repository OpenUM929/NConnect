# Quadruped (Go2) 학습 — NAVER Connect Robotics Cup 2026 예선

> **260901 캠페인 운영 정정:** 새 Go2 작업은 이 일반 강좌 README보다
> `AGENTS.md` → `../../../GO2_PROJECT_STATE.md` → `reports/NEW_SESSION_HANDOFF.md`를 먼저 따른다.
> 현재 1,000 iter 결과는 실질 4개 reward를 동시에 변경한 탐색 기준선이며 개별 튜닝 효과는
> 미측정이다. `server_run_Go2_videos.sh`는 제공 Go2 G1~G7과 매핑이 다른
> `LEGACY_INVALID_MAPPING`이므로 실행하거나 자체 점수 근거로 사용하지 않는다.

사족로봇 Unitree Go2 의 보행 정책 학습 패키지. **reward 수정 → 학습 → 영상으로 검증 → 제출** 단계.

> **실행 환경: Ubuntu + 클라우드 컨테이너 (headless, GUI 창 없음).**
> 학습·플레이 모두 `--headless` 로 돌리고, **결과 확인은 영상(mp4)으로만** 합니다.
> 런처는 `isaaclab.sh` — 이 문서는 `/workspace/IsaacLab/isaaclab.sh` 기준 (경로는 환경에 맞게).

## 학생이 수정하는 파일

**`quadruped_rewards.py`** 의 `REWARD_WEIGHTS` 안 값들을 자유롭게 바꿔 실험합니다.
핵심 5개 항목은 `[이동·등반]` / `[자세·안정]` 두 그룹으로 묶여 있고, 전부 조정 대상이에요. (파일 아래쪽 `[고급 옵션]` 은 주석 처리돼 있으니 필요하면 풀어서 실험하세요.)
어떤 reward 가 뭘 하는지는 파일 안 주석과 예선 가이드를 참고하세요. 그 외(`go2_task/`, `train.py`, `play.py`) 및 이 파일의 다른 코드는 건드리지 마세요.

---

## 1. 학습 (train.py)

학습은 몇 시간씩 걸려요. **반드시 `tmux` 안에서 시작하세요.** code-server 터미널은 끊기면 학습이 멈춥니다(죽지 않고 그대로 정지). tmux 안에서 돌리면 브라우저/SSH 가 끊기거나 창을 닫아도 계속 돕니다.

```bash
tmux new -As train     # train 세션 생성 → 이 안에서 아래 학습 명령 실행
# 학습이 돌기 시작하면: Ctrl+b 누른 뒤 d → 빠져나오기(detach). 창 닫아도 OK.
tmux attach -t train  # 나중에 다시 들어가 진행 확인
```

세션 안에서:

```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p train.py --task Quadruped-v0 \
    --num_envs 4096 --max_iterations 10000 --headless
```

- 명령 안의 `\` 는 줄바꿈 이어쓰기 — **블록째 복사**하면 됩니다.
- `--max_iterations`: 길수록 좋지만 수렴하면 정체. RTX 5080 기준 10000 iter ≈ 8h
  (Go2 는 H1 보다 **오래** 걸립니다 — 이유는 아래 §학습 시간 참고).
- 학습이 끝나면 best 체크포인트가 자동 선별돼 `exported/` 로 정리됩니다 (아래).

**학습이 잘 되는 중인지 (콘솔 로그):** `Curriculum/terrain_levels` 가 0 에서 점점 오르고,
`Metrics/base_velocity/error_vel_xy` 가 낮아지고, `Train/mean_reward` 가 (오르내림은 있어도) 전반적으로 우상향이면 정상 궤도예요.
`Mean episode length` 는 긴데 reward 만 높으면 편법(reward hacking)일 수 있으니 영상으로 꼭 확인하세요.
(Go2 가 제자리에서 빙빙 돌고 안 나아가면 — 전진을 못 배운 것. reward 재조정.)

### 학습 후 생기는 파일 — `quadruped/exported/`

| 파일 | 내용 |
|---|---|
| `model_best.pt` | ★ 예선 채점용 체크포인트 (best iter 자동 선별) |
| `model_best_<ts>.pt` | 백업 |
| `env.yaml` (+ `env_<ts>.yaml`) | 학습 환경·reward dump (학습 의도) |

전체 로그·중간 체크포인트: `quadruped/logs/rsl_rl/quadruped/<run>/`

### 이어서 학습 (resume) — 끊긴 학습 복구 / 추가 학습

이미 돌린 run 의 마지막 지점에서 **가중치를 이어받아** 더 학습합니다 (세션 끊김 복구, "조금 더 돌려보기"). 평소 학습 명령에 **`--resume`** 만 붙이면 가장 최근 run 을 이어받아요 — tmux 안에서:

```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p train.py --task Quadruped-v0 \
    --num_envs 4096 --max_iterations 10000 --headless --resume
```

- **`--resume`** : 값 없이 붙이기만 하면 됨. 가장 최근 run 의 마지막 체크포인트에서 이어 학습.
- `--max_iterations` : 이번에 더 돌릴 iteration. resume 하면 로그의 iter 번호가 이전 학습에서 *이어져* 올라갑니다.

특정 run / 체크포인트를 콕 집으려면:

```bash
ls logs/rsl_rl/quadruped/       # run 폴더 목록 확인 (예: 2026-06-19_10-00-00)

/workspace/IsaacLab/isaaclab.sh -p train.py --task Quadruped-v0 \
    --num_envs 4096 --max_iterations 10000 --headless \
    --resume --load_run 2026-06-19_10-00-00 --checkpoint model_5000.pt
```

- `--load_run <폴더명>` : `logs/rsl_rl/quadruped/` 안의 run 폴더 이름 (생략 = 가장 최근).
- `--checkpoint model_<iter>.pt` : 그 run 의 특정 체크포인트 (생략 = 마지막).

**`logs/` 가 통째로 날아갔을 때 (컨테이너 재시작 등) — `exported/model_best.pt` 로 이어받기**

`--load_run`/`--checkpoint` 는 `logs/<run>/` 폴더 안에서 모델을 찾기 때문에, 살려둔 best 모델을 *가짜 run 폴더*에 한 번 넣어주면 됩니다 (다른 PC 에서 받은 `model_best.pt` 도 똑같이):

```bash
cd /workspace/training/quadruped
mkdir -p logs/rsl_rl/quadruped/from_best
cp exported/model_best.pt logs/rsl_rl/quadruped/from_best/

/workspace/IsaacLab/isaaclab.sh -p train.py --task Quadruped-v0 \
    --num_envs 4096 --max_iterations 10000 --headless \
    --resume --load_run from_best --checkpoint model_best.pt
```

- ⚠️ 혹시 `model_best.pt` 를 못 찾는다고 나오면 **숫자 이름**으로 바꿔 넣으세요 — `cp exported/model_best.pt logs/rsl_rl/quadruped/from_best/model_99999.pt` 후 `--checkpoint model_99999.pt` (이어받을 iter 번호는 파일 내부 값이라 이름은 아무 숫자나 OK).

> resume 을 하면 이어받을 때 **지형 난이도(curriculum)가 쉬운 단계로 리셋**됩니다. 따라서 이어받은 직후 보상이 잠깐 부풀 수 있어요.
> 그래서 제출본은 가능하면 `from scratch` 로 한 번에 길게 돌리는 게 깔끔해요.


---

## 2. 플레이 = 영상 확인 (play.py)

**확인은 영상으로만 합니다.** `--video` 로 돌리면 정책이 걷는 mp4 가 만들어지고 `exported/` 로 자동 복사돼요. 카메라는 로봇을 따라다니도록 기본 설정돼 있습니다.

```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 1 \
    --headless --video --video_length 1000 --enable_cameras
```

- `--video_length 1000` = 50Hz × 1000 = **20초** (400 = 8초).
- `--num_envs N` = 화면에 띄울 로봇 대수. `1` = 한 대(걸음 확인용), 여러 대(16·100 등)는 아래 부감 카메라와 같이 쓰세요. 많을수록 GPU 메모리를 더 씁니다.
- 끝에 `[play] ★ 영상 export 완료` 로그와 함께 파일 위치가 찍힙니다.
- 플레이는 `model_best.pt` 가 있어야 합니다 (학습을 먼저).

### 플레이 후 생기는 파일 — `quadruped/exported/`

| 파일 | 내용 |
|---|---|
| `play_video.mp4` (+ `play_video_<ts>.mp4`) | ★ 확인용 영상 (최신 + 백업) |
| `policy.pt` (+ `policy_<ts>.pt`) | 매치용 정책 (TorchScript) |
| `policy.onnx` (+ `policy_<ts>.onnx`) | 매치용 ONNX |

→ **`exported/play_video.mp4`** 만 열거나 다운로드하면 됩니다 (`logs/.../videos/` 뒤질 필요 없음).
영상에서 로봇이 **앞으로 또박또박 걸으면 정상**, 제자리·휘청이면 reward 재조정 후 재학습.

### 카메라 — 멀리서 / 부감으로 보고 싶을 때

기본은 로봇 추적. 거리·시점은 명령 뒤에 붙여 조절.

**① 더 멀리서 따라가기** (추적 유지, 거리만 ↑):
```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 1 \
    --headless --video --video_length 1000 --enable_cameras \
    env.viewer.eye="[-10.0,-10.0,6.0]"
```

**② 고정 부감 — 여러 대를 위에서** (1대는 지형에 묻혀 안 보이니 여러 대로):
```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 16 \
    --headless --video --video_length 1000 --enable_cameras \
    env.viewer.origin_type=world \
    env.viewer.eye="[35.0,35.0,22.0]" \
    env.viewer.lookat="[8.0,8.0,0.0]"
```

- 부감이 듬성하면 `--num_envs 36`, `eye` 를 더 키우세요 (지형이 로봇을 ~8m 간격으로 흩뿌림).
- "잘 걷나" 확인엔 추적(기본 명령)이 더 명확합니다. 부감은 전경 분위기용.

### 밀침 테스트 — G6(밀침 회복) 대비 확인 (`--push`)

채점표의 **G6 밀침 회복**을 영상으로 확인하고 싶을 때 씁니다. 4초마다 무작위
방향으로 순간 충격이 가해지고, 로봇이 버티는지 영상에 그대로 찍힙니다.

```bash
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 1 \
    --headless --video --video_length 1000 --enable_cameras --push
```

- 세기 조절: `--push 0.8` (숫자 = 충격 속도 m/s, 기본 0.5). 여러 세기로 시험해 보세요.
- **play 전용**입니다 — 학습 환경에는 밀침이 없고 켤 수도 없습니다 (전 팀 동일 조건).
  실제 평가의 충격 크기·간격은 여기 값과 다르며 공개하지 않습니다.
- 밀침 회복력은 별도 학습 없이 자세·안정성 계열 reward 가 결정합니다 — 요철에서
  덜 휘청이게 만들면 밀침에서도 덜 넘어집니다.

---

## 3. 제출물 (예선)

운영자에게 내는 건 **세 가지**입니다. 정책 파일 하나만 내면 안 돼요.

| 제출물 | 위치 / 방법 | 설명 |
|---|---|---|
| `policy.pt` | `quadruped/exported/` | 학습한 정책 (TorchScript) — **`play.py` 를 돌려야 생깁니다** |
| `env.yaml` | `quadruped/exported/` | 어떤 reward 로 학습했는지 (의도) |
| 기술 개선 리포트 | **예선 대시보드에 입력** | reward 를 무엇을·왜 바꿨는지 설명 |

결과(pt) + 의도(yaml) + 기술 설명(코멘트)이 **함께** 평가됩니다.
영상으로 확인한 뒤 셋 다 **예선 대시보드에서 업로드**하세요.

> ⚠️ `policy.pt` 는 학습만으로는 안 생깁니다. `play.py` 를 실행하면 그 끝에 `exported/policy.pt` 로 복사됩니다 (`ls exported/policy.pt` 로 확인).
> `model_best.pt` 는 학습 체크포인트로, 이어받기(resume)·`play.py` 실행에 쓰는 파일입니다.

> 📄 `exported/report.html` (결과 분석 리포트)은 **제출물이 아닙니다** — 자기 학습 결과를
> 점검하도록 제공되는 참고 자료입니다.

---

## Go2 특징

- **사족보행** — 낮은 자세라 균형이 H1 보다 잡기 쉽습니다.
- 계단·경사 climb, 박스 미로 통과에 유리합니다.
- 학습 지형의 박스 높이가 **≤0.15m** 로 제한됩니다 — 0.45m 박스언덕 등반은 어려워요 (그건 H1 의 영역).
- **학습 시간은 H1 보다 오래 걸려요 (정상).** IsaacLab 이 H1 은 단순화 콜라이더(`H1_MINIMAL_CFG`), Go2 는 풀 콜라이더(`UNITREE_GO2_CFG`)로 돌려 Go2 쪽 step 당 충돌 계산이 더 무겁기 때문이에요. 물리 시뮬 속도는 관절 수가 아니라 충돌 계산량이 좌우합니다. **학습 품질과는 무관**하니 시간만 더 잡으면 돼요.
