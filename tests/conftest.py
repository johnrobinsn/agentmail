"""Pytest fixtures for AgentMail tests."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Generator, List
from unittest.mock import MagicMock

import pytest

# Add parent directory to path for importing agentmail
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary config file with test allowlist."""
    config_file = tmp_path / "agentmail.toml"
    config_file.write_text(
        """
[allowlist]
addresses = [
    "allowed@example.com",
    "another@test.org",
]

[audit]
log_file = "./agentmail.log"
"""
    )
    return config_file


@pytest.fixture
def tmp_config_no_audit(tmp_path: Path) -> Path:
    """Create a config file without audit log configured."""
    config_file = tmp_path / "agentmail.toml"
    config_file.write_text(
        """
[allowlist]
addresses = [
    "allowed@example.com",
]
"""
    )
    return config_file


@pytest.fixture
def tmp_config_empty_allowlist(tmp_path: Path) -> Path:
    """Create a config file with empty allowlist."""
    config_file = tmp_path / "agentmail.toml"
    config_file.write_text(
        """
[allowlist]
addresses = []

[audit]
log_file = "./agentmail.log"
"""
    )
    return config_file


@pytest.fixture
def tmp_config_invalid(tmp_path: Path) -> Path:
    """Create an invalid TOML config file."""
    config_file = tmp_path / "agentmail.toml"
    config_file.write_text("this is not valid toml [[[")
    return config_file


@pytest.fixture
def tmp_audit_log(tmp_path: Path) -> Path:
    """Return path for a temporary audit log file."""
    return tmp_path / "agentmail.log"


@pytest.fixture
def mock_yagmail() -> Generator[MagicMock, None, None]:
    """Mock yagmail.SMTP for testing without actual email sending."""
    import agentmail

    original = agentmail.yagmail.SMTP
    mock = MagicMock()
    agentmail.yagmail.SMTP = MagicMock(return_value=mock)
    yield mock
    agentmail.yagmail.SMTP = original


@pytest.fixture
def env_credentials() -> Generator[Dict[str, str], None, None]:
    """Set up Gmail credentials in environment."""
    original_user = os.environ.get("GMAIL_USER")
    original_pass = os.environ.get("GMAIL_APP_PASSWORD")

    os.environ["GMAIL_USER"] = "test@gmail.com"
    os.environ["GMAIL_APP_PASSWORD"] = "test-app-password"

    yield {"user": "test@gmail.com", "password": "test-app-password"}

    # Restore original values
    if original_user is not None:
        os.environ["GMAIL_USER"] = original_user
    else:
        os.environ.pop("GMAIL_USER", None)

    if original_pass is not None:
        os.environ["GMAIL_APP_PASSWORD"] = original_pass
    else:
        os.environ.pop("GMAIL_APP_PASSWORD", None)


@pytest.fixture
def no_credentials() -> Generator[None, None, None]:
    """Remove Gmail credentials from environment."""
    original_user = os.environ.pop("GMAIL_USER", None)
    original_pass = os.environ.pop("GMAIL_APP_PASSWORD", None)

    yield

    if original_user is not None:
        os.environ["GMAIL_USER"] = original_user
    if original_pass is not None:
        os.environ["GMAIL_APP_PASSWORD"] = original_pass


def read_audit_log(log_path: Path) -> List[Dict]:
    """Helper to read and parse audit log entries."""
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().strip().split("\n"):
        if line:
            entries.append(json.loads(line))
    return entries
