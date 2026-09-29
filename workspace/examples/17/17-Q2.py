# 17강 · 코드 실습하기 Q2 — 보통 · 숫자가 없으면 멈추기
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 숫자를 못 찾았을 때 나오는 vx 값을 입력해보세요.

def parse_velocity(reply):
    try:
        last = reply.strip().splitlines()[-1]
        vx, vy, yaw = [float(n) for n in last.strip("[] ").split(",")]
        return (vx, vy, yaw)
    except (ValueError, IndexError):
        return (0.0, 0.0, 0.0)

reply = "음, 지금은 왼쪽으로 도는 게 좋을 것 같아요!"
vx, vy, yaw = parse_velocity(reply)
print(f"명령 → {vx} {vy} {yaw}")
