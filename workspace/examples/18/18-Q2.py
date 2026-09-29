# 18강 · 코드 실습하기 Q2 — 보통 · 옆걸음만 범위가 좁아요
# 실행하면 아래 물음의 답이 출력 영역에 떠요.
# 출력된 velocity_y 값을 입력해보세요.

def clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))

def sanitize(cmd):
    return {
        "velocity_x":   clamp(cmd.get("velocity_x", 0.0),  -1.0, 1.0),
        "velocity_y":   clamp(cmd.get("velocity_y", 0.0),  -0.5, 0.5),
        "velocity_yaw": clamp(cmd.get("velocity_yaw", 0.0), -1.0, 1.0),
    }

out = sanitize({"velocity_x": 0.3, "velocity_y": 0.9, "velocity_yaw": 2.0})
print(out["velocity_y"])
