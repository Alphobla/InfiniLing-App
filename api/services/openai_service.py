"""OpenAI service for word enhancement and generation."""

from typing import Dict, List, Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from api.services.language_prompts import get_language_rules


FrequencyLevel = Literal["Essential", "Common", "Intermediate", "Advanced", "Rare"]


class EnhanceWordResult(BaseModel):
    lemma: str = Field(..., min_length=1)
    is_fixed_expression: bool
    translation: str = Field(..., min_length=1)
    secondary_translation: Optional[str] = None
    frequency_level: FrequencyLevel
    example_sentence: str = Field(..., min_length=1)
    example_sentence_translation: str = Field(..., min_length=1)


class GenerateTextResult(BaseModel):
    title: str = Field(..., min_length=1)
    story: str = Field(..., min_length=1)


class OpenAIService:
    """Service for OpenAI API calls."""

    def __init__(
        self,
        api_key: str,
        max_tokens: int,
        temperature: float,
        text_model: str = "gpt-5.4-mini",
        tts_model: str = "gpt-4o-mini-tts",
    ):
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.text_model = text_model
        self.tts_model = tts_model

    @staticmethod
    def _get_total_tokens(response) -> int:
        """Best-effort extraction of total token usage across SDK response shapes."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return 0

        total_tokens = getattr(usage, "total_tokens", None)
        if isinstance(total_tokens, int):
            return total_tokens

        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            return input_tokens + output_tokens

        return 0

    def enhance_word(
        self,
        word: str,
        language_from: str,
        language_to: str,
        existing_translation: Optional[str] = None,
    ) -> Dict:
        """
        Enhance a word with lemmatization, translation, example sentence, and frequency.

        Returns dict with: lemma, is_fixed_expression, translation, secondary_translation,
        example_sentence, example_sentence_translation, frequency_level, tokens_used

        If enhancement fails, returns dict with "enhancement_failed": True and "tokens_used".
        """
        language_rules = get_language_rules(language_from)

        context_line = (
            f'CONTEXT: Existing translation "{existing_translation}" may help disambiguate meaning.\n\n'
            if existing_translation
            else ""
        )

        prompt = f"""You are a professional lexicographer normalizing vocabulary entries.

INPUT: {language_from} word/expression "{word}"
{context_line}TASK: Normalize to dictionary headword (lemma), translate to {language_to}, and write one example sentence.

{language_rules}

TRANSLATION RULES:
- Translate to {language_to}.
- translation: the most common, everyday meaning.
- secondary_translation: the next most distinct meaning if the word is clearly polysemous, otherwise null.
  Do not invent a secondary meaning for words with one dominant sense.
  For Russian verbs: secondary_translation holds the perfective aspect partner only (e.g. "написать"), not a meaning.

FREQUENCY RULES:
- Judge how common the word/expression is for a native speaker.
- Return one of exactly these labels: "Essential", "Common", "Intermediate", "Advanced", "Rare".
  - Essential: top ~500 most basic words (e.g. "the", "be", "have", "yes", "water")
  - Common: everyday vocabulary roughly in the top 3,000
  - Intermediate: solid conversational range, roughly top 10,000
  - Advanced: literary, technical, or niche, roughly top 30,000
  - Rare: uncommon or highly specialized

EXAMPLE SENTENCE RULES:
- Write one natural sentence in {language_from} that uses the full lemma exactly as written.
- Do not use only part of a fixed expression.
- Length: 8-18 words.
- Translate the sentence into {language_to}.
"""

        try:
            response = self.client.responses.parse(
                model=self.text_model,
                input=[
                    {
                        "role": "developer",
                        "content": "Return only the requested structured result.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                text_format=EnhanceWordResult,
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            result = response.output_parsed
            tokens_used = self._get_total_tokens(response)

            if not result or not result.lemma or result.lemma.lower() in {"none", "null", ""}:
                return {
                    "enhancement_failed": True,
                    "tokens_used": tokens_used,
                }

            data = result.model_dump()
            data["tokens_used"] = tokens_used
            return data

        except Exception:
            return {
                "enhancement_failed": True,
                "tokens_used": 0,
            }

    def generate_text(
        self,
        words: List[str],
        language: str,
        target_length: int = 150,
        topic: Optional[str] = None,
        style: Optional[str] = None,
        format: Optional[str] = None,
    ) -> Dict:
        """
        Generate a text that naturally incorporates vocabulary words.

        Returns dict with: title, story, tokens_used
        """
        words_str = ", ".join(words)

        refinements = []
        if topic:
            refinements.append(f"- Topic/subject matter: {topic}")
        if style:
            refinements.append(f"- Language style: {style}")
        if format:
            refinements.append(f"- Format: {format}")

        refinements_block = "\n".join(refinements)
        if refinements_block:
            refinements_block = f"\n\nAdditional requirements:\n{refinements_block}"

        prompt = f"""Write a text (around {target_length} words) in {language} that naturally incorporates these vocabulary words: {words_str}

Requirements:
- Incorporate all the words naturally — they should feel like a seamless part of the text
- Make it engaging, coherent, and well-written
- The text should flow naturally and read like authentic {language} writing{refinements_block}
"""

        response = self.client.responses.parse(
            model=self.text_model,
            input=[
                {
                    "role": "developer",
                    "content": "Return only the requested structured result.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            text_format=GenerateTextResult,
            max_output_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        result = response.output_parsed
        tokens_used = self._get_total_tokens(response)

        return {
            "title": result.title,
            "story": result.story,
            "tokens_used": tokens_used,
        }

    def generate_audio(self, text: str, voice: str = "alloy") -> bytes:
        """
        Generate TTS audio for text.

        Returns audio bytes (mp3 format).
        """
        response = self.client.audio.speech.create(
            model=self.tts_model,
            voice=voice,
            input=text,
        )

        return response.content