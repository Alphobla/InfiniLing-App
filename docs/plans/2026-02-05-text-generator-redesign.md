# Text Generator Redesign

## Overview

Redesign the StoryGenerator page into a streamlined "Text Generator" with automatic word selection based on spaced repetition due dates, configurable output parameters, and improved audio playback with speed controls.

## Key Design Decisions

- **No manual word selection** — words are auto-picked by most overdue due date
- **Study words are invisible** — user sees natural text, no highlighting or word list
- **Mother tongue is fixed** (from settings), but user can learn multiple languages
- **Source Language dropdown** only shows languages where user has vocabulary
- **Difficulty removed** — replaced by optional Language Style + Conversation Format
- **All refinements are optional** with no defaults selected

## UI Structure

### Settings Panel

#### Step 1: Database Configuration

- **Source Language** — dropdown populated from user's vocabulary languages only. Auto-selects if only one language.
- **Study Words Count** — slider, range 5–20. Info note: "Higher counts may reduce natural flow."

#### Step 2: Output Parameters

- **Target Text Length** — slider, range 20–300 (words)
- **Optional Refinements** (all optional, nothing selected by default):
  - **Topic / Subject Matter** — free text input. Placeholder: "e.g. Philosophy, Space Travel"
  - **Language Style** — radio buttons: Informal, Business, Academic, Creative, Other (reveals text input for custom)
  - **Conversation Format** — radio buttons: Dialogue, Essay, Monologue, Creative, Other (reveals text input for custom)

#### Footer

- **Reset** button — clears all settings to defaults
- **Generate** button

### Generated Text Display (appears below settings after generation)

- Clean text display — no highlighting, no word list shown
- Text presented naturally so user doesn't know which words are study targets

### Audio Controls

- **Listen** button to trigger TTS generation
- HTML5 audio player (play/pause, progress bar)
- **Speed controls:** turtle icon (slower) and rabbit icon (faster) flanking the player
  - Each click adjusts by ~5% (turtle: 0.95x, 0.90x... rabbit: 1.05x, 1.10x...)
  - Current speed shown between buttons (e.g. "1.0x")
  - Clicking the speed label resets to 1.0x

## Backend Changes

### Endpoint: `POST /api/generate/story`

**New parameters:**
- `language` (string, required) — source language
- `word_count` (int, required) — number of overdue words to pull (5-20)
- `target_length` (int, required) — target text length in words (20-300)
- `topic` (string, optional) — topic/subject matter
- `style` (string, optional) — language style
- `format` (string, optional) — conversation format

**Removed parameters:** `word_ids`, `difficulty`, `word_multiplier`

**Logic:**
1. Query most overdue vocabulary words for the given language, limited by `word_count`
2. Build prompt with target length + optional refinements (topic, style, format)
3. Send to OpenAI
4. Return generated text only (no words_used list)

### Audio endpoint unchanged
- `POST /api/generate/audio` stays the same
- Speed control is client-side via `playbackRate`
