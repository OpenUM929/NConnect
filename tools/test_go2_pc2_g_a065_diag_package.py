"""G-A065 PC2 진단 재생 패키지 계약 테스트 — tools/build_go2_pc2_g_a065_diag_package.py.

GPU 없이 가짜 isaaclab.sh 로 run_all.sh 전체(정책 5개 × 12회 → 결과 ZIP·SHA, 두 번째 실행은 SKIP_DONE)를 돌린다.

python -B -m unittest tools.test_go2_pc2_g_a065_diag_package
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_go2_pc2_g_a065_diag_package as b  # noqa: E402

BASH = shutil.which("bash")
FAKE = r"""#!/usr/bin/env bash
# 가짜 isaaclab.sh: '-p play.py ...' 는 평가 출력을 쓰고, '-p <other>.py args' 는 실제 python 으로 실행한다.
[[ "$1" == -p ]] || exit 9
script=$2; shift 2
if [[ "$(basename "$script")" != play.py ]]; then exec python "$script" "$@"; fi
[[ -n "${NCRC_EVAL_OUT:-}" ]] || exit 8
mkdir -p "$NCRC_EVAL_OUT"
printf 'step,env\n0,0\n' >"$NCRC_EVAL_OUT/steps.csv"
echo '{"completed": true}' >"$NCRC_EVAL_OUT/summary.json"
echo 'EVAL_RC=0' >"$NCRC_EVAL_OUT/STATUS.txt"
if [[ -s go2_eval_diag_v2.py ]]; then
  printf 'x' | gzip >"$NCRC_EVAL_OUT/diag.csv.gz"; echo 'DIAG_OK=1' >"$NCRC_EVAL_OUT/DIAG_STATUS.txt"
fi
echo "$PWD|$*" >>"$FAKE_LOG"
"""


class G065(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.info = b.build()
        cls.f = cls.info["files"]

    def test_policy_files_match_harvest_identity(self):
        for key, keep_rel, _ in b.POLICIES:
            ident = json.loads((ROOT / keep_rel / "evaluation/candidate/identity.json").read_text(encoding="utf-8"))
            model, _ = self.f[f"runs/{key}/policy/model_best.pt"]
            self.assertEqual(hashlib.sha256(model).hexdigest(), ident["model_sha256"], key)
            cfg = self.f[f"runs/{key}/run_config.env"][0].decode()
            self.assertIn(f"MODEL_SHA={ident['model_sha256']}\n", cfg)
            self.assertIn(f"EXPECTED_EVALUATOR_SHA={b.EVALUATOR_SHA}\n", cfg)
        self.assertEqual([k for k, *_ in b.POLICIES], ["p0", "s04", "s11", "s13", "s07"])

    def test_ruler_bytes(self):
        with zipfile.ZipFile(b.G_A056_ZIP) as z:
            diag = z.read("go2_g_a056/diag/go2_eval_diag_v2.py")
            wrap = z.read("go2_g_a056/diag/go2_eval_telemetry.py")
        for key, *_ in b.POLICIES:
            self.assertEqual(self.f[f"runs/{key}/diag/go2_eval_diag_v2.py"][0], diag)
            self.assertEqual(self.f[f"runs/{key}/diag/go2_eval_telemetry.py"][0], wrap)
            for root in ("plain/go2_eval_telemetry.py", "diag/go2_eval_telemetry_v6.py"):
                self.assertEqual(hashlib.sha256(self.f[f"runs/{key}/{root}"][0]).hexdigest(), b.EVALUATOR_SHA)
            self.assertNotIn(f"runs/{key}/plain/train.py", self.f)

    def test_lf_and_bash_syntax(self):
        for name in ["run_all.sh"] + [f"runs/{k}/{b.RUNNER}" for k, *_ in b.POLICIES]:
            data = self.f[name][0]
            self.assertNotIn(b"\r", data, name)
            if BASH:
                with tempfile.NamedTemporaryFile("wb", suffix=".sh", delete=False) as t:
                    t.write(data)
                try:
                    self.assertEqual(subprocess.run([BASH, "-n", t.name]).returncode, 0, name)
                finally:
                    os.unlink(t.name)

    @unittest.skipUnless(BASH, "bash required")
    def test_full_batch_with_fake_isaaclab(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            zipfile.ZipFile(io.BytesIO(self.data)).extractall(tmp / "pkg")
            fake = tmp / "isaaclab.sh"
            fake.write_text(FAKE, encoding="utf-8", newline="\n")
            keep = tmp / "keep"
            env = {**os.environ, "ISAACLAB_SH": str(fake), "GO2_DIAG_KEEP_BASE": str(keep),
                   "FAKE_LOG": str(tmp / "calls.log")}
            run_all = tmp / "pkg" / b.PREFIX / "run_all.sh"
            r = subprocess.run([BASH, str(run_all)], env=env, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-3000:])
            calls = (tmp / "calls.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(calls), 5 * 12)
            for key, *_ in b.POLICIES:
                k = keep / f"go2_{b.SLUG}_pc2_{key}"
                self.assertIn("COLLECTION_STATUS=COMPLETE_12_OF_12", (k / "RESULT_STATUS.txt").read_text())
                rep = (k / "meta/REPRO_STATUS.txt").read_text()
                self.assertEqual(rep.count("=IDENTICAL"), 6, rep)
                z = keep / f"GO2_{b.UP}_PC2_{key.upper()}_RESULT.zip"
                self.assertTrue(z.is_file() and (keep / (z.name + ".sha256")).is_file())
                for s in (202, 101, 303):
                    for c in ("stairs_15_down", "rough_lateral"):
                        self.assertTrue((k / f"diag/cases/seed_{s}/{c}/diag.csv.gz").is_file())
            log = (keep / b.STATUS_DIR / "BATCH_RUN.log").read_text(encoding="utf-8")
            self.assertIn("[BATCH END]", log)
            r2 = subprocess.run([BASH, str(run_all)], env=env, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r2.returncode, 0)
            self.assertEqual(r2.stdout.count("SKIP_DONE"), 5)
            self.assertEqual(len((tmp / "calls.log").read_text(encoding="utf-8").splitlines()), 60)


if __name__ == "__main__":
    unittest.main()
