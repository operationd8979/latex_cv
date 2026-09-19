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
        contents = self.plan(["PRJ-WIDGET", "PRJ-API"])
        contents.update(job={"title": "Tester Intern"}, headline="Software Tester")
        plan.write_text(json.dumps(contents), encoding="utf-8")
        args = ["render_cv.py", "--profile", str(self.profile_path), "--plan", str(plan),
                "--template-root", str(ROOT / "templates"), "--out", str(self.root / "job")]
        with patch.object(sys, "argv", args), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(render_cv.main(), 0)
        doc = (self.root / "job/raw/cv.tex").read_text(encoding="utf-8")
        self.assertIn("Widget\\_Tool", doc)
        self.assertIn("Synthetic API", doc)
        self.assertIn(r"\cvheadline{Software Tester}", doc)

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

    def test_headline_matches_frontend_or_testing_job(self):
        cases = [
            ("Junior Frontend Developer (React)", "Frontend Developer"),
            ("Manual Tester - Banking UAT", "Software Tester"),
            ("QC Automation Tester", "QA Automation Engineer"),
            ("Software Engineer Intern - QA", "QA Engineer"),
            ("DevOps Engineer", "DevOps Engineer"),
        ]
        for title, headline in cases:
            with self.subTest(title=title):
                render_cv.check_headline_for_job({"job": {"title": title}, "headline": headline})

    def test_headline_rejects_wrong_or_multiple_roles(self):
        cases = [
            ("Manual Tester - Banking UAT", "Frontend Developer | Software Testing"),
            ("QA Automation Engineer", "Frontend Developer"),
            ("Frontend Developer", "Software Tester"),
            ("Frontend Developer", "Frontend Developer | React and TypeScript"),
            ("Tester Intern", "Frontend Developer & QA Engineer"),
        ]
        for title, headline in cases:
            with self.subTest(title=title, headline=headline), self.assertRaises(render_cv.PlanError):
                render_cv.check_headline_for_job({"job": {"title": title}, "headline": headline})

    def test_two_roles_allowed_only_for_explicitly_combined_job_title(self):
        render_cv.check_headline_for_job({"job": {"title": "Frontend Developer & QA Tester"},
                                          "headline": "Frontend Developer | QA Tester"})
        with self.assertRaises(render_cv.PlanError):
            render_cv.check_headline_for_job({"job": {"title": "Frontend Developer"},
                                              "headline": "Frontend Developer | QA Tester"})

    def test_approved_title_overrides_a_shortened_or_misleading_plan_title(self):
        plan = {"job": {"title": "Frontend Developer & QA Tester"},
                "headline": "Frontend Developer | QA Tester"}
        with self.assertRaises(render_cv.PlanError):
            render_cv.check_headline_for_job(plan, "Manual Tester - Banking UAT")
        render_cv.check_headline_for_job({"job": {"title": "Shortened title"},
                                          "headline": "Software Tester"},
                                         "Manual Tester - Banking UAT")

    def test_job_plan_requires_an_explicit_headline(self):
        with self.assertRaisesRegex(render_cv.PlanError, "job-specific headline"):
            render_cv.check_headline_for_job({"job": {"title": "Manual Tester"}})

    def test_build_cli_accepts_two_pages_but_rejects_three_by_default(self):
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
            with patch("build_and_validate.pdf_text", return_value=text + "Third page.\f"), \
                 patch.object(sys, "argv", args):
                self.assertEqual(build_and_validate.main(), 1)
            self.assertFalse(pdf.exists())


if __name__ == "__main__":
    unittest.main()
