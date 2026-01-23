# Multi-Language Support Design

**Date:** 2026-01-20
**Status:** Approved

## Overview

Add support for practicing vocabulary in multiple source languages, all translating to the user's mother tongue. Users can switch between languages in the database view using horizontal tabs.

## Core Concept

- **Mother tongue:** A global setting (e.g., German) - all translations go TO this language
- **Source languages:** Multiple (French, Spanish, etc.) - the languages being learned
- **Storage:** All words in one database table, filtered by `language_from`

## Data Model

### No Schema Changes Required

Existing `Vocabulary` table already has:
- `language_from` - source language code (e.g., 'fr', 'es')
- `language_to` - target language code (the mother tongue)

### Config Additions

```json
{
  "user": {
    "mother_tongue": "de",
    "openai_api_key": "sk-..."
  }
}
```

## Components

### 1. Setup Dialog

**Trigger:** On app launch, if `mother_tongue` or `openai_api_key` is missing from config.

**Fields:**
1. OpenAI API Key - text field with link to platform.openai.com
2. Mother Tongue - dropdown with available languages

**Behavior:**
- Both fields required
- Blocks app until complete
- Saves to config.json

### 2. Settings Page

**Access:** Small settings icon in main UI

**Minimal dialog containing:**
- OpenAI API Key - text field (no masking), pre-filled
- Mother Tongue - dropdown, pre-filled
- Save / Cancel buttons

**Note:** Changing mother tongue affects future words only.

### 3. Database View - Language Tabs

**Horizontal tabs above word table:**
- Tabs appear dynamically based on languages with words in database
- Display language names (e.g., "French" not "fr")
- Active tab highlighted
- Default selection: tab with most words

**Filtering:**
- Table shows only words where `language_from` matches selected tab
- Query: `WHERE language_from = :selected AND language_to = :mother_tongue`

**No empty state needed:** Tabs only exist for languages with words.

### 4. Add Word Dialog

**New field:** Source Language dropdown
- Position: Top of dialog, before word input
- Default: Currently active tab's language
- Options: All available languages from config

**Target language:** Not shown - automatically uses mother tongue from config

**Flow (Auto mode):**
1. User selects source language (or accepts default)
2. User enters word
3. GPT translates from selected language → mother tongue
4. Word saved with correct language codes

**Side effect:** Adding a word in a new language creates that language's tab.

## Files to Modify

| File | Changes |
|------|---------|
| `config.json` | Add `user.mother_tongue` field |
| `database_ui.py` | Add language tabs, settings icon, settings dialog |
| `database_ui.py` (AddWordDialog) | Add source language dropdown |
| New: setup dialog | First-time setup for API key + mother tongue |

## Files Unchanged

- `database_models.py` - schema already supports languages
- `gpt_translator.py` - already accepts language parameters
- `frequency_analysis.py` - already language-aware

## UI Mockup (ASCII)

```
┌─────────────────────────────────────────────────────────┐
│  InfiniLing                                    [⚙]     │
├─────────────────────────────────────────────────────────┤
│  [ French ] [ Spanish ] [ Russian ]          [+ Add]   │
├─────────────────────────────────────────────────────────┤
│  ▶ │ la maison    │ das Haus      │ Top 1k │ Jan 15   │
│  ▶ │ le chat      │ die Katze     │ Top 5k │ Jan 14   │
│  ▶ │ manger       │ essen         │ Top 100│ Jan 12   │
└─────────────────────────────────────────────────────────┘
```

## Implementation Order

1. Config changes (add mother_tongue support)
2. Setup dialog (first-time flow)
3. Settings dialog (change settings later)
4. Database view tabs (filtering)
5. Add Word dialog (language dropdown)
