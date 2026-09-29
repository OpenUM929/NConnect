# 17강 · 세 번째 걸음 — 판단을 속도 벡터로 받기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, threading

LLM_URL = "http://127.0.0.1:11434/api/chat"
MODEL   = "isaac-tutor-ko-9b"

situation = """너는 도서관 정리 로봇의 판단을 도와주는 시스템이야.

[지금 상황]
- 로봇은 입구에서 정면(+x)을 보고 서 있다.
- 책 B가 정면에서 살짝 왼쪽, 7m 앞 바닥에 있다.
- 임무: 책 B 쪽으로 천천히 이동 시작.

짧게 설명할 거면 한 문장마다 줄을 바꿔 적고,
답의 맨 마지막 줄은 [전진 m/s, 좌우 m/s, 회전 rad/s] 숫자 세 개로만 끝내. 예: [0.4, 0.0, 0.3]
대괄호 안에는 숫자만 적어라. 이름표나 단위(m/s 같은 것)를 넣지 마라.
그 뒤에 아무 말도, 코드도, 요약도 덧붙이지 마."""

def three_numbers(line):
    nums = []
    for chunk in line.replace("[", " ").replace("]", " ").replace(",", " ").split():
        try:
            nums.append(float(chunk))
        except ValueError:
            pass
    return nums if len(nums) == 3 else None

def worker():
    try:
        resp = requests.post(LLM_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": situation}],
            "think": False,
            "stream": False,
            "options": {"temperature": 0.3},
        }, timeout=60)
    except Exception as e:
        print("호출 실패:", e)
        return
    text = resp.json()["message"]["content"]
    print(text)
    velocity_command = None
    for line in reversed(text.strip().splitlines()):
        velocity_command = three_numbers(line)
        if velocity_command:
            break
    if velocity_command:
        print("velocity_command =", velocity_command)
    else:
        print("숫자 세 개를 못 찾았어요. LLM이 약속을 어긴 거죠. 18강에서 이걸 해결해요.")

threading.Thread(target=worker, daemon=True).start()
