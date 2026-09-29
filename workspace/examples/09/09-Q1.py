# 9강 · 코드 실습하기 Q1 — 기본 · 지금 눌려 있는 키
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 실습 코드와 같아요. add가 누름, discard가 뗌이에요. W와 D를 함께 누르고 있다가 W만 손을 뗐을 때 눌려 있는 키 수는?

pressed = set()

pressed.add("W")
pressed.add("D")
pressed.discard("W")

print(f"지금 눌려 있는 키 = {sorted(pressed)}")
print(f"눌려 있는 키 수 = {len(pressed)}")
