---
name: gws-google-docs
description: Read and edit Google Docs using the gws CLI — insert, delete, replace text, apply formatting, manage headings, lists, tables, and images. Use when the user asks to read, edit, update, or format a Google Doc.
---

# Google Docs Editing with gws CLI

Edit Google Docs programmatically using the `gws` CLI. This skill covers reading documents, inserting/deleting/replacing text, applying formatting, and managing structure.

## Prerequisites

- `gws` CLI installed and authenticated (`gws auth login`)
- Document ID: extract from URL `https://docs.google.com/document/d/{DOCUMENT_ID}/edit`

## Important: Google Docs uses plain text formatting, NOT markdown

When writing content to Google Docs, never use markdown syntax. Use the batchUpdate API for formatting (bold, italic, headings, etc.) instead of markdown characters.

---

## 1. Reading a Document

### Get full document structure (with content indexes)

```bash
gws docs documents get --params '{"documentId": "DOC_ID"}' --format json
```

The response contains `body.content[]` — an array of structural elements. Each element has `startIndex` and `endIndex` (zero-based, UTF-16 code units). You need these indexes for precise edits.

### Parse document to find text and indexes

```bash
gws docs documents get --params '{"documentId": "DOC_ID"}' --format json 2>/dev/null | python3 -c "
import json, sys
doc = json.load(sys.stdin)
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        style = elem['paragraph']['paragraphStyle'].get('namedStyleType', '')
        text = ''
        for e in elem['paragraph']['elements']:
            if 'textRun' in e:
                text += e['textRun']['content']
        print(f'{elem[\"startIndex\"]:5d}-{elem[\"endIndex\"]:5d} [{style:15s}] {text.rstrip()[:100]}')
"
```

### Search for specific text and get its index

```bash
gws docs documents get --params '{"documentId": "DOC_ID"}' --format json 2>/dev/null | python3 -c "
import json, sys
doc = json.load(sys.stdin)
search = 'YOUR SEARCH TEXT'
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for e in elem['paragraph']['elements']:
            if 'textRun' in e and search in e['textRun'].get('content',''):
                print(f'{e[\"startIndex\"]}-{e[\"endIndex\"]}: {e[\"textRun\"][\"content\"]!r}')
"
```

---

## 2. Appending Text (Simple)

```bash
gws docs +write --document "DOC_ID" --text "Text to append at end of document"
```

This is the simplest operation — appends plain text at the end of the document body.

---

## 3. Precise Edits via batchUpdate

All precise edits use `batchUpdate`. The general pattern:

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{"requests": [ ... ]}'
```

### CRITICAL RULES for batchUpdate

1. **Indexes shift after each request.** When sending multiple requests that insert or delete content, process them in **reverse index order** (highest index first) so earlier indexes remain valid.
2. **Cannot delete the final newline** of a segment. When deleting a paragraph's text, use `endIndex - 1` to exclude the trailing `\n`.
3. **Cannot delete across structural boundaries** (e.g., across table cells). Delete within a single paragraph or structural element.
4. **Indexes are UTF-16 code units**, not characters. Emojis and some Unicode chars count as 2.
5. **Re-read the document** after edits if you need to make further index-based changes, since indexes will have shifted.
6. **Paragraph style inheritance.** New paragraphs inherit the style of the paragraph they are inserted into. When inserting text after a heading, you MUST explicitly set `NORMAL_TEXT` on the body paragraphs, otherwise they will render as headings. Always include an `updateParagraphStyle` request for every non-heading paragraph range in the inserted text.
7. **Text style inheritance.** Inserted text inherits the text style (bold, italic, underline, etc.) of the text at the insertion point. If inserting next to bold text, the new text will also be bold. Always follow an `insertText` with an `updateTextStyle` request that explicitly resets formatting on the inserted range (e.g., `"bold": false, "italic": false` with `"fields": "bold,italic"`). Check the `textStyle` of adjacent elements before inserting to know what you'll inherit.

---

## 4. Insert Text at a Specific Position

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "insertText": {
        "location": {"index": 10},
        "text": "Hello, inserted text!\n"
      }
    }]
  }'
```

- `index`: the position to insert at (text is inserted *before* this index)
- Include `\n` to create a new paragraph

### Insert at end of document

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "insertText": {
        "endOfSegmentLocation": {"segmentId": ""},
        "text": "Appended paragraph\n"
      }
    }]
  }'
```

---

## 5. Delete Text

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "deleteContentRange": {
        "range": {
          "startIndex": 10,
          "endIndex": 25
        }
      }
    }]
  }'
```

**Remember:** You cannot include the final `\n` of a segment in the delete range. To delete a full paragraph including its newline, you must include the newline of the *previous* paragraph (i.e., start from the previous element's endIndex - 1).

---

## 6. Replace All Instances of Text

The easiest way to do targeted edits — no index math required:

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "replaceAllText": {
        "containsText": {
          "text": "old text to find",
          "matchCase": true
        },
        "replaceText": "new replacement text"
      }
    }]
  }'
