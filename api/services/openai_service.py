"""OpenAI service for word enhancement and generation."""

import json
from typing import Optional, Dict, List
from openai import OpenAI
from wordfreq import zipf_frequency
from api.services.text_utils import strip_prefix_words


def get_frequency_info(word: str, language: str) -> Dict:
    """Get word frequency information using wordfreq."""
    zipf_freq = zipf_frequency(word.lower(), language)

    if zipf_freq <= 0:
        return {"rank": None, "level": "Unknown"}

    rank = int(10 ** (8 - zipf_freq))

    if rank <= 1000:
        level = "Top 1,000"
    elif rank <= 5000:
        level = "Top 5,000"
    elif rank <= 10000:
        level = "Top 10,000"
    elif rank <= 20000:
        level = "Top 20,000"
    else:
        level = "Rare"

    return {"rank": rank, "level": level}


class OpenAIService:
    """Service for OpenAI API calls."""

    def __init__(self, api_key: str, max_tokens: int, temperature: float):
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens
        self.temperature = temperature

    def enhance_word(
        self,
        word: str,
        language_from: str,
        language_to: str,
        existing_translation: Optional[str] = None
    ) -> Dict:
        """
        Enhance a word with lemmatization, translation, example sentence, and frequency.

        Returns dict with: lemma, is_fixed_expression, translation, secondary_translation,
        example_sentence, example_sentence_translation, frequency_rank, frequency_level, tokens_used

        If enhancement fails, returns dict with "enhancement_failed": True and "tokens_used".
        """
        from api.services.language_prompts import get_language_rules
        language_rules = get_language_rules(language_from)

        context_line = (
            f'CONTEXT: Existing translation "{existing_translation}" may help disambiguate meaning.\n\n'
            if existing_translation else ""
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

EXAMPLE SENTENCE RULES:
- Write one natural sentence in {language_from} that uses the full lemma exactly as written.
- Do not use only part of a fixed expression.
- Length: 8-18 words.
- Translate the sentence into {language_to}.

OUTPUT: JSON only, no markdown.
{{
  "lemma": "...",
  "is_fixed_expression": true/false,
  "translation": "...",
  "secondary_translation": "...",
  "example_sentence": "...",
  "example_sentence_translation": "..."
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        content = response.choices[0].message.content.strip()

        # Strip markdown code blocks if present
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1])

        try:
            result = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return {
                "enhancement_failed": True,
                "tokens_used": response.usage.total_tokens
            }

        # Validate that lemma was identified
        lemma = result.get("lemma")
        if not lemma or lemma.lower() in ["none", "null", ""]:
            return {
                "enhancement_failed": True,
                "tokens_used": response.usage.total_tokens
            }

        # Add frequency info — skip strip_prefix_words for fixed expressions
        if not result.get("is_fixed_expression"):
            core_expression = strip_prefix_words(lemma, language_from)
        else:
            core_expression = lemma
        freq_info = get_frequency_info(core_expression, language_from)

        result["frequency_rank"] = freq_info["rank"]
        result["frequency_level"] = freq_info["level"]
        result["tokens_used"] = response.usage.total_tokens

        return result

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

        Returns dict with: story, tokens_used
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

Output JSON only, no markdown formatting.
{{
  "title": "<short creative title for the text, in {language}>",
  "story": "<the full text>"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        content = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1])

        result = json.loads(content)

        return {
            "title": result.get("title", ""),
            "story": result.get("story", content),
            "tokens_used": response.usage.total_tokens
        }

    def generate_audio(self, text: str, voice: str = "alloy") -> bytes:
        """
        Generate TTS audio for text.

        Returns audio bytes (mp3 format).
        """
        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text
        )

        return response.content
