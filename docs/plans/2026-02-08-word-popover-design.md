# Word Popover — Design

## Summary

Double-click (desktop) or long-press (mobile) a word in a generated story to see its translation, frequency, and example sentence in a popover. Save it to vocabulary directly from the popover.

## Interaction

- **Desktop:** Double-click a word in the story text
- **Mobile:** Long-press (~500ms) a word
- Popover appears **below** the clicked word (flips above if near viewport bottom)
- Dismiss: click outside or X button

## Popover Content

1. Lemma (bold, large)
2. Translation (accent color)
3. Secondary translation (muted, if exists)
4. Frequency badge (same component as VocabularyList)
5. Example sentence + translation (from Tatoeba via enhance endpoint)
6. Save button (full width, accent)

## States

- **Loading:** Spinner + "Translating..."
- **Result:** Full content with Save button
- **Error:** Error message + "Try again"
- **Saved:** Button shows "Saved!" for 800ms, then popover closes

## API

Uses existing `POST /api/vocabulary/enhance` for translation, then `POST /api/vocabulary` for saving. No new endpoints needed.

## Component

`WordPopover` — function component inside `StoryGenerator.jsx`. No new files.

## Design Decisions

- Popover (not modal) — keeps sentence visible
- Long-press on mobile (not tap) — avoids accidental triggers
- No visual highlighting of saved words — keep text clean
- No editable fields in popover — just show result and save. User can edit later in vocabulary list.
