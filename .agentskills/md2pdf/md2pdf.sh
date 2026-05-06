#!/usr/bin/env bash
# Convert a Markdown file to a clean PDF via pandoc + Chrome headless.
# Usage: md2pdf.sh INPUT.md [OUTPUT.pdf] [--style PATH/TO/style.css]

set -euo pipefail

INPUT=""
OUTPUT=""
STYLE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --style)
      STYLE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,4p' "$0"; exit 0 ;;
    *)
      if [[ -z "$INPUT" ]]; then INPUT="$1"
      elif [[ -z "$OUTPUT" ]]; then OUTPUT="$1"
      else echo "Unexpected arg: $1" >&2; exit 2; fi
      shift ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "Usage: md2pdf.sh INPUT.md [OUTPUT.pdf] [--style style.css]" >&2
  exit 2
fi

if [[ ! -f "$INPUT" ]]; then
  echo "Input not found: $INPUT" >&2
  exit 1
fi

OUTPUT="${OUTPUT:-${INPUT%.md}.pdf}"

# Resolve Chrome binary.
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)"; do
  if [[ -n "$c" && -x "$c" ]]; then CHROME="$c"; break; fi
done
if [[ -z "$CHROME" ]]; then
  echo "Chrome not found. Install Google Chrome or set CHROME env var to a chromium binary." >&2
  exit 1
fi

if ! command -v pandoc >/dev/null; then
  echo "pandoc not found. Install with: brew install pandoc" >&2
  exit 1
fi

# Default CSS lives next to this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STYLE="${STYLE:-$SCRIPT_DIR/style.css}"
if [[ ! -f "$STYLE" ]]; then
  echo "Style sheet not found: $STYLE" >&2
  exit 1
fi

WORK="$(mktemp -d -t md2pdf)"
trap 'rm -rf "$WORK"' EXIT

# hard_line_breaks: single \n becomes <br> — preserves address/date lines.
pandoc "$INPUT" \
  -f markdown+hard_line_breaks \
  -t html \
  -o "$WORK/body.html"

CSS_CONTENT="$(cat "$STYLE")"
{
  echo '<!DOCTYPE html>'
  echo '<html><head><meta charset="utf-8">'
  echo "<title>$(basename "$INPUT" .md)</title>"
  echo '<style>'
  echo "$CSS_CONTENT"
  echo '</style></head><body>'
  cat "$WORK/body.html"
  echo '</body></html>'
} > "$WORK/page.html"

"$CHROME" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUTPUT" \
  "file://$WORK/page.html" 2>/dev/null

echo "Wrote $OUTPUT"
