# Template contract — blue-banner-photo

A single-column CV based on the supplied demo: gradient blue banner, white
identity/contact text, circular portrait on the right, blue uppercase section
headings, orange rules, and pale blue skill group labels.

## Section order and content

The template fixes the order **Summary → Education → Skill → Certification →
Experience → Project**, regardless of the order of `sections` in the plan.
`example-plan.json` includes all six sections, grouped skills, both certifications,
all three employment entries, and two projects with role, date, tech stack,
GitHub, Demo, and evidence-backed descriptions.

Only selected plan entries are rendered, just as with the other templates.
The template does not invent or automatically select profile content. An empty
section is omitted. Additional sections, such as Languages, follow Project.
Headings may still be customized through the plan's `heading` field.

Education retains the degree, institution, graduation date, location, GPA and
classification. Certifications retain issuer/date when known and the credential
verification link. Jobs retain title, employer, dates, location, employment type
when recorded, and selected bullets.

Projects always show both recorded links in this template, including when an
older plan selects only `repo`. The clickable labels are **GitHub** and **Demo**;
the complete original URLs are stored in the PDF links. Role appears on its own
labelled line. `show_tech` still controls the tech stack. Missing links or roles
are omitted, with no placeholder or fabricated value. In the current profile,
Esme Chatbot has no demo URL; the example uses BrowserMind and Shopee UI Test
Automation, which each have both destinations.

## Markers

Each marker must appear alone on its own line exactly once.

| Marker | Content |
|---|---|
| `%%PDFMETA%%` | PDF metadata in the preamble |
| `%%HEADER%%` | Banner identity block, with or without the profile photo |
| `%%SUMMARY%%` | Approved summary selected by the plan |
| `%%EDUCATION%%` | Education sections |
| `%%SKILLS%%` | Grouped skill sections |
| `%%CERTIFICATIONS%%` | Certification sections |
| `%%EXPERIENCE%%` | Employment sections |
| `%%PROJECTS%%` | Project sections |
| `%%BODY%%` | Any additional sections, in their plan order |

Named section slots are for single-column templates; they cannot be combined
with `%%SIDEBAR%%`. Legacy templates retain their existing rendering behavior.

## Macros

The template provides the shared CV macro contract, including `\cvsubline` and
`\cvsubnote`. Its `\cvphoto` macro enables staging the photo alongside `cv.tex`.
`\cvheaderwithphoto` and `\cvheaderplain` both render the blue banner. Portrait
cropping is performed by LaTeX without changing the source image.

The optional `\cvlocation{text}` macro moves a job's location and employment
type below its headline, leaving the date next to the title. The optional
`\cvprojectrole{role}` macro opts into labelled project roles and both links.
These options are detected by the shared renderer for named-section templates.

Fonts and LaTeX packages come from the Tectonic bundle. Text remains selectable,
and the regular build validator checks section visibility and metadata order.
Longer plans can flow onto another page; the one-page limit remains enforced by
the build command, so adjust selected content when needed.

## Build the example

From the workspace root:

```powershell
python scripts/render_cv.py --plan templates/blue-banner-photo/example-plan.json --profile profile --template-root templates --out applications/blue-banner-photo-preview
python scripts/build_and_validate.py --dir applications/blue-banner-photo-preview --profile profile --max-pages 1
```

The example references this workspace's profile IDs. For another profile,
replace its summary, entry and evidence IDs and skill names with that profile's
facts. Choose a fresh output directory to keep an existing application intact.

The matching `cover-letter.tex` supports the shared cover-letter renderer. A
cover letter is generated only when requested.
