"""Apply the user-requested report-first documentation contract (no robot code)."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- GO2:REPORT-FIRST:START -->"
END = "<!-- GO2:REPORT-FIRST:END -->"
PLAN = "workspace/training/quadruped/upload/plan/GO2_A027_NEXT_TUNING_PREP_20260913.md"
RULE = """## 학습 report 필독·원인 우선 연구 계약 (2026-09-13 사용자 결정)

H1·Go2 튜닝 기획·평가·보고를 수행하는 메인과 모든 서브에이전트에 적용한다.
보고서 존재 확인이나 다른 배우의 요약만으로 읽었다고 하지 않는다.

1. **튜닝 후보 선정 전에 해당 정책과 대조군의 학습 `report.html` 본문을 직접 읽는다.**
   학습 run·checkpoint iter/model SHA·env reward snapshot·학습 로그와 대응을 확인한다.
   파일명/수정시각/같은 폴더만으로 대응을 확정하지 않는다. export 해시 차이는 tensor 의미 차이로 단정하지 않는다.
2. `REPORT_READ_STATUS=READ_MATCHED|READ_UNMATCHED|MISSING|NOT_APPLICABLE`를 출력한다.
   읽은 경로·보고서의 학습시각/iter/보상값·대조한 로그와 정책 식별자·일치/불일치·미확인 근거를 남긴다.
   `READ_MATCHED`는 대응 확인이지 성능 판정이 아니다.
3. 학습 HTML, 내부 `SELF_EVAL_REPORT`, 기술 개선 제출문은 서로 다른 자료다.
   평가 전용 run은 새 학습 HTML이 없을 수 있으나, 튜닝에 쓰는 정책의 원 학습 report 조회를 생략하지 않는다.
   `NOT_APPLICABLE`은 정책을 생성하지 않은 도구 smoke 등 실제 비해당 사유를 적을 때만 사용한다.
4. report 누락/오래된 파일/정책 대응 불명은 `REPORT_REQUIRED_NOT_ACQUIRED` 또는
   `REPORT_POLICY_UNMATCHED`로 기록한다. 먼저 로컬 원 학습 bundle·보존 snapshot·로그를 검색한다.
   그래도 없으면 회수/복구 방법을 기록한다. 추정 HTML을 원본인 것처럼 만들지 않는다.
   이 상태는 **새 reward 후보 확정·새 학습 착수**를 막지만 기존 증거 읽기·누락 자료 복구·진단 설계는 허용한다.
5. 연구 순서는 **학습 report·env·로그 대응 → 내부 시나리오 평가 → 영상/telemetry로 실패 유형 구분
   → 경쟁 가설 비교 → 근거 있는 단일변수 후보 → 대조 실험·독립 seed**다.
   HTML의 안정/공격 설명과 일반 경고는 가설 단서일 뿐 인과효과·최적 가중치 근거가 아니다.
6. 학습낙상률/terrain level/mean reward를 시나리오 survival/tracking 또는 공식 점수로 바꾸지 않는다.
   보고서 수치의 집계 구간과 지표 출처를 확인하고, 충돌은 원 로그와 evaluator 조건으로 해소한다.
7. 새 학습 회수에는 같은 run의 `report.html`과 로그·env·checkpoint 대응 자료를 결과 bundle 및 SHA 목록에 포함한다.
   누락하면 해당 공백을 기록하며 다운로드 완결 또는 튜닝 근거 완결로 보고하지 않는다.
8. 최신 지침은 역할 문서의 과거 다음 실행·고정 현재단계보다 우선한다. H1/Go2 캠페인은 분리한다.
   서브에이전트는 권한 범위 내 직접 읽기만 수행하고 공백을 상위에 보고한다. 이 계약은 편집/서버 권한을 추가하지 않는다.
