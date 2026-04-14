---
name: gmail
description: Send, draft, read, reply, forward, and triage Gmail emails using the gws CLI. Use when the user asks to do anything with email.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Gmail — Send, Draft, Read & Manage Emails

This skill uses the `gws` CLI (`/opt/homebrew/bin/gws`) to interact with Gmail. The CLI handles OAuth, MIME encoding, and base64 automatically.

## When to trigger

Activate this skill whenever the user asks to:
- Send an email
- Draft an email
- Read an email or check inbox
- Reply to or forward an email
- Triage/summarize unread emails
- Search for emails
- Manage drafts (list, update, delete, send)

## Quick Reference

### Send an email

```bash
gws gmail +send --to "recipient@example.com" --subject "Subject" --body "Body text"
```

Options:
- `--cc`, `--bcc` — additional recipients (comma-separated)
- `--from` — send-as alias
- `-a` / `--attach <PATH>` — attach file (repeatable, 25MB total limit)
- `--html` — treat body as HTML (use fragment tags like `<p>`, `<b>`, `<a>`, no wrapper needed)

### Create a draft

Drafts require building a `.eml` file and uploading it:

```bash
# 1. Write the .eml file (MUST be in current working directory — gws blocks paths outside cwd)
cat > draft-email.eml << 'EOF'
From: me
To: recipient@example.com
Subject: Your subject here
Content-Type: text/plain; charset="UTF-8"

Email body goes here.
EOF

# 2. Create the draft
gws gmail users drafts create \
  --params '{"userId":"me"}' \
  --upload draft-email.eml \
  --upload-content-type message/rfc822

# 3. Clean up
rm draft-email.eml
```

The response includes `id` (draft ID) and `message.id` (message ID).

For **CC/BCC** in drafts, add headers to the .eml file:
```
Cc: someone@example.com
Bcc: hidden@example.com
```

For **HTML drafts**, change the Content-Type and use HTML in the body:
```
Content-Type: text/html; charset="UTF-8"

<p>Hello <b>world</b></p>
```

### List drafts

```bash
gws gmail users drafts list --params '{"userId":"me"}'
```

### Send an existing draft

```bash
gws gmail users drafts send --params '{"userId":"me"}' --json '{"id":"DRAFT_ID"}'
```

### Update a draft

```bash
# Write updated .eml file, then:
gws gmail users drafts update \
  --params '{"userId":"me","id":"DRAFT_ID"}' \
  --upload updated-draft.eml \
  --upload-content-type message/rfc822
```

### Delete a draft

```bash
gws gmail users drafts delete --params '{"userId":"me","id":"DRAFT_ID"}'
```

**Warning:** This permanently deletes the draft — it does NOT trash it.

### Read a message

```bash
# Plain text body
gws gmail +read --id MESSAGE_ID

# With headers (From, To, Subject, Date)
gws gmail +read --id MESSAGE_ID --headers

# JSON output
gws gmail +read --id MESSAGE_ID --format json

# HTML body
gws gmail +read --id MESSAGE_ID --html
```

### Triage / inbox summary

```bash
# Show unread inbox (default: 20 messages)
gws gmail +triage

# Limit results
gws gmail +triage --max 5

# Custom search query
gws gmail +triage --query "from:boss@company.com"
gws gmail +triage --query "subject:urgent is:unread"

# Show labels
gws gmail +triage --labels

# Table format (default) or JSON
gws gmail +triage --format table
gws gmail +triage --format json
```

### Reply to a message

```bash
# Reply to sender only
gws gmail +reply --message-id MESSAGE_ID --body "Thanks, got it!"

# Reply with CC
gws gmail +reply --message-id MESSAGE_ID --body "Looping in Carol" --cc carol@example.com

# Reply with attachment
gws gmail +reply --message-id MESSAGE_ID --body "See attached" -a report.pdf

# HTML reply
gws gmail +reply --message-id MESSAGE_ID --body "<b>Noted</b>" --html
```

### Reply-all

```bash
# Reply to all recipients
gws gmail +reply-all --message-id MESSAGE_ID --body "Sounds good!"

# Reply-all but exclude someone
gws gmail +reply-all --message-id MESSAGE_ID --body "Updated" --remove bob@example.com
```

### Forward a message

```bash
# Forward with optional note
gws gmail +forward --message-id MESSAGE_ID --to dave@example.com --body "FYI see below"

# Forward with attachment
gws gmail +forward --message-id MESSAGE_ID --to dave@example.com -a notes.pdf
```

### Search for messages

```bash
# List messages matching a query
gws gmail users messages list --params '{"userId":"me","q":"from:someone@example.com subject:invoice"}'

# Get a specific message
gws gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID"}'
```

### Trash / untrash a message

```bash
gws gmail users messages trash --params '{"userId":"me","id":"MESSAGE_ID"}'
gws gmail users messages untrash --params '{"userId":"me","id":"MESSAGE_ID"}'
```

### Batch operations

```bash
# Add/remove labels from multiple messages
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["MSG_ID_1","MSG_ID_2"],"addLabelIds":["STARRED"]}'
```

## Important Notes

- The `gws` CLI is at `/opt/homebrew/bin/gws`
- Always use `--params '{"userId":"me"}'` for low-level API calls (drafts, messages)
- Helper commands (`+send`, `+read`, `+triage`, `+reply`, `+forward`) do NOT need userId
- Draft uploads MUST be from the current working directory — gws blocks paths outside cwd
- For drafts, always clean up the temporary `.eml` file after creation
- Attachments have a 25MB total size limit
- `+triage` is read-only and never modifies the mailbox
- When replying, threading headers (In-Reply-To, References) are handled automatically
