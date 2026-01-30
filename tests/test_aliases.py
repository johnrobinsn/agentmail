"""Tests for email alias resolution."""

import pytest

import agentmail


class TestResolveAlias:
    """Tests for resolve_alias function."""

    def test_resolves_exact_alias(self) -> None:
        """Exact alias match resolves to email."""
        aliases = {"me": "john@example.com", "wife": "jane@example.com"}
        assert agentmail.resolve_alias("me", aliases) == "john@example.com"
        assert agentmail.resolve_alias("wife", aliases) == "jane@example.com"

    def test_case_insensitive_alias(self) -> None:
        """Alias matching is case-insensitive."""
        aliases = {"Me": "john@example.com", "Wife": "jane@example.com"}
        assert agentmail.resolve_alias("me", aliases) == "john@example.com"
        assert agentmail.resolve_alias("ME", aliases) == "john@example.com"
        assert agentmail.resolve_alias("WIFE", aliases) == "jane@example.com"

    def test_no_alias_returns_original(self) -> None:
        """Non-matching input returns original value."""
        aliases = {"me": "john@example.com"}
        assert agentmail.resolve_alias("someone@example.com", aliases) == "someone@example.com"

    def test_empty_aliases_returns_original(self) -> None:
        """Empty aliases dict returns original value."""
        aliases: dict[str, str] = {}
        assert agentmail.resolve_alias("me", aliases) == "me"

    def test_email_address_not_resolved(self) -> None:
        """Email addresses pass through unchanged."""
        aliases = {"me": "john@example.com"}
        assert agentmail.resolve_alias("other@example.com", aliases) == "other@example.com"

    def test_multiple_aliases_same_email(self) -> None:
        """Multiple aliases can point to the same email."""
        aliases = {
            "me": "john@example.com",
            "myself": "john@example.com",
            "john": "john@example.com",
        }
        assert agentmail.resolve_alias("me", aliases) == "john@example.com"
        assert agentmail.resolve_alias("myself", aliases) == "john@example.com"
        assert agentmail.resolve_alias("john", aliases) == "john@example.com"
