# 전략을 LLM에게 주고, 두 루프로 3색 큐브를 순서대로 방문한다 (19강)
#
# ⚠ Script Editor 에 붙여 넣으면 안 돼요. 아래처럼 터미널에서 실행하세요.
#     cd /workspace/examples/19
#     /workspace/IsaacLab/isaaclab.sh -p 19-1.py
# 같은 폴더의 robot_sim.py 를 가져다 쓰기 때문에, 그 폴더에서 러너로 실행해야
# 찾을 수 있어요. Script Editor 는 코드를 임시 폴더로 복사해 돌리므로
# ModuleNotFoundError: No module named 'robot_sim' 이 나요.
import requests, threading, time
from robot_sim import World, Robot, Cube, parse_cube_order, load_gemini_key

# ── 내가 정하는 것 (딱 두 줄) ──
STRATEGY = "노란 큐브부터, 그다음 초록, 마지막에 빨강 순서로 가줘"   # 전략 (자연어)
POLICY   = "my_test.pt"                                        # 3챕터에서 만든 내 정책

# 느린 대뇌 = Gemini (클라우드). 로컬 GPU를 안 써서 시뮬 렌더·스트리밍과 안 부딪혀요.
GEMINI_KEY   = load_gemini_key()   # 환경변수 GEMINI_API_KEY → practice_key.bin 순으로 자동
GEMINI_MODEL = "gemini-3.1-flash-lite"
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
CUBES        = ["yellow", "green", "red"]
if GEMINI_KEY:
    print(f"[대뇌] ✅ LLM 활성 — Gemini({GEMINI_MODEL}) 가 전략을 해석합니다 (키 {len(GEMINI_KEY)}자 로드).")
else:
    print("[대뇌] ⚠ Gemini 키를 못 찾았어요 — practice_key.bin 을 이 폴더에 두거나 GEMINI_API_KEY 를 설정하세요.")
    print("[대뇌] → LLM 미사용: 규칙 기반 기본 순서(노랑→초록→빨강)로 진행합니다.")


# ── 🧠 느린 대뇌: 전략 + 지금까지 방문한 큐브를 주고 "다음에 갈 큐브"를 물어봄 ──
def ask_next(strategy, visited):
    remaining = [c for c in CUBES if c not in visited]
    if not remaining:
        return None
    prompt = (f'로봇에게 준 명령: "{strategy}"\n'
              f'큐브는 yellow, green, red 세 개다. '
              f'명령대로 방문할 전체 순서를 JSON 배열로만 답하라. 예: ["red","yellow","green"]')
    print(f"[대뇌] 🧠 Gemini 호출 → {GEMINI_MODEL}  (남은 큐브: {remaining})")
    t0 = time.time()
    resp = requests.post(GEMINI_URL,
        headers={"x-goog-api-key": GEMINI_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30)
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    order = parse_cube_order(text, CUBES)              # Gemini가 정한 전체 순서
    print(f"[대뇌] 🧠 Gemini 응답 ({time.time()-t0:.1f}s, HTTP {resp.status_code}): "
          f"{text.strip()!r} → 파싱 순서 {order}")
    return next((c for c in order if c in remaining), remaining[0])   # 아직 안 간 첫 큐브


# ── 씬: 로봇 + 3색 큐브 ──
world = World()
robot = Robot(world, POLICY)
cubes = {
    "yellow": Cube(world, x=8.0,  y=6.0,  color="yellow"),   # 서로 멀찍이 — 걷는 걸 오래 볼 수 있게
    "green":  Cube(world, x=16.0, y=0.0,  color="green"),
    "red":    Cube(world, x=8.0,  y=-6.0, color="red"),
}

# ── 공유 상태 (느린 대뇌 ↔ 빠른 소뇌) ──
visited = []
brain = {"next": None}

def think():
    """느린 대뇌를 백그라운드로 굴림 — 이래야 시뮬(빠른 소뇌)이 안 멈춰요 (19강 핵심)."""
    used = "🧠 Gemini(LLM)"
    try:
        nxt = ask_next(STRATEGY, list(visited))
    except Exception as e:
        used = "⚙ 규칙 fallback"
        rem = [c for c in CUBES if c not in visited]
        nxt = rem[0] if rem else None
        print(f"[대뇌] ⚠ Gemini 실패 → 규칙 fallback (남은 것부터): {type(e).__name__}: {e}")
    if nxt:
        print(f'[대뇌] {used} 결정: "{STRATEGY}" → 다음은 {nxt}  (방문함: {visited or "없음"})')
    else:
        print("[대뇌] 🧠 갈 곳 없음")
    brain["next"] = nxt


# ── 시작: 명령을 읽고, LLM이 생각을 마칠 때까지 서서 대기 ──
print(f'[대뇌] 명령 읽음: "{STRATEGY}" — LLM 생각 중...')
threading.Thread(target=think, daemon=True).start()   # 느린 대뇌 시작 (아래 대기와 동시에)

try:
    WAIT = 30.0
    print(f"[소뇌] 🧍 로딩 대기 시작 ({WAIT:.0f}초) — 브라우저 스트림 접속·씬 로딩·LLM 생각 시간을 벌려고")
    print( "[소뇌]    제자리에서 균형만 잡아요 (멈춘 게 아니라 '대기 중' — 곧 출발).")
    robot.stand(seconds=WAIT)                          # 스트리밍 접속·로딩 여유 (그동안 정책이 균형)
    print( "[소뇌] ▶ 대기 끝 — 이제 LLM이 정한 순서대로 큐브를 방문하러 출발합니다.")

    # ── 두 루프: 대뇌가 목표를 주면 걸어가고, 큐브에 닿으면 다시 대뇌에게 다음을 물어봄 ──
    target = None
    while world.is_running():
        if target is None and brain["next"] is not None:      # 대뇌가 결정했으면 출발
            target, brain["next"] = brain["next"], None       # 꺼내 오며 자리를 비움
            print(f"[소뇌] 🦿 출발 → {target}")

        if target is not None:
            goal = cubes[target].pos
            robot.walk_to(goal)                                # 빠른 소뇌: 정책으로 걸음
            if robot.reached(goal):                            # 큐브에 닿으면
                visited.append(target)
                print(f"[소뇌] ✅ 도착: {target}")
                target = None
                if len(visited) < len(CUBES):
                    threading.Thread(target=think, daemon=True).start()   # 다시 생각 → 다음 임무
                else:
                    print("[소뇌] 🎉 모든 큐브 방문 완료 — 종료합니다")
                    robot.stand(3.0)                           # 마지막 큐브 앞에서 잠깐 (완료 확인)
                    break                                       # 모두 방문 → 루프 종료
        else:
            robot.hold()                                       # 생각 중 — 제자리 대기
        world.step()
except KeyboardInterrupt:
    print("\n[소뇌] 종료 요청 — 정리 중...")                    # Ctrl+C 도 깔끔히
finally:
    world.close()      # 아이작심 종료 — 스트림·GPU 반환, 터미널이 준비 상태로 복귀
