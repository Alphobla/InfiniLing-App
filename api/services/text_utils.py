"""Shared text processing utilities."""

# Words to strip from the beginning of lemmas for frequency/search lookup
# These are articles, infinitive markers, reflexive pronouns, etc.
STRIP_PREFIXES = {
    "en": {"the", "a", "an", "to"},
    "de": {"der", "die", "das", "ein", "eine", "einen", "einem", "einer", "eines", "sich", "zu"},
    "fr": {"le", "la", "les", "l'", "un", "une", "des", "se", "s'"},
    "es": {"el", "la", "los", "las", "un", "una", "unos", "unas"},
    "it": {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una"},
    "pt": {"o", "a", "os", "as", "um", "uma", "uns", "umas"},
    "nl": {"de", "het", "een"},
}


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
