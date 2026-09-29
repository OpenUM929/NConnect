# 19강 · 코드 실습하기 Q3 — 도전 · 공유 상태 꺼내오기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 스왑 뒤 target 값을 입력해보세요.

brain = {"next": 2}     # 대뇌가 2번 큐브로 정해뒀어요
target = None

# 빠른 루프: 준비됐으면 꺼내오고, 자리는 비워요
if target is None and brain["next"] is not None:
    target, brain["next"] = brain["next"], None

print("target =", target, "/ brain[next] =", brain["next"])
