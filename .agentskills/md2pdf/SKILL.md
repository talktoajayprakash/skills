---
name: md2pdf
description: Convert a Markdown file into a clean, print-ready PDF. Use when the user asks to render a `.md` to PDF, generate a resume/report PDF from markdown, or produce a polished printable document from a markdown source. Wraps pandoc + Chrome headless and ships with a sensible default stylesheet you can swap out.
---

Convert a Markdown file into a polished PDF using pandoc + Chrome headless. The bundled `md2pdf.sh` is non-interactive and safe to call directly. The default `style.css` gives a clean, professional look suitable for resumes, briefs, and short reports.

## Usage

The skill ships two files in this directory:

- `md2pdf.sh` — the conversion script
- `style.css` — the default stylesheet (Letter, ~0.55in margins, Helvetica/Inter)

```bash
SKILL_DIR="$(dirname "$(realpath "$0")")"   # or hardcode the absolute path

# Default style, output next to input
"$SKILL_DIR/md2pdf.sh" path/to/input.md

# Custom output path
"$SKILL_DIR/md2pdf.sh" input.md output.pdf

# Custom stylesheet
"$SKILL_DIR/md2pdf.sh" input.md output.pdf --style ./custom.css
```

If `OUTPUT.pdf` is omitted, the script writes alongside the input as `<basename>.pdf`.

## Dependencies

Required (install once if missing):

- `pandoc` — `brew install pandoc`
- Google Chrome (or Chromium) — used headless to render HTML to PDF
  - The script auto-detects `/Applications/Google Chrome.app`, `chromium`, or `google-chrome`

If a dependency is missing, the script exits with a clear error pointing to the install command.

## Markdown conventions the default stylesheet expects

The default `style.css` is tuned for documents structured like:

- `# Title` — name / document title (rendered uppercase, large)
- The first paragraph after `# Title` is treated as a contact / metadata line (smaller, muted)
- `## Section` — major section heading (uppercase, underlined)
- `### Subsection` — subsection / job title (bold)
- The first paragraph after `### Subsection` renders as a metadata line (e.g. `Company | Location | Dates`)
- Lists (`- ...`) for bullet points

Single newlines become `<br>` (the script enables `markdown+hard_line_breaks` in pandoc), so address lines, contact lines, and date lines on consecutive lines stay on separate lines without needing trailing `  `.

## Customising the look

To adjust styling, copy `style.css` somewhere editable, tweak it, and pass `--style /path/to/edited.css`.

Common tweaks:

- **Page size / margins** — change `@page { size: ...; margin: ...; }`
- **Body font / size** — `body { font-family: ...; font-size: ...; }`
- **Section rule colour** — `h2 { border-bottom: ... }`
- **Link colour** — `a { color: ... }`

## How it works

1. `pandoc` converts the Markdown to an HTML fragment with `markdown+hard_line_breaks`.
2. The fragment is wrapped in a minimal HTML document with the stylesheet inlined.
3. Chrome headless prints the HTML to PDF (`--headless --print-to-pdf --no-pdf-header-footer`).

Chrome headless gives faithful CSS rendering and works reliably on macOS without LaTeX or native library dependencies (unlike weasyprint, which often breaks on Mac due to Cairo/Pango linking issues).

## Troubleshooting

- **Dates/addresses collapsing to one line** — make sure the stylesheet you pass doesn't override the `markdown+hard_line_breaks` behaviour; you can also force breaks by ending lines with two trailing spaces.
- **Awkward page breaks splitting a job/section** — the default CSS sets `page-break-after: avoid` on h3 and `page-break-inside: avoid` on list items. For tighter control, wrap the block in a `<div style="page-break-inside: avoid">…</div>`.
- **PDF is one giant page** — Chrome respects `@page { size: ... }`; verify the stylesheet declares it.
- **Unicode / emoji renders as boxes** — Chrome should render system fonts fine. If specific glyphs are missing, switch the body `font-family` to one installed on the system.
