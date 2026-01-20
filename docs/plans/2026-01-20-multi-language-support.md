# Multi-Language Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to practice vocabulary in multiple source languages, all translating to their configured mother tongue.

**Architecture:** Extend existing config system with `mother_tongue` setting. Modify SetupWindow to ask for both API key and mother tongue. Add language tabs to DatabaseView for filtering. Update AddWordDialog with language selector.

**Tech Stack:** Python, Tkinter, SQLite (existing), JSON config

---

## Task 1: Add Mother Tongue to Config System

**Files:**
- Modify: `src/shared/config.py:80-100`

**Step 1: Add save_mother_tongue method**

In `src/shared/config.py`, add after `save_api_key` method (around line 89):

```python
def save_mother_tongue(self, language_code):
    """Save mother tongue to user settings."""
    settings = self.load_user_settings()
    settings['mother_tongue'] = language_code
    path = self.get_user_settings_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

def get_mother_tongue(self):
    """Get mother tongue from user settings."""
    settings = self.load_user_settings()
    return settings.get('mother_tongue')
```

**Step 2: Verify by running the app**

Run: `python main.py`
Expected: App starts without errors (no functional change yet)

**Step 3: Commit**

```bash
git add src/shared/config.py
git commit -m "feat(config): add mother tongue save/get methods"
```

---

## Task 2: Update Setup Window for Mother Tongue

**Files:**
- Modify: `src/shared/setup_ui.py`

**Step 1: Add language dropdown to setup UI**

Replace `src/shared/setup_ui.py` content with updated version that includes mother tongue dropdown:

```python
import tkinter as tk
from tkinter import messagebox, ttk
from .styles import Colors, Fonts, Spacing, center_top_window

class SetupWindow:
    def __init__(self, master, config, on_success):
        self.master = master
        self.config = config
        self.on_success = on_success

        # Get available languages from config
        self.available_languages = self.config.get('vocabulary.languages.available_languages', [
            ["English", "en"],
            ["German", "de"],
            ["French", "fr"],
            ["Spanish", "es"]
        ])

        self.setup_ui()

    def setup_ui(self):
        self.master.title("InfiniLing - Setup")
        window_width, window_height = 450, 380
        self.master.configure(bg=Colors.BACKGROUND)
        center_top_window(self.master, width=window_width, height=window_height)

        main_frame = tk.Frame(self.master, bg=Colors.BACKGROUND, padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')

        # Title
        tk.Label(main_frame, text="Welcome to InfiniLing", font=("Segoe UI", 18, "bold"),
                 bg=Colors.BACKGROUND, fg=Colors.PRIMARY).pack(pady=(0, 20))

        tk.Label(main_frame, text="Let's set up your learning environment.",
                 font=Fonts.BODY, bg=Colors.BACKGROUND, justify="center").pack(pady=(0, 20))

        # API Key Section
        tk.Label(main_frame, text="OpenAI API Key", font=Fonts.BODY_BOLD,
                 bg=Colors.BACKGROUND).pack(anchor='w')
        self.key_entry = tk.Entry(main_frame, font=Fonts.BODY, width=40)
        self.key_entry.pack(pady=(5, 5), ipady=3)

        link_label = tk.Label(main_frame, text="Get your key at platform.openai.com",
                              font=Fonts.SMALL, bg=Colors.BACKGROUND, fg=Colors.PRIMARY, cursor="hand2")
        link_label.pack(anchor='w', pady=(0, 15))

        # Mother Tongue Section
        tk.Label(main_frame, text="Your Native Language", font=Fonts.BODY_BOLD,
                 bg=Colors.BACKGROUND).pack(anchor='w')
        tk.Label(main_frame, text="Translations will be shown in this language",
                 font=Fonts.SMALL, bg=Colors.BACKGROUND, fg=Colors.MEDIUM_GRAY).pack(anchor='w')

        self.language_var = tk.StringVar()
        language_names = [lang[0] for lang in self.available_languages]
        self.language_combo = ttk.Combobox(main_frame, textvariable=self.language_var,
                                           values=language_names, width=37, state='readonly')
        self.language_combo.pack(pady=(5, 20), ipady=3)
        # Default to first language
        if language_names:
            self.language_combo.current(0)

        # Buttons
        btn_frame = tk.Frame(main_frame, bg=Colors.BACKGROUND)
        btn_frame.pack(fill='x', pady=(10, 0))

        tk.Button(btn_frame, text="Save and Continue", command=self.save_settings,
                  font=Fonts.BODY_BOLD, bg=Colors.PRIMARY, fg="white",
                  padx=20, pady=8, relief='flat', cursor="hand2").pack(side='right')

        tk.Button(btn_frame, text="Exit", command=self.master.destroy,
                  font=Fonts.BODY, bg=Colors.LIGHT,
                  padx=20, pady=8, relief='flat', cursor="hand2").pack(side='left')

    def save_settings(self):
        user_key = self.key_entry.get().strip()
        selected_language_name = self.language_var.get()

        # Find language code from name
        language_code = None
        for name, code in self.available_languages:
            if name == selected_language_name:
                language_code = code
                break

        # Validate API Key
        if not (user_key.startswith("sk-") and len(user_key) > 20):
            messagebox.showerror("Error", "Please provide a valid OpenAI API Key (starting with 'sk-').")
            return

        # Validate language selection
        if not language_code:
            messagebox.showerror("Error", "Please select your native language.")
            return

        # Save both settings
        self.config.save_api_key(user_key)
        self.config.save_mother_tongue(language_code)

        messagebox.showinfo("Success", "Settings saved successfully!")
        self.on_success()
```

