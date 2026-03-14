"""Tests for the updated enhance_word() method."""
import json
from unittest.mock import MagicMock, patch
from api.services.openai_service import OpenAIService


def _make_service():
    """Return an OpenAIService with a dummy key."""
    with patch("api.services.openai_service.OpenAI"):
        svc = OpenAIService(api_key="test", max_tokens=400, temperature=0.3)
    return svc


def _mock_response(content: str, total_tokens: int = 50):
    """Build a fake OpenAI chat completion response."""
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage.total_tokens = total_tokens
    return resp


class TestEnhanceWordPrompt:

    def test_prompt_contains_language_rules(self):
        """The prompt sent to the LLM must include language-specific rules."""
        svc = _make_service()
        captured_messages = []

        good_json = json.dumps({
            "lemma": "le chien",
            "is_fixed_expression": False,
            "translation": "der Hund",
            "secondary_translation": None,
            "example_sentence": "Le chien court dans le parc chaque matin.",
            "example_sentence_translation": "Der Hund rennt jeden Morgen im Park.",
        })

        svc.client.chat.completions.create = MagicMock(
            side_effect=lambda **kwargs: (
                captured_messages.extend(kwargs["messages"]) or _mock_response(good_json)
            )
        )

        svc.enhance_word("chien", "fr", "de")

        prompt_text = captured_messages[0]["content"]
        assert "LEMMATIZATION RULES FOR FRENCH" in prompt_text

    def test_prompt_uses_language_to(self):
        """language_to must appear in the prompt so the LLM knows the translation target."""
        svc = _make_service()
        captured_messages = []

        good_json = json.dumps({
            "lemma": "le chat",
            "is_fixed_expression": False,
            "translation": "die Katze",
            "secondary_translation": None,
            "example_sentence": "Le chat dort sur le canapé toute la journée.",
            "example_sentence_translation": "Die Katze schläft den ganzen Tag auf dem Sofa.",
        })

        svc.client.chat.completions.create = MagicMock(
            side_effect=lambda **kwargs: (
                captured_messages.extend(kwargs["messages"]) or _mock_response(good_json)
            )
        )

        svc.enhance_word("chat", "fr", "de")
        assert "de" in captured_messages[0]["content"]

    def test_fixed_expression_skips_strip_prefix(self):
        """is_fixed_expression=true must prevent strip_prefix_words from being applied."""
        svc = _make_service()

        good_json = json.dumps({
            "lemma": "au début",
            "is_fixed_expression": True,
            "translation": "am Anfang",
            "secondary_translation": "zu Beginn",
            "example_sentence": "Au début, il ne savait pas quoi faire de sa vie.",
            "example_sentence_translation": "Am Anfang wusste er nicht, was er mit seinem Leben anfangen sollte.",
        })

        svc.client.chat.completions.create = MagicMock(return_value=_mock_response(good_json))

        with patch("api.services.openai_service.strip_prefix_words") as mock_strip:
            result = svc.enhance_word("au début", "fr", "de")
            mock_strip.assert_not_called()

        assert result["lemma"] == "au début"

    def test_non_fixed_expression_calls_strip_prefix(self):
        """is_fixed_expression=false must allow strip_prefix_words to run."""
        svc = _make_service()

        good_json = json.dumps({
            "lemma": "le chien",
            "is_fixed_expression": False,
            "translation": "der Hund",
            "secondary_translation": None,
            "example_sentence": "Le chien aboie très fort quand il entend la sonnette.",
            "example_sentence_translation": "Der Hund bellt sehr laut, wenn er die Klingel hört.",
        })

        svc.client.chat.completions.create = MagicMock(return_value=_mock_response(good_json))

        with patch("api.services.openai_service.strip_prefix_words", return_value="chien") as mock_strip:
            svc.enhance_word("le chien", "fr", "de")
            mock_strip.assert_called_once_with("le chien", "fr")

    def test_malformed_json_returns_enhancement_failed(self):
        """A non-JSON LLM response must return enhancement_failed=True, not raise."""
        svc = _make_service()
        svc.client.chat.completions.create = MagicMock(
            return_value=_mock_response("Sorry, I cannot help with that.", total_tokens=10)
        )

        result = svc.enhance_word("test", "fr", "de")

        assert result["enhancement_failed"] is True
        assert result["tokens_used"] == 10

    def test_example_sentence_fields_returned(self):
        """Result must include example_sentence and example_sentence_translation."""
        svc = _make_service()

        good_json = json.dumps({
            "lemma": "la maison",
            "is_fixed_expression": False,
            "translation": "das Haus",
            "secondary_translation": None,
            "example_sentence": "La maison est grande et très confortable pour toute la famille.",
            "example_sentence_translation": "Das Haus ist groß und sehr komfortabel für die ganze Familie.",
        })

        svc.client.chat.completions.create = MagicMock(return_value=_mock_response(good_json))

        result = svc.enhance_word("maison", "fr", "de")

        assert result["example_sentence"] == "La maison est grande et très confortable pour toute la famille."
        assert result["example_sentence_translation"] == "Das Haus ist groß und sehr komfortabel für die ganze Familie."

    def test_tokens_used_returned_on_success(self):
        """tokens_used must equal the total_tokens from the API response."""
        svc = _make_service()

        good_json = json.dumps({
            "lemma": "le soleil",
            "is_fixed_expression": False,
            "translation": "die Sonne",
            "secondary_translation": None,
            "example_sentence": "Le soleil brille intensément sur la mer aujourd'hui.",
            "example_sentence_translation": "Die Sonne scheint heute intensiv auf das Meer.",
        })

        svc.client.chat.completions.create = MagicMock(
            return_value=_mock_response(good_json, total_tokens=87)
        )

        result = svc.enhance_word("soleil", "fr", "de")
        assert result["tokens_used"] == 87

    def test_markdown_code_block_stripped(self):
        """LLM response wrapped in ```json ... ``` must still parse correctly."""
        svc = _make_service()

        inner = json.dumps({
            "lemma": "la nuit",
            "is_fixed_expression": False,
            "translation": "die Nacht",
            "secondary_translation": None,
            "example_sentence": "La nuit tombe doucement sur la ville endormie.",
            "example_sentence_translation": "Die Nacht bricht sanft über die schlafende Stadt herein.",
        })
        wrapped = f"```json\n{inner}\n```"

        svc.client.chat.completions.create = MagicMock(return_value=_mock_response(wrapped))

        result = svc.enhance_word("nuit", "fr", "de")
        assert result["lemma"] == "la nuit"
