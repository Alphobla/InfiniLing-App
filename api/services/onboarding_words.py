"""Service for loading static onboarding word lists."""

import json
from pathlib import Path
from functools import lru_cache
from typing import List

# Path to the JSON files — relative to this file's location
DATA_DIR = Path(__file__).parent.parent / "data" / "onboarding_words"


@lru_cache(maxsize=8)
def load_word_list(language_code: str) -> List[dict]:
    """
    Load the 200-word list for a language from its static JSON file.
    Results are cached in memory so we only read from disk once per language.
    """
    file_path = DATA_DIR / f"{language_code}.json"
    if not file_path.exists():
        return []
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def get_words_by_indices(language_code: str, indices: List[int]) -> List[dict]:
    """
    Get specific words from a language's list by their indices.
    Returns only the entries at the given positions.
    """
    words = load_word_list(language_code)
    result = []
    for idx in indices:
        if 0 <= idx < len(words):
            result.append(words[idx])
    return result


def get_supported_languages() -> List[str]:
    """Get list of language codes that have onboarding word files."""
    return [f.stem for f in DATA_DIR.glob("*.json")]
