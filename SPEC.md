# AgentMail Specification

## Overview

AgentMail is a command-line tool for sending emails from a Gmail account via scripts. It is designed for:
- CI/CD notifications
- Scheduled reports
- Agent/LLM integration
- Alerting systems

## Technical Stack

- **Language**: Python 3.8+
- **Package Manager**: uv (inline script dependencies)
- **Email Library**: yagmail
- **Authentication**: Gmail App Password (SMTP)
- **Config Format**: TOML
- **Testing**: pytest + coverage.py

## Features

### Email Capabilities
- Plain text emails
- HTML emails
- File attachments (documents, images, small archives)
- Inline images via CID references (`<img src="cid:image1">`)
- CC/BCC: Not supported (keep scope minimal)
- Body from stdin (pipe support)

### Safety & Governance
- **Recipient Allowlist**: Only send to pre-approved email addresses
  - Configured via TOML config file
  - Exact addresses only (no wildcards)
  - Hard fail if any recipient not on allowlist
- **Audit Logging**: All email operations logged to JSON Lines file
  - Metadata only (no body content for privacy)
  - Fields: timestamp, to, subject, attachment_names, status, error_message (if any)

### Error Handling
- Fail fast on errors (exit immediately, let caller handle retries)
- Exit codes: 0 for success, 1 for any failure
- Silent on success (no output, Unix philosophy)
- Errors written to stderr

## Configuration

### Hierarchy
1. Command-line flags (highest priority)
2. Environment variables (for secrets)
3. Config file (`./agentmail.toml` in working directory)

### Environment Variables
```bash
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Config File (`agentmail.toml`)
```toml
[allowlist]
addresses = [
    "allowed@example.com",
    "team@company.org",
]

[audit]
log_file = "./agentmail.log"  # JSON Lines format

[defaults]
# Optional default values
# from_name = "AgentMail"
```

## CLI Interface

### Basic Usage
```bash
# Text email
uv run agentmail.py --to recipient@example.com --subject "Subject" --body "Message"

# With attachments
uv run agentmail.py --to recipient@example.com --subject "Report" --body "See attached" \
    --attach report.pdf data.csv

# HTML email
uv run agentmail.py --to recipient@example.com --subject "Newsletter" \
    --body "<h1>Hello</h1><p>Content here</p>" --html

# HTML with inline image
uv run agentmail.py --to recipient@example.com --subject "Photo" \
    --body '<h1>Check this out</h1><img src="cid:photo">' --html \
    --inline photo=./image.jpg

# Body from stdin
echo "Message from pipeline" | uv run agentmail.py --to recipient@example.com --subject "Piped"

# Dry run (validate without sending)
uv run agentmail.py --to recipient@example.com --subject "Test" --body "Test" --dry-run
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--to` | Yes | Recipient email address |
| `--subject` | Yes | Email subject line |
| `--body` | No* | Email body text (* required unless stdin provided) |
| `--html` | No | Treat body as HTML content |
| `--attach` | No | File path(s) to attach (multiple allowed) |
| `--inline` | No | Inline image: `name=path` for CID reference |
| `--config` | No | Path to config file (default: `./agentmail.toml`) |
| `--dry-run` | No | Validate everything but don't send |

## Authentication Setup (One-time)

1. Enable 2FA on Gmail account (if not already)
2. Go to Google Account → Security → App Passwords
3. Generate App Password for "Mail"
4. Store the 16-character password in `GMAIL_APP_PASSWORD` environment variable

## Audit Log Format

Each line in the audit log is a JSON object:

```json
{"timestamp": "2024-01-15T10:30:00Z", "to": "user@example.com", "subject": "Report", "attachments": ["report.pdf"], "status": "sent"}
{"timestamp": "2024-01-15T10:31:00Z", "to": "blocked@unknown.com", "subject": "Test", "attachments": [], "status": "blocked", "error": "Recipient not in allowlist"}
{"timestamp": "2024-01-15T10:32:00Z", "to": "user@example.com", "subject": "Alert", "attachments": [], "status": "failed", "error": "SMTP connection refused"}
```

## Testing Strategy

### Test Framework
- pytest for test execution
- coverage.py for coverage analysis
- Target: High coverage on error conditions and allowlist enforcement

### Test Categories

#### Unit Tests
- Allowlist validation logic
- Config file parsing
- Argument parsing
- Audit log formatting

#### Integration Tests (with dry-run)
- Full CLI invocation with `--dry-run`
- Verify allowlist enforcement (blocked recipients)
- Verify config file loading
- Verify stdin body handling

#### Coverage Requirements
- Focus on error paths and edge cases
- Verify correct exit codes for all failure modes
- Ensure all code paths through allowlist logic are covered

### Running Tests
```bash
# Run tests with coverage
uv run pytest --cov=agentmail --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=agentmail --cov-report=html
```

## Error Conditions

| Condition | Behavior | Exit Code |
|-----------|----------|-----------|
| Missing required argument | Print usage to stderr | 1 |
| Config file not found | Use defaults (empty allowlist blocks all) | 1 |
| Invalid config file | Print parse error to stderr | 1 |
| Recipient not in allowlist | Log to audit, print error to stderr | 1 |
| Attachment file not found | Print error to stderr | 1 |
| SMTP authentication failed | Print error to stderr | 1 |
| SMTP send failure | Log to audit, print error to stderr | 1 |
| Success | Silent (no output) | 0 |

## Project Structure

```
agentmail/
├── agentmail.py          # Main script with inline dependencies
├── agentmail.toml        # Example config file
├── SPEC.md               # This specification
├── tests/
│   ├── test_allowlist.py
│   ├── test_config.py
│   ├── test_cli.py
│   └── test_audit.py
└── .github/
    └── workflows/
        └── test.yml      # CI workflow (optional)
```

## Dependencies (inline in script)

```python
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "yagmail",
#     "tomli; python_version < '3.11'",
# ]
# ///
```

## Future Considerations (Out of Scope)

These features are explicitly not part of the initial implementation:
- Multiple sender accounts/profiles
- Built-in retry logic
- HTTP API endpoint
- Scheduling/cron integration
- CC/BCC support
- Domain wildcards in allowlist
- Verbose output modes
