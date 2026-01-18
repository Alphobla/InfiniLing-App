# My Database Feature Design

## Overview

Add a "My Database" kachel to the main menu that opens an elegant-minimalist table view of all vocabulary words stored in the database.

## Navigation & Layout

### Menu Integration
- New "My Database" kachel on main menu (alongside Transcriber/Gentexter)
- Color: Blue (#3498db)
- Icon: 📖
- Label: "My\nDatabase"

### Window Behavior
- Opens in same window (replaces menu content)
- Back button to return to menu
- Window resizes for table view (wider than menu)

### Layout Structure
```
┌─────────────────────────────────────────────────┐
│  ← Back          My Database                    │
├─────────────────────────────────────────────────┤
│  [+ Add Word]                    Total: 47 words│
├─────────────────────────────────────────────────┤
│  Word    │ Translation │ Freq  │ Added  │ Next │ Actions │
│──────────┼─────────────┼───────┼────────┼──────┼─────────│
│ ▶ chien  │ der Hund [& das Hündchen] │ Top 1k│ Jan 15 │ Jan 20│ ✏️ 🗑️ │
│ ▶ maison │ das Haus    │ Top 1k│ Jan 14 │ Jan 18│ ✏️ 🗑️ │
│   └─ Example: "Le chien dort." / "Der Hund..." │
└─────────────────────────────────────────────────┘
```

## Table Specifications

### Columns
| Column | Content | Width |
|--------|---------|-------|
| Word | Root word (e.g., "chien (m.)") | Flexible |
| Translation | Primary [& secondary] | Flexible |
| Frequency | Level badge (Top 1k, etc.) | Fixed ~70px |
| Added | Date added (e.g., "Jan 15") | Fixed ~70px |
| Next | Next review date | Fixed ~70px |
| Actions | Edit + Delete buttons | Fixed ~80px |

### Sorting
- Default: by date added (newest first)

### Row Expansion
- Click row (outside action buttons) to expand/collapse
- Expanded view shows example sentence (original + translation)
- Visual indicator: ▶ (collapsed) / ▼ (expanded)
- Expanded area has light gray background

### Visual Style
- Frequency badges color-coded (green common → red rare)
- "Due!" label in red when overdue
- Subtle row hover effect
- Matches app aesthetic (Segoe UI, white/gray palette)

## Inline Editing

### Trigger
- Click ✏️ button on row

### Edit Mode
- Row fields become editable inputs
- Action buttons change: ✏️🗑️ → ✅ Save / ❌ Cancel

### Editable Fields
- Word
- Translation (primary)
- Translation (secondary)
- Frequency level
- Example sentences (original + translation)

### Non-Editable
- Date added (auto-managed)
- Next review date (algorithm-managed)

### Exit Edit Mode
- Save: validates & saves changes, restores normal view
- Cancel: discards changes, restores normal view

## Add Word Form

### Modal Dialog
Opens when clicking "+ Add Word" button.

```
┌─────────────────────────────────────────┐
│           Add New Word            ✕     │
├─────────────────────────────────────────┤
│  Mode:   [Auto ●───○ Manual]            │
├─────────────────────────────────────────┤
│                                         │
│  Word*:  [________________]             │
│                                         │
│  ─ ─ ─ Auto mode fills these ─ ─ ─ ─   │
│                                         │
│  Translation*:    [________________]    │
│  Alt Translation: [________________]    │
│  Frequency:       [▼ Select level  ]    │
│  Example (orig):  [________________]    │
│  Example (trans): [________________]    │
│                                         │
│         [Cancel]    [Add Word]          │
└─────────────────────────────────────────┘
```

### Auto Mode (default)
- Only "Word" field enabled/required
- Other fields disabled (grayed out)
- On submit: GPT fills translation, frequency, examples

### Manual Mode
- All fields enabled
- Required: Word, Translation
- Optional: Alt Translation, Frequency, Examples
- Frequency dropdown options: Top 100, Top 1k, Top 5k, Top 10k, Top 20k, Top 50k, Rare

## Delete Confirmation

### Dialog
```
┌─────────────────────────────────────┐
│         Delete Word?                │
├─────────────────────────────────────┤
│                                     │
│  Are you sure you want to delete    │
│  "chien (m.)" from your database?   │
│                                     │
│  This action cannot be undone.      │
│                                     │
│      [Cancel]    [Delete]           │
└─────────────────────────────────────┘
```

## Implementation Files

### New File
- `src/shared/database_ui.py` - Contains `DatabaseView` class

### Modified Files
- `src/shared/menu.py` - Add new kachel and navigation
- `src/shared/database_models.py` - Add delete method if missing

## Database Methods Required
- `get_all_words()` - existing
- `add_word()` - existing
- `enhance_word()` - existing (for auto mode)
- `delete_word(id)` - add if missing
- `update_word(id, **fields)` - add if missing
- `get_due_days(id)` - existing
