"""CV content and page-limit behavior, using only synthetic profile facts."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_and_validate
import render_cv
from parse_profile import load_profile


class ContentPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.profile_path = self.root / "profile"
        shutil.copytree(ROOT / "tests/fixtures/profile", self.profile_path)
        path = self.profile_path / "projects.md"
        path.write_text(path.read_text(encoding="utf-8") + """

## PRJ-API — Synthetic API

- **Role:** Developer
- **Start:** 2025-10
- **End:** 2025-12
- **Tech:** Python

**Evidence**

- `PRJ-API-01` — Built a synthetic test API.
""", encoding="utf-8")
        self.profile = load_profile(self.profile_path)

    def plan(self, ids):
        return {"sections": [{"type": "projects", "entries": [
            {"source": source} for source in ids
        ]}]}

    def test_two_distinct_projects_render_through_cli(self):
        plan = self.root / "plan.json"
        plan.write_text(json.dumps(self.plan(["PRJ-WIDGET", "PRJ-API"])), encoding="utf-8")
        args = ["render_cv.py", "--profile", str(self.profile_path), "--plan", str(plan),
                "--template-root", str(ROOT / "templates"), "--out", str(self.root / "job")]
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(render_cv.main(), 0)
        doc = (self.root / "job/raw/cv.tex").read_text(encoding="utf-8")
        self.assertIn("Widget\\_Tool", doc)
        self.assertIn("Synthetic API", doc)

    def test_zero_or_one_project_is_rejected(self):
        for ids in ([], ["PRJ-WIDGET"]):
            with self.subTest(ids=ids), self.assertRaisesRegex(render_cv.PlanError, "at least 2"):
                render_cv.check_project_selection(self.profile, self.plan(ids))

    def test_duplicate_across_sections_does_not_meet_minimum(self):
        plan = self.plan(["PRJ-WIDGET"])
        plan["sections"] += self.plan(["PRJ-WIDGET"])["sections"]
        with self.assertRaisesRegex(render_cv.PlanError, "duplicate project"):
            render_cv.check_project_selection(self.profile, plan)

    def test_unknown_or_non_project_evidence_cannot_fill_second_slot(self):
        for source in ("PRJ-MISSING", "EXP-ACME"):
            with self.subTest(source=source), self.assertRaises(render_cv.PlanError):
                render_cv.check_project_selection(self.profile, self.plan(["PRJ-WIDGET", source]))

    def test_profile_with_one_project_reports_missing_factual_data(self):
        profile = load_profile(ROOT / "tests/fixtures/profile")
        with self.assertRaisesRegex(render_cv.PlanError, "needs another factual project"):
            render_cv.check_project_selection(profile, self.plan(["PRJ-WIDGET"]))

    def test_cli_does_not_emit_cv_for_one_project(self):
        plan = self.root / "plan.json"
        plan.write_text(json.dumps(self.plan(["PRJ-WIDGET"])), encoding="utf-8")
        args = ["render_cv.py", "--profile", str(self.profile_path), "--plan", str(plan),
                "--template-root", str(ROOT / "templates"), "--out", str(self.root / "job")]
        with patch.object(sys, "argv", args), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(render_cv.main(), 1)
        self.assertFalse((self.root / "job/raw/cv.tex").exists())

    def test_build_cli_accepts_multiple_pages_unless_limit_is_explicit(self):
        out = self.root / "job"
        (out / "raw").mkdir(parents=True)
        (out / "raw/cv.tex").write_text("Synthetic CV", encoding="utf-8")
        text = " ".join(self.profile["personal"][f] for f in ("full_name", "email", "phone"))
        text += " Synthetic supported details." * 20 + "\fSecond page with two projects.\f"

        def compile_fixture(*args):
            (out / "cv.pdf").write_bytes(b"%PDF synthetic fixture")
            return ""

        args = ["build_and_validate.py", "--dir", str(out), "--profile", str(self.profile_path)]
        pdf = out / "AlexSample_CV.pdf"
        with patch("build_and_validate.find_engine", return_value="fixture"), \
             patch("build_and_validate.compile_tex", side_effect=compile_fixture), \
             patch("build_and_validate.pdf_text", return_value=text), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(sys, "argv", args):
                self.assertEqual(build_and_validate.main(), 0)
            self.assertTrue(pdf.exists())
            with patch.object(sys, "argv", args + ["--max-pages", "1"]):
                self.assertEqual(build_and_validate.main(), 1)
            self.assertFalse(pdf.exists())


if __name__ == "__main__":
    unittest.main()