**Step 2: Update main.py to check for mother tongue**

In `main.py`, update the check around line 48:

```python
if not api_key or not config.get_mother_tongue():
    # Launch setup if no key or mother tongue found
    SetupWindow(root, config, start_app)
else:
    # Update environment for immediate use
    os.environ['OPENAI_API_KEY'] = api_key
    start_app()
```

**Step 3: Test the setup flow**

Run: `python main.py`
- Delete `~/.infiniling/settings.json` first to trigger setup
- Verify setup dialog shows both API key and language dropdown
- Verify saving works

**Step 4: Commit**

```bash
git add src/shared/setup_ui.py main.py
git commit -m "feat(setup): add mother tongue selection to setup wizard"
```

---

## Task 3: Add Settings Dialog

**Files:**
- Modify: `src/shared/database_ui.py`

**Step 1: Create SettingsDialog class**

Add this class at the top of `database_ui.py` (after imports, before AddWordDialog):

```python
class SettingsDialog:
    """Minimal settings dialog for API key and mother tongue."""

    def __init__(self, parent, config, on_save=None):
        self.parent = parent
        self.config = config
        self.on_save = on_save

        self.available_languages = self.config.get('vocabulary.languages.available_languages', [
            ["English", "en"],
            ["German", "de"],
            ["French", "fr"],
            ["Spanish", "es"]
        ])

        self.create_dialog()

    def create_dialog(self):
        """Create the settings dialog."""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("Settings")
        self.dialog.configure(bg=Colors.WHITE)
        self.dialog.resizable(False, False)

        # Center dialog
        dialog_width, dialog_height = 350, 250
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog_width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Title
        title_frame = Frame(self.dialog, bg=Colors.WHITE)
        title_frame.pack(fill='x', padx=Spacing.LG, pady=Spacing.MD)

        Label(title_frame, text="Settings", font=Fonts.HEADING,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        close_btn = Button(title_frame, text="X", font=Fonts.BODY,
                          bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY, relief='flat', bd=0,
                          command=self.dialog.destroy)
        close_btn.pack(side='right')

        # Form
        form_frame = Frame(self.dialog, bg=Colors.WHITE)
        form_frame.pack(fill='both', expand=True, padx=Spacing.LG, pady=Spacing.MD)

        # API Key
        Label(form_frame, text="OpenAI API Key", font=Fonts.BODY_BOLD,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.key_entry = Entry(form_frame, font=Fonts.BODY, width=35)
        self.key_entry.pack(fill='x', pady=(0, Spacing.MD))

        # Pre-fill current API key
        current_key = self.config.get_api_key() or ""
        self.key_entry.insert(0, current_key)

        # Mother Tongue
        Label(form_frame, text="Native Language", font=Fonts.BODY_BOLD,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')

        self.language_var = StringVar()
        language_names = [lang[0] for lang in self.available_languages]
        self.language_combo = ttk.Combobox(form_frame, textvariable=self.language_var,
                                           values=language_names, width=32, state='readonly')
        self.language_combo.pack(fill='x', pady=(0, Spacing.MD))

        # Pre-select current mother tongue
        current_code = self.config.get_mother_tongue()
        for i, (name, code) in enumerate(self.available_languages):
            if code == current_code:
                self.language_combo.current(i)
                break

        # Buttons
        btn_frame = Frame(self.dialog, bg=Colors.WHITE)
        btn_frame.pack(fill='x', padx=Spacing.LG, pady=Spacing.MD)

        cancel_btn = Button(btn_frame, text="Cancel", font=Fonts.BODY,
                           bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, relief='flat', bd=0,
                           padx=Spacing.LG, pady=Spacing.SM,
                           command=self.dialog.destroy)
        cancel_btn.pack(side='left')

        save_btn = Button(btn_frame, text="Save", font=Fonts.BODY_BOLD,
                         bg=Colors.PRIMARY, fg=Colors.WHITE, relief='flat', bd=0,
                         padx=Spacing.LG, pady=Spacing.SM,
                         command=self.save_settings)
        save_btn.pack(side='right')

    def save_settings(self):
        """Save settings and close dialog."""
        api_key = self.key_entry.get().strip()
        selected_name = self.language_var.get()

        # Find language code
        language_code = None
        for name, code in self.available_languages:
            if name == selected_name:
                language_code = code
                break

        # Validate
        if api_key and not (api_key.startswith("sk-") and len(api_key) > 20):
            messagebox.showerror("Error", "Invalid API key format", parent=self.dialog)
            return

        # Save
        if api_key:
            self.config.save_api_key(api_key)
        if language_code:
            self.config.save_mother_tongue(language_code)

        self.dialog.destroy()
        if self.on_save:
            self.on_save()
```

