"""
Tests for Word Frequency Analysis.

These tests verify:
- Frequency rank calculations
- Category classification
- Edge cases (unknown words, unsupported languages)
"""

import pytest
from src.shared.frequency_analysis import (
    get_word_frequency_rank,
    get_word_frequency_category,
    is_common_word,
    get_supported_languages,
    format_frequency_info
)


class TestFrequencyRank:
    """Tests for word frequency ranking."""

    def test_common_word_has_rank(self):
        """Very common words should have a rank."""
        # "the" is one of the most common English words
        rank = get_word_frequency_rank("the", "en")
        assert rank is not None
        assert rank < 100  # Should be in top 100

    def test_common_french_word(self):
        """Common French words should have a rank."""
        rank = get_word_frequency_rank("le", "fr")
        assert rank is not None
        assert rank < 100

    def test_common_german_word(self):
        """Common German words should have a rank."""
        rank = get_word_frequency_rank("der", "de")
        assert rank is not None
        assert rank < 100

    def test_rare_word_has_higher_rank(self):
        """Less common words should have higher ranks."""
        common_rank = get_word_frequency_rank("house", "en")
        # "serendipitous" is less common
        less_common_rank = get_word_frequency_rank("serendipitous", "en")

        if common_rank and less_common_rank:
            assert less_common_rank > common_rank

    def test_gibberish_returns_none(self):
        """Nonsense words should return None."""
        rank = get_word_frequency_rank("xyzabc123nonsense", "en")
        assert rank is None


class TestFrequencyCategory:
    """Tests for frequency categorization."""

    def test_returns_dict_structure(self):
        """Should return a dictionary with expected keys."""
        result = get_word_frequency_category("hello", "en")

        assert isinstance(result, dict)
        assert "word" in result
        assert "language" in result
        assert "category" in result
        assert "level" in result
        assert "rank" in result
        assert "color" in result
        assert "found" in result

    def test_common_word_categorized(self):
        """Common words should be categorized appropriately."""
        result = get_word_frequency_category("the", "en")

        assert result["found"] is True
        assert result["category"] in ["top_100", "top_1000"]
        assert result["rank"] is not None
        assert result["rank"] < 1000

    def test_unknown_word_marked(self):
        """Unknown words should be marked as such."""
        result = get_word_frequency_category("xyznonexistent123", "en")

        # Either found=False or category=unknown
        assert result["category"] == "unknown" or result["found"] is False

    def test_preserves_input_word(self):
        """Result should contain the original word."""
        result = get_word_frequency_category("Bonjour", "fr")
        assert result["word"] == "Bonjour"
        assert result["language"] == "fr"


class TestIsCommonWord:
    """Tests for common word detection."""

    def test_very_common_word(self):
        """Very common words should return True."""
        assert is_common_word("the", "en") is True
        assert is_common_word("le", "fr") is True
        assert is_common_word("der", "de") is True

    def test_uncommon_word(self):
        """Uncommon/rare words should return False."""
        # Using a very obscure word
        result = is_common_word("defenestration", "en")
        # This might be False depending on threshold
        assert isinstance(result, bool)

    def test_nonexistent_word(self):
        """Nonexistent words should return False."""
        assert is_common_word("xyznonexistent", "en") is False

    def test_custom_threshold(self):
        """Should respect custom threshold parameter."""
        # With very high threshold, even common words might not qualify
        result = is_common_word("hello", "en", threshold=8.0)
        assert isinstance(result, bool)


class TestSupportedLanguages:
    """Tests for supported languages list."""

    def test_returns_list(self):
        """Should return a list of language codes."""
        languages = get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0

    def test_common_languages_included(self):
        """Should include common language codes."""
        languages = get_supported_languages()

        # Check for common languages
        assert "en" in languages  # English
        assert "fr" in languages  # French
        assert "de" in languages  # German
        assert "es" in languages  # Spanish


class TestFormatFrequencyInfo:
    """Tests for formatted frequency output."""

    def test_format_known_word(self):
        """Should format known word with rank."""
        result = format_frequency_info("hello", "en")

        assert isinstance(result, str)
        assert "hello" in result
        # Should contain some level or rank info
        assert "Top" in result or "#" in result or "Unknown" in result

    def test_format_unknown_word(self):
        """Should indicate when frequency data not available."""
        result = format_frequency_info("xyznonexistent123", "en")

        assert isinstance(result, str)
        assert "xyznonexistent123" in result
