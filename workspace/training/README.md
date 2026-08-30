# NAVER Connect Robotics Cup 2026 — 예선 (Preliminary)

학생이 **reward 수정 → 학습 → 영상으로 검증 → 제출**하는 단계예요. (본선은 별도 단계.)

> **실행 환경: Ubuntu + 클라우드 컨테이너 (headless, GUI 창 없음).**
> 학습·플레이 모두 `--headless`로 돌리고, **결과 확인은 영상(mp4)으로만** 합니다.
> 런처는 IsaacLab의 `isaaclab.sh` — 이 문서는 `/workspace/IsaacLab/isaaclab.sh` 기준 (경로는 환경에 맞게).

## 폴더 구조

```
training/
├── humanoid/                 # 휴머노이드 H1 학습 패키지
│   ├── humanoid_rewards.py   ← ★ 학생이 reward 수정하는 파일
│   ├── h1_task/              ← env/agent config (import 패키지, 수정 X)
│   ├── train.py              ← 학습
│   ├── play.py               ← 플레이 (영상 + policy.pt 추출)
│   └── README.md
│
└── quadruped/                # 사족 Go2 학습 패키지 (구조 동일)
    ├── quadruped_rewards.py  ← ★ 학생용
    ├── go2_task/
    ├── train.py
    ├── play.py
    └── README.md
```

## 학생이 수정하는 파일

| 파일 | 권한 | 설명 |
|---|---|---|
| `humanoid/humanoid_rewards.py` | ✅ 수정 | H1 reward 가중치 |
| `quadruped/quadruped_rewards.py` | ✅ 수정 | Go2 reward 가중치 |
| 그 외 (`h1_task/`, `go2_task/`, train/play) | ❌ 수정 금지 | env config, network |

---

## 1. 학습 (train.py)

학습은 몇 시간씩 걸려요. **반드시 `tmux` 안에서 시작하세요.** code-server 터미널은 끊기면 학습이 멈춥니다(죽지 않고 그대로 정지). tmux 안에서 돌리면 브라우저/SSH 가 끊기거나 창을 닫아도 계속 돕니다.

```bash
tmux new -As train    # train 세션 생성(있으면 재접속) → 이 안에서 아래 학습 명령 실행
# 학습이 돌기 시작하면: Ctrl+b 누른 뒤 d → 빠져나오기(detach). 창 닫아도 OK.
tmux attach -t train  # 나중에 다시 들어가 진행 확인
```

세션 안에서 각 로봇 폴더로 이동해 실행. `--headless` 필수(컨테이너에 창 없음). 명령 안의 `\` 는 줄바꿈 이어쓰기라 **블록째 복사**하면 됩니다.

```bash
# H1 (휴머노이드)
cd /workspace/training/humanoid
/workspace/IsaacLab/isaaclab.sh -p train.py --task Humanoid-v0 \
    --num_envs 4096 --max_iterations 10000 --headless
```

```bash
# Go2 (사족)
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p train.py --task Quadruped-v0 \
    --num_envs 4096 --max_iterations 10000 --headless
