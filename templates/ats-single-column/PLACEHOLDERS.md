# Template contract — ats-single-column

A template owns the *design*. `render_cv.py` owns the *content*. The two meet
at the markers and macros below. A new template only has to provide these; it
is otherwise free.

## Markers

Each must appear **alone on its own line**, exactly once per file. The renderer
matches whole lines, so a marker mentioned inside a `%` comment is treated as
documentation and left alone.

| File | Markers |
|---|---|
| `template.tex` | `%%PDFMETA%%` (preamble), `%%BODY%%` (inside `document`) |
| `cover-letter.tex` | `%%PDFMETA%%`, `%%HEADER%%`, `%%BODY%%` |

## Macros the CV body calls

| Macro | Arguments | Used for |
|---|---|---|
| `\cvname` | name | Candidate name |
| `\cvheadline` | headline | Target role under the name |
| `\cvcontact` | inline list | Email, phone, links — no home address |
| `\cvsection` | title | Section heading |
| `\cvsummary` | paragraph | Summary text |
| `\cvitem` | headline, metadata | Any dated entry: job, project, degree |
| `\cvitemplain` | headline | An entry with no metadata line |
| `\cvsubline` | text | One continuation line under an entry headline |
| `\cvmeta` | text | Tech stack line under a project |
| `\cvlinks` | labelled link | One project URL, e.g. `Demo: …` — emitted once per link |
| `cvbullets` | *(environment)* | Achievement bullets |
| `\cvskill` | label, value | One skill group row, or one language row |
| `\cvplain` | text | Single-line row (certifications) |

## Cover-letter macros

`\clname{name}`, `\clcontact{inline list}`, `\cldate{date}`.

## Design constraints a template must respect

**Keep an entry's metadata on the headline's own line.** Dates and location sit
at the right margin, and that is safe only because `\cvitem` puts them in the
same line box as the headline — one paragraph, not a second column. Build a
real column out of them (a minipage, a `tabular`, `paracol`) and PDF text
extraction emits it as a separate block, which detaches a date from its job and
reattaches it to a different one.

**At most one `\cvsubline` under a `\cvitem`.** Same failure, reached from the
other side, and it is measured rather than assumed. With the metadata at the
right margin, two or more flush-left lines beneath the headline give poppler a
tall left block beside a lone right-hand cell; it reads that as two columns,
emits the whole left column first, and the graduation date lands under the next
section heading. One continuation line extracts in order; two do not. Anything
extra goes on that same line, not on another one.

`build_and_validate.py` re-checks both on every build, and fails the build if
an entry's metadata drifts past a section heading **or** past the next entry.

**Depend only on Tectonic's bundle.** The font is TeX Gyre Heros, loaded by
file name through `fontspec`, so no system font install is required. Do not
reference a font by family name that only exists on one machine.

**Stay ATS-safe.** Single column, real text, standard section names. No images,
no multi-column tables, no progress bars, nothing that carries meaning by
position alone.

**Ragged right, not justified.** The column is narrow enough that justification
forces mid-word hyphenation, which can split a keyword an ATS is scanning for.