9. **report 필독은 영상·움직임 로그·원 학습 로그 생략 허가가 아니다.** 자료별로 직접 답할 수 있는
   질문을 구분한다. 기존 유효 자료는 재사용하고 새로운 의사결정을 가르는 결측만 측정한다.
   중복 요약 문서는 줄일 수 있지만 원자료·정책 identity·필수 영상 회수는 생략하지 않는다.
   Go2 대체 가능성 표: `workspace/training/quadruped/upload/plan/GO2_EVIDENCE_NECESSITY_REVIEW_20260913.md`.
"""

UPDATE = """## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
"""

ROLE_DUTIES = {
    "go2-campaign-manager": "두 정책의 REPORT_READ_STATUS와 근거 경로를 확인하고 READ_MATCHED 이전 새 튜닝 승인을 보류한다.",
    "go2-test-planner": "보고서 본문과 원 로그를 직접 대조하고 수치·경고·경쟁 가설·반증조건을 연결한 뒤 단일변수를 선정한다.",
    "go2-evaluation-auditor": "보고서 run/정책 대응과 지표 집계 구간을 독립 확인한다. 학습낙상률을 G5 생존으로 바꾸거나 HTML 없이 읽음으로 보고하면 지적한다.",
    "go2-report-writer": "보고서 본문을 직접 읽고 배포 시작값→최종값·실측·한계를 구분한다. 다른 정책의 HTML을 제출 후보 근거로 인용하지 않는다.",
}


def append_block(path: Path, content: str) -> None:
    old = path.read_text(encoding="utf-8")
    block = f"{START}\n{content.rstrip()}\n{END}"
    if START in old:
        left, rest = old.split(START, 1)
        _, right = rest.split(END, 1)
        new = left + block + right
    else:
        new = old.rstrip() + "\n\n" + block + "\n"
    path.write_text(new, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roles-only", action="store_true")
    args = parser.parse_args()
    if args.roles_only:
        for role, duty in ROLE_DUTIES.items():
            append_block(ROOT / ".codex" / "agents" / f"{role}.md",
                         "## 학습 report 필독 (2026-09-13)\n"
                         "상위 AGENTS.md의 「학습 report 필독·원인 우선 연구 계약」을 먼저 읽고 적용한다.\n"
                         "해당 정책과 대조군의 report.html 본문을 직접 읽고 REPORT_READ_STATUS 및 경로·run 대응 근거를 출력한다.\n"
                         + duty + "\n누락/불일치 시 후보 확정 금지; 근거 조회와 진단 준비는 허용.\n"
                         "연구 순서: report·로그 대응 → 평가 → 원인 진단 → 경쟁 가설 → 단일변수.\n"
                         "G-D-REPORT-FIRST-20260913: -0.06은 DEFERRED_HYPOTHESIS이며 다음 실행값이 아니다.\n")
        return
    append_block(ROOT / "AGENTS.md", RULE)
    append_block(ROOT / "workspace/training/quadruped/AGENTS.md", RULE + "\n" + UPDATE)
    for filename in ("GO2_PROJECT_STATE.md", "GO2_CAMPAIGN_SCHEDULE.md",
                     "GO2_REWARD_EVIDENCE_MASTER.md", "ARTIFACT_MANAGEMENT.md", PLAN,
                     "workspace/training/quadruped/upload/plan/PLANNER_BRIEF.md",
                     "workspace/training/quadruped/upload/plan/GO2_DEFAULT_BASELINE_TEST_PRD.md"):
        append_block(ROOT / filename, UPDATE)
    import json
    spec = (ROOT / PLAN).with_suffix(".json")
    data = json.loads(spec.read_text(encoding="utf-8"))
    data.update(research_direction="report_log_identity_then_diagnosis_then_candidate",
                decision_id="G-D-REPORT-FIRST-20260913",
                candidate_status="DEFERRED_HYPOTHESIS", cases_status="PROPOSED_NOT_FROZEN",
                report_gate={"a017": "MISSING", "pilot": "READ_UNMATCHED"})
    spec.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