**Step 2: Add settings icon to DatabaseView header**

In `DatabaseView.create_header()` method (around line 297), add settings button:

```python
def create_header(self):
    """Create header with navigation."""
    header_frame = Frame(self.main_frame, bg=Colors.CONTENT_BG)
    header_frame.pack(fill='x', pady=(0, Spacing.MD))

    # Back button
    back_btn = StyledWidgets.create_back_button(header_frame, self.go_back)
    back_btn.pack(side='left')

    # Title
    title = Label(header_frame, text="My Database",
                 font=Fonts.TITLE, bg=Colors.CONTENT_BG, fg=Colors.DARK_GRAY)
    title.pack(side='left', padx=(Spacing.LG, 0))

    # Settings button (right side)
    settings_btn = Button(header_frame, text="\u2699", font=("Segoe UI", 16),
                         bg=Colors.CONTENT_BG, fg=Colors.MEDIUM_GRAY, relief='flat', bd=0,
                         command=self.show_settings)
    settings_btn.pack(side='right')

def show_settings(self):
    """Show settings dialog."""
    SettingsDialog(self.master, self.config)
```

**Step 3: Test settings dialog**

Run: `python main.py`
- Go to "My Database"
- Click settings icon (gear) in header
- Verify dialog shows current settings
- Test saving changes

**Step 4: Commit**

```bash
git add src/shared/database_ui.py
git commit -m "feat(ui): add settings dialog with API key and mother tongue"
```

---

## Task 4: Add Language Tabs to DatabaseView

**Files:**
- Modify: `src/shared/database_ui.py`

