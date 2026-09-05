"""Tests for the deterministic parts of latex-cv-tailor.

All candidate data here is synthetic (Alex Sample). Real profile data must
never appear in a fixture.

    python -m unittest discover -s .claude/skills/latex-cv-tailor/tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
WORKSPACE_ROOT = TESTS.parents[3]
SCRIPTS = WORKSPACE_ROOT / "scripts"
FIXTURE = WORKSPACE_ROOT / "tests" / "fixtures" / "profile"
sys.path.insert(0, str(SCRIPTS))

import build_and_validate  # noqa: E402
import new_job_dir  # noqa: E402
import render_cover_letter  # noqa: E402
import render_cv  # noqa: E402
from parse_profile import check_profile, load_profile  # noqa: E402


def base_plan(**over):
    plan = {
        "job": {"company": "Acme & Sons", "title": "Widget Engineer"},
        "template": "ats-single-column",
        "summary": {"source": "SUM-01", "text": "Widget engineer with 100% focus."},
        "sections": [
            {
                "type": "experience",
                "heading": "Experience",
                "entries": [
                    {
                        "source": "EXP-ACME",
                        "bullets": [
                            {"source": ["EXP-ACME-01"], "text": "Built widgets with 50% less waste."}
                        ],
                    }
                ],
            },
            {
                "type": "skills",
                "heading": "Technical Skills",
                "groups": [{"label": "Core", "items": ["C#", "Python"]}],
            },
        ],
        "requirements": [],
    }
    plan.update(over)
    return plan


class LatexEscaping(unittest.TestCase):
    def test_every_special_character(self):
        raw = r"a & b % c $ d # e _ f {g} h ~ i ^ j \ k"
        out = render_cv.tex(raw)
        self.assertEqual(
            out,
            r"a \& b \% c \$ d \# e \_ f \{g\} h \textasciitilde{} i "
            r"\textasciicircum{} j \textbackslash{} k",
        )

    def test_backslash_is_not_double_escaped(self):
        # A naive sequential replace would turn \ into \textbackslash{} and then
        # escape that replacement's own braces.
        self.assertEqual(render_cv.tex("\\"), r"\textbackslash{}")
        self.assertNotIn(r"\{\}", render_cv.tex("\\"))

    def test_url_escaping_leaves_query_strings_usable(self):
        self.assertEqual(
            render_cv.tex_url("https://x.test/a?b=1&c=2"), "https://x.test/a?b=1&c=2"
        )
        self.assertEqual(render_cv.tex_url("https://x.test/100%"), r"https://x.test/100\%")

    def test_accented_and_vietnamese_text_survives(self):
        self.assertEqual(render_cv.tex("Nguyễn Thị — café"), "Nguyễn Thị — café")


class DateFormatting(unittest.TestCase):
    def test_month_names(self):
        self.assertEqual(render_cv.fmt_month("2026-07"), "Jul 2026")
        self.assertEqual(render_cv.fmt_month("present"), "Present")
        self.assertEqual(render_cv.fmt_month("unknown"), "")

    def test_range(self):
        self.assertEqual(render_cv.fmt_range("2025-08", "2026-03"), "Aug 2025 – Mar 2026")
        self.assertEqual(render_cv.fmt_range("2026-07", "present"), "Jul 2026 – Present")


class Slugs(unittest.TestCase):
    def test_diacritics_folded(self):
        self.assertEqual(new_job_dir.slugify("Công ty Việt Nam"), "cong_ty_viet_nam")

    def test_punctuation_collapsed(self):
        self.assertEqual(new_job_dir.slugify("Acme, Inc. — Senior/Lead"), "acme_inc_senior_lead")

    def test_traversal_characters_are_neutralised(self):
        self.assertEqual(new_job_dir.slugify("../../etc/passwd"), "etc_passwd")
        self.assertEqual(new_job_dir.slugify("C:\\Windows\\system32"), "c_windows_system32")

    def test_empty_slug_is_rejected(self):
        with self.assertRaises(ValueError):
            new_job_dir.build_slug("!!!", "***", None, "2026-09-05")

    def test_slug_shape(self):
        self.assertEqual(
            new_job_dir.build_slug("Acme Ltd", "Senior Engineer", "482910", "2026-09-05"),
            "2026-09-05_acme_ltd_senior_engineer_482910",
        )


class JobDirectories(unittest.TestCase):
    def test_collision_creates_a_new_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "job").mkdir()
            self.assertEqual(new_job_dir.resolve_dir(root, "job").name, "job_v2")
            (root / "job_v2").mkdir()
            self.assertEqual(new_job_dir.resolve_dir(root, "job").name, "job_v3")

    def test_escape_from_output_root_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                new_job_dir.resolve_dir(Path(tmp), "../escaped")

    def test_root_itself_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                new_job_dir.resolve_dir(Path(tmp), ".")


class OutputLayout(unittest.TestCase):
    """Only the two PDFs belong at the top of a job directory."""

    def test_render_writes_into_raw(self):
        profile = load_profile(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            job = Path(tmp) / "job"
            raw = job / "raw"
            raw.mkdir(parents=True)
            (raw / "cv.tex").write_text(
                render_cv.render_body(profile, base_plan()), encoding="utf-8"
            )
            (raw / "match-report.md").write_text(
                render_cv.build_match_report(profile, base_plan()), encoding="utf-8"
            )
            top = sorted(p.name for p in job.iterdir())
            self.assertEqual(top, ["raw"])

    def test_build_reads_from_raw_and_writes_pdf_to_the_top(self):
        # the path contract, without invoking LaTeX
        import inspect

        source = inspect.getsource(build_and_validate.main)
        self.assertIn('args.dir / "raw" / f"{args.target}.tex"', source)
        self.assertIn('args.dir / f"{args.target}.pdf"', source)
        self.assertIn("args.dir / output_pdf_name(profile, args.target)", source)

    def test_the_pdf_is_named_after_the_candidate(self):
        profile = load_profile(FIXTURE)
        self.assertEqual(
            build_and_validate.output_pdf_name(profile, "cv"), "AlexSample_CV.pdf"
        )
        self.assertEqual(
            build_and_validate.output_pdf_name(profile, "cover-letter"),
            "AlexSample_CoverLetter.pdf",
        )

    def test_diacritics_are_folded_out_of_the_filename(self):
        profile = {"personal": {"full_name": "Nguyễn Thị Diệu Hằng"}}
        self.assertEqual(
            build_and_validate.output_pdf_name(profile, "cv"), "NguyenThiDieuHang_CV.pdf"
        )


class ProfileContract(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def test_fixture_is_sound(self):
        self.assertEqual(check_profile(self.profile), [])

    def test_ids_are_indexed(self):
        for key in ("EXP-ACME", "EXP-ACME-01", "PRJ-WIDGET", "SUM-01", "CERT-WIDGET"):
            self.assertIn(key, self.profile["index"])

    def test_comments_are_not_facts(self):
        self.assertNotIn("<!--", json.dumps(self.profile))

    def test_multiline_field_is_joined(self):
        entry = self.profile["experience"][0]
        self.assertEqual(entry["company"], "Acme & Sons")
        self.assertEqual(entry["start"], "2024-03")

    def test_skill_tiers_parsed(self):
        tiers = {s["name"]: s["tier"] for s in self.profile["skills"]}
        self.assertEqual(tiers["Rust"], "unverified")
        self.assertEqual(tiers["C#"], "professional")


class RenderGuards(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def render(self, plan):
        return render_cv.render_body(self.profile, plan)

    def test_happy_path_escapes_content(self):
        out = self.render(base_plan())
        self.assertIn(r"Acme \& Sons", out)
        self.assertIn(r"50\% less waste", out)
        self.assertIn("Mar 2024 – Present", out)

    def test_unverified_skill_is_refused(self):
        plan = base_plan()
        plan["sections"][1]["groups"][0]["items"].append("Rust")
        with self.assertRaisesRegex(render_cv.PlanError, "unverified"):
            self.render(plan)

    def test_skill_absent_from_profile_is_refused(self):
        plan = base_plan()
        plan["sections"][1]["groups"][0]["items"].append("Kubernetes")
        with self.assertRaisesRegex(render_cv.PlanError, "not in skills.md"):
            self.render(plan)

    def test_unknown_source_is_refused(self):
        plan = base_plan()
        plan["sections"][0]["entries"][0]["source"] = "EXP-NOPE"
        with self.assertRaisesRegex(render_cv.PlanError, "does not exist"):
            self.render(plan)

    def test_bullet_citing_another_entry_is_refused(self):
        plan = base_plan()
        plan["sections"][0]["entries"][0]["bullets"][0]["source"] = ["PRJ-WIDGET-01"]
        with self.assertRaisesRegex(render_cv.PlanError, "not evidence under"):
            self.render(plan)

    def test_bullet_without_a_source_is_refused(self):
        plan = base_plan()
        plan["sections"][0]["entries"][0]["bullets"][0]["source"] = []
        with self.assertRaisesRegex(render_cv.PlanError, "no source"):
            self.render(plan)

    def test_draft_summary_is_refused(self):
        plan = base_plan(summary={"source": "SUM-02", "text": "nope"})
        with self.assertRaisesRegex(render_cv.PlanError, "approved"):
            self.render(plan)

    def test_dates_come_from_the_profile_not_the_plan(self):
        plan = base_plan()
        plan["sections"][0]["entries"][0]["dates"] = "1999 – 2050"
        self.assertNotIn("1999", self.render(plan))

    def test_match_report_lists_withheld_skills(self):
        report = render_cv.build_match_report(self.profile, base_plan())
        self.assertIn("Skills withheld as unverified", report)
        self.assertIn("- Rust", report)
        self.assertIn("EXP-ACME-01", report)

    def test_match_report_rejects_bogus_requirement_evidence(self):
        plan = base_plan(requirements=[{"requirement": "x", "status": "met", "evidence": ["EXP-GONE"]}])
        with self.assertRaisesRegex(render_cv.PlanError, "does not exist"):
            render_cv.build_match_report(self.profile, plan)


class EntryLayout(unittest.TestCase):
    """Dates and location sit at the right margin, on the headline's own line."""

    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def render(self, plan):
        return render_cv.render_body(self.profile, plan)

    def test_metadata_is_the_second_argument_of_cvitem(self):
        out = self.render(base_plan())
        self.assertIn(
            r"\cvitem{\textbf{Widget Engineer}, Acme \& Sons}"
            r"{Testville $\cdot$ Mar 2024 – Present}",
            out,
        )

    def test_the_header_carries_no_home_address(self):
        # every entry states its own location; the header line is too dense to
        # spend on repeating it
        self.profile["personal"]["location"] = "Testville, Testland"
        out = self.render(base_plan())
        header = out.split(r"\cvsection")[0]
        self.assertIn("alex@example.com", header)
        self.assertNotIn("Testville, Testland", header)

    def test_education_takes_one_continuation_line_not_two(self):
        # two stacked lines under a right-aligned \cvitem make poppler read the
        # entry as two columns and strand the graduation date
        plan = base_plan(sections=[
            {"type": "education", "heading": "Education",
             "entries": [{"source": "EDU-TESTU"}]},
        ])
        out = self.render(plan)
        self.assertEqual(out.count(r"\cvsubline{"), 1)
        self.assertIn(r"\cvitem{\textbf{Bachelor of Widgets}}{Jan 2024}", out)
        self.assertIn(r"\cvsubline{Test University $\cdot$ GPA 3.9 / 4.0}", out)

    def test_certification_link_gets_its_own_visible_label(self):
        plan = base_plan(sections=[
            {"type": "certifications", "heading": "Certifications",
             "entries": [{"source": "CERT-WIDGET"}]},
        ])
        out = self.render(plan)
        self.assertIn(r"{Verify Credential}", out)
        # the name must stay plain text, not become the link
        self.assertIn(r"\cvplain{Certified Widget Pro $\cdot$", out)

    def test_project_links_are_labelled_one_per_line(self):
        plan = base_plan(sections=[
            {"type": "projects", "heading": "Projects", "entries": [
                {"source": "PRJ-WIDGET", "links": ["repo"], "bullets": [
                    {"source": ["PRJ-WIDGET-01"], "text": "Wrote a tool."},
                ]},
            ]},
        ])
        out = self.render(plan)
        self.assertIn(
            r"\cvlinks{Git: \href{https://github.com/alexsample/widget_tool}"
            r"{https://github.com/alexsample/widget\_tool}}",
            out,
        )

    def test_a_link_the_plan_did_not_ask_for_is_left_out(self):
        entry = {"demo": "https://demo.test", "repo": "https://repo.test"}
        self.assertEqual(
            render_cv.render_project_links(entry, ["demo"]),
            [r"\cvlinks{Demo: \href{https://demo.test}{https://demo.test}}"],
        )


