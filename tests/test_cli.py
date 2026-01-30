"""Integration tests for CLI via subprocess."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pytest


def run_agentmail(
    args: List[str],
    stdin: str | None = None,
    env: Dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run agentmail.py as subprocess."""
    script_path = Path(__file__).parent.parent / "agentmail.py"
    cmd = [sys.executable, str(script_path)] + args

    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    return subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        env=run_env,
        cwd=cwd,
    )


class TestCLIDryRun:
    """Tests for --dry-run mode."""

    def test_dry_run_allowed_recipient(self, tmp_path: Path) -> None:
        """Dry run with allowed recipient succeeds."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test body",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_dry_run_blocked_recipient(self, tmp_path: Path) -> None:
        """Dry run with blocked recipient fails."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["allowed@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "blocked@example.com",
                "--subject",
                "Test",
                "--body",
                "Test body",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "not in allowlist" in result.stderr

    def test_dry_run_no_credentials_ok(self, tmp_path: Path) -> None:
        """Dry run doesn't require credentials."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        # Ensure no credentials in environment
        env = {k: v for k, v in os.environ.items() if k not in ("GMAIL_USER", "GMAIL_APP_PASSWORD")}

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test body",
                "--config",
                str(config),
                "--dry-run",
            ],
            env=env,
        )

        assert result.returncode == 0


class TestCLIStdin:
    """Tests for stdin body handling."""

    def test_body_from_stdin(self, tmp_path: Path) -> None:
        """Body can be provided via stdin."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--config",
                str(config),
                "--dry-run",
            ],
            stdin="Body from stdin",
        )

        assert result.returncode == 0

    def test_body_flag_overrides_stdin(self, tmp_path: Path) -> None:
        """--body flag is used when both stdin and flag are provided."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Flag body",
                "--config",
                str(config),
                "--dry-run",
            ],
            stdin="Stdin body",
        )

        assert result.returncode == 0


class TestCLIConfig:
    """Tests for config file handling."""

    def test_missing_config_blocks_all(self, tmp_path: Path) -> None:
        """Missing config file means empty allowlist (blocks all)."""
        result = run_agentmail(
            [
                "--to",
                "anyone@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--config",
                str(tmp_path / "nonexistent.toml"),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "not in allowlist" in result.stderr

    def test_invalid_config_fails(self, tmp_path: Path) -> None:
        """Invalid config file causes error."""
        config = tmp_path / "agentmail.toml"
        config.write_text("invalid toml [[[")

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "Invalid config file" in result.stderr


class TestCLIAttachments:
    """Tests for attachment handling."""

    def test_attachment_not_found(self, tmp_path: Path) -> None:
        """Missing attachment file causes error."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--attach",
                "/nonexistent/file.pdf",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "Attachment not found" in result.stderr

    def test_valid_attachment_dry_run(self, tmp_path: Path) -> None:
        """Valid attachment passes dry run."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )
        attachment = tmp_path / "test.txt"
        attachment.write_text("test content")

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--attach",
                str(attachment),
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 0


class TestCLIInlineImages:
    """Tests for inline image handling."""

    def test_inline_image_not_found(self, tmp_path: Path) -> None:
        """Missing inline image causes error."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--inline",
                "img=/nonexistent/image.jpg",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "Inline image not found" in result.stderr

    def test_invalid_inline_format(self, tmp_path: Path) -> None:
        """Invalid inline format causes error."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--inline",
                "invalid-no-equals",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert "Invalid inline format" in result.stderr


class TestCLIAuditLog:
    """Tests for audit log integration."""

    def test_blocked_recipient_logged(self, tmp_path: Path) -> None:
        """Blocked recipient is logged to audit file."""
        log_file = tmp_path / "agentmail.log"
        config = tmp_path / "agentmail.toml"
        config.write_text(
            f"""
[allowlist]
addresses = ["allowed@example.com"]

[audit]
log_file = "{log_file}"
"""
        )

        result = run_agentmail(
            [
                "--to",
                "blocked@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test body",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 1
        assert log_file.exists()

        entries = [json.loads(line) for line in log_file.read_text().strip().split("\n")]
        assert len(entries) == 1
        assert entries[0]["to"] == "blocked@example.com"
        assert entries[0]["subject"] == "Test Subject"
        assert entries[0]["status"] == "blocked"
        assert "allowlist" in entries[0]["error"]

    def test_dry_run_success_logged(self, tmp_path: Path) -> None:
        """Successful dry run is logged."""
        log_file = tmp_path / "agentmail.log"
        config = tmp_path / "agentmail.toml"
        config.write_text(
            f"""
[allowlist]
addresses = ["allowed@example.com"]

[audit]
log_file = "{log_file}"
"""
        )

        result = run_agentmail(
            [
                "--to",
                "allowed@example.com",
                "--subject",
                "Test Subject",
                "--body",
                "Test body",
                "--config",
                str(config),
                "--dry-run",
            ]
        )

        assert result.returncode == 0
        assert log_file.exists()

        entries = [json.loads(line) for line in log_file.read_text().strip().split("\n")]
        assert len(entries) == 1
        assert entries[0]["to"] == "allowed@example.com"
        assert entries[0]["status"] == "dry_run"


class TestCLICredentials:
    """Tests for credential handling."""

    def test_missing_gmail_user_without_dry_run(self, tmp_path: Path) -> None:
        """Missing GMAIL_USER fails without --dry-run."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        # Filter out both credentials and run from tmp_path to avoid loading .env
        env = {k: v for k, v in os.environ.items() if k not in ("GMAIL_USER", "GMAIL_APP_PASSWORD")}

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--config",
                str(config),
            ],
            env=env,
            cwd=tmp_path,  # Run from tmp_path so dotenv doesn't find .env
        )

        assert result.returncode == 1
        assert "GMAIL_USER" in result.stderr

    def test_missing_gmail_password_without_dry_run(self, tmp_path: Path) -> None:
        """Missing GMAIL_APP_PASSWORD fails without --dry-run."""
        config = tmp_path / "agentmail.toml"
        config.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
"""
        )

        # Filter out password and run from tmp_path to avoid loading .env
        env = {k: v for k, v in os.environ.items() if k not in ("GMAIL_USER", "GMAIL_APP_PASSWORD")}
        env["GMAIL_USER"] = "test@gmail.com"

        result = run_agentmail(
            [
                "--to",
                "test@example.com",
                "--subject",
                "Test",
                "--body",
                "Test",
                "--config",
                str(config),
            ],
            env=env,
            cwd=tmp_path,  # Run from tmp_path so dotenv doesn't find .env
        )

        assert result.returncode == 1
        assert "GMAIL_APP_PASSWORD" in result.stderr


class TestCLIRequiredArgs:
    """Tests for required argument handling."""

    def test_missing_to_fails(self, tmp_path: Path) -> None:
        """Missing --to fails."""
        result = run_agentmail(
            ["--subject", "Test", "--body", "Test", "--dry-run"]
        )

        assert result.returncode != 0
        assert "--to" in result.stderr

    def test_missing_subject_fails(self, tmp_path: Path) -> None:
        """Missing --subject fails."""
        result = run_agentmail(
            ["--to", "test@example.com", "--body", "Test", "--dry-run"]
        )

        assert result.returncode != 0
        assert "--subject" in result.stderr
