"""Shared text processing utilities."""

from api.services.languages import STRIP_PREFIXES


def strip_prefix_words(text: str, language: str) -> str:
    """
    Strip known prefix words (articles, etc.) from the beginning of text.

    Examples:
        strip_prefix_words("der Hund", "de") -> "Hund"
        strip_prefix_words("to be", "en") -> "be"
        strip_prefix_words("en tant que", "fr") -> "en tant que"  # "en" not in French prefixes
    """
    prefixes = STRIP_PREFIXES.get(language, set())
    if not prefixes:
        return text

    words = text.split()
    # Strip prefix words from the beginning only
    while words and words[0].lower() in prefixes:
        words = words[1:]

    return " ".join(words) if words else text
