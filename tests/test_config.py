"""Tests for config file parsing."""

from pathlib import Path

import pytest

import agentmail


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_config: Path) -> None:
        """Valid config file is parsed correctly."""
        config = agentmail.load_config(tmp_config)

        assert "allowlist" in config
        assert "addresses" in config["allowlist"]
        assert "allowed@example.com" in config["allowlist"]["addresses"]
        assert "another@test.org" in config["allowlist"]["addresses"]
        assert config["audit"]["log_file"] == "./agentmail.log"

    def test_missing_config_returns_defaults(self, tmp_path: Path) -> None:
        """Missing config file returns empty allowlist."""
        config = agentmail.load_config(tmp_path / "nonexistent.toml")

        assert config["allowlist"]["addresses"] == []
        assert config["audit"] == {}
        assert config["defaults"] == {}

    def test_invalid_toml_raises_error(self, tmp_config_invalid: Path) -> None:
        """Invalid TOML raises ValueError."""
        with pytest.raises(ValueError, match="Invalid config file"):
            agentmail.load_config(tmp_config_invalid)

    def test_missing_sections_get_defaults(self, tmp_path: Path) -> None:
        """Config with missing sections gets defaults filled in."""
        config_file = tmp_path / "minimal.toml"
        config_file.write_text("[defaults]\nfrom_name = 'Test'\n")

        config = agentmail.load_config(config_file)

        assert config["allowlist"]["addresses"] == []
        assert config["audit"] == {}
        assert config["defaults"]["from_name"] == "Test"

    def test_empty_config_file(self, tmp_path: Path) -> None:
        """Empty config file gets all defaults."""
        config_file = tmp_path / "empty.toml"
        config_file.write_text("")

        config = agentmail.load_config(config_file)

        assert config["allowlist"]["addresses"] == []
        assert config["audit"] == {}
        assert config["defaults"] == {}

    def test_config_preserves_extra_fields(self, tmp_path: Path) -> None:
        """Config preserves extra fields for forward compatibility."""
        config_file = tmp_path / "extended.toml"
        config_file.write_text(
            """
[allowlist]
addresses = ["test@example.com"]
some_future_field = true

[audit]
log_file = "./test.log"
retention_days = 30
"""
        )

        config = agentmail.load_config(config_file)

        assert config["allowlist"]["some_future_field"] is True
        assert config["audit"]["retention_days"] == 30
