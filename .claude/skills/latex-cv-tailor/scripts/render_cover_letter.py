#!/usr/bin/env python3
"""Turn the agent-written cover-letter.md into cover-letter.tex.

The letter's prose is the agent's work; this script only supplies the header
from the profile, escapes LaTeX, and lays out paragraphs — so the contact block
can never drift from `personal.md`.

Usage:
    python render_cover_letter.py --dir ./applications/<slug> --profile ./profile \
        --template-root ./templates [--template ats-single-column]
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_profile import ProfileError, load_profile  # noqa: E402
from render_cv import (  # noqa: E402
    PlanError,
    is_empty,
    link,
    substitute_markers,
    tex,
    tex_url,
)


def md_to_tex(markdown: str) -> str:
    """Blank-line separated blocks become paragraphs. Inline markup is stripped
    rather than interpreted — a cover letter needs no formatting, and stripping
    keeps injected markup out of the LaTeX."""
    body = re.sub(r"^#.*$", "", markdown, flags=re.MULTILINE)  # drop headings
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    out = []
    for block in blocks:
        flat = " ".join(line.strip() for line in block.splitlines())
        flat = re.sub(r"\*\*(.+?)\*\*", r"\1", flat)
        flat = re.sub(r"(?<!\w)[*_](.+?)[*_](?!\w)", r"\1", flat)
        out.append(tex(flat))
    return "\n\n".join(out)


def build_header(profile: dict) -> str:
    p = profile["personal"]
    bits = []
    if not is_empty(p.get("email")):
        bits.append(rf"\href{{mailto:{tex_url(p['email'])}}}{{{tex(p['email'])}}}")
    for key in ("phone", "location"):
        if not is_empty(p.get(key)):
            bits.append(tex(p[key]))
    for key in ("linkedin", "github"):
        if not is_empty(p.get(key)):
            bits.append(link(p[key]))
    return "\n".join(
        [
            rf"\clname{{{tex(p['full_name'])}}}",
            r"\clcontact{" + r" $\cdot$ ".join(bits) + "}",
            rf"\cldate{{{tex(date.today().strftime('%d %B %Y'))}}}",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--template-root", required=True, type=Path)
    ap.add_argument("--template", default="ats-single-column")
    args = ap.parse_args()

    source = args.dir / "cover-letter.md"
    template_file = args.template_root / args.template / "cover-letter.tex"

    try:
        if not source.exists():
            raise ProfileError(f"{source} does not exist - write the letter first")
        if not template_file.exists():
            raise ProfileError(f"no cover-letter template at {template_file}")
        profile = load_profile(args.profile)

        name = tex(profile["personal"]["full_name"])
        doc = substitute_markers(
            template_file.read_text(encoding="utf-8"),
            {
                "%%PDFMETA%%": (
                    "\\hypersetup{\n"
                    f"  pdftitle={{{name} - Cover letter}},\n"
                    f"  pdfauthor={{{name}}},\n"
                    "  pdfcreator={},\n}"
                ),
                "%%HEADER%%": build_header(profile),
                "%%BODY%%": md_to_tex(source.read_text(encoding="utf-8")),
            },
        )
    except (ProfileError, PlanError, OSError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1

    target = args.dir / "cover-letter.tex"
    target.write_text(doc, encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
