# What the build checks, and what to do when it fails

```bash
python scripts/build_and_validate.py \
  --dir <job dir> --profile ./profile --max-pages 1
python scripts/build_and_validate.py \
  --dir <job dir> --target cover-letter --max-pages 1
```

Compilation runs Tectonic with **shell escape off** (its default — never turn
it on). The `.log` is parsed and then deleted, so no build artifacts survive
into the deliverable.

**A failed build deletes its PDF.** This is deliberate: a leftover PDF from an
earlier run is indistinguishable from a fresh success, and would be reported as
one. Never claim a CV is ready without a passing run.

## Checks

| Check | Fails when |
|---|---|
| Engine present | Tectonic is not on PATH |
| Compilation | Tectonic exits non-zero; the last 15 log lines are shown |
| PDF exists | No file, or zero bytes |
| Text layer | Under 200 extractable characters — the PDF is not ATS-readable |
| Page count | More pages than `--max-pages` |
| Placeholders | A `%%MARKER%%` survived into the rendered text |
| Section headings | A heading in `cv.tex` is unreadable in the PDF |
| Contact details | Name, email or phone unreadable in the text layer |
| Reading order | An entry's dates or location drifted past a section heading |
| Missing glyphs | The font lacks a character the document uses |
| Overfull boxes | *(warning)* a line exceeds the text block by more than 5pt |

Matching ignores spacing and punctuation, comparing letters and digits only —
the LaTeX source and the extracted text disagree about both, and comparing them
naively makes a check pass without testing anything.

## Fixing each failure

**`is N pages; the limit is 1`** — cut content and re-render. Drop the weakest
bullet, merge two related ones, or drop the least relevant project. Do **not**
shrink margins, reduce the font, or raise `--max-pages` to force a fit: the
template's spacing is already tuned, and a cramped CV reads worse than a
shorter one.

**`entry '...': its 'Jan 2025' is separated from it by the 'Education'
heading`** — this is the right-aligned-dates regression. PDF text extraction
has pulled a right-hand column into its own block, so an ATS would attach that
date to the wrong entry. It means the template has regressed to `\hfill`
layout. Report it; do not disable the check.

**`entry '...' is not readable in the PDF`** — the entry compiled but its text
cannot be extracted. Usually a font or encoding problem. Report it.

**`font is missing glyphs for: ...`** — the text contains a character TeX Gyre
Heros lacks. Replace the character (a fancy dash, an emoji, a CJK character) in
your plan text.

**`unresolved template placeholders`** — the template has a marker the renderer
does not supply, or a marker is not alone on its line. See
`templates/<name>/PLACEHOLDERS.md`.

**`... is not readable in the PDF text layer` (contact)** — the header did not
render. Check `personal.md` has the field, then report.

**`Tectonic is not installed`** — the message carries three install commands.
Relay them to the user; do not attempt a different engine.

**Warning: `N line(s) overflow the text block`** — a long unbreakable string
(usually a URL) is running into the margin. Shorten what is printed, or drop
that link. A warning does not fail the build, but it does mean the page has a
visible defect, so mention it.

## Verifying by eye

`pdftotext -enc UTF-8 <dir>/<FullName>_CV.pdf -` shows exactly what an ATS
reads. Check
that each job's dates sit next to that job, that section headings are intact,
and that no placeholder text survived. This is the cheapest way to catch a
layout problem that compiles cleanly.
