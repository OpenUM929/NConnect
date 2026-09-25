"""참고 자료 나침반 — 무엇이 있고, 왜 있고, 지금 실제로 존재하는가.

왜 있는가.  2026-09-18: 회차 추천이 원장을 읽지 않고 나왔고(옛 초안 재사용), 받아 둔 Isaac Lab 원문은
scratchpad 에만 있어 아무도 검증할 수 없었다.  "어떤 자료가 있는지"와 "그 자료가 왜 있는지"가
사람 머릿속에만 있으면 같은 일이 반복된다.

무엇을 하는가.  저장소를 훑어 참고 자료 목록을 만들고, 각 자료에 대해
  - 존재 여부 (파일이 실제로 있는가, 비어 있지 않은가)
  - **존재 이유** — 자료가 **스스로 적어 둔** 목적만 쓴다:
      .py  → 모듈 docstring 첫 줄
      .md  → 제목 다음의 첫 문장(보통 "> 생성 …" 또는 요약 줄)
      증거 폴더 → `SOURCES.csv` 의 `why` 칸, 없으면 이 폴더를 인용한 문서
      .csv/.json → 이 파일을 인용한 문서·도구
  - 생성 도구 / 계약 테스트 / 인용하는 문서
를 모은다.  이유를 스스로 적지 않은 자료는 `WHY_MISSING` 으로 표시한다 — 그것이 결함이다.
여기에 이유를 손으로 적어 넣지 않는다(적으면 그 순간 근거가 아니라 주장이 된다).

    python -B tools/go2_reference_compass.py        # 문서·증거 CSV 재생성
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAD = ROOT / "workspace/training/quadruped"
REPORTS = QUAD / "reports"
RUNS = REPORTS / "runs"
EVIDENCE = REPORTS / "evidence"
TOOLS = ROOT / "tools"
OUT_DOC = REPORTS / "GO2_REFERENCE_COMPASS.md"
OUT_DIR = EVIDENCE / "go2_reference_compass_20260918"
OUT_CSV = OUT_DIR / "COMPASS.csv"

# 나침반이 훑는 곳.  (묶음 이름, 경로들, 이 묶음이 답하는 질문)
GROUPS: tuple[tuple[str, str], ...] = (
    ("규칙·현재 상태", "지금 무엇을 하고 있고 무엇이 금지돼 있는가"),
    ("회차 원장", "어떤 회차가 실제로 돌았고 무엇이 측정됐는가"),
    ("외부 기준 원문", "Isaac Lab v2.3.1 이 원래 무엇을 하는가"),
    ("보상 변수 분석", "항의 역할·값·변화량을 무엇으로 아는가"),
    ("증거 CSV", "위 문서의 숫자가 어디서 나왔는가"),
    ("회차 사양", "다음 회차가 무엇을 바꾸고 무엇으로 반증되는가"),
    ("판정·제작 코드", "무엇이 합격/불합격을 결정하고 무엇이 패키지를 만드는가"),
    ("역할 정의", "누가 어떤 권한으로 무엇을 하는가"),
)

# ─────────────────────────────────────────────────────────────────────────────
# 자료의 성격 — 측정 / 예측 / 이득 구간.  섞으면 안 되는 세 가지다.
#   측정   : 학습 로그·평가 기록에서 **집계만** 한 값.  반박되면 기록이 틀린 것이다.
#   예측   : 보상 산술로 **계산한** 값.  관측이 아니다.  방향만 쓰고 크기는 대조 후에만 쓴다.
#   이득구간: 잡음 폭·검출 한계·사전 등록 하한.  "이득"이라 부르려면 이 구간 **밖**이어야 한다.
# 분류는 각 생성기 문서가 밝힌 산출 방식에 따른다.  새 CSV 는 여기 등록돼야 하고,
# 등록되지 않으면 `UNCLASSIFIED` 로 나와 관문이 실패한다.
FORECAST_FILES = {
    "PROBES.csv": "가중치를 바꿨을 때 걷기 margin 이 어디로 가는지 — 보상 산술 계산",
    "PROBE_SITUATIONS.csv": "같은 계산의 네 구간(걷기·계단·흔들림·밀침) 분해. 빈 칸은 0 이 아니라 측정 없음",
    "RUN_MARGIN.csv": "회차별 걷기 margin — 학습 로그 원값에 보상 식을 적용한 계산값",
    "FORECAST_CHECK.csv": "예측 방향과 관측 방향의 사후 대조표",
    "DIAL_MODEL.csv": "반박된 모델(REFUTED_BY_G_A038) — 근거로 쓰지 않는다",
}
LIMIT_FILES = {
    "BASELINE_MARGIN.csv": "시나리오별 재표집 표준편차(delta_resample_sd) — 사전 등록 한도의 출처",
    "CLIMB_GUARD.csv": "계단 오른 로봇 수 하한(묶음별 baseline_sum·max_drop)",
    "BAND_RUNS.csv": "걷기/정지 경계대에 있는 회차 — 이 안의 차이는 seed 운과 구별되지 않는다",
    "TERM_HEADROOM.csv": "항별로 경계대까지 남은 거리(edge_over_value)",
    "EVAL_SEED_SPREAD.csv": "평가 seed 사이 흔들림 폭 — 이 폭 안의 차이는 이득이 아니다",
    "TIER1_REGRESSION.csv": "tier1 비열등 한도 대비 회귀",
}
# 외부 원문 자체에서 뽑은 표 — 우리 측정도 아니고 우리 예측도 아니다.
SOURCE_TABLES = {
    "SOURCES.csv": "보관한 외부 원문의 URL·SHA256 목록 — 원문이 진짜인지 여기서 대조한다",
    "CURRICULUM_FACTS.csv": "Isaac Lab 원문을 파싱해 뽑은 커리큘럼 사실표(행별 계단 높이·학습 길이·평균 레벨 한계)",
}

RULE_DOCS = ("GO2_NOW.md", "GO2_REWARD_EVIDENCE_MASTER.md", "GO2_PROJECT_STATE.md",
             "ARTIFACT_MANAGEMENT.md", "AGENTS.md")
ANALYSIS_DOCS = ("GO2_TUNING_BASE_DATA.md", "GO2_REWARD_MECHANISM_FORECAST.md",
                 "GO2_VARIABLE_INFLUENCE.md", "GO2_SEED_SENSITIVITY.md",
                 "GO2_STAIRS_BEHAVIOR_ANALYSIS_20260916.md", "GO2_G_A038_READOUT.md",
                 "GO2_RUN_SYNTHESIS_20260916.md")
DECIDING_CODE = ("go2_target_gate.py", "go2_fact_rules.py", "go2_climb_count.py",
                 "go2_run_ledger.py", "go2_reward_mechanism.py", "go2_tuning_base_data.py",
                 "go2_curriculum_facts.py", "verify_go2_basic_motion_harvest.py",
                 "verify_go2_g_a030_harvest.py", "build_go2_a033_reward_package.py",
                 "build_go2_training_length_campaign.py")


def tool_texts() -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8", errors="replace") for p in sorted(TOOLS.glob("*.py"))}


TOOL_TEXT = tool_texts()
DOC_TEXT = {p: p.read_text(encoding="utf-8", errors="replace")
            for p in list(ROOT.glob("*.md")) + list(REPORTS.rglob("*.md")) + list((ROOT / ".claude/agents").glob("*.md"))}


def why_py(path: Path) -> str:
    """모듈 docstring 첫 줄.  shebang·인코딩 주석·빈 줄·future import 는 건너뛴다."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'\A(?:\s*(?:#[^\n]*|from __future__[^\n]*)\n)*', "", text)
    match = re.match(r'\s*"""(.+?)(?:\n|""")', text)
    return match.group(1).strip() if match else ""


