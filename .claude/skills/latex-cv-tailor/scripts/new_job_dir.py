#!/usr/bin/env python3
"""Create the output directory for one job, safely and reproducibly.

Slug shape: <YYYY-MM-DD>_<company>_<role>. The date prefix sorts applications
chronologically and makes collisions rare; a real collision gets _v2, _v3
rather than silently overwriting an earlier application.

Company and role come from a job page, so they are untrusted input: diacritics
are folded, everything outside [a-z0-9] collapses to `_`, and the result is
verified to stay inside the output root before any directory is created.

Usage:
    python new_job_dir.py --output-root ./applications --company "Acme Ltd." \
        --role "Senior Frontend Engineer" [--job-id 4821] [--date 2026-09-05]
    python new_job_dir.py ... --print-only     # show the path, create nothing
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
import re
from datetime import date
from pathlib import Path

MAX_PART = 40
MAX_VERSIONS = 50


def slugify(value: str, max_len: int = MAX_PART) -> str:
    """Fold to ASCII, lowercase, collapse everything else to underscores."""
    if value is None:
        return ""
    # Vietnamese đ/Đ has no NFKD decomposition to a bare `d`.
    value = value.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", str(value))
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_only).strip("_").lower()
    slug = re.sub(r"_+", "_", slug)
    return slug[:max_len].strip("_")


def build_slug(company: str, role: str, job_id: str | None, when: str) -> str:
    parts = [p for p in (slugify(company), slugify(role), slugify(job_id, 20)) if p]
    if not parts:
        raise ValueError(
            "company and role produced an empty slug — pass usable values"
        )
    return "_".join([when, *parts])


def resolve_dir(output_root: Path, slug: str) -> Path:
    """Return a fresh directory inside output_root, versioning on collision."""
    root = output_root.resolve()
    candidate = (root / slug).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"refusing to write outside {root}: {candidate}")
    if candidate == root:
        raise ValueError("slug resolved to the output root itself")

    if not candidate.exists():
        return candidate
    for n in range(2, MAX_VERSIONS + 1):
        versioned = root / f"{slug}_v{n}"
        if not versioned.exists():
            return versioned
    raise ValueError(f"more than {MAX_VERSIONS} versions of {slug} already exist")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-root", required=True, type=Path)
    ap.add_argument("--company", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--job-id", default=None)
    ap.add_argument("--date", default=None, help="defaults to today")
    ap.add_argument("--print-only", action="store_true")
    args = ap.parse_args()

    when = args.date or date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
        print(f"invalid --date {when!r}, expected YYYY-MM-DD", file=sys.stderr)
        return 1

    try:
        slug = build_slug(args.company, args.role, args.job_id, when)
        target = resolve_dir(args.output_root, slug)
    except ValueError as exc:
        print(f"cannot create job directory: {exc}", file=sys.stderr)
        return 1

    if not args.print_only:
        target.mkdir(parents=True, exist_ok=False)
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
