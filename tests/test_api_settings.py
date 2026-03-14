"""Tests for api.config Settings defaults."""
import os
import pytest


def _make_settings():
    """Instantiate Settings with minimal required env vars."""
    os.environ.setdefault("SUPABASE_URL", "x")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "x")
    os.environ.setdefault("SUPABASE_JWT_SECRET", "x")
    os.environ.setdefault("OPENAI_API_KEY", "x")
    from api.config import Settings
    return Settings()


class TestSettingsDefaults:

    def test_enhance_max_tokens_is_400(self):
        """enhance_max_tokens default must be 400 to fit the expanded LLM schema."""
        s = _make_settings()
        assert s.enhance_max_tokens == 400
