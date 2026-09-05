# Template contract — two-column-photo

A full-width identity band (photo, name, headline, contacts), then a narrow
sidebar beside a wide main column.

## When to use this instead of ats-single-column

Use it when a **person** reads the CV first: a small company, a direct email, a
referral, or a recruiter in Vietnam where an ID photo is expected.

Use `ats-single-column` when the CV goes through an **applicant portal**. Two
columns and a photo are measurably harder on automated parsers, and no amount
of care in this template removes that.

## Markers

Each must appear **alone on its own line**, exactly once.

| Marker | Where | Holds |
|---|---|---|
| `%%PDFMETA%%` | preamble | `\hypersetup` |
| `%%HEADER%%` | document | photo, name, headline, contacts |
| `%%SIDEBAR%%` | left column | skills, education, languages |
| `%%BODY%%` | right column | summary, experience, projects, certifications |

Declaring `%%SIDEBAR%%` is what tells `render_cv.py` to split sections into two
columns. Declaring `%%HEADER%%` moves identity out of the sidebar. Defining a
`\cvphoto` macro is what tells it to stage the profile photo.

## Macros

Everything in `ats-single-column`, plus:

| Macro | Arguments | Used for |
|---|---|---|
| `\cvphoto` | image file | The photo; its presence enables photo staging |
| `\cvheaderwithphoto` | image file, text block | Identity band with a photo |
| `\cvheaderplain` | text block | Identity band when no photo is set |
| `\cvcontactline` | one detail | Stacked contact, for sidebar-identity templates |
| `\cvskilllabel` | group label | Narrow-column skills: the group heading |
| `\cvskillitem` | one skill | Narrow-column skills: one item per line |

## Four findings that shaped this template

Each was measured on a rendered PDF, not assumed.

**The name must not sit in the narrow column.** At sidebar width it wraps, and
text extraction reported it as `Nguyen Thi Hang` … `Dieu` — pieces out of
order. A parser reading that gets the candidate's name wrong, which is the one
field it cannot afford to get wrong. Hence the full-width header.

**Skills stack, one per line.** As a comma-separated run in a narrow column,
`Tailwind CSS, shadcn/ui` wrapped mid-phrase and extracted as `Tailwind` /
`CSS,` in separate blocks, so a search for "Tailwind CSS" found nothing. One
item per line keeps each keyword whole.

**paracol, not two minipages.** A minipage cannot break across pages, so
content one line too long shunted *both* columns onto page two and left page
one holding only the header. paracol fills page one and breaks normally. It
also fixed a fragmentation problem the minipage version had, where sidebar
entries extracted a word or two per line.

**Certifications belong in the main column.** They used to sit in the sidebar,
and stopped fitting there the moment a credential row began printing its
verification address in full: the Azure URL is 118 characters, which is six
lines at 5.9cm, and the sidebar is the taller of the two columns, so those
lines decided where the page broke. In the main column the same row takes two.
A plan that wants the old placement can still ask for it with
`"column": "side"`.

## Capacity

The main column is about 64% of the text width, so it holds roughly 15% less
than `ats-single-column` at the same page count. A plan tuned for the
single-column template usually needs one bullet removed here.

Spelling URLs out costs height that a `Demo` label did not — one extra line per
project, plus one for a credential URL. `\cvlinks` and `\cvplain` are set at
`\footnotesize` to pay part of that back; the rest comes out of the plan.
