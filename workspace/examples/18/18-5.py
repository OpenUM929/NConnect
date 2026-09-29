# 18강 · 전체 실행본, 이 탭을 통째로 복사하세요
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, json, re, threading

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

def extract_json(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m is None:
        raise ValueError(f"JSON 없음: {text[:80]}")
    return json.loads(m.group(0))

def clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))

def sanitize(cmd):
    return {
        "velocity_x":   clamp(cmd.get("velocity_x", 0.0),  -1.0, 1.0),
        "velocity_y":   clamp(cmd.get("velocity_y", 0.0),  -0.5, 0.5),
        "velocity_yaw": clamp(cmd.get("velocity_yaw", 0.0), -1.0, 1.0),
        "reason": str(cmd.get("reason", ""))[:100],
    }

STOP = {"velocity_x": 0.0, "velocity_y": 0.0, "velocity_yaw": 0.0, "reason": "안전 정지"}

def command_from_speech(text, retries=3):
    for attempt in range(1, retries + 1):
        try:
            raw = ask_velocity(text)
            return sanitize(extract_json(raw))
        except Exception as e:
            print(f"  {attempt}차 시도 실패: {e}")
    return STOP

def run():
    for speech in ["뒤로 천천히", "제자리에서 오른쪽으로 돌아",
                   "전속력으로 가줘!", "음... 알아서 해줘"]:
        cmd = command_from_speech(speech)
        print(f"'{speech}' -> [{cmd['velocity_x']}, {cmd['velocity_y']},"
              f" {cmd['velocity_yaw']}]  ({cmd['reason']})")

threading.Thread(target=run, daemon=True).start()
