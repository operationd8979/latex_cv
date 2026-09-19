# CV templates

Select a template with the `template` field in a content plan, then render it
with `scripts/render_cv.py`. The workspace default is `navy-header-photo`.

| Template | Layout |
|---|---|
| `ats-single-column` | Plain single column, without a photo |
| `clean-modern-single-column` | Polished monochrome single column with centered header, without a photo |
| `two-column-photo` | Full-width identity/photo header, sidebar and main column |
| `blue-banner-photo` | Blue banner and round photo; Summary → Education → Skill → Certification → Experience → Project |
| `navy-header-photo` | Reference-inspired single column with a flat navy header, round photo and short orange section accents |

The [blue banner example](blue-banner-photo/example-plan.json) is ready to render
against the selected candidate profile. It includes grouped skills and project role, tech stack,
GitHub and Demo links. See its [template contract](blue-banner-photo/PLACEHOLDERS.md)
for build commands and behavior when optional profile fields are missing.

All templates show short clickable labels: LinkedIn, GitHub and Portfolio in
contacts; Demo and GitHub on one project line; Verify Credential for
certifications. Complete destination URLs, including query parameters, remain
in the PDF hyperlinks. A Demo recorded in the profile is always displayed,
even if an older plan lists only `"links": ["repo"]` or an empty list. Missing
demos are never invented. Project dates still come from the factual profile.

All CV templates use 12pt body text, approximately 11pt supporting details
(including contact information, dates and links), and 1.08 line spacing. Keep
at least two distinct factual projects within a maximum of two pages. Select
concise relevant evidence; never shrink typography. Build validation rejects
PDFs over two pages. Revise the content plan and build again.