class Languages(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def section(self, *ids):
        return {"type": "languages", "heading": "Languages",
                "entries": [{"source": i} for i in ids]}

    def test_proficiency_and_descriptor_are_printed(self):
        self.assertEqual(
            render_cv.render_languages(self.profile, self.section("LANG-EN")),
            [r"\cvskill{English}{Fluent (Works entirely in English)}"],
        )

    def test_an_unrecorded_descriptor_leaves_no_empty_parentheses(self):
        self.assertEqual(
            render_cv.render_languages(self.profile, self.section("LANG-XX")),
            [r"\cvskill{Widgetish}{Basic}"],
        )

    def test_a_language_section_citing_a_certification_is_refused(self):
        with self.assertRaisesRegex(render_cv.PlanError, "but a language was expected"):
            render_cv.render_languages(self.profile, self.section("CERT-WIDGET"))

    def test_the_plan_cannot_invent_a_proficiency(self):
        plan = base_plan(sections=[self.section("LANG-EN")])
        plan["sections"][0]["entries"][0]["proficiency"] = "Native"
        self.assertNotIn("Native", render_cv.render_body(self.profile, plan))

    def test_a_profile_without_the_file_still_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for f in FIXTURE.iterdir():
                if f.name != "languages.md":
                    (root / f.name).write_bytes(f.read_bytes())
            self.assertEqual(load_profile(root)["languages"], [])


class TwoColumnLayout(unittest.TestCase):
    SIDEBAR_TEMPLATE = (
        "%%PDFMETA%%\n"
        r"\newcommand{\cvphoto}[1]{#1}" "\n"
        "\\begin{document}\n%%HEADER%%\n%%SIDEBAR%%\n%%BODY%%\n\\end{document}\n"
    )

    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def test_marker_detection_requires_a_line_of_its_own(self):
        self.assertTrue(render_cv.declares_marker("a\n%%SIDEBAR%%\nb", "%%SIDEBAR%%"))
        self.assertFalse(
            render_cv.declares_marker("% mentions %%SIDEBAR%% inline", "%%SIDEBAR%%")
        )

    def test_sections_split_by_default_type(self):
        plan = base_plan()
        side, main = render_cv.split_columns(plan)
        self.assertEqual([s["type"] for s in side], ["skills"])
        self.assertEqual([s["type"] for s in main], ["experience"])

    def test_explicit_column_overrides_the_default(self):
        plan = base_plan()
        plan["sections"][1]["column"] = "main"  # skills into the main column
        side, main = render_cv.split_columns(plan)
        self.assertEqual(side, [])
        self.assertEqual(len(main), 2)

    def test_bad_column_value_is_refused(self):
        plan = base_plan()
        plan["sections"][0]["column"] = "middle"
        with self.assertRaisesRegex(render_cv.PlanError, "not 'side' or 'main'"):
            render_cv.split_columns(plan)

    def test_sidebar_skills_are_stacked_one_per_line(self):
        values = render_cv.render_marked(
            self.profile, base_plan(), self.SIDEBAR_TEMPLATE, "avatar.jpg"
        )
        self.assertIn(r"\cvskilllabel{Core}", values["%%SIDEBAR%%"])
        self.assertIn(r"\cvskillitem{C\#}", values["%%SIDEBAR%%"])
        self.assertNotIn(r"\cvskill{", values["%%SIDEBAR%%"])

    def test_name_goes_in_the_full_width_header_not_the_sidebar(self):
        values = render_cv.render_marked(
            self.profile, base_plan(), self.SIDEBAR_TEMPLATE, "avatar.jpg"
        )
        self.assertIn("Alex Sample", values["%%HEADER%%"])
        self.assertNotIn("Alex Sample", values["%%SIDEBAR%%"])
        self.assertIn(r"\cvheaderwithphoto{avatar.jpg}", values["%%HEADER%%"])

    def test_single_column_template_gets_one_body_and_no_photo(self):
        plain = "%%PDFMETA%%\n\\begin{document}\n%%BODY%%\n\\end{document}\n"
        values = render_cv.render_marked(self.profile, base_plan(), plain, None)
        self.assertEqual(set(values), {"%%PDFMETA%%", "%%BODY%%"})
        self.assertIn("Alex Sample", values["%%BODY%%"])
        self.assertNotIn(r"\cvphoto", values["%%BODY%%"])


class PhotoStaging(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(FIXTURE)

    def test_template_without_cvphoto_gets_no_photo(self):
        self.profile["personal"]["photo"] = "avatar.jpg"
        with tempfile.TemporaryDirectory() as tmp:
            got = render_cv.stage_photo(
                self.profile, FIXTURE, Path(tmp), "no photo macro here"
            )
            self.assertIsNone(got)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_missing_file_is_reported_not_silently_skipped(self):
        self.profile["personal"]["photo"] = "nope.jpg"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(render_cv.PlanError, "does not exist"):
                render_cv.stage_photo(
                    self.profile, FIXTURE, Path(tmp), r"\newcommand{\cvphoto}[1]{#1}"
                )

    def test_path_traversal_out_of_the_profile_is_refused(self):
        self.profile["personal"]["photo"] = "../../secret.jpg"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(render_cv.PlanError, "outside the profile"):
                render_cv.stage_photo(
                    self.profile, FIXTURE, Path(tmp), r"\newcommand{\cvphoto}[1]{#1}"
                )

    def test_photo_is_copied_next_to_the_tex(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = FIXTURE / "fixture-photo.jpg"
            src.write_bytes(b"\xff\xd8\xff\xe0 not a real jpeg")
            try:
                self.profile["personal"]["photo"] = "fixture-photo.jpg"
                got = render_cv.stage_photo(
                    self.profile, FIXTURE, Path(tmp), r"\newcommand{\cvphoto}[1]{#1}"
                )
                self.assertEqual(got, "fixture-photo.jpg")
                self.assertTrue((Path(tmp) / "fixture-photo.jpg").is_file())
            finally:
                src.unlink()


class ReadingOrder(unittest.TestCase):
    """The check that guards against right-aligned dates drifting away from
    their entry when a PDF's text layer is extracted."""

    SOURCE = (
        r"\cvsection{Experience}" "\n"
        r"\cvitem{\textbf{Widget Engineer}, Acme}{Testville $\cdot$ Mar 2024 – Present}" "\n"
        r"\cvsection{Education}" "\n"
    )

    def test_balanced_args_handles_nested_braces(self):
        args = build_and_validate.balanced_args(self.SOURCE, "cvitem", 2)
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0][0], r"\textbf{Widget Engineer}, Acme")
        self.assertIn("Mar 2024", args[0][1])

    def test_strip_tex_reduces_to_words(self):
        self.assertEqual(
            build_and_validate.strip_tex(r"\textbf{Widget Engineer}, Acme"),
            "widget engineer , acme",
        )

    def test_attached_metadata_passes(self):
        good = "Experience Widget Engineer, Acme Testville · Mar 2024 – Present Education"
        self.assertEqual(build_and_validate.check_reading_order(self.SOURCE, good), [])

    def test_metadata_pushed_past_a_heading_is_caught(self):
        # exactly the failure right-aligned dates produce
        bad = "Experience Widget Engineer, Acme did things Education Testville · Mar 2024 – Present"
        problems = build_and_validate.check_reading_order(self.SOURCE, bad)
        self.assertTrue(problems)
        self.assertIn("wrong entry", problems[0])

    def test_metadata_pushed_into_the_next_entry_is_caught(self):
        # the quiet version of the same failure: no heading in between, but the
        # date has still landed on somebody else's job
        source = (
            r"\cvsection{Experience}" "\n"
            r"\cvitem{\textbf{Widget Engineer}, Acme}{Mar 2024 – Present}" "\n"
            r"\cvitem{\textbf{Widget Intern}, Cogs}{Jan 2023 – Feb 2023}" "\n"
        )
        bad = (
            "Experience Widget Engineer, Acme did things "
            "Widget Intern, Cogs Mar 2024 – Present Jan 2023 – Feb 2023"
        )
        problems = build_and_validate.check_reading_order(source, bad)
        self.assertTrue(problems)
        self.assertIn("wrong entry", problems[0])

    def test_an_entry_is_not_a_boundary_for_itself(self):
        good = (
            "Experience Widget Engineer, Acme Testville · Mar 2024 – Present "
            "Education"
        )
        self.assertEqual(build_and_validate.check_reading_order(self.SOURCE, good), [])

    def test_missing_metadata_is_caught(self):
        problems = build_and_validate.check_reading_order(
            self.SOURCE, "Experience Widget Engineer, Acme Education"
        )
        self.assertTrue(any("missing from the PDF" in p for p in problems))


class CoverLetter(unittest.TestCase):
    def test_paragraphs_and_escaping(self):
        out = render_cover_letter.md_to_tex(
            "# Cover letter\n\nDear Hiring Team,\n\nI cut costs by 50% & shipped.\n"
        )
        self.assertNotIn("#", out)
        self.assertIn("Dear Hiring Team,", out)
        self.assertIn(r"50\% \& shipped", out)
        self.assertEqual(len(out.split("\n\n")), 2)

    def test_inline_markup_is_stripped_not_interpreted(self):
        out = render_cover_letter.md_to_tex("I am **very** good and _fast_.")
        self.assertEqual(out, "I am very good and fast.")

    def test_sign_off_keeps_its_line_break(self):
        out = render_cover_letter.md_to_tex("Body.\n\nSincerely,\nAlex Sample\n")
        self.assertIn("Sincerely, \\\\\nAlex Sample", out)

    def test_no_trailing_line_break_at_a_paragraph_end(self):
        # a stray \\ before a blank line is a LaTeX error
        out = render_cover_letter.md_to_tex("One line.\n\nAnother.\n")
        for para in out.split("\n\n"):
            self.assertFalse(para.rstrip().endswith("\\\\"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
