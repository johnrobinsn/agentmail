# AgentMail

A command-line tool for sending emails via Gmail, designed for safe use by AI agents and automated systems.

## Features

- **Allowlist Safety**: Only send to pre-approved email addresses
- **Audit Logging**: All email operations logged to JSON Lines file
- **Dry Run Mode**: Validate everything without actually sending
- **Stdin Support**: Pipe email body from other commands
- **Attachments**: Send files with your emails
- **HTML Emails**: Send rich HTML content with inline images
- **Zero Config Install**: Uses uv inline dependencies

## Security Model

AgentMail is designed for scenarios where an AI agent or automated system needs to send emails on your behalf. The allowlist ensures the agent can only email addresses you've explicitly approved, preventing accidental or malicious emails to unintended recipients.

**Recommendation**: Create a dedicated Google account for your agent rather than using your personal account. This provides better isolation and makes it easier to revoke access if needed.

## Setup

### 1. Install uv

AgentMail uses [uv](https://docs.astral.sh/uv/) to manage dependencies. Install it if you haven't:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create a Dedicated Gmail Account (Recommended)

For agent use, create a separate Google account:

1. Go to [accounts.google.com](https://accounts.google.com) and create a new account
2. Use a clear naming convention like `myproject-agent@gmail.com`
3. This isolates agent activity from your personal email

### 3. Enable 2-Factor Authentication

App Passwords require 2FA to be enabled:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Under "How you sign in to Google", click **2-Step Verification**
3. Follow the prompts to enable 2FA (you can use your phone or an authenticator app)

### 4. Generate an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. You may need to sign in again
3. Enter a name for the app (e.g., "AgentMail")
4. Click **Create**
5. Copy the 16-character password (shown with spaces, but use it without spaces)

**Important**: This password grants full access to send email from this account. Store it securely and never commit it to version control.

### 5. Configure Environment Variables

Create a `.env` file in your working directory (see `.env.example`):

```bash
cp .env.example .env
# Edit .env with your credentials
```

AgentMail automatically loads `.env` from the current working directory.

Alternatively, export directly:

```bash
export GMAIL_USER="your-agent@gmail.com"
export GMAIL_APP_PASSWORD="xxxxxxxxxxxx"
```

### 6. Configure the Allowlist

Create `agentmail.toml` in your working directory:

```bash
cp agentmail.example.toml agentmail.toml
# Edit agentmail.toml with your allowed recipients
```

## Configuration

### Config File (`agentmail.toml`)

```toml
[allowlist]
# Only these addresses can receive emails (exact match, case-insensitive)
addresses = [
    "you@example.com",
    "team@company.org",
]

[audit]
# JSON Lines format audit log (optional)
log_file = "./agentmail.log"
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GMAIL_USER` | Yes* | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Yes* | 16-character app password |

*Not required for `--dry-run` mode.

## Usage

### Basic Email

```bash
uv run agentmail.py --to recipient@example.com --subject "Hello" --body "Message body"
```

### With Attachments

```bash
uv run agentmail.py --to recipient@example.com --subject "Report" \
    --body "Please see attached." \
    --attach report.pdf data.csv
```

### HTML Email

```bash
uv run agentmail.py --to recipient@example.com --subject "Newsletter" \
    --body "<h1>Welcome</h1><p>Thanks for subscribing!</p>" \
    --html
```

### HTML with Inline Image

```bash
uv run agentmail.py --to recipient@example.com --subject "Photo Update" \
    --body '<h1>Check this out</h1><img src="cid:photo">' \
    --html \
    --inline photo=./image.jpg
```

### Body from Stdin (Piping)

```bash
echo "Build completed successfully" | uv run agentmail.py \
    --to ops@example.com \
    --subject "Build Notification"
```

```bash
cat report.txt | uv run agentmail.py \
    --to team@example.com \
    --subject "Daily Report"
```

### Dry Run (Validation Only)

Test your configuration without actually sending:

```bash
uv run agentmail.py --to recipient@example.com --subject "Test" --body "Test" --dry-run
```

### Custom Config Path

```bash
uv run agentmail.py --to recipient@example.com --subject "Test" --body "Test" \
    --config /path/to/custom.toml
```

## CLI Reference

```
usage: agentmail [-h] --to TO --subject SUBJECT [--body BODY] [--html]
                 [--attach [FILE ...]] [--inline [NAME=PATH ...]]
                 [--config CONFIG] [--dry-run]

Send emails via Gmail with allowlist safety

options:
  -h, --help            show this help message and exit
  --to TO               Recipient email address
  --subject SUBJECT     Email subject line
  --body BODY           Email body text
  --html                Treat body as HTML
  --attach [FILE ...]   File(s) to attach
  --inline [NAME=PATH ...]
                        Inline image: name=path for CID reference
  --config CONFIG       Path to config file (default: ./agentmail.toml)
  --dry-run             Validate everything but don't send
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (email sent or dry-run passed) |
| 1 | Error (see stderr for details) |

## Audit Log Format

Each line in the audit log is a JSON object:

```json
{"timestamp": "2024-01-15T10:30:00Z", "to": "user@example.com", "subject": "Report", "attachments": ["report.pdf"], "status": "sent"}
{"timestamp": "2024-01-15T10:31:00Z", "to": "blocked@unknown.com", "subject": "Test", "attachments": [], "status": "blocked", "error": "Recipient not in allowlist"}
{"timestamp": "2024-01-15T10:32:00Z", "to": "user@example.com", "subject": "Alert", "attachments": [], "status": "failed", "error": "SMTP connection refused"}
```

Status values:
- `sent` - Email delivered successfully
- `dry_run` - Validation passed (no email sent)
- `blocked` - Recipient not in allowlist
- `failed` - SMTP or other error

## Error Handling

AgentMail follows Unix philosophy:
- **Silent on success**: No output when email sends successfully
- **Errors to stderr**: All error messages go to stderr
- **Fail fast**: Exits immediately on first error

Common errors:

| Error | Cause | Solution |
|-------|-------|----------|
| "Recipient not in allowlist" | Email address not in config | Add address to `allowlist.addresses` |
| "GMAIL_USER environment variable not set" | Missing credential | Set `GMAIL_USER` env var |
| "GMAIL_APP_PASSWORD environment variable not set" | Missing credential | Set `GMAIL_APP_PASSWORD` env var |
| "Attachment not found" | File doesn't exist | Check file path |
| "Invalid config file" | Malformed TOML | Fix syntax in config file |

## Testing

Run the test suite:

```bash
uv run --with pytest --with pytest-cov --with yagmail --with tomli \
    pytest tests/ -v
```

With coverage report:

```bash
uv run --with pytest --with pytest-cov --with yagmail --with tomli \
    pytest tests/ --cov=agentmail --cov-report=term-missing
```

## License

MIT
