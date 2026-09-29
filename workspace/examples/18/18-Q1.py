# 18강 · 코드 실습하기 Q1 — 기본 · 범위 밖 값 잘라내기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력된 값을 입력해보세요.

def clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))

print(clamp(1.8, -1.0, 1.0))
