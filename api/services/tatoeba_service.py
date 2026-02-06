"""Tatoeba service for fetching example sentences."""

import httpx
from typing import Optional, Dict
from api.services.text_utils import strip_prefix_words

# Map language codes to Tatoeba language codes
LANGUAGE_MAP = {
    "en": "eng",
    "de": "deu",
    "fr": "fra",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
    "ru": "rus",
    "ja": "jpn",
    "zh": "cmn",
    # Also map full language names (in case stored as names instead of codes)
    "english": "eng",
    "german": "deu",
    "french": "fra",
    "spanish": "spa",
    "italian": "ita",
    "portuguese": "por",
    "dutch": "nld",
    "russian": "rus",
    "japanese": "jpn",
    "chinese": "cmn",
}


from typing import Dict, Optional
import httpx

def get_example_sentence(
    word: str,
    language_from: str,
    language_to: str
) -> Optional[Dict[str, str]]:
    """
    Fetch an example sentence from Tatoeba.

    Args:
        word: The word to find an example for (use lemma without article)
        language_from: Source language code (e.g., "de")
        language_to: Target language code (e.g., "en")

    Returns:
        Dict with "original" and "translation" keys, or None if not found
    """
    # Convert to Tatoeba language codes (case-insensitive lookup)
    from_code = LANGUAGE_MAP.get(language_from.lower(), language_from)
    to_code = LANGUAGE_MAP.get(language_to.lower(), language_to)

    # Strip articles for search (e.g., "der Hund" -> "Hund")
    search_word = strip_prefix_words(word, language_from)

    # Force exact token match in Tatoeba search:
    # - single word: "=sel"
    # - multiple words: "=word1 =word2"
    exact_q = " ".join("=" + w for w in search_word.split())

    params = {
        "lang": from_code,
        "q": exact_q,
        "trans:lang": to_code,
        "showtrans": "matching",
        "sort": "relevance",
        "limit": 30,
    }

    def _word_count_ok(text: str) -> bool:
        # split on whitespace; 2-15 word heuristic
        n = len(text.split())
        return 2 <= n <= 15

    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get("https://api.tatoeba.org/unstable/sentences", params=params)
            resp.raise_for_status()

            results = resp.json().get("data", [])
            if not results:
                return None

            for s in results:
                original = (s.get("text") or "").strip()
                if not original or not _word_count_ok(original):
                    continue

                # Translations are a flat list of dicts
                translations = s.get("translations") or []
                for t in translations:
                    if isinstance(t, dict) and t.get("lang") == to_code:
                        translation = (t.get("text") or "").strip()
                        if translation:
                            return {"original": original, "translation": translation}

            return None

    except httpx.TimeoutException:
        print(f"Tatoeba timeout for '{search_word}'")
        return None
    except httpx.HTTPStatusError as e:
        print(f"Tatoeba HTTP error for '{search_word}': {e.response.status_code}")
        return None
    except Exception as e:
        print(f"Tatoeba error for '{search_word}': {type(e).__name__}: {e}")
        return None
