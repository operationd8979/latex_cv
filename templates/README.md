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

All three print addresses in full — a project's `Demo:` and `GitHub:` lines and
a certification's `Verify:` line show the whole URL as visible text, not a
one-word label over a hidden link, so a printed copy stays as useful as the
clickable one. Projects are dated `Start: – End:` from the profile, like every
other entry. Both cost vertical space: a plan that used to fit a page may need
one bullet fewer, and `build_and_validate.py` is what tells you.
