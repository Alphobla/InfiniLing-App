"""
Language configuration for the API.

This is a copy of the core language data from src/shared/languages.py
to avoid import issues in serverless deployments.
"""

# Language code to name mapping (ISO 639-1)
LANGUAGES = {
    'de': 'German',
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'ru': 'Russian',
    'ar': 'Arabic',
    'zh': 'Chinese',
}

# Words to strip from the beginning of lemmas for frequency/search lookup
STRIP_PREFIXES = {
    "en": {"the", "a", "an", "to"},
    "de": {"der", "die", "das", "ein", "eine", "einen", "einem", "einer", "eines", "sich", "zu"},
    "fr": {"le", "la", "les", "l'", "un", "une", "des", "se", "s'"},
    "es": {"el", "la", "los", "las", "un", "una", "unos", "unas"},
    "it": {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una"},
    "ru": {"в", "на", "с", "к", "о", "у", "по"},
    "ar": {"ال", "في", "من", "إلى", "على"},
    "zh": {"的", "了", "在", "是", "我", "你", "他"},
}

# Set of valid codes for quick lookup
VALID_CODES = set(LANGUAGES.keys())


def get_name(code: str) -> str:
    """Get language name from code."""
    if not code:
        return ''
    return LANGUAGES.get(code.lower(), code)


def get_code(name_or_code: str) -> str | None:
    """Get language code from name or code."""
    if not name_or_code:
        return None

    lower = name_or_code.lower()

    # Already a valid code
    if lower in VALID_CODES:
        return lower

    # Look up by name
    for code, name in LANGUAGES.items():
        if name.lower() == lower:
            return code

    return None


def get_all_languages() -> list[tuple[str, str]]:
    """Get all languages as list of (name, code) tuples, sorted by name."""
    return [(name, code) for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1])]


def is_valid_code(code: str) -> bool:
    """Check if a language code is valid."""
    return code.lower() in VALID_CODES if code else False
