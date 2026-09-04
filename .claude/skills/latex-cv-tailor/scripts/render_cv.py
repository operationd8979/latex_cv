#!/usr/bin/env python3
"""Render a content plan plus the profile into cv.tex and match-report.md.

This script is the factual gatekeeper. It refuses to render when the plan
references anything the profile does not support, so an evidence trail is a
structural guarantee rather than a promise in a prompt.

Enforced invariants:
  * Every `source` ID in the plan resolves to a real profile ID.
  * A bullet may only cite IDs belonging to the entry it sits under.
  * Company, role, dates, location, GPA and credential URLs come from the
    profile verbatim — the plan cannot override them.
  * Every listed skill exists in skills.md, and no `unverified` skill is
    allowed onto the page.
  * The chosen summary variant must be marked `status: approved`.

Usage:
    python render_cv.py --plan plan.json --profile ./profile \
        --template-root ./templates --out ./applications/<slug>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_profile import ProfileError, load_profile  # noqa: E402

MONTHS = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}
EMPTY_VALUES = {"", "unknown", "none recorded", "none", "n/a"}
PLACEHOLDER_RE = re.compile(r"%%[A-Z_]+%%")
TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)

_ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_ESCAPE_RE = re.compile("[" + re.escape("".join(_ESCAPE_MAP)) + "]")


class PlanError(Exception):
    pass


def substitute_markers(doc: str, values: dict[str, str]) -> str:
    """Replace each %%MARKER%% that occupies a line of its own.

    A plain str.replace would also fire inside the template's own comments —
    a template documenting `%%BODY%%` in a comment would be destroyed by its
    own documentation. Requiring the marker to be the whole line makes the
    substitution unambiguous, and a marker that is missing or repeated is an
    error rather than a silently malformed document.
    """
    out: list[str] = []
    seen = {k: 0 for k in values}
    for line in doc.splitlines(keepends=True):
        key = line.strip()
        if key in values:
            seen[key] += 1
            out.append(values[key] + ("\n" if line.endswith("\n") else ""))
        else:
            out.append(line)
    for key, count in seen.items():
        if count == 0:
            raise PlanError(f"template has no line containing only {key}")
        if count > 1:
            raise PlanError(f"template repeats {key} on {count} lines")

    rendered = "".join(out)
    # A marker mentioned inside a LaTeX comment is documentation, not an
    # unresolved placeholder, so scan only what actually typesets.
    leftover = set(PLACEHOLDER_RE.findall(TEX_COMMENT_RE.sub("", rendered)))
    if leftover:
        raise PlanError("placeholders left unresolved: " + ", ".join(sorted(leftover)))
    return rendered


def tex(value: str) -> str:
    """Escape every LaTeX-special character in one pass."""
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_MAP[m.group()], str(value))


def tex_url(url: str) -> str:
    """Escape only what breaks inside \\href's URL argument."""
    return url.replace("\\", r"\\").replace("%", r"\%").replace("#", r"\#")


def is_empty(value: str | None) -> bool:
    return value is None or value.strip().lower() in EMPTY_VALUES


def fmt_month(value: str) -> str:
    """`2026-07` -> `Jul 2026`; `present` -> `Present`; junk -> as written."""
    if is_empty(value):
        return ""
    value = value.strip()
    if value.lower() == "present":
        return "Present"
    m = re.fullmatch(r"(\d{4})-(\d{2})", value)
    return f"{MONTHS[m.group(2)]} {m.group(1)}" if m else value


def fmt_range(start: str, end: str) -> str:
    left, right = fmt_month(start), fmt_month(end)
    return " – ".join(p for p in (left, right) if p)


def link(url: str, label: str | None = None) -> str:
    shown = label or re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return rf"\href{{{tex_url(url)}}}{{{tex(shown)}}}"


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------

