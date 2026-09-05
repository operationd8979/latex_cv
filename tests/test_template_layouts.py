"""Regression checks for the named-section layout using synthetic profile facts."""
import copy
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from parse_profile import load_profile
from render_cv import PlanError, render_marked, substitute_markers


class BlueBannerLayout(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile(ROOT / "tests/fixtures/profile")
        self.profile["projects"][0]["demo"] = "https://example.test/widget?x=1&y=2"
        self.template = (ROOT / "templates/blue-banner-photo/template.tex").read_text(encoding="utf-8")
        self.plan = {
            "template": "blue-banner-photo",
            "summary": {"source": "SUM-01", "text": "Widget engineer with practical experience."},
            # Deliberately use a different order from the design.
            "sections": [
                {"type": "projects", "entries": [{"source": "PRJ-WIDGET", "links": ["repo"]}]},
                {"type": "experience", "entries": [{"source": "EXP-ACME"}]},
                {"type": "certifications", "entries": [{"source": "CERT-WIDGET"}]},
                {"type": "skills", "groups": [{"label": "Core", "items": ["C#", "Python"]}]},
                {"type": "education", "entries": [{"source": "EDU-TESTU"}]},
            ],
        }

    def render(self, template=None, photo=None):
        template = self.template if template is None else template
        return substitute_markers(template, render_marked(self.profile, self.plan, template, photo))

    def test_order_facts_and_grouping_survive_an_old_plan(self):
        before = copy.deepcopy(self.plan)
        doc = self.render()
        self.assertEqual(re.findall(r"\\cvsection\{([^}]+)\}", doc), [
            "Summary", "Education", "Skills", "Certifications", "Experience", "Projects",
        ])
        for fact in ("Test University", "GPA 3.9 / 4.0", "Verify Credential",
                     r"\cvskill{Core}{C\#, Python}", "Acme", "Apr 2025"):
            self.assertIn(fact, doc)
        self.assertEqual(self.plan, before)

    def test_project_role_and_both_real_destinations_are_visible(self):
        doc = self.render()
        self.assertIn(r"\cvprojectrole{Developer}", doc)
        self.assertIn(r"\href{https://github.com/alexsample/widget_tool}{GitHub}", doc)
        self.assertIn(r"\href{https://example.test/widget?x=1&y=2}{Demo}", doc)
        self.assertIn(r"\cvmeta{Python, C++}", doc)

    def test_missing_optional_project_fields_are_not_invented(self):
        project = self.profile["projects"][0]
        project.pop("demo")
        project.pop("role")
        doc = self.render()
        self.assertNotIn("{Demo}", doc)
        self.assertNotIn(r"\cvprojectrole{", doc)
        self.assertIn("{GitHub}", doc)

    def test_show_tech_false_is_respected(self):
        self.plan["sections"][0]["entries"][0]["show_tech"] = False
        self.assertNotIn(r"\cvmeta{Python, C++}", self.render())

    def test_empty_sections_and_photo_fallback(self):
        self.plan["sections"] = []
        self.plan.pop("summary")
        doc = self.render()
        self.assertNotIn(r"\cvsection{", doc)
        self.assertIn(r"\cvheaderplain{\cvname{Alex Sample}", doc)
        self.assertIn(r"\cvheaderwithphoto{avatar.jpg}", self.render(photo="avatar.jpg"))

    def test_additional_section_is_preserved_in_body(self):
        self.template = self.template.replace("%%CERTIFICATIONS%%\n", "")
        doc = self.render()
        self.assertGreater(doc.index(r"\cvsection{Certifications}"), doc.index(r"\cvsection{Projects}"))

    def test_bad_section_and_unverified_skills_still_fail(self):
        self.plan["sections"].append({"type": "invented"})
        with self.assertRaisesRegex(PlanError, "unknown section type"):
            self.render()
        self.plan["sections"].pop()
        self.plan["sections"][3]["groups"][0]["items"].append("Rust")
        with self.assertRaisesRegex(PlanError, "unverified"):
            self.render()

    def test_legacy_layout_keeps_plan_order_and_selected_links(self):
        for name in ("ats-single-column", "two-column-photo"):
            with self.subTest(template=name):
                template = (ROOT / f"templates/{name}/template.tex").read_text(encoding="utf-8")
                values = render_marked(self.profile, self.plan, template, None)
                body = values["%%BODY%%"]
                self.assertLess(body.index(r"\cvsection{Projects}"), body.index(r"\cvsection{Experience}"))
                self.assertNotIn("{Demo}", body)
                self.assertNotIn(r"\cvprojectrole{", body)
                self.assertIn("Developer", body)


if __name__ == "__main__":
    unittest.main()