```

- `matchCase`: set to `false` for case-insensitive matching
- This replaces **all** occurrences. To replace only one, use delete + insert at a specific index.

---

## 7. Text Formatting (Bold, Italic, etc.)

Apply formatting to a range of text:

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "updateTextStyle": {
        "range": {
          "startIndex": 10,
          "endIndex": 25
        },
        "textStyle": {
          "bold": true
        },
        "fields": "bold"
      }
    }]
  }'
```

### Available textStyle fields

| Field | Type | Example |
|-------|------|---------|
| `bold` | boolean | `true` |
| `italic` | boolean | `true` |
| `underline` | boolean | `true` |
| `strikethrough` | boolean | `true` |
| `smallCaps` | boolean | `true` |
| `fontSize` | object | `{"magnitude": 14, "unit": "PT"}` |
| `foregroundColor` | object | `{"color": {"rgbColor": {"red": 1.0, "green": 0, "blue": 0}}}` |
| `backgroundColor` | object | (same structure as foregroundColor) |
| `link` | object | `{"url": "https://example.com"}` |
| `weightedFontFamily` | object | `{"fontFamily": "Roboto", "weight": 400}` |
| `baselineOffset` | string | `"SUPERSCRIPT"`, `"SUBSCRIPT"`, `"NONE"` |

**The `fields` parameter is a comma-separated list of which textStyle fields to update.** Use `"*"` to update all fields (resets unlisted ones to defaults). Always specify only the fields you're changing.

### Example: Bold + Red text

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "updateTextStyle": {
        "range": {"startIndex": 10, "endIndex": 25},
        "textStyle": {
          "bold": true,
          "foregroundColor": {
            "color": {"rgbColor": {"red": 1.0, "green": 0, "blue": 0}}
          }
        },
        "fields": "bold,foregroundColor"
      }
    }]
  }'
```

---

## 8. Paragraph Styling (Headings, Alignment)

### Set a heading style

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "updateParagraphStyle": {
        "range": {"startIndex": 10, "endIndex": 30},
        "paragraphStyle": {
          "namedStyleType": "HEADING_1"
        },
        "fields": "namedStyleType"
      }
    }]
  }'
```

### Named style types

- `NORMAL_TEXT`, `TITLE`, `SUBTITLE`
- `HEADING_1` through `HEADING_6`

### Set alignment

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "updateParagraphStyle": {
        "range": {"startIndex": 10, "endIndex": 30},
        "paragraphStyle": {
          "alignment": "CENTER"
        },
        "fields": "alignment"
      }
    }]
  }'
```

Alignment values: `START`, `CENTER`, `END`, `JUSTIFIED`

### Other paragraph style fields

| Field | Type | Notes |
|-------|------|-------|
| `namedStyleType` | string | Heading level |
| `alignment` | string | START, CENTER, END, JUSTIFIED |
| `lineSpacing` | number | 100 = single, 200 = double |
| `spaceAbove` | object | `{"magnitude": 12, "unit": "PT"}` |
| `spaceBelow` | object | `{"magnitude": 12, "unit": "PT"}` |
| `indentStart` | object | `{"magnitude": 36, "unit": "PT"}` |
| `indentFirstLine` | object | First-line indent |
| `direction` | string | `LEFT_TO_RIGHT`, `RIGHT_TO_LEFT` |

---

## 9. Bullet Lists

### Create bullets

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "createParagraphBullets": {
        "range": {"startIndex": 10, "endIndex": 80},
        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
      }
    }]
  }'
```

### Bullet presets

- `BULLET_DISC_CIRCLE_SQUARE` — standard unordered
- `BULLET_DIAMONDX_ARROW3D_SQUARE` — diamond/arrow/square
- `BULLET_CHECKBOX` — checkboxes
- `NUMBERED_DECIMAL_ALPHA_ROMAN` — 1. a. i.
- `NUMBERED_DECIMAL_NESTED` — 1. 1.1. 1.1.1.

### Remove bullets

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "deleteParagraphBullets": {
        "range": {"startIndex": 10, "endIndex": 80}
      }
    }]
  }'
```

---

## 10. Insert a Table

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "insertTable": {
        "rows": 3,
        "columns": 3,
        "location": {"index": 50}
      }
    }]
  }'
```

After inserting, re-read the document to get the new table cell indexes, then use `insertText` to populate cells.

---

## 11. Insert an Inline Image

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "insertInlineImage": {
        "location": {"index": 50},
        "uri": "https://example.com/image.png",
        "objectSize": {
          "width": {"magnitude": 300, "unit": "PT"},
          "height": {"magnitude": 200, "unit": "PT"}
        }
      }
    }]
  }'