```

- `--max_iterations`: 길수록 좋지만 수렴하면 정체. RTX 5080 기준 10000 iter ≈ **H1 5h · Go2 8h**.
- 학습이 끝나면 best 체크포인트가 자동 선별돼 `exported/`로 정리됩니다 (아래).

> **참고 — Go2는 H1보다 학습이 오래 걸려요 (정상이에요).**
> IsaacLab은 H1을 학습용으로 **콜라이더를 단순화한 버전**(`H1_MINIMAL_CFG`)으로 제공해 충돌 계산이 가볍고, Go2는 **풀 콜라이더**(`UNITREE_GO2_CFG`)라 매 step 접촉 계산이 더 무겁습니다. 그래서 관절 수는 H1(19개)이 Go2(12개)보다 많아도 **Go2가 더 느려요** — 물리 시뮬 속도는 관절 수가 아니라 **충돌 계산량**이 좌우하거든요. IsaacLab 기본 설정이고 **학습 품질과는 무관**하니, Go2는 시간만 더 잡으면 됩니다.

### 학습 후 생기는 파일 — `<로봇>/exported/`

| 파일 | 내용 |
|---|---|
| `model_best.pt` | ★ 예선 채점용 체크포인트 (best iter 자동 선별) |
| `model_best_<타임스탬프>.pt` | 백업 |
| `env.yaml` (+ `env_<ts>.yaml`) | 학습 환경·reward dump (의도 검증용) |

전체 로그·중간 체크포인트: `<로봇>/logs/rsl_rl/<humanoid|quadruped>/<run>/`

---

## 2. 플레이 = 영상 확인 (play.py)

**확인은 영상으로만 합니다.** `--video`로 돌리면 정책이 걷는 mp4가 만들어지고 `exported/`로 자동 복사돼요. 카메라는 **로봇을 따라다니도록** 기본 설정돼 있습니다.

```bash
# H1
cd /workspace/training/humanoid
/workspace/IsaacLab/isaaclab.sh -p play.py --task Humanoid-v0 --num_envs 1 \
    --headless --video --video_length 1000 --enable_cameras
```

```bash
# Go2
cd /workspace/training/quadruped
/workspace/IsaacLab/isaaclab.sh -p play.py --task Quadruped-v0 --num_envs 1 \
    --headless --video --video_length 1000 --enable_cameras
```

- `--video_length 1000` = 50Hz × 1000 = **20초** (400 = 8초).
- 끝에 `[play] ★ 영상 export 완료` 로그와 함께 파일 위치가 찍힙니다.
- 플레이는 model_best.pt 가 있어야 합니다 (학습을 먼저).

### 플레이 후 생기는 파일 — `<로봇>/exported/`

| 파일 | 내용 |
|---|---|
| `play_video.mp4` (+ `play_video_<ts>.mp4`) | ★ 확인용 영상 (최신 + 백업) |
| `policy.pt` (+ `policy_<ts>.pt`) | ★ 예선 제출물 · 본선 매치용 정책 (TorchScript) |
| `policy.onnx` (+ `policy_<ts>.onnx`) | ONNX 포맷 |

→ **`exported/play_video.mp4`** 만 열거나 다운로드하면 됩니다 (`logs/.../videos/` 뒤질 필요 없음).
영상에서 로봇이 **앞으로 또박또박 걸으면 정상**, 제자리 회전·휘청이면 reward 재조정 후 재학습.

---

## 3. 제출물 (예선)

운영자에게 내는 건 **세 가지**입니다. 정책 파일 하나만 내면 안 돼요.

| 제출물 | 위치 / 방법 | 설명 |
|---|---|---|
| `policy.pt` | `<로봇>/exported/` | 학습한 정책 (TorchScript) — **`play.py` 를 돌려야 생깁니다** |
| `env.yaml` | `<로봇>/exported/` | 어떤 reward로 학습했는지 (학습 의도) |
| 기술 개선 리포트 | **팀 대시보드에 입력** | reward를 무엇을·왜 바꿨는지 설명 |

`policy.pt`(결과)뿐 아니라 `env.yaml`(의도)과 기술 개선 리포트(개선 설명)까지 **함께** 평가됩니다. 영상으로 정책을 확인한 뒤, 세 가지를 모두 **팀 대시보드에서** 제출하세요.

> ⚠️ `model_best.pt` 는 학습 체크포인트로 **제출물이 아닙니다.** 제출용 `policy.pt` 는
> `play.py` 를 실행하면 `exported/` 에 생성됩니다 (`ls exported/policy.pt` 로 확인).

> 📄 `exported/report.html` (결과 분석 리포트)도 자동 생성되지만 **제출물이 아닙니다** —
> 자기 학습 결과를 점검하는 참고 자료입니다.
