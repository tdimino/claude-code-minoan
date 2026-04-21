# Resend

Send transactional and notification emails from the terminal via the Resend API. Text and HTML content, multiple recipients, CC/BCC, reply-to, file attachments, stdin pipe support, and dry-run mode---all from a single Python script.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Sending a quick email from a Claude Code session---build notifications, reports, invoices---shouldn't require a full email client. This skill wraps the Resend API in a single script with sensible defaults, stdin piping for command output, and a dry-run mode for safety.

---

## Structure

```
resend/
  SKILL.md                          # Full usage guide with all flags
  README.md                         # This file
  scripts/
    send.py                         # Email sender CLI
    _resend_utils.py                # Shared utilities (API key resolution)
```

---

## Usage

```bash
# Simple text email
python3 send.py --to "recipient@example.com" --subject "Hello" --body "Test email."

# HTML email from a file
python3 send.py --to "recipient@example.com" --subject "Report" --html report.html

# Pipe command output as body
echo "Build passed" | python3 send.py --to "team@example.com" --subject "CI Results"

# Multiple recipients with CC and attachments
python3 send.py \
  --to "alice@example.com" "bob@example.com" \
  --cc "manager@example.com" \
  --subject "Meeting Notes" \
  --body "See attached." \
  --attachments notes.pdf

# Dry run (preview payload without sending)
python3 send.py --to "test@example.com" --subject "Test" --body "Hello" --dry-run
```

---

## Flags

| Flag | Description | Required |
|------|-------------|----------|
| `--to EMAIL [...]` | Recipient(s) | Yes |
| `--subject TEXT` | Subject line | Yes |
| `--body TEXT` | Plain text body (or pipe via stdin) | One of body/html/stdin |
| `--html FILE_OR_STRING` | HTML body (file path or inline string) | One of body/html/stdin |
| `--from EMAIL` | Sender address or alias (`tom`, `kothar`, `claudius`, `minoan`) | No |
| `--cc EMAIL [...]` | CC recipients | No |
| `--bcc EMAIL [...]` | BCC recipients | No |
| `--reply-to EMAIL` | Reply-to address | No |
| `--attachments FILE [...]` | File paths to attach | No |
| `--dry-run` | Print payload without sending | No |

`--body` and `--html` can be combined for multipart email (text + HTML). If neither is provided, stdin is used as plain text.

**Important**: Always confirm with the user before sending. Email is not reversible.

### Rate Limits

Resend enforces 2 requests per second. Add a 1-second delay between sends when sending multiple emails.

### Test Addresses

- `delivered@resend.dev` --- simulates successful delivery
- `bounced@resend.dev` --- simulates a bounce

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`
- Resend API key (get one at resend.com/api-keys, format: `re_xxxxxxxxx`)
- Add `export RESEND_API_KEY=re_xxxxxxxxx` to `~/.config/env/secrets.env`
- (Optional) Verify a custom sending domain at resend.com/domains

### API Key Resolution

Checked in order: `RESEND_API_KEY` env var > `~/.config/env/secrets.env` > `~/.claude.json`

---

## Related Skills

- **`sms`**: Send SMS/MMS messages (Twilio)---for text-message notifications instead of email.
- **`telegram`**: Send Telegram messages---for chat-based notifications.

---

## Requirements

- Python 3.9+
- `requests`
- Resend API key

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/resend ~/.claude/skills/
```
