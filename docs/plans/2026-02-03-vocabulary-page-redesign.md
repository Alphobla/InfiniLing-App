# Vocabulary Page Redesign

## Overview

Redesign the "My Words" vocabulary page to provide a well-organized view of all saved words with language tabs, sorting, expandable cards with full details, and inline editing.

## Structure

```
┌─────────────────────────────────────────────────────┐
│  My Words                            [+ Add Word]   │
├─────────────────────────────────────────────────────┤
│  [German (42)]  [French (18)]  [Spanish (7)]        │  ← Language tabs
├─────────────────────────────────────────────────────┤
│  Sort: [Date added ▼]  [Frequency]  [Due]           │  ← Sort controls
│  Search: [________________]                          │
├─────────────────────────────────────────────────────┤
│  Word cards...                                       │
└─────────────────────────────────────────────────────┘
```

- **Language tabs** at top showing language name + word count
- **Sort controls**: Date added (default), Frequency, Due
- **Search** filters current language tab
- Clicking same sort toggles ascending/descending

---

## Collapsed Card

Shows minimal info for quick scanning:

```
┌─────────────────────────────────────────────────────┐
│ der Hund        dog         [Top 1,000]  🔴         │
└─────────────────────────────────────────────────────┘
  ↑ lemma         ↑ translation  ↑ frequency   ↑ due indicator
```

**Due indicators:**
- 🔴 Red dot = due today or overdue
- 🟢 "New" badge = never reviewed
- Nothing = not due yet

---

## Expanded Card (View Mode)

Click card to expand inline:

```
┌─────────────────────────────────────────────────────────┐
│ der Hund                                    [Edit] [🗑]  │
│ ─────────────────────────────────────────────────────── │
│                                                         │
│ Translation      dog                                    │
│ Secondary        hound, canine                          │
│                                                         │
│ Frequency        [Top 1,000] (#847)                     │
│                                                         │
│ Example          Der Hund spielt im Garten.             │
│                  The dog plays in the garden.           │
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ Added: Jan 15, 2026                                     │
│ Next review: Tomorrow (interval: 4 days)                │
│ Reviewed: 3 times                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Expanded Card (Edit Mode)

Click "Edit" to make fields editable:

```
┌─────────────────────────────────────────────────────────┐
│ [der Hund___________]               [Save] [Cancel] [🗑] │
│ ─────────────────────────────────────────────────────── │
│                                                         │
│ Translation      [dog__________________]                │
│ Secondary        [hound, canine________]                │
│                                                         │
│ Frequency        [Top 1,000] (#847)       (read-only)   │
│                                                         │
│ Example          [Der Hund spielt im Garten.__________] │
│                  [The dog plays in the garden._________]│
│                                                         │
│ ─────────────────────────────────────────────────────── │
│ Added: Jan 15, 2026                       (read-only)   │
│ Next review: Tomorrow                     (read-only)   │
└─────────────────────────────────────────────────────────┘
```

**Editable fields:** lemma, translation, secondary translation, example sentences

**Read-only fields:** frequency (from GPT), dates, SRS stats

---

## Add Word Flow

Click "+ Add Word" → form appears at top of list:

```
┌─────────────────────────────────────────────────────────┐
│ Add Word                                       [Cancel] │
│ ─────────────────────────────────────────────────────── │
│                                                         │
│ Word             [________________]                     │
│ Language         [German ▼]                             │
│                                                         │
│                              [Translate]                │
└─────────────────────────────────────────────────────────┘
```

After "Translate" → GPT enhances word → shows expanded edit mode:

```
┌─────────────────────────────────────────────────────────┐
│ [der Hund___________]               [Save] [Cancel] [🗑] │
│ ─────────────────────────────────────────────────────── │
│ ... all fields editable, pre-filled from GPT ...        │
└─────────────────────────────────────────────────────────┘
```

- **Save** = keep the word
- **Cancel** = discard (not saved to DB)
- **Delete** = same as cancel for new words (consistent UI)

Language dropdown defaults to current tab. Mother tongue comes from user settings (not selectable).

---

## Frequency Badge Colors

| Level | Color | Hex |
|-------|-------|-----|
| Top 1,000 | Dark green | `#2E7D32` |
| Top 5,000 | Green | `#388E3C` |
| Top 10,000 | Light green | `#689F38` |
| Top 20,000 | Yellow | `#FBC02D` |
| Top 50,000 | Orange | `#FF8F00` |
| Rare | Red | `#D32F2F` |
| Unknown | Gray | `#757575` |

Badge has colored background with white text (dark text on yellow).

---

## Sort Behavior

| Sort | Order |
|------|-------|
| Date added | Newest first (default) |
| Frequency | Most common first (Top 1,000 → Rare) |
| Due | Most urgent first (overdue → due today → new → later) |

Active sort button is highlighted. Click again to toggle ascending/descending.

---

## Data Requirements

**From API (already available):**
- `lemma`, `word`, `translation`, `secondary_translation`
- `language_from`, `language_to`
- `frequency_rank`, `frequency_level`
- `example_sentence_original`, `example_sentence_translation`
- `next_review_date`, `review_interval_days`, `easiness_factor`
- `created_at`

**Needs to be added:**
- Review count (count of `vocabulary_occurrence` records per word)

---

## Component Structure

```
VocabularyList.jsx
├── LanguageTabs
├── SortControls
├── SearchInput
├── AddWordForm (when adding)
└── WordCard (map over words)
    ├── CollapsedView
    └── ExpandedView
        ├── ViewMode
        └── EditMode
```

---

## Implementation Notes

- Language tabs derived from distinct `language_from` values in user's vocabulary
- Default tab = user's `last_language` from settings, or first available
- Expanded state stored locally (only one card expanded at a time)
- Edit mode transforms labels → inputs (same layout)
- Add form appears inline at top, not in modal
- New word goes through: Add form → Translate (GPT) → Edit mode → Save
