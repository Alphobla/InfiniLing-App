"""Tests for per-language lemmatization rule injection."""
from api.services.language_prompts import get_language_rules


class TestGetLanguageRules:

    def test_french_rules_returned_for_fr(self):
        rules = get_language_rules("fr")
        assert "LEMMATIZATION RULES FOR FRENCH" in rules
        assert "l'" in rules  # elision rule must be present
        assert "le" in rules
        assert "la" in rules

    def test_spanish_rules_returned_for_es(self):
        rules = get_language_rules("es")
        assert "LEMMATIZATION RULES FOR SPANISH" in rules
        assert "el" in rules
        assert "levantarse" in rules  # reflexive example

    def test_italian_rules_returned_for_it(self):
        rules = get_language_rules("it")
        assert "LEMMATIZATION RULES FOR ITALIAN" in rules
        assert "lo" in rules
        assert "l'" in rules

    def test_russian_rules_returned_for_ru(self):
        rules = get_language_rules("ru")
        assert "LEMMATIZATION RULES FOR RUSSIAN" in rules
        assert "no articles" in rules.lower()
        assert "imperfective" in rules
        # Must use native Cyrillic script, not romanised transliteration
        assert "книга" in rules
        assert "писать" in rules

    def test_chinese_rules_returned_for_zh(self):
        rules = get_language_rules("zh")
        assert "LEMMATIZATION RULES FOR CHINESE" in rules
        assert "pinyin" in rules
        assert "no articles" in rules.lower()
        # Must use native Hanzi characters
        assert "开始" in rules

    def test_unknown_language_returns_default(self):
        # "ja" is not a named language — must return the default block
        rules = get_language_rules("ja")
        assert "LEMMATIZATION RULES FOR" not in rules  # no named-language header
        assert "LEMMATIZATION RULES" in rules           # but still has a rules block

    def test_empty_string_returns_default(self):
        rules = get_language_rules("")
        assert "LEMMATIZATION RULES FOR" not in rules
        assert "LEMMATIZATION RULES" in rules

    def test_returns_string(self):
        # Named languages and fallback codes all return strings
        for code in ["fr", "es", "it", "ru", "zh"]:
            assert isinstance(get_language_rules(code), str)
        # These fall through to the default — still strings
        for code in ["en", "de", "ja"]:
            assert isinstance(get_language_rules(code), str)