def _resolve(profile: dict, source: str, expect: str | None = None) -> dict:
    index = profile["index"]
    if source not in index:
        raise PlanError(f"source {source!r} does not exist in the profile")
    if expect and index[source] != expect:
        raise PlanError(
            f"source {source!r} is a {index[source]}, but a {expect} was expected"
        )
    for group in ("experience", "projects", "education", "certifications"):
        for entry in profile[group]:
            if entry["id"] == source:
                return entry
    for s in profile["summaries"]:
        if s["id"] == source:
            return s
    raise PlanError(f"source {source!r} could not be loaded")


def _check_bullets(entry: dict, bullets: list[dict]) -> None:
    known = {b["id"] for b in entry.get("bullets", [])}
    for b in bullets:
        sources = b.get("source") or []
        if not sources:
            raise PlanError(
                f"a bullet under {entry['id']} has no source — every claim must"
                " cite the profile ID it came from"
            )
        for sid in sources:
            if sid not in known:
                raise PlanError(
                    f"bullet cites {sid!r}, which is not evidence under"
                    f" {entry['id']} (available: {', '.join(sorted(known)) or 'none'})"
                )
        if not str(b.get("text", "")).strip():
            raise PlanError(f"a bullet under {entry['id']} has empty text")


def _check_skills(profile: dict, groups: list[dict]) -> None:
    by_name = {s["name"]: s for s in profile["skills"]}
    unverified, unknown = [], []
    for group in groups:
        for item in group.get("items", []):
            skill = by_name.get(item)
            if skill is None:
                unknown.append(item)
            elif skill["tier"] == "unverified":
                unverified.append(item)
    if unknown:
        raise PlanError(
            "these skills are not in skills.md and may not be claimed: "
            + ", ".join(sorted(unknown))
        )
    if unverified:
        raise PlanError(
            "these skills are tiered 'unverified' and must never reach a CV: "
            + ", ".join(sorted(unverified))
        )


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def cv_item(headline: str, meta_parts: list[str]) -> str:
    """One entry: headline line plus a flush-left metadata line.

    Metadata is joined here rather than in the template so an absent location
    or date leaves no dangling separator.
    """
    meta = " $\\cdot$ ".join(
        tex(part.strip()) for part in meta_parts if not is_empty(part)
    )
    if not meta:
        return rf"\cvitemplain{{{headline}}}"
    return r"\cvitem{%s}{%s}" % (headline, meta)


def render_header(profile: dict, plan: dict) -> list[str]:
    p = profile["personal"]
    out = [rf"\cvname{{{tex(p['full_name'])}}}"]
    headline = plan.get("headline") or profile["preferences"].get("target_roles", "")
    headline = headline.split(",")[0].strip()
    if headline:
        out.append(rf"\cvheadline{{{tex(headline)}}}")

    bits = []
    if not is_empty(p.get("email")):
        bits.append(rf"\href{{mailto:{tex_url(p['email'])}}}{{{tex(p['email'])}}}")
    for key in ("phone", "location"):
        if not is_empty(p.get(key)):
            bits.append(tex(p[key]))
    for key in ("linkedin", "github", "portfolio"):
        if not is_empty(p.get(key)):
            bits.append(link(p[key]))
    out.append(r"\cvcontact{" + r" $\cdot$ ".join(bits) + "}")
    return out


def render_bullets(bullets: list[dict]) -> list[str]:
    if not bullets:
        return []
    out = [r"\begin{cvbullets}"]
    out += [rf"  \item {tex(b['text'])}" for b in bullets]
    out.append(r"\end{cvbullets}")
    return out


def render_experience(profile: dict, section: dict) -> list[str]:
    out = []
    for item in section.get("entries", []):
        entry = _resolve(profile, item["source"], "experience")
        bullets = item.get("bullets", [])
        _check_bullets(entry, bullets)
        role = entry.get("title_role") or entry.get("title", "").split(",")[0]
        headline = rf"\textbf{{{tex(role)}}}, {tex(entry.get('company', ''))}"
        out.append(cv_item(headline, [
            entry.get("location", ""),
            fmt_range(entry.get("start", ""), entry.get("end", "")),
            entry.get("employment", ""),
        ]))
        out += render_bullets(bullets)
    return out


