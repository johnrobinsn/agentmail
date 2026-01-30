#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "yagmail",
#     "tomli; python_version < '3.11'",
# ]
# ///
"""
AgentMail - CLI tool for sending emails via Gmail with allowlist safety.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Conditional import for TOML parsing
try:
    import tomllib
except ImportError:
    import tomli as tomllib

import yagmail


def load_config(path: Path) -> Dict[str, Any]:
    """Load and parse TOML config file.

    Returns empty config structure if file doesn't exist.
    Raises ValueError for invalid TOML.
    """
    if not path.exists():
        return {"allowlist": {"addresses": []}, "audit": {}, "defaults": {}}

    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid config file: {e}")

    # Ensure required sections exist with defaults
    config.setdefault("allowlist", {})
    config["allowlist"].setdefault("addresses", [])
    config.setdefault("audit", {})
    config.setdefault("defaults", {})

    return config


def is_allowed(recipient: str, allowlist: List[str]) -> bool:
    """Check if recipient is in the allowlist (exact match, case-insensitive)."""
    recipient_lower = recipient.lower()
    return any(addr.lower() == recipient_lower for addr in allowlist)


def audit_log(log_file: Optional[Path], entry: Dict[str, Any]) -> None:
    """Append a JSON log entry to the audit log file."""
    if log_file is None:
        return

    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def send_email(
    yag: yagmail.SMTP,
    to: str,
    subject: str,
    body: str,
    html: bool = False,
    attachments: Optional[List[str]] = None,
    inline_images: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> None:
    """Send email using yagmail.

    If dry_run is True, validates but doesn't send.
    """
    if dry_run:
        return

    # Build contents list for yagmail
    contents: List[Any] = []

    if html:
        contents.append(yagmail.inline(body))
    else:
        contents.append(body)

    # Add inline images if provided
    if inline_images:
        for name, path in inline_images.items():
            contents.append(yagmail.inline(path, cid=name))

    yag.send(
        to=to,
        subject=subject,
        contents=contents,
        attachments=attachments,
    )


def parse_inline_arg(inline_args: Optional[List[str]]) -> Dict[str, str]:
    """Parse inline image arguments in format 'name=path'."""
    result = {}
    if not inline_args:
        return result

    for arg in inline_args:
        if "=" not in arg:
            raise ValueError(f"Invalid inline format '{arg}', expected 'name=path'")
        name, path = arg.split("=", 1)
        if not name or not path:
            raise ValueError(f"Invalid inline format '{arg}', expected 'name=path'")
        result[name] = path

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Send emails via Gmail with allowlist safety",
        prog="agentmail",
    )
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--body", help="Email body text")
    parser.add_argument("--html", action="store_true", help="Treat body as HTML")
    parser.add_argument(
        "--attach", nargs="*", metavar="FILE", help="File(s) to attach"
    )
    parser.add_argument(
        "--inline",
        nargs="*",
        metavar="NAME=PATH",
        help="Inline image: name=path for CID reference",
    )
    parser.add_argument(
        "--config",
        default="./agentmail.toml",
        help="Path to config file (default: ./agentmail.toml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate everything but don't send",
    )

    args = parser.parse_args()

    # Get body from stdin if not provided
    body = args.body
    if body is None:
        if sys.stdin.isatty():
            print("Error: --body required when not piping from stdin", file=sys.stderr)
            return 1
        body = sys.stdin.read()

    # Load config
    config_path = Path(args.config)
    try:
        config = load_config(config_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Get audit log file path
    log_file_str = config["audit"].get("log_file")
    log_file = Path(log_file_str) if log_file_str else None

    # Parse inline images
    try:
        inline_images = parse_inline_arg(args.inline)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Validate attachments exist
    if args.attach:
        for attachment in args.attach:
            if not Path(attachment).exists():
                print(f"Error: Attachment not found: {attachment}", file=sys.stderr)
                return 1

    # Validate inline image files exist
    for name, path in inline_images.items():
        if not Path(path).exists():
            print(f"Error: Inline image not found: {path}", file=sys.stderr)
            return 1

    # Build audit entry
    attachment_names = [Path(a).name for a in (args.attach or [])]
    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "to": args.to,
        "subject": args.subject,
        "attachments": attachment_names,
    }

    # Check allowlist
    allowlist = config["allowlist"]["addresses"]
    if not is_allowed(args.to, allowlist):
        audit_entry["status"] = "blocked"
        audit_entry["error"] = "Recipient not in allowlist"
        audit_log(log_file, audit_entry)
        print(f"Error: Recipient not in allowlist: {args.to}", file=sys.stderr)
        return 1

    # Get credentials from environment
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not args.dry_run:
        if not gmail_user:
            print("Error: GMAIL_USER environment variable not set", file=sys.stderr)
            return 1
        if not gmail_password:
            print(
                "Error: GMAIL_APP_PASSWORD environment variable not set",
                file=sys.stderr,
            )
            return 1

    # Send email
    try:
        if not args.dry_run:
            yag = yagmail.SMTP(gmail_user, gmail_password)
            send_email(
                yag=yag,
                to=args.to,
                subject=args.subject,
                body=body,
                html=args.html,
                attachments=args.attach,
                inline_images=inline_images,
                dry_run=False,
            )

        audit_entry["status"] = "sent" if not args.dry_run else "dry_run"
        audit_log(log_file, audit_entry)
        return 0

    except Exception as e:
        audit_entry["status"] = "failed"
        audit_entry["error"] = str(e)
        audit_log(log_file, audit_entry)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
