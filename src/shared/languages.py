"""
Central language configuration for all modules.

This is the single source of truth for language mappings.
All modules should import from here instead of defining their own.
"""

# Language code to name mapping
LANGUAGES = {
    'de': 'German',
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
}

# Set of valid codes for quick lookup
VALID_CODES = set(LANGUAGES.keys())


def get_name(code: str) -> str:
    """Get language name from code.

    Args:
        code: Language code (e.g., 'fr')

    Returns:
        Language name (e.g., 'French'), or the code itself if not found
    """
    if not code:
        return ''
    return LANGUAGES.get(code.lower(), code)


def get_code(name_or_code: str) -> str | None:
    """Get language code from name or code.

    Accepts both 'French' and 'fr', returns 'fr' for both.

    Args:
        name_or_code: Language name or code

    Returns:
        Language code, or None if not found
    """
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
    """Get all languages as list of (name, code) tuples.

    Sorted alphabetically by name. Suitable for dropdown menus.

    Returns:
        List of (name, code) tuples, e.g., [('Arabic', 'ar'), ('Chinese', 'zh'), ...]
    """
    return [(name, code) for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1])]


def is_valid_code(code: str) -> bool:
    """Check if a language code is valid."""
    return code.lower() in VALID_CODES if code else False
