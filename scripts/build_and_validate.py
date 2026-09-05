#!/usr/bin/env python3
"""Compile a .tex with Tectonic and prove the resulting PDF is actually usable.

A build that fails must never leave a stale PDF behind, because a leftover file
from an earlier run looks exactly like a success.

Usage:
    python build_and_validate.py --dir ./applications/<slug> --profile ./profile
    python build_and_validate.py --dir ./applications/<slug> --target cover-letter
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_profile import ProfileError, load_profile  # noqa: E402

PLACEHOLDER_RE = re.compile(r"%%[A-Z_]+%%")
SECTION_RE = re.compile(r"\\cvsection\{(.+?)\}")
MISSING_GLYPH_RE = re.compile(r"Missing character: There is no (.+?) in font", re.I)
OVERFULL_RE = re.compile(r"Overfull \\[hv]box \((\d+(?:\.\d+)?)pt too wide\)")
OVERFULL_LIMIT_PT = 5.0
TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
TARGET_LABEL = {"cv": "CV", "cover-letter": "CoverLetter"}
INSTALL_HINT = (
    "Tectonic is not installed or not on PATH. Install it with one of:\n"
    "    scoop install tectonic\n"
    "    winget install TectonicProject.Tectonic\n"
    "    cargo install tectonic"
)


class BuildError(Exception):
    pass


def find_engine(name: str = "tectonic") -> str:
    found = shutil.which(name)
    if not found:
        raise BuildError(INSTALL_HINT)
    return found


def output_pdf_name(profile: dict, target: str) -> str:
    """The deliverable's filename, e.g. `AlexSample_CV.pdf`.

    An employer's inbox fills with attachments called cv.pdf, so the name comes
    from `personal.md` rather than from the .tex stem. Diacritics are folded and
    everything but letters and digits dropped, because the file travels through
    mail clients and portals that mangle both.
    """
    folded = unicodedata.normalize("NFKD", profile["personal"]["full_name"])
    stem = re.sub(r"[^A-Za-z0-9]", "", folded.encode("ascii", "ignore").decode())
    return f"{stem}_{TARGET_LABEL[target]}.pdf" if stem else f"{target}.pdf"


def discard(*paths: Path) -> None:
    """A failed build must leave no PDF behind - a stale one reads as success."""
    for path in paths:
        path.unlink(missing_ok=True)


def compile_tex(tex_path: Path, engine: str, out_dir: Path) -> str:
    """Compile raw/<name>.tex, landing the PDF in the job directory itself.

    Shell escape stays off — Tectonic's default.
    """
    proc = subprocess.run(
        [engine, "-X", "compile", str(tex_path), "--outdir", str(out_dir), "--keep-logs"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    log_file = out_dir / (tex_path.stem + ".log")
    log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
    if log_file.exists():
        log_file.unlink()  # build artifacts must not pollute the deliverable

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = "\n".join(f"    {line}" for line in tail[-15:])
        raise BuildError(f"{engine} failed (exit {proc.returncode}):\n{detail}")
    return log


def pdf_text(pdf: Path) -> str:
    if not shutil.which("pdftotext"):
        raise BuildError(
            "pdftotext not found - cannot verify the PDF text layer. "
            "Install poppler-utils, or re-run with --skip-text-checks."
        )
    proc = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    if proc.returncode != 0:
        raise BuildError(f"pdftotext failed: {proc.stderr.strip()}")
    return proc.stdout


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def squash(text: str) -> str:
    """Letters and digits only - a spacing-insensitive comparison key."""
    return re.sub(r"[^a-z0-9]", "", strip_tex(text).lower())


def strip_tex(fragment: str) -> str:
    """Reduce a LaTeX fragment to the words it typesets."""
    out = re.sub(r"\$\\cdot\$", " ", fragment)
    out = re.sub(r"\\href\{[^}]*\}", " ", out)
    out = re.sub(r"\\[a-zA-Z]+\s*", " ", out)
    out = out.replace("{", " ").replace("}", " ").replace("$", " ")
    return normalise(out)


def balanced_args(source: str, macro: str, count: int) -> list[list[str]]:
    """Pull `count` brace-balanced arguments from each \\macro occurrence.

    A regex cannot do this: an entry headline legitimately contains
    \\textbf{...}, so the braces nest.
    """
    results, needle = [], "\\" + macro + "{"
    pos = 0
    while (start := source.find(needle, pos)) != -1:
        i = start + len(needle) - 1
        args: list[str] = []
        for _ in range(count):
            if i >= len(source) or source[i] != "{":
                break
            depth, j = 0, i
            while j < len(source):
                if source[j] == "{":
                    depth += 1
                elif source[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            args.append(source[i + 1 : j])
            i = j + 1
        if len(args) == count:
            results.append(args)
        pos = start + len(needle)
    return results


def entry_headlines(source: str) -> list[str]:
    """Every entry headline in the document, dated or not."""
    return [args[0] for args in balanced_args(source, "cvitem", 2)] + [
        args[0] for args in balanced_args(source, "cvitemplain", 1)
    ]


def check_reading_order(source: str, text: str) -> list[str]:
    """Each entry's metadata must stay with its entry when text is extracted.

    Dates set at the right margin are the risk here: poppler groups a page
    into blocks before it reads them, and a tall enough stack of flush-left
    lines beside a lone right-hand cell turns the entry into two columns. It
    then emits the whole left column first and the date lands somewhere later
    in the document, attached to whatever it happens to follow.

    Both kinds of somewhere-later count. A date that crosses a section heading
    is the loud version; a date that merely crosses into the next entry of the
    same section is the quiet one, and it is worse - a reader has no way to
    tell that the dates on two adjacent jobs have swapped.
    """
    problems = []
    # Match on letters and digits only: the extracted text and the LaTeX source
    # disagree about spacing and punctuation, and comparing those differences
    # would make this check pass without ever testing anything.
    flat = squash(text)
    boundaries = [
        (strip_tex(h), squash(h))
        for h in SECTION_RE.findall(source) + entry_headlines(source)
    ]

    for headline, meta in balanced_args(source, "cvitem", 2):
        label = strip_tex(headline)
        probe = squash(headline)
        start = flat.find(probe)
        if not probe or start < 0:
            problems.append(f"entry {label!r} is not readable in the PDF")
            continue
        for part in [p for p in meta.split(r"$\cdot$") if strip_tex(p)]:
            at = flat.find(squash(part), start)
            if at < 0:
                problems.append(
                    f"entry {label!r}: metadata {strip_tex(part)!r} is missing from the PDF"
                )
                continue
            between = flat[start + len(probe) : at]
            drifted = [
                name for name, sq in boundaries
                if sq and sq != probe and sq in between
            ]
            if drifted:
                problems.append(
                    f"entry {label!r}: its {strip_tex(part)!r} is separated from it "
                    f"by {drifted[0]!r} - an ATS would attach it to the wrong entry"
                )
    return problems


def validate(
    tex_path: Path, pdf: Path, log: str, profile: dict | None, max_pages: int
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not pdf.exists():
        return [f"{pdf.name} was not produced"], warnings
    if pdf.stat().st_size == 0:
        return [f"{pdf.name} is empty"], warnings

    text = pdf_text(pdf)
    flat = normalise(text)
    if len(flat) < 200:
        errors.append(
            f"{pdf.name} has almost no extractable text ({len(flat)} chars) - "
            "the PDF is probably not ATS-readable"
        )

    pages = text.count("\f") or 1
    if pages > max_pages:
        errors.append(f"{pdf.name} is {pages} pages; the limit is {max_pages}")

    leftover = set(PLACEHOLDER_RE.findall(text))
    if leftover:
        errors.append("unresolved template placeholders in the PDF: " + ", ".join(sorted(leftover)))

    # Scan only what typesets: a template documents its own macros in comments,
    # and those examples are not entries.
    source = TEX_COMMENT_RE.sub("", tex_path.read_text(encoding="utf-8"))
    for heading in SECTION_RE.findall(source):
        clean = re.sub(r"\\[a-zA-Z]+\s*", "", heading)
        if normalise(clean) not in flat:
            errors.append(f"section heading {clean!r} is not readable in the PDF")

    if profile is not None:
        for field in ("full_name", "email", "phone"):
            value = profile["personal"].get(field, "")
            if not value:
                continue
            # phone/name spacing varies in the text layer; compare digits/letters
            probe = squash(value)
            if probe and probe not in squash(text):
                errors.append(f"{field} ({value}) is not readable in the PDF text layer")

    errors += check_reading_order(source, text)

    glyphs = set(MISSING_GLYPH_RE.findall(log))
    if glyphs:
        errors.append("font is missing glyphs for: " + ", ".join(sorted(glyphs)))

    bad_boxes = [float(pt) for pt in OVERFULL_RE.findall(log) if float(pt) > OVERFULL_LIMIT_PT]
    if bad_boxes:
        warnings.append(
            f"{len(bad_boxes)} line(s) overflow the text block by up to "
            f"{max(bad_boxes):.1f}pt - check the right margin"
        )
    if "LaTeX Warning: Reference" in log:
        warnings.append("the log contains unresolved references")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", required=True, type=Path, help="job output directory")
    ap.add_argument("--target", default="cv", choices=("cv", "cover-letter"))
    ap.add_argument(
        "--profile", required=True, type=Path,
        help="supplies the candidate name the PDF is named after, and the "
             "contact fields the CV build verifies",
    )
    ap.add_argument("--engine", default="tectonic")
    ap.add_argument("--max-pages", type=int, default=1)
    args = ap.parse_args()

    tex_path = args.dir / "raw" / f"{args.target}.tex"
    # Tectonic names its output after the .tex stem; the deliverable is renamed
    # once the profile has supplied the candidate's name.
    compiled_path = args.dir / f"{args.target}.pdf"
    pdf_path = compiled_path

    try:
        if not tex_path.exists():
            raise BuildError(f"{tex_path} does not exist - render it first")
        engine = find_engine(args.engine)

        profile = load_profile(args.profile)
        pdf_path = args.dir / output_pdf_name(profile, args.target)

        # A previous run's PDF must never survive into a failed build.
        discard(compiled_path, pdf_path)

        log = compile_tex(tex_path, engine, args.dir)
        if compiled_path.exists() and compiled_path != pdf_path:
            compiled_path.replace(pdf_path)
        errors, warnings = validate(
            tex_path, pdf_path, log,
            profile if args.target == "cv" else None,
            args.max_pages,
        )

    except (BuildError, ProfileError) as exc:
        discard(compiled_path, pdf_path)
        print(f"BUILD FAILED\n{exc}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        discard(compiled_path, pdf_path)
        print("BUILD FAILED\ncompilation timed out after 600s", file=sys.stderr)
        return 1

    for w in warnings:
        print(f"warning: {w}")

    if errors:
        discard(compiled_path, pdf_path)
        print(f"\nVALIDATION FAILED - {pdf_path.name} was discarded:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    size_kb = pdf_path.stat().st_size / 1024
    print(f"OK  {pdf_path} ({size_kb:.1f} KiB, text layer verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
