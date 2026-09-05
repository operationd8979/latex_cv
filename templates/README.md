# CV templates

Select a template with the `template` field in a content plan, then render it
with `scripts/render_cv.py`. The workspace default is `ats-single-column`.

| Template | Layout |
|---|---|
| `ats-single-column` | Plain single column, without a photo |
| `two-column-photo` | Full-width identity/photo header, sidebar and main column |
| `blue-banner-photo` | Blue banner and round photo; Summary → Education → Skill → Certification → Experience → Project |

The [blue banner example](blue-banner-photo/example-plan.json) is ready to render
against `profile/`. It includes grouped skills and project role, tech stack,
GitHub and Demo links. See its [template contract](blue-banner-photo/PLACEHOLDERS.md)
for build commands and behavior when optional profile fields are missing.