def why_md(path: Path) -> str:
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        text = line.strip().lstrip("> ").strip()
        if text and not text.startswith("#"):
            return re.sub(r"\s+", " ", text)[:200]
    return ""


def cited_by(needle: str) -> list[str]:
    out = [p.name for p, t in DOC_TEXT.items() if needle in t]
    out += [p.name for p, t in TOOL_TEXT.items() if needle in t and not p.name.startswith("test_")]
    return sorted(set(out))


def tests_for(needle: str) -> list[str]:
    return sorted({p.name for p, t in TOOL_TEXT.items() if p.name.startswith("test_") and needle in t})


def generator_for(needle: str) -> list[str]:
    return sorted({p.name for p, t in TOOL_TEXT.items()
                   if not p.name.startswith("test_") and needle in t})


def kind_of(path: Path, group: str) -> str:
    """자료의 성격.  데이터 표(CSV)는 측정/예측/이득구간 중 하나로 반드시 분류된다."""
    if path.suffix != ".csv":
        return {"외부 기준 원문": "원문", "역할 정의": "규칙", "규칙·현재 상태": "규칙",
                "회차 사양": "사양", "판정·제작 코드": "코드"}.get(group, "문서")
    if path.name in FORECAST_FILES:
        return "예측"
    if path.name in LIMIT_FILES:
        return "이득구간"
    if path.name in SOURCE_TABLES:
        return "원문"
    if path.parent.name.startswith("go2_") or path.parent.name == "runs":
        return "측정"
    return "UNCLASSIFIED"


