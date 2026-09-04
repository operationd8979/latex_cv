# raw/plan.json — the content plan

The plan lives at `<job dir>/raw/plan.json`. It is your selection, in
structured form. You choose *what* goes on the
page and *how it is worded*; the renderer supplies every hard fact from the
profile and refuses anything the profile does not support.

## What you do NOT put in the plan

Company names, role titles, employment dates, locations, institution names,
GPA, credential URLs, project tech stacks and project links. The renderer reads
all of those from `profile/` by ID. Anything you write for those fields is
ignored — which is the point: a date cannot drift.

## Shape

```json
{
  "job": {
    "company": "Northwind Digital",
    "title": "Frontend Developer (React/Next.js)",
    "job_id": "NW-114",
    "url": "https://example.test/jobs/nw-114"
  },
  "template": "ats-single-column",
  "headline": "Frontend Developer",

  "summary": {
    "source": "SUM-01",
    "text": "Frontend Developer and Information Technology graduate ..."
  },

  "sections": [
    {
      "type": "experience",
      "heading": "Experience",
      "entries": [
        {
          "source": "EXP-VILIHA",
          "bullets": [
            {
              "source": ["EXP-VILIHA-04"],
              "text": "Build production interfaces with Next.js App Router ..."
            },
            {
              "source": ["EXP-VILIHA-02", "EXP-VILIHA-03"],
              "text": "Translate Figma designs into clean code and build reusable components ..."
            }
          ]
        }
      ]
    },
    {
      "type": "projects",
      "heading": "Selected Projects",
      "entries": [
        {
          "source": "PRJ-SHOPEE-QA",
          "links": ["repo"],
          "show_tech": true,
          "bullets": [
            {
              "source": ["PRJ-SHOPEE-QA-01", "PRJ-SHOPEE-QA-02"],
              "text": "Built a Playwright framework covering 21 test cases across 4 targets."
            }
          ]
        }
      ]
    },
    {
      "type": "skills",
      "heading": "Technical Skills",
      "groups": [
        { "label": "Frontend", "items": ["React.js", "React Native"] }
      ]
    },
    { "type": "education", "heading": "Education",
      "entries": [{ "source": "EDU-HUTECH" }] },
    { "type": "certifications", "heading": "Certifications",
      "entries": [{ "source": "CERT-AZ900" }] }
  ],

  "requirements": [
    { "requirement": "React and Next.js in production",
      "status": "met", "evidence": ["EXP-VILIHA"] },
    { "requirement": "3+ years experience", "status": "partial",
      "evidence": ["EXP-VILIHA", "EXP-CHIPNOVA"],
      "note": "about 1 year professional" },
    { "requirement": "GraphQL", "status": "missing", "evidence": [] }
  ]
}
```

## Field notes

- **`sections`** render in the order you list them. Put what the posting cares
  about first. A section whose content renders empty is skipped.
- **`type`** is one of `experience`, `projects`, `skills`, `education`,
  `certifications`.
- **`bullets[].source`** is a list because you may legitimately merge two
  profile bullets into one tighter line. Cite both.
- **`bullets[].text`** is your wording. Rewrite freely for concision and the
  posting's vocabulary — but the meaning must survive unchanged, and any number
  in it must already exist in the profile.
- **`links`** picks which of the project's URLs to print: `["repo"]`,
  `["demo"]`, or both. Defaults to `["repo"]`.
- **`show_tech`** prints the project's tech stack line. Defaults to `true`.
- **`skills.groups[].label`** is yours to choose; group by what the posting
  emphasises rather than copying the profile's own categories.
- **`skills.groups[].items`** must match names in `skills.md` **exactly**.
- **`requirements`** feeds the match report. `status` is `met`, `partial`, or
  `missing`. Be honest here — this is the file that says what the CV cannot
  claim.

## What the renderer will reject

| Error | Meaning |
|---|---|
| `source 'X' does not exist in the profile` | Typo, or you invented an ID |
| `source 'X' is a project, but a experience was expected` | Wrong section type |
| `bullet cites 'X', which is not evidence under 'Y'` | Citation belongs to another entry |
| `a bullet under 'Y' has no source` | Every claim needs a citation |
| `these skills are not in skills.md` | You cannot add a skill via the plan |
| `tiered 'unverified' and must never reach a CV` | No evidence exists for it |
| `summary SUM-02 has status 'draft'` | Only approved variants may be used |
| `requirement evidence 'X' does not exist` | Bad ID in the requirements table |

Every one of these is a factual-integrity failure, not a formatting nit. Fix
the plan; never work around the check.
