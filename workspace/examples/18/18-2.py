# 18강 · 자연어 명령을 velocity JSON으로 바꾸기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, json, threading

LLM_URL = "http://127.0.0.1:11434/api/chat"
MODEL   = "isaac-tutor-ko-9b"

SYSTEM_PROMPT = """너는 사족보행 로봇의 속도 벡터 변환기다.
사용자의 자연어 명령을 읽고, 로봇이 따라야 할 속도를 결정한다.

제약:
- velocity_x: 전진 속도 (m/s), -1.0 ~ 1.0 (양수=전진)
- velocity_y: 측면 속도 (m/s), -0.5 ~ 0.5 (양수=왼쪽)
- velocity_yaw: 회전 속도 (rad/s), -1.0 ~ 1.0 (양수=반시계)

출력은 반드시 아래 JSON 한 개뿐이다.
JSON 앞뒤로 인사말, 설명, 마크다운을 절대 붙이지 마라.

{"velocity_x": <float>, "velocity_y": <float>, "velocity_yaw": <float>, "reason": "<한 문장>"}"""

def ask_velocity(command_text):
    resp = requests.post(LLM_URL, json={
        "model": MODEL, "think": False, "stream": False,
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": command_text},
        ],
    }, timeout=60)
    return resp.json()["message"]["content"]

def run():
    raw = ask_velocity("앞으로 천천히 가면서 살짝 왼쪽으로 틀어.")
    cmd = json.loads(raw)
    print("velocity_command =", [cmd["velocity_x"], cmd["velocity_y"], cmd["velocity_yaw"]])

threading.Thread(target=run, daemon=True).start()