```

The image must be publicly accessible via URL.

---

## 12. Common Multi-Step Patterns

### Pattern: Replace specific text with formatted text

1. Use `replaceAllText` to swap the content
2. Re-read the doc to get the new indexes of the replacement
3. Use `updateTextStyle` to format it

### Pattern: Insert a new section with heading

Send as a single batchUpdate. The insert happens first (requests are applied sequentially), so format ranges can reference the newly inserted indexes. **You MUST reset body paragraphs to NORMAL_TEXT** — otherwise they inherit the heading style:

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [
      {
        "insertText": {
          "location": {"index": 100},
          "text": "New Section Title\nSection body text here.\n"
        }
      },
      {
        "updateParagraphStyle": {
          "range": {"startIndex": 100, "endIndex": 118},
          "paragraphStyle": {"namedStyleType": "HEADING_2"},
          "fields": "namedStyleType"
        }
      },
      {
        "updateParagraphStyle": {
          "range": {"startIndex": 118, "endIndex": 142},
          "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
          "fields": "namedStyleType"
        }
      }
    ]
  }'
```

**Why the NORMAL_TEXT request is required:** Google Docs paragraphs inherit the style of the paragraph they are inserted into. Without it, "Section body text here." would render as HEADING_2.

### Pattern: Insert plain text next to formatted text

When inserting near bold/italic text, always reset the text style in the same batchUpdate:

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [
      {
        "insertText": {
          "location": {"index": 100},
          "text": "New plain text line\n"
        }
      },
      {
        "updateTextStyle": {
          "range": {"startIndex": 100, "endIndex": 120},
          "textStyle": {"bold": false, "italic": false},
          "fields": "bold,italic"
        }
      }
    ]
  }'
```

### Pattern: Safe text replacement at a specific location

When you need to replace only ONE occurrence (not all):

1. Read the doc and find the exact `startIndex` and `endIndex`
2. Delete the old text (exclude trailing `\n`: use `endIndex - 1`)
3. Insert new text at `startIndex`
4. Process delete before insert in the requests array (delete first, then insert at same position)

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [
      {
        "deleteContentRange": {
          "range": {"startIndex": 50, "endIndex": 70}
        }
      },
      {
        "insertText": {
          "location": {"index": 50},
          "text": "replacement text"
        }
      }
    ]
  }'
```

---

## 13. Person Mentions (@-tagging)

Insert clickable person chips (like @-mentions) that link to a user's profile.

### Insert a person mention

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [{
      "insertPerson": {
        "personProperties": {
          "email": "user@company.com"
        },
        "location": {"index": 50}
      }
    }]
  }'
```

**Important rules:**
- Only `email` is accepted in `personProperties`. Do NOT include `name` — it is auto-resolved from the email and the API rejects the request if `name` is provided.
- Person mentions render as blue clickable chips in the document.
- Person mentions count as 1 index unit (like an inline image).
- Person mentions cannot be inserted inside equations.
- When inserting multiple person mentions in the same cell (e.g., two assignees), insert them at the same index in reverse order so both appear.

### Insert multiple people in one cell

```bash
gws docs documents batchUpdate \
  --params '{"documentId": "DOC_ID"}' \
  --json '{
    "requests": [
      {"insertPerson": {"personProperties": {"email": "second@company.com"}, "location": {"index": 50}}},
      {"insertPerson": {"personProperties": {"email": "first@company.com"}, "location": {"index": 50}}}
    ]
  }'
```

Both insert at the same index — the second request pushes the first forward. Result: `@first @second`.

### Read person mentions from a document

Person mentions appear as `person` elements (not `textRun`) in the paragraph elements array:

```bash
gws docs documents get --params '{"documentId": "DOC_ID"}' --format json 2>/dev/null | python3 -c "
import json, sys
doc = json.load(sys.stdin)
for elem in doc['body']['content']:
    if 'paragraph' in elem:
        for e in elem['paragraph']['elements']:
            if 'person' in e:
                email = e['person']['personProperties']['email']
                print(f'{e[\"startIndex\"]}: @{email}')
"
```

### Common pitfall: duplicate mentions

If you insert a person mention into a cell that already has content at that index, you may get duplicates. Always check the cell content before inserting, and delete existing person mentions first if replacing an owner.

---

## 14. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `range cannot include the newline character at the end of the segment` | Delete range includes the final `\n` of a segment | Use `endIndex - 1` |
| `Invalid range` | Indexes out of bounds or crossing structural elements | Re-read the doc to get fresh indexes |
| `400 bad request` on delete | Trying to delete across table/section boundaries | Constrain range to a single structural element |
| `Auth error (exit code 2)` | Token expired or not authenticated | Run `gws auth login` |

## 15. Extract Document ID from URL

Document URLs follow this pattern:
```
https://docs.google.com/document/d/{DOCUMENT_ID}/edit?tab=t.0#heading=h.xyz
```

Extract just the ID between `/d/` and `/edit`.