**Step 1: Add tab bar creation method**

Add this method to `DatabaseView` class:

```python
def create_language_tabs(self):
    """Create horizontal language tabs for filtering."""
    # Get languages with word counts from database
    language_counts = self.db_manager.get_language_counts()

    if not language_counts:
        self.current_language = None
        return

    # Sort by count descending, select the one with most words
    sorted_langs = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
    if not hasattr(self, 'current_language') or self.current_language is None:
        self.current_language = sorted_langs[0][0]  # Language code with most words

    # Tab container
    self.tab_frame = Frame(self.main_frame, bg=Colors.CONTENT_BG)
    self.tab_frame.pack(fill='x', pady=(0, Spacing.SM))

    # Get language name mapping
    available_languages = self.config.get('vocabulary.languages.available_languages', [])
    code_to_name = {code: name for name, code in available_languages}

    self.tab_buttons = {}
    for lang_code, count in sorted_langs:
        lang_name = code_to_name.get(lang_code, lang_code.upper())
        is_active = lang_code == self.current_language

        bg_color = Colors.PRIMARY if is_active else Colors.LIGHT_GRAY
        fg_color = Colors.WHITE if is_active else Colors.DARK_GRAY

        tab_btn = Button(self.tab_frame, text=f"{lang_name}",
                        font=Fonts.BODY_BOLD if is_active else Fonts.BODY,
                        bg=bg_color, fg=fg_color, relief='flat', bd=0,
                        padx=Spacing.MD, pady=Spacing.XS,
                        command=lambda lc=lang_code: self.switch_language(lc))
        tab_btn.pack(side='left', padx=(0, Spacing.XS))
        self.tab_buttons[lang_code] = tab_btn

def switch_language(self, language_code):
    """Switch to a different language tab."""
    self.current_language = language_code

    # Update tab button styles
    for code, btn in self.tab_buttons.items():
        if code == language_code:
            btn.config(bg=Colors.PRIMARY, fg=Colors.WHITE, font=Fonts.BODY_BOLD)
        else:
            btn.config(bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, font=Fonts.BODY)

    # Reload words with new filter
    self.load_words()
```

**Step 2: Add get_language_counts to DatabaseManager**

In `src/shared/database_models.py`, add this method to `DatabaseManager` class:

```python
def get_language_counts(self):
    """Get count of words per source language."""
    with self.session_scope() as session:
        from sqlalchemy import func
        results = session.query(
            Vocabulary.language_from,
            func.count(Vocabulary.id)
        ).group_by(Vocabulary.language_from).all()
        return {lang: count for lang, count in results if lang}
```

**Step 3: Update create_widgets to include tabs**

In `DatabaseView.create_widgets()`, add tab creation after header:

```python
def create_widgets(self):
    """Create all UI widgets."""
    # Main container
    self.main_frame = Frame(self.master, bg=Colors.CONTENT_BG)
    self.main_frame.pack(fill='both', expand=True, padx=Spacing.LG, pady=Spacing.LG)

    # Header with back button and title
    self.create_header()

    # Language tabs
    self.current_language = None
    self.create_language_tabs()

    # Toolbar with Add button and word count
    self.create_toolbar()

    # Table area
    self.create_table_area()
```

**Step 4: Update load_words to filter by language**

Modify `load_words()` method to filter by current language:

```python
def load_words(self):
    """Load words from database and update display."""
    # Clear existing rows
    for widget in self.table_frame.winfo_children():
        widget.destroy()

    # Get words filtered by current language
    if self.current_language:
        words = self.db_manager.get_words_by_language(self.current_language)
    else:
        words = self.db_manager.get_all_words()

    words.sort(key=lambda w: w.date_added or '', reverse=True)

    self.count_label.config(text=f"Total: {len(words)} words")

    # Track expanded rows
    self.expanded_rows = set()
    self.row_widgets = {}

    for word in words:
        self.create_word_row(word)
```

**Step 5: Add get_words_by_language to DatabaseManager**

In `src/shared/database_models.py`:

