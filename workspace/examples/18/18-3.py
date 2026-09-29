# 18강 · 안전망 1 · 응답에서 JSON만 도려내기
# Isaac Sim Script Editor 에 붙여 실행하세요 (강의 본문과 같은 코드).

import json, re

def extract_json(text):
    """응답에서 첫 JSON 오브젝트만 도려내기 (앞뒤 잡담·코드펜스 무시)."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m is None:
        raise ValueError(f"JSON 없음: {text[:80]}")
    return json.loads(m.group(0))

messy = '네! 요청하신 명령입니다: {"velocity_x": 0.4, "velocity_y": 0.0, "velocity_yaw": 0.0} 확인하세요.'
print(extract_json(messy))