def render_projects(profile: dict, section: dict) -> list[str]:
    out = []
    for item in section.get("entries", []):
        entry = _resolve(profile, item["source"], "project")
        bullets = item.get("bullets", [])
        _check_bullets(entry, bullets)
        when = fmt_month(entry.get("month", "")) or entry.get("year", "")
        out.append(cv_item(
            rf"\textbf{{{tex(entry['title'])}}}",
            [entry.get("role", ""), when],
        ))
        if item.get("show_tech", True) and not is_empty(entry.get("tech")):
            out.append(rf"\cvmeta{{{tex(entry['tech'])}}}")
        links = [
            link(entry[key], label)
            for key, label in (("demo", None), ("repo", None))
            if not is_empty(entry.get(key)) and key in item.get("links", ["repo"])
        ]
        if links:
            out.append(r"\cvlinks{" + r" $\cdot$ ".join(links) + "}")
        out += render_bullets(bullets)
    return out


def render_skills(profile: dict, section: dict) -> list[str]:
    groups = section.get("groups", [])
    _check_skills(profile, groups)
    return [
        r"\cvskill{%s}{%s}" % (tex(g["label"]), tex(", ".join(g["items"])))
        for g in groups
        if g.get("items")
    ]


def render_education(profile: dict, section: dict) -> list[str]:
    out = []
    for item in section.get("entries", []):
        e = _resolve(profile, item["source"], "education")
        headline = rf"\textbf{{{tex(e['title'])}}}, {tex(e.get('institution', ''))}"
        meta = [fmt_month(e.get("graduated", "")), e.get("location", "")]
        if not is_empty(e.get("gpa")):
            meta.append(f"GPA {e['gpa']}")
        if not is_empty(e.get("classification")):
            meta.append(e["classification"])
        out.append(cv_item(headline, meta))
    return out


def render_certifications(profile: dict, section: dict) -> list[str]:
    out = []
    for item in section.get("entries", []):
        c = _resolve(profile, item["source"], "certification")
        name = tex(c["title"])
        if not is_empty(c.get("credential_url")):
            name = link(c["credential_url"], c["title"])
        parts = [name]
        issuer = c.get("issuer", "")
        # "Microsoft Certified: Azure Fundamentals - Microsoft" reads badly;
        # skip the issuer when the certification name already carries it.
        if not is_empty(issuer) and issuer.lower() not in c["title"].lower():
            parts.append(tex(issuer))
        issued = fmt_month(c.get("issued", ""))
        if issued:
            parts.append(tex(issued))
        out.append(r"\cvplain{%s}" % r" $\cdot$ ".join(parts))
    return out


RENDERERS = {
    "experience": render_experience,
    "projects": render_projects,
    "skills": render_skills,
    "education": render_education,
    "certifications": render_certifications,
}


def render_body(profile: dict, plan: dict) -> str:
    out = render_header(profile, plan)

    summary = plan.get("summary")
    if summary:
        variant = _resolve(profile, summary["source"], "summary")
        if variant["status"] != "approved":
            raise PlanError(
                f"summary {variant['id']} has status {variant['status']!r};"
                " only 'approved' variants may be used"
            )
        out.append(r"\cvsection{Summary}")
        out.append(rf"\cvsummary{{{tex(summary['text'])}}}")

    for section in plan.get("sections", []):
        kind = section.get("type")
        if kind not in RENDERERS:
            raise PlanError(f"unknown section type {kind!r}")
        lines = RENDERERS[kind](profile, section)
        if not lines:
            continue
        out.append(rf"\cvsection{{{tex(section.get('heading', kind.title()))}}}")
        out += lines

    return "\n".join(out) + "\n"


def render_pdfmeta(profile: dict, plan: dict) -> str:
    job = plan.get("job", {})
    title = f"{profile['personal']['full_name']} — CV"
    if job.get("title"):
        title += f" — {job['title']}"
    return (
        "\\hypersetup{\n"
        f"  pdftitle={{{tex(title)}}},\n"
        f"  pdfauthor={{{tex(profile['personal']['full_name'])}}},\n"
        "  pdfcreator={},\n"
        "}"
    )


