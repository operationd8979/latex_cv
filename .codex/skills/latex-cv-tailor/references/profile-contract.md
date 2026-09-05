# How `profile/` is structured and what is enforced

`profile/README.md` is the authoritative contract and is written for the person
who edits the files. This page is the version you need when generating a CV.

## Files

| File | Holds | Addressable by |
|---|---|---|
| `personal.md` | Name, contact, links | field name |
| `preferences.md` | Target roles, work model, exclusions | field name |
| `summary.md` | Pre-approved summary variants | `SUM-01`, ... |
| `experience.md` | Employment | `EXP-<ORG>`, bullets `EXP-<ORG>-01` |
| `projects.md` | Projects | `PRJ-<NAME>`, bullets `PRJ-<NAME>-01` |
| `education.md` | Degrees | `EDU-<INST>` |
| `certifications.md` | Certifications | `CERT-<NAME>` |
| `skills.md` | Skills with tier + evidence | exact skill name |

IDs are permanent. A retired bullet leaves its number unused rather than
renumbering, because past match reports reference it.

## Reading the files

- Dates are `YYYY-MM` in separate `Start:` / `End:` fields; `End: present` for
  ongoing. The renderer formats them — never format a date yourself.
- URLs are absolute. Do not add or strip a scheme.
- `Metrics:` may say `none recorded`. That is an honest value; treat it as
  absent, and never fill the gap with a plausible-sounding number.
- **HTML comments are notes to the owner, not facts.** They often contain
  TODOs, open questions and verification notes. The parser strips them before
  you ever see the data. Never quote one on a CV.

## Skill tiers

| Tier | Means | May appear on a CV |
|---|---|---|
| `professional` | Delivered paid/production work with it | yes |
| `working` | Used hands-on in a real project or part of a role | yes |
| `familiar` | Coursework, certification, or a small hobby project | yes, described honestly |
| `unverified` | Listed, but no evidence exists in the profile | **never** |

`unverified` is not a weak yes. It exists so a gap stays visible. When a
posting demands an `unverified` skill, the answer is to record it as a missing
requirement in the match report — not to quietly include it, and not to
substitute a different unsupported skill that sounds adjacent.

A `familiar` skill may be listed, but must not be described as expertise. A
certification is evidence of familiarity, not of production experience.

## Summary variants

Only a variant marked `status: approved` may be used. `draft` variants are
proposals awaiting the owner's sign-off; the renderer refuses them. Pick the
variant closest to the posting and trim it if needed — do not compose a new
summary out of fragments.

## What the renderer enforces for you

You cannot override these from the plan, so you do not need to police them:

- Company, role, dates, location, institution, GPA, credential URL, project
  tech and project links all come from the profile verbatim.
- Every cited ID must exist, and a bullet may only cite evidence from its own
  entry.
- Every listed skill must exist in `skills.md` and must not be `unverified`.
- The summary must come from an approved variant.

What the renderer **cannot** check is whether your rewording preserved the
meaning of the evidence you cited. That part is yours. "Wrote end-to-end tests
with Playwright" may become "Wrote Playwright end-to-end tests covering
critical flows" only if the profile says something about critical flows — the
citation must justify the whole sentence, not just its first half.

## Validating the profile

```text
python scripts/parse_profile.py --profile ./profile --check
```

Reports duplicate IDs, malformed dates, unknown tiers, evidence that resolves
to nothing, tiers that claim evidence they do not have, entries with no
bullets, and a missing approved summary. If it fails, report the violations to
the user — the profile is theirs to fix, never yours.