```python
def get_words_by_language(self, language_from):
    """Get all words for a specific source language."""
    with self.session_scope() as session:
        words = session.query(Vocabulary).filter(
            Vocabulary.language_from == language_from
        ).all()
        # Detach from session
        for word in words:
            session.expunge(word)
        return words
```

**Step 6: Test language tabs**

Run: `python main.py`
- Add some words (they'll be in default language)
- Go to "My Database"
- Verify tabs appear for languages with words
- Test switching tabs filters the list

**Step 7: Commit**

```bash
git add src/shared/database_ui.py src/shared/database_models.py
git commit -m "feat(ui): add language tabs to database view"
```

---

## Task 5: Update AddWordDialog with Language Selector

**Files:**
- Modify: `src/shared/database_ui.py`

**Step 1: Modify AddWordDialog to accept current_language parameter**

Update `AddWordDialog.__init__`:

```python
def __init__(self, parent, db_manager, config=None, current_language=None, on_success=None):
    """
    Initialize Add Word dialog.

    Args:
        parent: Parent window
        db_manager: DatabaseManager instance
        config: ConfigManager instance
        current_language: Currently selected language code (default for new words)
        on_success: Callback when word is added successfully
    """
    self.parent = parent
    self.db_manager = db_manager
    self.config = config
    self.current_language = current_language
    self.on_success = on_success
    self.is_auto_mode = True

    self.available_languages = []
    if config:
        self.available_languages = config.get('vocabulary.languages.available_languages', [])
    if not self.available_languages:
        self.available_languages = [["French", "fr"], ["German", "de"], ["English", "en"], ["Spanish", "es"]]

    self.create_dialog()
```

**Step 2: Add language dropdown to dialog**

In `AddWordDialog.create_dialog()`, add language selector at the top of the form (after mode toggle, before word field):

```python
# Form fields
form_frame = Frame(self.dialog, bg=Colors.WHITE)
form_frame.pack(fill='both', expand=True, padx=Spacing.LG, pady=Spacing.MD)

# Source Language dropdown (NEW)
Label(form_frame, text="Source Language", font=Fonts.BODY_BOLD,
      bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
self.lang_var = StringVar()
language_names = [lang[0] for lang in self.available_languages]
self.lang_combo = ttk.Combobox(form_frame, textvariable=self.lang_var,
                               values=language_names, width=37, state='readonly')
self.lang_combo.pack(fill='x', pady=(0, Spacing.SM))

# Set default to current language
if self.current_language:
    for i, (name, code) in enumerate(self.available_languages):
        if code == self.current_language:
            self.lang_combo.current(i)
            break
elif language_names:
    self.lang_combo.current(0)

# Word field (always enabled)
Label(form_frame, text="Word *", font=Fonts.BODY_BOLD,
      bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
# ... rest of fields ...
```

**Step 3: Update add_word_auto to use selected language**

```python
def add_word_auto(self, word_text):
    """Add word using GPT auto-fill."""
    self.status_label.config(text="Processing with GPT...")
    self.add_btn.config(state='disabled')
    self.dialog.update()

    # Get selected language
    selected_name = self.lang_var.get()
    language_from = 'fr'  # default
    for name, code in self.available_languages:
        if name == selected_name:
            language_from = code
            break

    # Get mother tongue
    language_to = 'de'  # default
    if self.config:
        language_to = self.config.get_mother_tongue() or 'de'

    import threading

    def worker():
        try:
            word = self.db_manager.add_word(
                word=word_text,
                translation=word_text,
                language_from=language_from,
                language_to=language_to
            )

            from src.shared.database_models import Vocabulary
            with self.db_manager.session_scope() as session:
                vocab = session.query(Vocabulary).filter(Vocabulary.id == word.id).first()
                if vocab:
                    enhanced = self.db_manager.enhance_word(vocab)
                    for attr in ['word', 'primary_translation', 'secondary_translation',
                               'translation', 'frequency_level', 'frequency_rank',
                               'example_sentence_original', 'example_sentence_translation']:
                        if hasattr(enhanced, attr):
                            setattr(vocab, attr, getattr(enhanced, attr))

            self.dialog.after(0, self.on_add_success)
        except Exception as e:
            self.dialog.after(0, lambda: self.on_add_error(str(e)))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
```

**Step 4: Update add_word_manual similarly**

```python
def add_word_manual(self, word_text):
    """Add word with manual entries."""
    translation = self.trans_entry.get().strip()

    if not translation:
        messagebox.showerror("Error", "Translation is required", parent=self.dialog)
        return

    # Get selected language
    selected_name = self.lang_var.get()
    language_from = 'fr'
    for name, code in self.available_languages:
        if name == selected_name:
            language_from = code
            break

    # Get mother tongue
    language_to = 'de'
    if self.config:
        language_to = self.config.get_mother_tongue() or 'de'

    try:
        self.db_manager.add_word(
            word=word_text,
            translation=translation,
            primary_translation=translation,
            secondary_translation=self.alt_trans_entry.get().strip() or None,
            frequency_level=self.freq_var.get() or None,
            example_sentence_original=self.example_orig_entry.get().strip() or None,
            example_sentence_translation=self.example_trans_entry.get().strip() or None,
            language_from=language_from,
            language_to=language_to
        )
        self.on_add_success()
    except Exception as e:
        self.on_add_error(str(e))
```

**Step 5: Update DatabaseView.show_add_dialog to pass config and current_language**

```python
def show_add_dialog(self):
    """Show the Add Word dialog."""
    AddWordDialog(
        self.master,
        self.db_manager,
        config=self.config,
        current_language=self.current_language,
        on_success=self.on_word_added
    )

def on_word_added(self):
    """Handle word added - refresh tabs and words."""
    # Recreate tabs in case a new language was added
    if hasattr(self, 'tab_frame'):
        self.tab_frame.destroy()
    self.create_language_tabs()
    self.load_words()
```

**Step 6: Increase dialog height**

Update dialog dimensions in `create_dialog`:
```python
dialog_width, dialog_height = 400, 480  # Increased from 420
```

**Step 7: Test adding words with language selection**

Run: `python main.py`
- Go to "My Database"
- Click "+ Add Word"
- Verify language dropdown appears with current tab's language selected
- Add word in a new language
- Verify new language tab appears

**Step 8: Commit**

```bash
git add src/shared/database_ui.py
git commit -m "feat(ui): add language selector to Add Word dialog"
```

---

## Task 6: Update Config Available Languages

**Files:**
- Modify: `config.json`

**Step 1: Expand available languages list**

Update `config.json` vocabulary.languages section:

```json
"languages": {
  "from": "fr",
  "to": "de",
  "available_languages": [
    ["German", "de"],
    ["English", "en"],
    ["French", "fr"],
    ["Spanish", "es"],
    ["Italian", "it"],
    ["Portuguese", "pt"],
    ["Russian", "ru"],
    ["Arabic", "ar"],
    ["Japanese", "ja"],
    ["Korean", "ko"],
    ["Chinese", "zh"]
  ]
}
```

**Step 2: Test with expanded language list**

Run: `python main.py`
- Check setup dialog shows all languages
- Check Add Word dialog shows all languages

**Step 3: Commit**

```bash
git add config.json
git commit -m "config: expand available languages list"
```

---

## Summary

After completing all tasks:
1. Users set mother tongue during setup (alongside API key)
2. Settings dialog allows changing both later
3. Database view has horizontal tabs filtering by source language
4. Add Word dialog includes language selector (defaults to active tab)
5. All translations go to the user's configured mother tongue

**Files modified:**
- `src/shared/config.py` - mother tongue save/get
- `src/shared/setup_ui.py` - setup flow with language
- `src/shared/database_ui.py` - settings dialog, tabs, language selector
- `src/shared/database_models.py` - language query methods
- `config.json` - expanded language list
- `main.py` - check for mother tongue in startup
