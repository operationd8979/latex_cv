# Profile — data contract

This directory is the **single source of truth** about the candidate. Any CV or
cover letter generated from this workspace may only contain claims traceable to
an entry here.

Everything is Markdown so it stays editable by hand. The only rule that makes it
machine-usable is the **stable ID** on every fact.

## ID scheme

| Prefix  | Meaning         | Example              |
|---------|-----------------|----------------------|
| `EXP-`  | Employment      | `EXP-VILIHA`         |
| `PRJ-`  | Project         | `PRJ-SHOPEE-QA`      |
| `EDU-`  | Education       | `EDU-HUTECH`         |
| `CERT-` | Certification   | `CERT-AZ900`         |
| `LANG-` | Spoken language | `LANG-EN`            |
| `SUM-`  | Summary variant | `SUM-01`             |

Individual bullets are numbered under their entry: `EXP-VILIHA-01`,
`PRJ-ESME-03`. **IDs are permanent.** Never renumber or reuse an ID — reports
from past applications reference them. To retire a bullet, delete the line and
leave the number unused.

Skills are keyed by their exact name (unique within `skills.md`), not by ID.

## Field conventions

- **Dates** use `YYYY-MM` in separate `Start:` / `End:` fields. `End: present`
  for anything ongoing. No free-text dates — the renderer formats them. This
  covers `projects.md` as well as `experience.md`: a project used to carry a
  single `Month:`, which says when it was touched but not how long it ran, and
  that is what a reader weighs it by. `parse_profile.py --check` fails a
  project without both. A legacy `Month:`/`Year:` still renders, as one date.
- **URLs** are absolute and include `https://`. Never store a bare domain.
  The CV prints them in full, so what is stored here is what a person reads off
  a printed page and types into a browser — a repo URL that only works through
  a GitHub rename redirect should be replaced with the name it redirects to.
- **Tech** lists concrete, nameable technologies only, comma-separated.
- **Metrics** holds quantified outcomes. `none recorded` is an honest value;
  an invented number is not.
- `<!-- ... -->` comments are notes to the human owner. They are never rendered
  into a CV and never treated as facts.
- **Photo** in `personal.md` is a filename relative to this directory. Only a
  template that declares a `\cvphoto` macro uses it, so `ats-single-column`
  stays image-free while `two-column-photo` shows it. The renderer copies the
  file into the job directory rather than linking to it.

## Skill proficiency tiers

Every skill in `skills.md` carries exactly one tier and an evidence list:

| Tier           | Means                                                              |
|----------------|--------------------------------------------------------------------|
| `professional` | Used to deliver paid/production work; backed by an `EXP-` entry     |
| `working`      | Used hands-on in a real project or part of a role                   |
| `familiar`     | Coursework, certification, or a small hobby project only            |
| `unverified`   | Listed, but **no supporting evidence exists in this profile**       |

**An `unverified` skill must never appear on a generated CV.** It exists so the
gap is visible, not so it can be claimed. Upgrade the tier only by adding real
evidence (an `EXP-`/`PRJ-` entry that demonstrates it).

## No duplication

Each fact has exactly one home. The portfolio URL lives in `personal.md`, not
`projects.md`. Duplicated facts drift and produce contradictory CVs.

Spoken languages are split along that line rather than duplicated:
`certifications.md` records *which credential* proves a level (CEFR B1, and the
URL that verifies it), `languages.md` records *the level you work at*, which is
what the CV's Languages section prints. A `languages.md` entry names its
credential in `Certification:` instead of restating it. `skills.md` holds
neither — it is for technical skills.

`languages.md` is optional. A profile without it simply renders no Languages
section.

## Open items — need the owner's input

These are gaps that block a stronger CV. A generator may not fill them in.

1. **Metrics for the two employers are still empty.** `projects.md` now carries
   real figures measured from the public repositories, but `EXP-VILIHA` and
   `EXP-CHIPNOVA` sit on private code that only you can describe. Each entry has
   a short TODO with the specific questions — answering them is the single
   highest-value improvement left.
2. **Employment gap 2026-04 → 2026-06** between `EXP-CHIPNOVA` and
   `EXP-VILIHA`. Decide how to account for it factually.
3. **Certification dates missing** for `CERT-AZ900` and `CERT-ENG-B1`; issuer
   and credential ID missing for `CERT-ENG-B1`. Without a credential URL there
   is no address for the CV's `Verify:` line to print, so that certification
   appears as a bare claim a reader cannot check.
4. **`unverified` skills**: Angular, .NET, Java, Bitbucket, Jira, GitHub Actions,
   GitHub Copilot, Codex. Either add evidence or accept that they are excluded
   from every generated CV.
5. **GitHub Actions specifically.** All five public repositories were checked on
   2026-09-04 and none contains `.github/workflows/` on any branch, so the CI
   claim was downgraded. `PRJ-SHOPEE-QA` is CI-*ready* (retries, workers, JUnit
   reporter) but has no pipeline. Committing one workflow would restore the
   claim honestly and is worth doing.
6. **`preferences.md` is mostly unfilled** — see the TODO comments there.
7. **Draft summary variants** `SUM-02` and `SUM-03` need approval before use.
