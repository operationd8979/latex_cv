# Template contract — clean-modern-single-column

This template is a polished, ATS-friendly, single-column design based on the
structure of `CV_NguyenThiDieuHang_Frontend.docx`.

It uses the standard renderer contract:

- `template.tex`: `%%PDFMETA%%`, `%%BODY%%`, `%%SUMMARY%%`, `%%EDUCATION%%`,
  `%%SKILLS%%`, `%%CERTIFICATIONS%%`, `%%LANGUAGES%%`, `%%EXPERIENCE%%`, and
  `%%PROJECTS%%`
- `cover-letter.tex`: `%%PDFMETA%%`, `%%HEADER%%`, `%%BODY%%`
- CV macros: `\cvname`, `\cvheadline`, `\cvcontact`, `\cvsection`,
  `\cvsummary`, `\cvcontactsplit`, `\cvitem`, `\cvitemplain`, `\cvsubline`, `\cvmeta`,
  `\cvlinks`, `cvbullets`, `\cvskill`, `\cvskilllabel`, `\cvskillitem`,
  and `\cvplain`

The design contains no photo, table, text box, icon-only contact field, or
multi-column content. It uses black for primary text and headings, gray for
secondary text and rules, and no accent color. The centered identity header is
followed by the fixed source-document order: Summary, Education, Technical
Skills, Certifications, Languages, Experience, and Projects. Entry metadata
is placed immediately below its headline to preserve reading order for long
company names in extracted PDF text.

Use it in a plan with:

```json
"template": "clean-modern-single-column"
```

## Content limits

At most two pages, at least two distinct factual projects, and readable 12pt body
text. Use concise relevant bullets. Links display short clickable labels with
full destination URLs preserved. Build with `--max-pages 2`.
