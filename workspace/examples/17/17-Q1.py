# 17강 · 코드 실습하기 Q1 — 기본 · 답에서 속도 뽑아내기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 실행하면 나오는 yaw 값을 입력해보세요.

reply = """장애물이 왼쪽에 있어 오른쪽으로 살짝 틀며 갈게요.
[0.6, 0.0, -0.4]"""

last = reply.strip().splitlines()[-1]
vx, vy, yaw = [float(n) for n in last.strip("[] ").split(",")]
print(f"vx={vx}  vy={vy}  yaw={yaw}")
