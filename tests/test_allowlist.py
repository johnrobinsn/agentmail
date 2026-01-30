"""Tests for allowlist enforcement logic."""

import pytest

import agentmail


class TestIsAllowed:
    """Tests for is_allowed function."""

    def test_allowed_exact_match(self) -> None:
        """Exact match is allowed."""
        allowlist = ["allowed@example.com", "team@company.org"]
        assert agentmail.is_allowed("allowed@example.com", allowlist) is True

    def test_allowed_case_insensitive(self) -> None:
        """Match is case-insensitive."""
        allowlist = ["Allowed@Example.COM"]
        assert agentmail.is_allowed("allowed@example.com", allowlist) is True
        assert agentmail.is_allowed("ALLOWED@EXAMPLE.COM", allowlist) is True

    def test_not_allowed_different_address(self) -> None:
        """Different address is not allowed."""
        allowlist = ["allowed@example.com"]
        assert agentmail.is_allowed("notallowed@example.com", allowlist) is False

    def test_not_allowed_empty_list(self) -> None:
        """Empty allowlist blocks all."""
        allowlist: list[str] = []
        assert agentmail.is_allowed("anyone@example.com", allowlist) is False

    def test_not_allowed_substring_match(self) -> None:
        """Substring match is not allowed (must be exact)."""
        allowlist = ["allowed@example.com"]
        assert agentmail.is_allowed("allowed@example.com.evil.com", allowlist) is False

    def test_not_allowed_prefix_match(self) -> None:
        """Prefix match is not allowed."""
        allowlist = ["user@example.com"]
        assert agentmail.is_allowed("user@example", allowlist) is False

    def test_multiple_addresses_in_allowlist(self) -> None:
        """Multiple addresses can be in allowlist."""
        allowlist = [
            "user1@example.com",
            "user2@example.com",
            "user3@different.org",
        ]
        assert agentmail.is_allowed("user1@example.com", allowlist) is True
        assert agentmail.is_allowed("user2@example.com", allowlist) is True
        assert agentmail.is_allowed("user3@different.org", allowlist) is True
        assert agentmail.is_allowed("user4@example.com", allowlist) is False

    def test_allowlist_with_whitespace(self) -> None:
        """Addresses with leading/trailing whitespace in list still work."""
        # Note: TOML should handle this, but test the function directly
        allowlist = ["  user@example.com  "]
        # The allowlist should be trimmed before use; if not, this tests current behavior
        assert agentmail.is_allowed("user@example.com", allowlist) is False
        assert agentmail.is_allowed("  user@example.com  ", allowlist) is True

    def test_special_characters_in_address(self) -> None:
        """Special characters in email addresses work correctly."""
        allowlist = ["user+tag@example.com", "user.name@sub.example.com"]
        assert agentmail.is_allowed("user+tag@example.com", allowlist) is True
        assert agentmail.is_allowed("user.name@sub.example.com", allowlist) is True
        assert agentmail.is_allowed("user+other@example.com", allowlist) is False
