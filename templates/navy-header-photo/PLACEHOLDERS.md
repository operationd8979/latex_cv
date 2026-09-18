# Template contract — navy-header-photo

This is a readable, one-column A4 CV with a flat navy identity banner, an
optional circular portrait, uppercase blue section headings, and short orange
underlines. It follows the visual style of the supplied reference while keeping
all text selectable and links clickable.

The renderer fills sections in this order: Summary, Education, Certification,
Core Skills, Experience, and Projects. It uses `%%HEADER%%`, `%%SUMMARY%%`,
`%%EDUCATION%%`, `%%CERTIFICATIONS%%`, `%%SKILLS%%`, `%%EXPERIENCE%%`,
`%%PROJECTS%%`, `%%LANGUAGES%%`, and `%%BODY%%`. Empty sections are omitted.
Extra section types are appended at `%%BODY%%`.

If the selected profile's `personal.md` contains a valid `Photo` value, the renderer copies
that image beside `cv.tex` and uses it in the banner. If the photo field is
missing, the same banner renders cleanly without an empty frame.

Build the included example from the repository root:

```powershell
python scripts/render_cv.py --plan templates/navy-header-photo/example-plan.json --profile profile/hang --template-root templates --out applications/navy-header-photo-preview
python scripts/build_and_validate.py --dir applications/navy-header-photo-preview --profile profile/hang
```
