# 17강 · 첫 걸음 — 코드로 LLM과 대화하기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import requests, threading

LLM_URL = "http://127.0.0.1:11434/api/chat"
MODEL   = "isaac-tutor-ko-9b"

def ask_llm(prompt):
    resp = requests.post(LLM_URL, json={
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "think": False,
        "stream": False,
        "options": {"temperature": 0.3},
    }, timeout=60)
    return resp.json()["message"]["content"]

def run(prompt):
    def worker():
        try:
            print(ask_llm(prompt))
        except Exception as e:
            print("호출 실패:", e)
    threading.Thread(target=worker, daemon=True).start()

run("자율 이동 로봇이 뭔지 딱 한 문장으로만 답해줘. 코드, 목록, 부가 설명은 쓰지 마.")
