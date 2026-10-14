# H1 본선 예상 환경 — 180초 실제 Gemini 연습 결과

완주 결과는 로컬 내부 연습 점수다. 공식 맵·운영진 엔진·최고점 전략 검증이 아니다.

- 영상: [3분 원본](../../../server_returns/H-FINALS-PRACTICE-20261010/llm180_v6/practice.mp4)
- 지도와 실제 궤적: [SVG](../../../server_returns/H-FINALS-PRACTICE-20261010/llm180_v6/map_trajectories.svg)
- 프롬프트와 실제 Gemini 요청/응답: [JSON](../../../server_returns/H-FINALS-PRACTICE-20261010/llm180_v6/llm_decisions.json)
- 검증: [verification.json](../../../server_returns/H-FINALS-PRACTICE-20261010/llm180_v6/verification.json)
- 규정 원문: https://robotics.connect.or.kr/rules/finals_regulations.html

| 팀 | 선택 방식 | 점수 | 큐브 | 낙상 | 차량 충돌 |
|---|---|---:|---:|---:|---:|
| 우리 H1(blue) | 실제 Gemini + 아래 전략 | 400 | 4 | 0 | 0 |
| 비교 H1(red) | 가장 가까운 도달 가능한 목표 | 400 | 4 | 0 | 0 |

내부 동점 기준에서는 최초 획득 시간이 blue8.52초/red17.68초여서 blue 우선이다. 양쪽 시작 위치가 다르고 한 맵·한 seed뿐이므로 프롬프트 우수성이나 공식 승리를 뜻하지 않는다. Run06 iter9900/총10000 정책을 사용했으며 공식 최고점 제출과 동일한 정책인지 미확정이다.

## 차량을 잘 피했는가

우리 H1은 차량 구역 노출0초, 차량 중심과의 최소거리2.5089m, 대체 충돌판정0회였다. 차량 구역을 우회했다는 근거이며 가까이 오는 차를 감지해 피하는 능력을 측정하지 않았다. red 노출3.36초·최소거리2.1990m·충돌0회. 차량은 이동하는 빨간 상자와 가정한 footprint/knockback으로 구현했으며 공식 차량 접촉 물리와 동일하지 않다.

## 실제 사용 전략 — 177자

> 180초 총점을 최대화하라. 이동거리와 차량 구역 노출을 고려해 시간당 획득점수가 높은 도달 가능한 큐브를 선택하라. 가까운 평지와 통행 가능한 미로를 우선하되 우회가 긴 목표는 미뤄라. 등반 능력이 확인되지 않은 박스언덕·계단·경사 구역은 제외하라. 이미 획득된 큐브는 선택하지 말고, 남은 목표가 없으면 대기하라.

연습용 호출에는 위 전략 외에 JSON 형식 지시, 남은 시간, 도달 가능한 ID/거리/점수/차량 위험을 붙였다. 실제 전체 입력과 응답은 연결한 JSON에 보존했다. 운영진 system prompt는 미공개다. 각 선택 전2.5 시뮬레이션 초를 대기했고 네트워크 호출 중 물리는 정지했다.

## 검증과 한계

ARTIFACT_VERIFIED: 18000행, 8획득event, 점수 재계산, checkpoint SHA, 영상180초·960×720·10fps·H264 전체decode, SHA manifest 확인. 정책 actor tensor8/8 일치 재검증. 단위검사15/15 및 Python 문법 검사 성공. VIDEO_UNKNOWN: 8/28/75/149/167/179초 표본에서는 직립과 위치 변화를 관찰했으나 전체 영상을 행동 판독하지 않았다. OFFICIAL_RESULT 없음.

등반 미검증 구역은 목표 선택에서 제외했다. 이 결과는 계단·언덕·경사 성능, 예선 H1~H7, 최적 전략, 본선 점수를 보장하지 않는다. 초기 강좌asset 실패는 원 학습asset과의 adapter 불일치로 제외했고, 완주 결과에는 원 task의 학습용 asset URI를 사용했다. 학습·배포 코드는 수정하지 않았다.
