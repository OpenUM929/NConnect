# 19강 · 코드 실습하기 Q2 — 보통 · Gemini 실패 시 fallback
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력된 남은 큐브 수를 입력해보세요.

cubes = ["노랑", "초록", "빨강"]
visited = ["노랑"]

remaining = [c for c in cubes if c not in visited]
print("남은 큐브 수:", len(remaining))
print("fallback이 고를 큐브:", remaining[0])
