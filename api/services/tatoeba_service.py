"""Tatoeba service for fetching example sentences."""

import httpx
from typing import Optional, Dict

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
}


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
    # Convert to Tatoeba language codes
    from_code = LANGUAGE_MAP.get(language_from, language_from)
    to_code = LANGUAGE_MAP.get(language_to, language_to)

    # Strip articles for search (e.g., "der Hund" -> "Hund")
    search_word = word.split()[-1] if " " in word else word

    url = "https://tatoeba.org/en/api_v0/search"
    params = {
        "from": from_code,
        "to": to_code,
        "query": search_word,
        "limit": 10,
    }

    try:
        # Use longer timeout for serverless cold starts
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        # Find a sentence with a translation in the target language
        for sentence in results:
            text = sentence.get("text", "")
            translations = sentence.get("translations", [])

            # translations is a list of lists - iterate through all groups
            for translation_group in translations:
                if not isinstance(translation_group, list):
                    continue
                for translation in translation_group:
                    if not isinstance(translation, dict):
                        continue
                    if translation.get("lang") == to_code:
                        return {
                            "original": text,
                            "translation": translation.get("text", "")
                        }

        # No translation found in target language
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