# --------------------------------------------------------------------------
# match report
# --------------------------------------------------------------------------

def build_match_report(profile: dict, plan: dict) -> str:
    job = plan.get("job", {})
    lines = [
        "# Match report",
        "",
        f"- **Company:** {job.get('company', 'unknown')}",
        f"- **Role:** {job.get('title', 'unknown')}",
    ]
    if job.get("job_id"):
        lines.append(f"- **Job ID:** {job['job_id']}")
    if job.get("url"):
        lines.append(f"- **Source:** {job['url']}")
    lines += [
        f"- **Template:** {plan.get('template', 'unknown')}",
        f"- **Generated:** {date.today().isoformat()}",
        "",
        "## Evidence trail",
        "",
        "Every line on the CV and the profile ID it came from.",
        "",
        "| Section | CV line | Source |",
        "|---|---|---|",
    ]

    def row(section: str, text: str, sources: list[str]) -> str:
        clean = text.replace("|", "\\|")
        if len(clean) > 90:
            clean = clean[:87] + "..."
        return f"| {section} | {clean} | {', '.join(sources)} |"

    if plan.get("summary"):
        lines.append(row("Summary", plan["summary"]["text"], [plan["summary"]["source"]]))

    for section in plan.get("sections", []):
        heading = section.get("heading", section.get("type", ""))
        for item in section.get("entries", []):
            entry = _resolve(profile, item["source"])
            lines.append(row(heading, entry["title"], [entry["id"]]))
            for b in item.get("bullets", []):
                lines.append(row(heading, b["text"], b["source"]))
        for group in section.get("groups", []):
            by_name = {s["name"]: s for s in profile["skills"]}
            for name in group.get("items", []):
                ev = by_name[name]["evidence"]
                lines.append(row(heading, name, ev or ["tier-only"]))

    lines += ["", "## Job requirements", "", "| Requirement | Status | Evidence |", "|---|---|---|"]
    reqs = plan.get("requirements", [])
    for r in reqs:
        for ev in r.get("evidence", []):
            if ev not in profile["index"]:
                raise PlanError(f"requirement evidence {ev!r} does not exist")
        note = f" — {r['note']}" if r.get("note") else ""
        lines.append(
            f"| {r['requirement']} | {r.get('status', 'unknown')}{note} |"
            f" {', '.join(r.get('evidence', [])) or '—'} |"
        )
    if not reqs:
        lines.append("| _none recorded_ | | |")

    missing = [r for r in reqs if r.get("status") == "missing"]
    lines += ["", "## Requirements the profile does not meet", ""]
    lines += [f"- {r['requirement']}" for r in missing] or [
        "- None identified."
    ]

    excluded = sorted(s["name"] for s in profile["skills"] if s["tier"] == "unverified")
    lines += [
        "",
        "## Skills withheld as unverified",
        "",
        "Present in the profile but excluded from the CV because no evidence"
        " supports them:",
        "",
    ]
    lines += [f"- {name}" for name in excluded] or ["- None."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", required=True, type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--template-root", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    try:
        profile = load_profile(args.profile)
        plan = json.loads(args.plan.read_text(encoding="utf-8"))

        name = plan.get("template", "ats-single-column")
        template_file = args.template_root / name / "template.tex"
        if not template_file.exists():
            raise PlanError(
                f"template {name!r} not found at {template_file}. Available: "
                + (", ".join(sorted(p.name for p in args.template_root.iterdir()
                                    if p.is_dir())) or "none")
            )

        doc = substitute_markers(
            template_file.read_text(encoding="utf-8"),
            {
                "%%PDFMETA%%": render_pdfmeta(profile, plan),
                "%%BODY%%": render_body(profile, plan),
            },
        )

        report = build_match_report(profile, plan)
    except (PlanError, ProfileError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"render failed: {exc!r}", file=sys.stderr)
        return 1

    raw = args.out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "cv.tex").write_text(doc, encoding="utf-8")
    (raw / "match-report.md").write_text(report, encoding="utf-8")
    print(f"wrote {raw / 'cv.tex'}")
    print(f"wrote {raw / 'match-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