def row(group: str, path: Path, why: str) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if path.is_dir():
        exists, size = path.is_dir(), sum(1 for _ in path.iterdir())
    elif path in (OUT_CSV, OUT_DOC):
        # 자기 자신의 크기를 적으면 재생성할 때마다 값이 흔들려 관문이 무의미해진다.
        exists, size = path.is_file(), "self"
    else:
        exists, size = path.is_file(), path.stat().st_size if path.is_file() else 0
    needle = path.name
    kind = kind_of(path, group)
    why = FORECAST_FILES.get(path.name) or LIMIT_FILES.get(path.name) or SOURCE_TABLES.get(path.name) or why
    return [group, kind, rel, "YES" if exists else "MISSING", str(size),
            why or "WHY_MISSING",
            ";".join(generator_for(needle))[:120],
            ";".join(tests_for(needle))[:160],
            ";".join(c for c in cited_by(needle) if c != path.name)[:200]]


def rows() -> list[list[str]]:
    out = [["group", "kind", "path", "exists", "size_or_files", "why_as_recorded",
            "generator", "contract_tests", "cited_by"]]

    for name in RULE_DOCS:
        for base in (ROOT, QUAD):
            path = base / name
            if path.is_file():
                out.append(row("규칙·현재 상태", path, why_md(path)))

    for path in sorted(RUNS.glob("*.csv")) + sorted(RUNS.glob("INDEX.md")) + sorted(RUNS.glob("CHRONOLOGY.md")):
        why = why_md(path) if path.suffix == ".md" else ""
        if not why:
            first = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
            why = f"열: {first[0][:120]}" if first else ""
        out.append(row("회차 원장", path, why))

    for directory in sorted(EVIDENCE.iterdir()):
        if not directory.is_dir():
            continue
        sources = directory / "SOURCES.csv"
        if sources.is_file():
            with sources.open(encoding="utf-8", newline="") as handle:
                items = list(csv.DictReader(handle))
            why = f"Isaac Lab v2.3.1 원문 {len(items)}개 + URL·SHA256"
            out.append(row("외부 기준 원문", directory, why))
            for item in items:
                out.append(row("외부 기준 원문", directory / item["file"],
                               item.get("why") or f"원문 {item['url'].rsplit('/', 1)[-1]}"))
            for table in sorted(directory.glob("*.csv")):
                out.append(row("외부 기준 원문", table, ""))
        else:
            citing = [c for c in cited_by(directory.name) if c.endswith(".md")]
            out.append(row("증거 CSV", directory,
                           f"인용 문서: {', '.join(citing)}" if citing else ""))
            # 표 하나하나가 측정인지 예측인지 이득 구간인지 드러나야 한다 — 폴더 단위로는 섞인다.
            for table in sorted(directory.glob("*.csv")):
                header = table.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
                out.append(row("증거 CSV", table, f"열: {header[0][:120]}" if header else ""))

    for name in ANALYSIS_DOCS:
        path = REPORTS / name
        out.append(row("보상 변수 분석", path, why_md(path) if path.is_file() else ""))

    for path in sorted((QUAD / "config/experiments").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        status = re.search(r'"status":\s*"(RECOMMENDED|HOLD_\w+|INFORMATION_RUN)"', text)
        single = re.search(r'"single_change":\s*\{\s*"name":\s*"([^"]+)"[^}]*?"from":\s*([-\d.eE+]+)[^}]*?"to":\s*([-\d.eE+]+)', text)
        why = (f"{single.group(1)} {single.group(2)}->{single.group(3)}" if single else "")
        if status:
            why += f" [{status.group(1)}]"
        out.append(row("회차 사양", path, why.strip()))

    for name in DECIDING_CODE:
        for base in (TOOLS, QUAD):
            path = base / name
            if path.is_file():
                out.append(row("판정·제작 코드", path, why_py(path)))
                break

    for path in sorted((ROOT / ".claude/agents").glob("*.md")) + sorted((ROOT / ".codex/agents").glob("go2-*.md")):
        out.append(row("역할 정의", path, why_md(path)))
    return out


def document(table: list[list[str]]) -> str:
    body = table[1:]
    lines = [
        "# Go2 참고 자료 나침반",
        "",
        "> **생성 문서 — 손으로 고치지 않는다.** `python -B tools/go2_reference_compass.py` 가 만든다.",
        f"> 증거 `{OUT_CSV.relative_to(QUAD).as_posix()}`, 관문 `tools/test_go2_reference_compass_contract.py`.",
        "> **존재 이유는 자료가 스스로 적어 둔 것만 옮긴다**(모듈 docstring 첫 줄 · 문서 머리말 · `SOURCES.csv` 의 `why`).",
        "> 이유를 적어 두지 않은 자료는 `WHY_MISSING` 이다 — 채워야 할 결함이지 나침반에 손으로 쓸 것이 아니다.",
        "",
        "## 0. 섞으면 안 되는 세 가지",
        "",
        "| 성격 | 무엇인가 | 어떻게 쓰는가 |",
        "|---|---|---|",
        "| **측정** | 학습 로그·평가 기록에서 집계만 한 값 | 사실로 인용한다. 계측 세대가 다르면 비교하지 않는다 |",
        "| **예측** | 보상 산술로 계산한 값(관측이 아니다) | 방향만 쓴다. 크기는 사후 대조 뒤에만. 빈 칸은 0 이 아니라 측정 없음 |",
        "| **이득구간** | 잡음 폭·검출 한계·사전 등록 하한 | **이 구간 밖이어야 '이득'이다.** 안쪽 차이는 seed 운과 구별되지 않는다 |",
        "",
    ]
    for kind in ("측정", "예측", "이득구간"):
        items = [r for r in body if r[1] == kind]
        lines += [f"### {kind} 표 {len(items)}개", "",
                  "| 자료 | 무엇인가 | 생성 | 관문 |", "|---|---|---|---|"]
        for r in items:
            lines.append(f"| `{r[2]}` | {r[5].replace('|', '/')} | `{r[6] or '-'}` | `{r[7] or '-'}` |")
        lines.append("")

    lines += ["## 1. 묶음별 현황", "",
              "| 묶음 | 이 묶음이 답하는 질문 | 자료 | 없음 | 이유 미기재 |", "|---|---|---:|---:|---:|"]
    for group, question in GROUPS:
        items = [r for r in body if r[0] == group]
        missing = sum(1 for r in items if r[3] != "YES")
        nowhy = sum(1 for r in items if r[5] == "WHY_MISSING")
        lines.append(f"| {group} | {question} | {len(items)} | {missing} | {nowhy} |")
    lines += ["", f"합계 {len(body)}개 · 없음 {sum(1 for r in body if r[3] != 'YES')}개 · "
                  f"이유 미기재 {sum(1 for r in body if r[5] == 'WHY_MISSING')}개 · "
                  f"성격 미분류 {sum(1 for r in body if r[1] == 'UNCLASSIFIED')}개", ""]

    for group, question in GROUPS:
        items = [r for r in body if r[0] == group]
        if not items:
            continue
        lines += [f"## {group}", "", f"*{question}*", "",
                  "| 자료 | 성격 | 있음 | 왜 있는가(자료가 적어 둔 그대로) | 생성 | 관문 |", "|---|---|---|---|---|---|"]
        for r in items:
            lines.append(f"| `{r[2]}` | {r[1]} | {r[3]} | {r[5].replace('|', '/')} | `{r[6] or '-'}` | `{r[7] or '-'}` |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    table = rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(table)
    OUT_DOC.write_text(document(table), encoding="utf-8")
    print(OUT_CSV.relative_to(ROOT).as_posix())
    print(OUT_DOC.relative_to(ROOT).as_posix())
    missing = [r[2] for r in table[1:] if r[3] != "YES"]
    nowhy = [r[2] for r in table[1:] if r[5] == "WHY_MISSING"]
    unclassified = [r[2] for r in table[1:] if r[1] == "UNCLASSIFIED"]
    print(f"없음 {len(missing)}개, 이유 미기재 {len(nowhy)}개, 성격 미분류 {len(unclassified)}개")
    for item in missing + nowhy + unclassified:
        print("   ", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
