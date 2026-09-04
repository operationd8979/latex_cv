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
| `\cvcontact` | inline list | Email, phone, location, links |
| `\cvsection` | title | Section heading |
| `\cvsummary` | paragraph | Summary text |
| `\cvitem` | headline, metadata | Any dated entry: job, project, degree |
| `\cvitemplain` | headline | An entry with no metadata line |
| `\cvmeta` | text | Tech stack line under a project |
| `\cvlinks` | inline list | Demo/repo links under a project |
| `cvbullets` | *(environment)* | Achievement bullets |
| `\cvskill` | label, items | One skill group row |
| `\cvplain` | text | Single-line row (certifications) |

## Cover-letter macros

`\clname{name}`, `\clcontact{inline list}`, `\cldate{date}`.

## Design constraints a template must respect

**Lay entries out linearly.** Right-aligned dates via `\hfill` look tidier, but
PDF text extraction pulls the right-hand column into a separate block — which
detaches a date from its job and can reattach it to a different one. This was
measured on this template, not assumed, and `build_and_validate.py` now fails a
build where it happens. Put metadata on its own flush-left line.

**Depend only on Tectonic's bundle.** The font is TeX Gyre Heros, loaded by
file name through `fontspec`, so no system font install is required. Do not
reference a font by family name that only exists on one machine.

**Stay ATS-safe.** Single column, real text, standard section names. No images,
no multi-column tables, no progress bars, nothing that carries meaning by
position alone.

**Ragged right, not justified.** The column is narrow enough that justification
forces mid-word hyphenation, which can split a keyword an ATS is scanning for.
