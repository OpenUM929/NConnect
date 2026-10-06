<!-- PC2_HANDOFF
WORK_ID: G-A067
STATUS: READY
START_AFTER: NONE
START_MARKER: NONE
PACKAGE: workspace/training/quadruped/upload/G-A067/current/GO2_G_A067_PC2_BEHAVIOR_ANALYSIS_v1.zip
PACKAGE_SHA256: 9feae0fb4b3e576e402ac9295a3458e1759e429081d16cb1f43652f53968a66f
-->
# G-A067 인계 — PC2 분석 작업: G-A066 진단 재생 기록의 행동 판독 (학습 없음·GPU 없음, PC2 Claude 세션용, 2026-10-06)

PC2의 Claude는 이 문서를 처음부터 끝까지 읽고 §1 → §5 순서로 진행한다. 루트 `AGENTS.md` 「PC2 작업 인계」의 **"분석 작업도 PC2에 맡길 수 있다"** 절이 이 작업의 규칙이다.

## 0. 한눈에
- **왜 PC2인가:** 작성 PC에서 이 판독을 돌리다가 메모리 부족으로 중단됐다(2026-10-06). 사용자 지시: 메모리 문제가 생기면 PC2에 분석을 맡긴다.
- **무엇을 하나:** 학습·재생을 하지 않는다. 저장소에 이미 있는 G-A066 결과(`workspace/_keep/go2_g_a066_pc2_{p0,s04,s07,s11,s13}/diag/cases/…`의 steps.csv·diag.csv.gz)를 읽어 계단·험지 행동을 분류한다. 표준 라이브러리 Python 하나만 쓴다.
- **GPU를 쓰지 않는다.** G-A064 학습이 돌고 있어도 시작해도 된다. `nice -n 10`으로 돈다. 학습을 멈추거나 느리게 만들면 안 된다.
- **시간 [추정]:** 수십 분. PC2 실측은 없다.
- **설계·합의:** `workspace/training/quadruped/upload/plan/GO2_STAIRS_ROUGH_SITUATION_DEBATE_20261006.md` §5·§7-5·§10, `GO2_STAIRS_ROUGH_INVESTIGATION_DISCUSSION_20261006.md` §3-6·§3-7. 정의는 스크립트 맨 위 설명에 고정돼 있다.

## 1. 준비 확인
1. `git pull` 뒤 패키지 SHA를 확인한다: `cd workspace/training/quadruped/upload/G-A067/current && sha256sum -c GO2_G_A067_PC2_BEHAVIOR_ANALYSIS_v1.zip.sha256`
2. 원장에 `G-A067<TAB>STARTED<TAB>시각`을 적고 커밋·푸시한다.
3. ZIP을 `/workspace/`에 풀어 둔다: `unzip -oq workspace/training/quadruped/upload/G-A067/current/GO2_G_A067_PC2_BEHAVIOR_ANALYSIS_v1.zip -d /workspace`

## 2. 실행 (Git Bash, 저장소 루트에서)
```bash
bash /workspace/go2_g_a067_pc2/run.sh "$(pwd)"
```
- 입력이 하나라도 없으면 `[FAIL] missing input …`(rc 2)로 멈춘다.
- 끝나면 `[DONE] G-A067 workspace/_keep/go2_g_a067_analysis`가 찍힌다.

## 3. 실패 처리
- rc 2(입력 없음): `git pull`로 G-A066 결과가 받아졌는지 확인한다. 받아졌는데도 없으면 FAILED로 적고 보고한다.
- 파이썬 오류: `workspace/_keep/go2_g_a067_analysis/RUN.log`를 그대로 회수하고 `FAILED<TAB>rc`로 적는다. 스크립트를 고치지 않는다.

## 4. 회수
- `workspace/_keep/go2_g_a067_analysis/`(SUMMARY.json, PER_ENV.csv, STATUS.txt, RUN.log)를 커밋·푸시한다. 100MB를 넘지 않을 것으로 예상한다. 넘으면 parts 규칙을 따른다.
- 커밋 메시지 예: `chore: publish G-A067 PC2 behaviour analysis`
- 원장에 `G-A067<TAB>DONE<TAB>시각`을 추가한다.

## 5. 보고 (판독은 하지 않는다)
- STATUS.txt 내용과 실행 시간만 적는다. 계단·험지 해석, 예측 판정, 다음 값 선택은 작성 PC가 한다.
