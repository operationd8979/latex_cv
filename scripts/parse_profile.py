#!/usr/bin/env python3
"""Parse the Markdown profile store into structured JSON keyed by stable ID.

The profile contract lives in profile/README.md. This parser is the only place
that knows the file format; everything downstream consumes the JSON.

Usage:
    python parse_profile.py --profile ./profile              # emit JSON
    python parse_profile.py --profile ./profile --check      # validate only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ENTRY_PREFIXES = ("EXP", "PRJ", "EDU", "CERT", "SUM")
TIERS = ("professional", "working", "familiar", "unverified")

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(?P<id>[A-Z]+-[A-Z0-9-]+)\s+—\s+(?P<title>.+?)\s*$")
PLAIN_HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$")
FIELD_RE = re.compile(r"^-\s+\*\*(?P<key>[^*]+?):\*\*\s*(?P<value>.*)$")
BULLET_RE = re.compile(r"^-\s+`(?P<id>[A-Z]+-[A-Z0-9-]+-\d+)`\s+—\s+(?P<text>.+)$")
SKILL_RE = re.compile(
    r"^-\s+\*\*(?P<name>.+?)\*\*\s+—\s+(?P<tier>\w+)\s+—\s+evidence:\s*(?P<evidence>.+?)\s*$"
)
DATE_RE = re.compile(r"^(\d{4}-\d{2}|present|unknown)$")


class ProfileError(Exception):
    pass


def _slug(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def _strip_comments(text: str) -> str:
    """HTML comments are notes to the owner and are never facts."""
    return COMMENT_RE.sub("", text)


def _read(path: Path) -> list[str]:
    if not path.exists():
        raise ProfileError(f"missing profile file: {path.name}")
    return _strip_comments(path.read_text(encoding="utf-8")).splitlines()


def _collect_fields(lines: list[str], start: int, stop: int) -> dict[str, str]:
    """Read `- **Key:** value` pairs, joining 2-space-indented continuations."""
    fields: dict[str, str] = {}
    key: str | None = None
    for raw in lines[start:stop]:
        m = FIELD_RE.match(raw)
        if m:
            key = _slug(m.group("key"))
            fields[key] = m.group("value").strip()
        elif key and raw.startswith("  ") and raw.strip():
            fields[key] = (fields[key] + " " + raw.strip()).strip()
        elif not raw.strip():
            key = None
        elif not raw.startswith(" "):
            key = None
    return fields


def _split_entries(lines: list[str]) -> list[tuple[str, str, int, int]]:
    """Return (id, title, body_start, body_end) for each `## ID — Title`."""
    marks: list[tuple[str, str, int]] = []
    for i, raw in enumerate(lines):
        m = HEADING_RE.match(raw)
        if m:
            marks.append((m.group("id"), m.group("title"), i))
    out = []
    for n, (eid, title, i) in enumerate(marks):
        end = marks[n + 1][2] if n + 1 < len(marks) else len(lines)
        out.append((eid, title, i + 1, end))
    return out


def _parse_bullets(lines: list[str], start: int, stop: int, parent: str) -> list[dict]:
    bullets = []
    for raw in lines[start:stop]:
        m = BULLET_RE.match(raw)
        if not m:
            continue
        bid = m.group("id")
        if not bid.startswith(parent + "-"):
            raise ProfileError(f"bullet {bid} does not belong to entry {parent}")
        bullets.append({"id": bid, "text": m.group("text").strip()})
    return bullets


def _parse_entry_file(path: Path, kind: str) -> list[dict]:
    lines = _read(path)
    entries = []
    for eid, title, start, stop in _split_entries(lines):
        ev_at = next(
            (i for i in range(start, stop) if lines[i].strip() == "**Evidence**"), stop
        )
        entry = {
            "id": eid,
            "kind": kind,
            "title": title,
            **_collect_fields(lines, start, ev_at),
        }
        entry["bullets"] = _parse_bullets(lines, ev_at, stop, eid)
        if "tech" in entry:
            entry["tech_list"] = [
                t.strip() for t in entry["tech"].split(",") if t.strip()
            ]
        entries.append(entry)
    return entries


def _parse_summaries(path: Path) -> list[dict]:
    lines = _read(path)
    out = []
    for eid, title, start, stop in _split_entries(lines):
        fields = _collect_fields(lines, start, stop)
        quote = [
            raw.lstrip()[1:].strip()
            for raw in lines[start:stop]
            if raw.lstrip().startswith(">")
        ]
        out.append(
            {
                "id": eid,
                "title": title,
                "status": fields.get("status", "").split("—")[0].strip(),
                "text": " ".join(q for q in quote if q).strip(),
            }
        )
    return out


def _parse_skills(path: Path) -> list[dict]:
    lines = _read(path)
    category = ""
    out = []
    for raw in lines:
        pm = PLAIN_HEADING_RE.match(raw)
        if pm:
            category = pm.group("title").strip()
            continue
        m = SKILL_RE.match(raw)
        if not m:
            continue
        ev = m.group("evidence").strip()
        out.append(
            {
                "name": m.group("name").strip(),
                "tier": m.group("tier").strip(),
                "category": category,
                "evidence": [] if ev == "none" else [e.strip() for e in ev.split(",")],
            }
        )
    return out


def _parse_kv_file(path: Path) -> dict[str, str]:
    lines = _read(path)
    return _collect_fields(lines, 0, len(lines))


def load_profile(root: Path) -> dict:
    profile = {
        "personal": _parse_kv_file(root / "personal.md"),
        "preferences": _parse_kv_file(root / "preferences.md"),
        "summaries": _parse_summaries(root / "summary.md"),
        "experience": _parse_entry_file(root / "experience.md", "experience"),
        "projects": _parse_entry_file(root / "projects.md", "project"),
        "education": _parse_entry_file(root / "education.md", "education"),
        "certifications": _parse_entry_file(root / "certifications.md", "certification"),
        "skills": _parse_skills(root / "skills.md"),
    }
    profile["index"] = _build_index(profile)
    return profile


def _build_index(profile: dict) -> dict[str, str]:
    """Map every addressable ID -> what kind of thing it is."""
    index: dict[str, str] = {}

    def add(key: str, kind: str) -> None:
        if key in index:
            raise ProfileError(f"duplicate ID: {key}")
        index[key] = kind

    for s in profile["summaries"]:
        add(s["id"], "summary")
    for group in ("experience", "projects", "education", "certifications"):
        for entry in profile[group]:
            add(entry["id"], entry["kind"])
            for b in entry.get("bullets", []):
                add(b["id"], "bullet")
    return index


def check_profile(profile: dict) -> list[str]:
    """Return a list of contract violations. Empty means the profile is sound."""
    problems: list[str] = []
    index = profile["index"]

    for field in ("full_name", "email", "phone"):
        if not profile["personal"].get(field):
            problems.append(f"personal.md is missing required field: {field}")

    if not any(s["status"] == "approved" for s in profile["summaries"]):
        problems.append("summary.md has no variant with status 'approved'")

    for entry in profile["experience"]:
        for field in ("start", "end"):
            value = entry.get(field, "")
            if not DATE_RE.match(value):
                problems.append(
                    f"{entry['id']}: {field} is {value!r}, expected YYYY-MM or 'present'"
                )
        if not entry.get("bullets"):
            problems.append(f"{entry['id']}: has no evidence bullets")

    for skill in profile["skills"]:
        if skill["tier"] not in TIERS:
            problems.append(
                f"skill {skill['name']!r}: unknown tier {skill['tier']!r}"
                f" (expected one of {', '.join(TIERS)})"
            )
        for ev in skill["evidence"]:
            if ev not in index:
                problems.append(
                    f"skill {skill['name']!r}: evidence {ev!r} resolves to nothing"
                )
        if skill["tier"] != "unverified" and not skill["evidence"]:
            problems.append(
                f"skill {skill['name']!r}: tier {skill['tier']!r} but no evidence listed"
            )
        if skill["tier"] == "unverified" and skill["evidence"]:
            problems.append(
                f"skill {skill['name']!r}: tier 'unverified' but evidence is listed"
            )

    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--check", action="store_true", help="validate, emit no JSON")
    ap.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    args = ap.parse_args()

    try:
        profile = load_profile(args.profile)
    except ProfileError as exc:
        print(f"profile error: {exc}", file=sys.stderr)
        return 2

    problems = check_profile(profile)
    if problems:
        print("Profile contract violations:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    if args.check:
        counts = {k: len(v) for k, v in profile.items() if isinstance(v, list)}
        print("profile OK: " + ", ".join(f"{k}={n}" for k, n in sorted(counts.items())))
        return 0

    payload = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
