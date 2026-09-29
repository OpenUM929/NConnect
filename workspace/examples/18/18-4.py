# 18강 · 안전망 2 · 범위 밖 값은 잘라내기 (clamp)
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

def clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))

def sanitize(cmd):
    """LLM이 무슨 값을 주든 정책이 소화 가능한 범위로 자른다."""
    return {
        "velocity_x":   clamp(cmd.get("velocity_x", 0.0),  -1.0, 1.0),
        "velocity_y":   clamp(cmd.get("velocity_y", 0.0),  -0.5, 0.5),
        "velocity_yaw": clamp(cmd.get("velocity_yaw", 0.0), -1.0, 1.0),
        "reason": str(cmd.get("reason", ""))[:100],
    }

print(sanitize({"velocity_x": 5.0, "velocity_yaw": -9.0, "reason": "전속력"}))
