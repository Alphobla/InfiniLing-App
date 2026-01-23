"""
Tests for Configuration Management.

These tests verify:
- Config file loading
- Dot-notation access (e.g., 'ui.window_sizes.reader.width')
- Path resolution
- Default values
"""

import pytest
import os
import tempfile
import json
from src.shared.config import ConfigManager


class TestConfigLoading:
    """Tests for loading configuration files."""

    def test_loads_valid_config(self, temp_config_file):
        """Should load a valid JSON config file."""
        config = ConfigManager(config_file=temp_config_file)
        assert config.config is not None
        assert isinstance(config.config, dict)

    def test_missing_config_raises(self):
        """Should raise error for missing config file."""
        with pytest.raises(FileNotFoundError):
            ConfigManager(config_file="/nonexistent/config.json")


class TestDotNotationAccess:
    """Tests for dot-notation config access."""

    def test_get_nested_value(self, temp_config_file):
        """Should retrieve nested values using dot notation."""
        config = ConfigManager(config_file=temp_config_file)

        # Access nested value
        source_lang = config.get("vocabulary.languages.source")
        assert source_lang == "fr"

    def test_get_deeply_nested(self, temp_config_file):
        """Should handle deeply nested paths."""
        config = ConfigManager(config_file=temp_config_file)

        width = config.get("ui.window_sizes.reader.width")
        assert width == 800

    def test_get_returns_default_for_missing(self, temp_config_file):
        """Should return default value for missing keys."""
        config = ConfigManager(config_file=temp_config_file)

        result = config.get("nonexistent.path", default="fallback")
        assert result == "fallback"

    def test_get_returns_none_without_default(self, temp_config_file):
        """Should return None for missing keys without default."""
        config = ConfigManager(config_file=temp_config_file)

        result = config.get("nonexistent.path")
        assert result is None

    def test_get_partial_path(self, temp_config_file):
        """Should return dict for partial paths."""
        config = ConfigManager(config_file=temp_config_file)

        result = config.get("vocabulary.languages")
        assert isinstance(result, dict)
        assert result["source"] == "fr"
        assert result["target"] == "de"


class TestWindowSize:
    """Tests for window size helper method."""

    def test_get_window_size_existing(self, temp_config_file):
        """Should return configured window size."""
        config = ConfigManager(config_file=temp_config_file)

        width, height = config.get_window_size("reader")
        assert width == 800
        assert height == 600

    def test_get_window_size_unconfigured_raises(self, temp_config_file):
        """Should raise KeyError for unconfigured window type."""
        config = ConfigManager(config_file=temp_config_file)

        with pytest.raises(KeyError) as exc_info:
            config.get_window_size("nonexistent")
        assert "nonexistent" in str(exc_info.value)


class TestPathResolution:
    """Tests for path resolution."""

    def test_resolve_relative_path(self, temp_config_file):
        """Should resolve relative paths from config root."""
        config = ConfigManager(config_file=temp_config_file)

        resolved = config.resolve_path("some/relative/path")
        assert os.path.isabs(resolved)
        assert "some/relative/path" in resolved or "some\\relative\\path" in resolved

    def test_resolve_absolute_path(self, temp_config_file):
        """Should leave absolute paths unchanged."""
        config = ConfigManager(config_file=temp_config_file)

        abs_path = "/absolute/path/to/file"
        resolved = config.resolve_path(abs_path)
        assert resolved == os.path.normpath(abs_path)

    def test_resolve_empty_path(self, temp_config_file):
        """Should return config root for empty path."""
        config = ConfigManager(config_file=temp_config_file)

        resolved = config.resolve_path("")
        assert resolved == config.config_root


class TestUserDataDir:
    """Tests for user data directory."""

    def test_get_user_data_dir_creates_directory(self, temp_config_file):
        """Should create user data directory if it doesn't exist."""
        config = ConfigManager(config_file=temp_config_file)

        data_dir = config.get_user_data_dir()
        assert os.path.exists(data_dir)
        assert os.path.isdir(data_dir)

    def test_user_data_dir_in_home(self, temp_config_file):
        """User data directory should be in home folder."""
        config = ConfigManager(config_file=temp_config_file)

        data_dir = config.get_user_data_dir()
        home = os.path.expanduser("~")
        assert data_dir.startswith(home)


class TestTempPath:
    """Tests for temp file paths."""

    def test_get_temp_path(self, temp_config_file):
        """Should return path in system temp directory."""
        config = ConfigManager(config_file=temp_config_file)

        temp_path = config.get_temp_path("test_file.txt")
        assert tempfile.gettempdir() in temp_path
        assert "test_file.txt" in temp_path
