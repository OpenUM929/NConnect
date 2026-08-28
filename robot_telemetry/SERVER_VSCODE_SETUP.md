# 서버 VS Code에서의 설치·연결 절차

대상 작업공간은 브라우저 VS Code의 `/workspace`입니다. 이 패키지는 외부 Python
라이브러리를 설치하지 않으므로, 서버의 Python 환경을 바꾸지 않고 파일만 복사해 사용할 수
있습니다.

## 1. 파일 배치

VS Code Explorer에서 `/workspace/robot_telemetry` 폴더를 만들고 아래 파일을 업로드합니다.

```text
/workspace/robot_telemetry/
  telemetry.py
  config/motion_plan.json
  README.md
  TEST_RUNBOOK.md
```

`demo.py`와 `tests/`는 서버에서 형식을 사전 검증할 때만 추가합니다.

## 2. 서버에서 형식만 먼저 확인

VS Code Terminal에서 실행합니다.

```bash
cd /workspace/robot_telemetry
python -m unittest discover -s tests -v
python demo.py
```

`demo.py` 결과는 기본적으로 시스템 임시 폴더에 생성됩니다. 실제 서버 테스트 로그는
`/workspace/robot_telemetry/runs/<run_name>/run.jsonl`처럼 실행별 새 폴더에 둡니다.

## 3. 붙일 위치 선택

| 목적 | 보통 붙일 파일 | 이유 |
|---|---|---|
| 학습 중 정책 경향만 보기 | `training/quadruped/train.py` 또는 `training/humanoid/train.py` | 학습 단계별 관측·보상과 함께 기록 가능 |
| 학습된 정책의 서기/이동/언덕 시험 | `training/quadruped/play.py` 또는 `training/humanoid/play.py` | 정책을 고정하고 시나리오별 행동만 비교 가능 |
| 큐브 수집 실제 미션 시험 | `practice_sim/practice_sim.py` | 전략문, 목표 선택, 차량·충돌까지 함께 관찰 가능 |

처음에는 **`play.py`의 정책 평가 루프**에 연결합니다. 학습을 섞지 않아 원인 분리가 가장
쉽습니다. S01~S06이 안정화된 뒤에만 `practice_sim.py` 미션 로그를 추가합니다.

## 4. Isaac 루프 연결 규칙

1. 로봇/정책/맵을 모두 불러온 직후 `TelemetryRecorder`를 하나 만든다.
2. 시나리오 시작 시 `start_phase`를 한 번 호출한다.
3. 제어 반복문에서 `sample_period_s`마다 Isaac 텐서를 SI 단위로 변환해 `sample`을 호출한다.
4. 낙상·충돌·시간초과가 감지된 순간 `incident`를 호출한다.
5. 환경을 리셋하기 전에 `evaluate_phase`와 `complete_phase`를 호출한다.

경로 예시:

```python
from pathlib import Path
import sys
sys.path.insert(0, "/workspace/robot_telemetry")
from telemetry import TelemetryRecorder, evaluate_phase

run_dir = Path("/workspace/robot_telemetry/runs/run_20260827_001")
recorder = TelemetryRecorder(run_dir / "run.jsonl", "Go2", {
    "policy_path": str(policy_path),
    "map": "practice_map",
    "task": "Quadruped-v0",
    "motion_plan_path": "/workspace/robot_telemetry/config/motion_plan.json",
})
```

## 5. 서버에서 실행 후 보관할 것

매 실행 폴더에 다음을 남깁니다.

```text
run.jsonl             # 원본: 분석의 기준, 절대 편집하지 않음
motion_plan.json      # 실제 사용한 설정의 사본
run_note.txt          # 이번 변경값·예상·실제 관찰
samples.csv           # 원본 로그에서 내보낸 시점별 데이터
phase_summary.csv     # 단계별 비교표
phase_summary.md      # 빠른 확인용 표
```

`run.jsonl`이 생성된 뒤, 같은 서버 터미널에서 다음처럼 표를 만들 수 있습니다.

```python
from pathlib import Path
import sys
sys.path.insert(0, "/workspace/robot_telemetry")
from telemetry import export_artifacts
export_artifacts(Path("/workspace/robot_telemetry/runs/run_20260827_001/run.jsonl"),
                 Path("/workspace/robot_telemetry/runs/run_20260827_001"))
```

## 주의

* `/workspace` 안의 실제 소스 구조와 변수명은 이 문서만으로 확정할 수 없습니다.
* 현재 `play.py` 또는 `practice_sim.py` 소스를 열었을 때, 제어 루프와 로봇 상태 텐서를
  제공하는 부분이 확인되면 그 코드에 맞춘 정확한 삽입 패치를 작성할 수 있습니다.
* 로그 기능 추가 전에는 원본 파일을 VS Code에서 복사해 백업합니다.
