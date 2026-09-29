# 18강 · 보너스, 예시 3개로 일관성 끌어올리기 (전체 실행본)
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, json, threading

LLM_URL = "http://127.0.0.1:11434/api/chat"
MODEL   = "isaac-tutor-ko-9b"

BASE_PROMPT = """너는 사족보행 로봇의 속도 벡터 변환기다.
사용자의 자연어 명령을 읽고, 로봇이 따라야 할 속도를 결정한다.

제약:
- velocity_x: 전진 속도 (m/s), -1.0 ~ 1.0 (양수=전진)
- velocity_y: 측면 속도 (m/s), -0.5 ~ 0.5 (양수=왼쪽)
- velocity_yaw: 회전 속도 (rad/s), -1.0 ~ 1.0 (양수=반시계)

출력은 반드시 아래 JSON 한 개뿐이다.
JSON 앞뒤로 인사말, 설명, 마크다운을 절대 붙이지 마라.

{"velocity_x": <float>, "velocity_y": <float>, "velocity_yaw": <float>, "reason": "<한 문장>"}"""

FEWSHOT = """

예시:
[명령] 앞으로 빠르게
[출력] {"velocity_x": 0.9, "velocity_y": 0.0, "velocity_yaw": 0.0, "reason": "고속 전진"}

[명령] 멈춰
[출력] {"velocity_x": 0.0, "velocity_y": 0.0, "velocity_yaw": 0.0, "reason": "정지"}

[명령] 왼쪽으로 크게 돌아
[출력] {"velocity_x": 0.3, "velocity_y": 0.0, "velocity_yaw": 0.8, "reason": "전진하며 좌선회"}"""

def ask_velocity(command_text, system_prompt):
    resp = requests.post(LLM_URL, json={
        "model": MODEL, "think": False, "stream": False,
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": command_text},
        ],
    }, timeout=60)
    return resp.json()["message"]["content"]

def try_five(label, system_prompt, command):
    print(label)
    for i in range(5):
        try:
            cmd = json.loads(ask_velocity(command, system_prompt))
            print(f"  {i + 1}회  vx={cmd['velocity_x']}")
        except Exception as e:
            print(f"  {i + 1}회  실패: {e}")

def run():
    command = "앞으로 적당히 빠르게"
    try_five("[예시 없이]", BASE_PROMPT, command)
    try_five("[예시 3개]", BASE_PROMPT + FEWSHOT, command)

threading.Thread(target=run, daemon=True).start()
