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
    search_word = word.split()[-1] if " " in word else word

    # Use the unstable API with trans:lang filter to only get sentences
    # that have translations in the target language
    search_url = "https://api.tatoeba.org/unstable/sentences"
    params = {
        "lang": from_code,
        "trans:lang": to_code,  # Only sentences with translations in target lang
        "word_count": "4-12",   # Reasonable sentence length
        "q": search_word,
        "sort": "random",       # Required parameter
        "limit": 5,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            # Search for sentences
            response = client.get(search_url, params=params)
            response.raise_for_status()
            results = response.json().get("data", [])

            if not results:
                return None

            # Fetch details for each result to get the translation
            for entry in results:
                sentence_id = entry.get("id")
                if not sentence_id:
                    continue

                detail_url = f"https://api.tatoeba.org/unstable/sentences/{sentence_id}"
                detail_resp = client.get(detail_url, timeout=10.0)
                if not detail_resp.is_success:
                    continue

                data = detail_resp.json()
                sentence = data.get("data", data) if isinstance(data, dict) else {}

                original_text = sentence.get("text", "")
                translations = sentence.get("translations", [])

                # Find the first translation in the target language
                for item in translations:
                    group = item if isinstance(item, list) else [item]
                    for trans in group:
                        if isinstance(trans, dict) and trans.get("lang") == to_code:
                            return {
                                "original": original_text,
                                "translation": trans.get("text", "")
                            }

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
