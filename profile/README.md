# Candidate profiles

Each candidate has an independent directory under `profile/<name>/`.

- `hang/`: the existing profile, moved without changing its contents or IDs.
- `dung/`: a draft scaffold to complete before generating a CV.

`cv.config.yaml` sets `profile_root: ./profile/hang` as the default. An explicit
profile selection overrides that default for the entire generation batch.
For example, pass `--profile ./profile/dung` to the parser, renderer and builder.
Never combine evidence from different candidate directories.

Each directory contains `personal.md`, `preferences.md`, `summary.md`,
`skills.md`, `experience.md`, `projects.md`, `education.md`, `certifications.md`
and optionally `languages.md` and a photo. See `hang/README.md` for the data
format, stable IDs and evidence tiers; its candidate-specific notes apply only
to Hang. The skill's `references/profile-contract.md` also describes the format.

To add a candidate, create a new directory with those files and validate it:

```text
python scripts/parse_profile.py --profile ./profile/<name> --check
```

The seek_job UI discovers each directory containing `personal.md`. Choose the
candidate separately when creating a CV batch; search presets do not select a
candidate. Approval belongs to the job in the search run.
