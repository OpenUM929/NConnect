#!/usr/bin/env python3
"""강화학습 결과(exported/model_best.pt + env.yaml + report.html)를 zip 으로 묶어 제출 서버에 업로드.

report.html = 학습 종료 시 finalize() 가 자동 생성하는 분석 리포트 (_finalize.py 내장).
exported/ 에 있으면 zip 에 함께 포함, 없으면 생략.

사용 (GPU 학습 서버에서, 학습+finalize 가 끝나 exported/ 가 생긴 뒤):
  python3 training/upload_submission.py
  #   (training/ 폴더 안에서라면: python3 upload_submission.py)
  # 제출 서버 지정 — env(SUBMIT_HOST / SUBMIT_TOKEN) 또는 arg:
  python3 training/upload_submission.py --host <URL> --token <TOKEN>

옵션:
  --exported <dir>   model_best.pt + env.yaml 폴더 (생략 시 training/*/exported 자동 탐지)
  --comment "..."    회고/전략 코멘트 (zip 안에 comment.txt 로 포함 — 채점 의도/코멘트용)
  --dry-run          전송 없이 zip 만 만들어 저장 (점검용)

ℹ️ 제출 서버 설정은 코드에 두지 않는다 (training/ 은 참가자 배포 영역).
   운영 서버에만 env(SUBMIT_HOST / SUBMIT_TOKEN) 또는
   <repo>/submit_config.txt (gitignored, "host=..." / "token=..." 두 줄) 를 배치.
   stdlib(urllib)만 사용 — 추가 설치 불필요.
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
import uuid
import zipfile
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent   # finals_game/
API_PATH = "/api/front/v1/studyFile"
# ⚠️ 제출 서버 host/token 은 코드에 두지 않는다 — training/ 은 참가자에게 배포되는
#    영역이라 자격증명이 노출되면 임의 제출/조작이 가능해진다.
#    운영 서버에만 env(SUBMIT_HOST/SUBMIT_TOKEN) 또는 submit_config.txt 를 둔다.
DEFAULT_HOST = ""
DEFAULT_TOKEN = ""


def _submit_config() -> tuple[str, str]:
    """제출 서버 host/token — env > <repo>/submit_config.txt (gitignored).
    형식: "host=https://..." / "token=..." 두 줄 (# 주석 허용)."""
    host = (os.environ.get("SUBMIT_HOST") or DEFAULT_HOST).strip()
    token = (os.environ.get("SUBMIT_TOKEN") or DEFAULT_TOKEN).strip()
    if not (host and token):
        try:
            cfg = ROOT / "submit_config.txt"
            if cfg.exists():
                for ln in cfg.read_text(encoding="utf-8").splitlines():
                    ln = ln.strip()
                    if not ln or ln.startswith("#") or "=" not in ln:
                        continue
                    k, v = (x.strip() for x in ln.split("=", 1))
                    if k.lower() == "host" and not host:
                        host = v
                    elif k.lower() == "token" and not token:
                        token = v
        except Exception:
            pass
    return host.rstrip("/"), token


def _find_exported() -> Path | None:
    """training/humanoid|quadruped/exported 중 model_best.pt 있는 폴더 (최신)."""
    cands = []
    for robot in ("humanoid", "quadruped"):
        d = ROOT / "training" / robot / "exported"
        pt = d / "model_best.pt"
        if pt.exists():
            cands.append((pt.stat().st_mtime, d))
    if not cands:
        return None
    cands.sort()
    return cands[-1][1]   # mtime 최신


def _build_zip(exported: Path, comment: str | None) -> bytes:
    pt = exported / "model_best.pt"
    yaml = exported / "env.yaml"
    missing = [f.name for f in (pt, yaml) if not f.exists()]
    if missing:
        raise FileNotFoundError(
            f"{exported} 에 {missing} 없음 — 학습 후 finalize 가 끝났는지 확인하세요.")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(pt, "model_best.pt")
        z.write(yaml, "env.yaml")
        report = exported / "report.html"          # finalize() 가 만든 분석 리포트
        if report.exists():
            z.write(report, "report.html")
        if comment:
            z.writestr("comment.txt", comment)
    return buf.getvalue()


def _multipart(field: str, filename: str, data: bytes,
               content_type: str = "application/zip") -> tuple[bytes, str]:
    """단일 파일 multipart/form-data 본문 + Content-Type 헤더값."""
    boundary = "----finalsgame" + uuid.uuid4().hex
    pre = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    post = f"\r\n--{boundary}--\r\n".encode("utf-8")
    return pre + data + post, f"multipart/form-data; boundary={boundary}"


def main() -> None:
    p = argparse.ArgumentParser(description="학습 결과(zip) 제출 서버 업로드")
    p.add_argument("--host", default=None,
                   help="제출 서버 base URL (생략 시 env SUBMIT_HOST / submit_config.txt)")
    p.add_argument("--token", default=None,
                   help="인증 토큰 (생략 시 env SUBMIT_TOKEN / submit_config.txt)")
    p.add_argument("--exported", default=None,
                   help="model_best.pt+env.yaml 폴더 (생략 시 training/*/exported 자동 탐지)")
    p.add_argument("--comment", default="", help="회고/전략 코멘트 (zip 에 comment.txt 로 포함)")
    p.add_argument("--dry-run", action="store_true", help="전송 없이 zip 만 저장")
    a = p.parse_args()

    # 서버 설정 — arg > env > submit_config.txt. 코드에 기본 자격증명 없음.
    cfg_host, cfg_token = _submit_config()
    a.host = (a.host or cfg_host or "").rstrip("/")
    a.token = a.token or cfg_token
    if not a.dry_run and not (a.host and a.token):
        print("❌ 제출 서버 설정이 없습니다.\n"
              "   env SUBMIT_HOST / SUBMIT_TOKEN 을 설정하거나,\n"
              "   <repo>/submit_config.txt 에 host=... / token=... 두 줄을 두거나,\n"
              "   --host / --token 인자로 지정하세요. (설정은 운영진에게 문의)")
        sys.exit(2)

    exported = Path(a.exported) if a.exported else _find_exported()
    if not exported or not exported.exists():
        print("❌ exported 폴더를 못 찾음. --exported <경로> 로 지정하세요 "
              "(model_best.pt + env.yaml 있는 곳).")
        sys.exit(2)
    print(f"[upload] exported: {exported}")

    try:
        zip_bytes = _build_zip(exported, a.comment or None)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(2)

    fname = f"submission_{int(time.time())}.zip"   # 서버가 팀별(토큰) 저장 — 이름은 참고용
    parts = ["model_best.pt", "env.yaml"]
    if (exported / "report.html").exists():
        parts.append("report.html")
    if a.comment:
        parts.append("comment.txt")
    print(f"[upload] zip 생성: {fname} ({len(zip_bytes) / 1024:.0f} KB, {' + '.join(parts)})")

    if a.dry_run:
        out = exported / fname
        out.write_bytes(zip_bytes)
        print(f"[upload] --dry-run: 전송 안 함. zip 저장 → {out}")
        return

    if not a.host or not a.token:
        print("❌ --host 와 --token (또는 env SUBMIT_HOST / SUBMIT_TOKEN) 가 필요합니다.")
        sys.exit(2)

    url = a.host.rstrip("/") + API_PATH
    body, ctype = _multipart("upfile", fname, zip_bytes)
    req = urlrequest.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {a.token}",
        "Content-Type": ctype,
        "Content-Length": str(len(body)),
    })
    tok_tail = a.token[-4:] if len(a.token) >= 4 else "?"
    print(f"[upload] POST {url}  (Bearer ***{tok_tail})")
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:
            print(f"[upload] ✅ {resp.status} {getattr(resp, 'reason', '')}")
            print(resp.read().decode("utf-8", "replace")[:800])
    except HTTPError as e:
        print(f"[upload] ❌ HTTP {e.code} — {e.read().decode('utf-8', 'replace')[:800]}")
        sys.exit(1)
    except URLError as e:
        print(f"[upload] ❌ 연결 실패: {e.reason}  (--host 와 네트워크 확인)")
        sys.exit(1)


if __name__ == "__main__":
    main()
