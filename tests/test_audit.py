"""Tests for audit logging."""

import json
from pathlib import Path

import pytest

import agentmail
from conftest import read_audit_log


class TestAuditLog:
    """Tests for audit_log function."""

    def test_creates_log_file(self, tmp_audit_log: Path) -> None:
        """Log file is created if it doesn't exist."""
        entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "to": "user@example.com",
            "subject": "Test",
            "attachments": [],
            "status": "sent",
        }

        agentmail.audit_log(tmp_audit_log, entry)

        assert tmp_audit_log.exists()

    def test_writes_json_line(self, tmp_audit_log: Path) -> None:
        """Entry is written as JSON line."""
        entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "to": "user@example.com",
            "subject": "Test Subject",
            "attachments": ["file.pdf"],
            "status": "sent",
        }

        agentmail.audit_log(tmp_audit_log, entry)

        entries = read_audit_log(tmp_audit_log)
        assert len(entries) == 1
        assert entries[0]["to"] == "user@example.com"
        assert entries[0]["subject"] == "Test Subject"
        assert entries[0]["attachments"] == ["file.pdf"]
        assert entries[0]["status"] == "sent"

    def test_appends_multiple_entries(self, tmp_audit_log: Path) -> None:
        """Multiple entries are appended to the log."""
        entries = [
            {"timestamp": "2024-01-15T10:30:00Z", "to": "a@example.com", "status": "sent"},
            {"timestamp": "2024-01-15T10:31:00Z", "to": "b@example.com", "status": "blocked"},
            {"timestamp": "2024-01-15T10:32:00Z", "to": "c@example.com", "status": "failed"},
        ]

        for entry in entries:
            agentmail.audit_log(tmp_audit_log, entry)

        logged = read_audit_log(tmp_audit_log)
        assert len(logged) == 3
        assert logged[0]["to"] == "a@example.com"
        assert logged[1]["to"] == "b@example.com"
        assert logged[2]["to"] == "c@example.com"

    def test_none_log_file_does_nothing(self) -> None:
        """None log file path is a no-op."""
        entry = {"to": "user@example.com", "status": "sent"}
        # Should not raise
        agentmail.audit_log(None, entry)

    def test_blocked_entry_has_error_field(self, tmp_audit_log: Path) -> None:
        """Blocked entries include error field."""
        entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "to": "blocked@example.com",
            "subject": "Test",
            "attachments": [],
            "status": "blocked",
            "error": "Recipient not in allowlist",
        }

        agentmail.audit_log(tmp_audit_log, entry)

        entries = read_audit_log(tmp_audit_log)
        assert entries[0]["status"] == "blocked"
        assert entries[0]["error"] == "Recipient not in allowlist"

    def test_failed_entry_has_error_field(self, tmp_audit_log: Path) -> None:
        """Failed entries include error field."""
        entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "to": "user@example.com",
            "subject": "Test",
            "attachments": [],
            "status": "failed",
            "error": "SMTP connection refused",
        }

        agentmail.audit_log(tmp_audit_log, entry)

        entries = read_audit_log(tmp_audit_log)
        assert entries[0]["status"] == "failed"
        assert entries[0]["error"] == "SMTP connection refused"

    def test_preserves_attachment_names(self, tmp_audit_log: Path) -> None:
        """Attachment names are preserved in log."""
        entry = {
            "timestamp": "2024-01-15T10:30:00Z",
            "to": "user@example.com",
            "subject": "Report",
            "attachments": ["report.pdf", "data.csv", "image.png"],
            "status": "sent",
        }

        agentmail.audit_log(tmp_audit_log, entry)

        entries = read_audit_log(tmp_audit_log)
        assert entries[0]["attachments"] == ["report.pdf", "data.csv", "image.png"]


class TestParseInlineArg:
    """Tests for parse_inline_arg function."""

    def test_single_inline_image(self) -> None:
        """Single inline image is parsed correctly."""
        result = agentmail.parse_inline_arg(["photo=./image.jpg"])
        assert result == {"photo": "./image.jpg"}

    def test_multiple_inline_images(self) -> None:
        """Multiple inline images are parsed correctly."""
        result = agentmail.parse_inline_arg(["img1=a.jpg", "img2=b.png"])
        assert result == {"img1": "a.jpg", "img2": "b.png"}

    def test_none_returns_empty_dict(self) -> None:
        """None input returns empty dict."""
        result = agentmail.parse_inline_arg(None)
        assert result == {}

    def test_empty_list_returns_empty_dict(self) -> None:
        """Empty list returns empty dict."""
        result = agentmail.parse_inline_arg([])
        assert result == {}

    def test_missing_equals_raises_error(self) -> None:
        """Missing equals sign raises ValueError."""
        with pytest.raises(ValueError, match="Invalid inline format"):
            agentmail.parse_inline_arg(["invalid"])

    def test_empty_name_raises_error(self) -> None:
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid inline format"):
            agentmail.parse_inline_arg(["=path.jpg"])

    def test_empty_path_raises_error(self) -> None:
        """Empty path raises ValueError."""
        with pytest.raises(ValueError, match="Invalid inline format"):
            agentmail.parse_inline_arg(["name="])

    def test_path_with_equals(self) -> None:
        """Path containing equals sign is handled correctly."""
        result = agentmail.parse_inline_arg(["img=path/with=equals.jpg"])
        assert result == {"img": "path/with=equals.jpg"}
