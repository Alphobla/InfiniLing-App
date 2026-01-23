# Centralized Language Configuration Design

## Summary

Consolidate all language mappings and defaults into a single central module. Remove hardcoded French defaults and implement "remember last used language" globally.

## Problem

- 12+ files have hardcoded `'fr'` defaults or duplicate language lists
- `LANGUAGE_CODE_MAP` defined in multiple places
- User has to re-select language every time despite using the same one

## Solution

### 1. Central Language Module (`src/shared/languages.py`)

```python
"""Central language configuration for all modules."""

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

def get_name(code: str) -> str:
    """Get language name from code. e.g., 'fr' -> 'French'"""

def get_code(name_or_code: str) -> str | None:
    """Get language code from name or code. Handles both."""

def get_all_languages() -> list[tuple[str, str]]:
    """Get all languages as [(name, code), ...] for dropdowns."""
```

### 2. Last Used Language Persistence

ConfigManager additions:
- `get_last_language() -> str`: Returns last used language code
- `save_last_language(code: str)`: Persists the selection

Saved when: User generates text, starts transcription, or switches DB language tab
Loaded when: Each module initializes

### 3. Files to Update

| File | Changes |
|------|---------|
| `src/shared/languages.py` | CREATE |
| `src/shared/database_models.py` | Remove 'fr' defaults |
| `src/shared/database_ui.py` | Import languages.py, use get_last_language() |
| `src/shared/setup_ui.py` | Import languages.py |
| `src/shared/reader_ui.py` | Remove defaults |
| `src/shared/gpt_translator.py` | Import languages.py, remove hardcoded dicts |
| `src/shared/vocabulary_panel.py` | Remove 'fr' default |
| `src/gentexter_mode/gentexter_config_ui.py` | Use get_last_language(), save on generate |
| `src/gentexter_mode/orchestrator_updated.py` | Remove defaults |
| `src/gentexter_mode/text_generator.py` | Remove 'French' default |
| `src/gentexter_mode/spaced_repetition_selector.py` | Delete LANGUAGE_CODE_MAP, import languages.py |
| `src/transcriber_mode/ui.py` | Import languages.py, use get_last_language() |
| `src/transcriber_mode/transcriber.py` | Remove 'fr' default |

## Behavior Change

Before: Always defaults to French, user must change every session
After: Remembers last selected language across all modules
