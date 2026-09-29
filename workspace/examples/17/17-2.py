# 17강 · 두 번째 걸음 — 판단을 글로 맡기기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, threading

LLM_URL = "http://127.0.0.1:11434/api/chat"
MODEL   = "isaac-tutor-ko-9b"

situation = """너는 도서관 정리 로봇의 판단을 도와주는 시스템이야.

[지금 상황]
- 로봇은 도서관 입구에 서 있다.
- 정리할 책이 두 권 보인다.
  · 책 A: 가까운 책상 위 (3m 거리)
  · 책 B: 통로 한가운데 바닥 (7m) - 사람이 밟고 미끄러질 수 있다
- 임무: 책을 모두 제자리에. 단, 사람에게 피해를 주면 안 된다.

어떤 순서로 움직이는 게 좋을까?
판단과 이유만 글로 짧게 답해줘. 한 문장마다 줄을 바꾸고, 코드나 코드 블록은 절대 쓰지 마."""

def worker():
    try:
        resp = requests.post(LLM_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": situation}],
            "think": False,
            "stream": False,
            "options": {"temperature": 0.3},
        }, timeout=60)
        answer = resp.json()["message"]["content"]
        answer = answer.split("```")[0].strip()
        print(answer)
    except Exception as e:
        print("호출 실패:", e)

threading.Thread(target=worker, daemon=True).start()
