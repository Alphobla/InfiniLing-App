"""
Database View UI for browsing and managing vocabulary words.
"""

import tkinter as tk
from tkinter import Frame, Label, Button, messagebox, Entry, Canvas, Scrollbar, ttk, Toplevel, StringVar, filedialog
from .styles import Colors, Fonts, Spacing, center_top_window
from .style_utils import StyledWidgets, CommonPatterns
from .database_models import DatabaseManager
from .languages import get_all_languages, get_name, get_code


class SettingsDialog:
    """Minimal settings dialog for API key and mother tongue."""

    def __init__(self, parent, config, on_save=None):
        self.parent = parent
        self.config = config
        self.on_save = on_save

        self.available_languages = get_all_languages()  # [(name, code), ...]

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


class AddWordDialog:
    """Modal dialog for adding new words."""

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

        self.available_languages = get_all_languages()  # [(name, code), ...]

        self.create_dialog()

    def create_dialog(self):
        """Create the dialog window."""
        self.dialog = Toplevel(self.parent)
        self.dialog.title("Add New Word")
        self.dialog.configure(bg=Colors.WHITE)
        self.dialog.resizable(False, False)

        # Center dialog
        dialog_width, dialog_height = 400, 700
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog_width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog_height // 2)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        # Make modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Title
        title_frame = Frame(self.dialog, bg=Colors.WHITE)
        title_frame.pack(fill='x', padx=Spacing.LG, pady=Spacing.MD)

        Label(title_frame, text="Add New Word", font=Fonts.HEADING,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(side='left')

        close_btn = Button(title_frame, text="X", font=Fonts.BODY,
                          bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY, relief='flat', bd=0,
                          command=self.dialog.destroy)
        close_btn.pack(side='right')

        # Mode toggle
        mode_frame = Frame(self.dialog, bg=Colors.LIGHT_GRAY)
        mode_frame.pack(fill='x', padx=Spacing.LG, pady=Spacing.SM)

        Label(mode_frame, text="Mode:", font=Fonts.BODY,
              bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY).pack(side='left', padx=Spacing.SM)

        self.auto_btn = Button(mode_frame, text="Auto", font=Fonts.BODY_BOLD,
                              bg=Colors.PRIMARY, fg=Colors.WHITE, relief='flat', bd=0,
                              padx=Spacing.MD, pady=Spacing.XS,
                              command=lambda: self.set_mode(True))
        self.auto_btn.pack(side='left', padx=2)

        self.manual_btn = Button(mode_frame, text="Manual", font=Fonts.BODY,
                                bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, relief='flat', bd=0,
                                padx=Spacing.MD, pady=Spacing.XS,
                                command=lambda: self.set_mode(False))
        self.manual_btn.pack(side='left', padx=2)

        # Form fields
        form_frame = Frame(self.dialog, bg=Colors.WHITE)
        form_frame.pack(fill='both', expand=True, padx=Spacing.LG, pady=Spacing.MD)

        # Source Language dropdown
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
        self.word_entry = Entry(form_frame, font=Fonts.BODY, width=40)
        self.word_entry.pack(fill='x', pady=(0, Spacing.SM))

        # Separator
        Label(form_frame, text="--- Auto mode fills these ---",
              font=Fonts.SMALL, bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY).pack(pady=Spacing.XS)

        # Translation field
        Label(form_frame, text="Translation *", font=Fonts.BODY_BOLD,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.trans_entry = Entry(form_frame, font=Fonts.BODY, width=40, state='disabled')
        self.trans_entry.pack(fill='x', pady=(0, Spacing.SM))

        # Alt translation
        Label(form_frame, text="Alt Translation", font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.alt_trans_entry = Entry(form_frame, font=Fonts.BODY, width=40, state='disabled')
        self.alt_trans_entry.pack(fill='x', pady=(0, Spacing.SM))

        # Frequency dropdown
        Label(form_frame, text="Frequency", font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.freq_var = StringVar()
        freq_options = ["", "Top 100", "Top 1,000", "Top 5,000", "Top 10,000",
                       "Top 20,000", "Top 50,000", "Top 100,000", "Rare"]
        self.freq_combo = ttk.Combobox(form_frame, textvariable=self.freq_var,
                                       values=freq_options, width=37, state='disabled')
        self.freq_combo.pack(fill='x', pady=(0, Spacing.SM))

        # Example sentence
        Label(form_frame, text="Example (original)", font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.example_orig_entry = Entry(form_frame, font=Fonts.BODY, width=40, state='disabled')
        self.example_orig_entry.pack(fill='x', pady=(0, Spacing.SM))

        Label(form_frame, text="Example (translation)", font=Fonts.BODY,
              bg=Colors.WHITE, fg=Colors.DARK_GRAY).pack(anchor='w')
        self.example_trans_entry = Entry(form_frame, font=Fonts.BODY, width=40, state='disabled')
        self.example_trans_entry.pack(fill='x', pady=(0, Spacing.SM))

        # Buttons
        btn_frame = Frame(self.dialog, bg=Colors.WHITE)
        btn_frame.pack(fill='x', padx=Spacing.LG, pady=Spacing.MD)

        cancel_btn = Button(btn_frame, text="Cancel", font=Fonts.BODY,
                           bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, relief='flat', bd=0,
                           padx=Spacing.LG, pady=Spacing.SM,
                           command=self.dialog.destroy)
        cancel_btn.pack(side='left')

        self.add_btn = Button(btn_frame, text="Add Word", font=Fonts.BODY_BOLD,
                             bg=Colors.SUCCESS, fg=Colors.WHITE, relief='flat', bd=0,
                             padx=Spacing.LG, pady=Spacing.SM,
                             command=self.add_word)
        self.add_btn.pack(side='right')

        # Status label for loading
        self.status_label = Label(self.dialog, text="", font=Fonts.SMALL,
                                  bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY)
        self.status_label.pack(pady=(0, Spacing.SM))

    def set_mode(self, is_auto):
        """Switch between auto and manual mode."""
        self.is_auto_mode = is_auto

        # Update button styles
        if is_auto:
            self.auto_btn.config(bg=Colors.PRIMARY, fg=Colors.WHITE, font=Fonts.BODY_BOLD)
            self.manual_btn.config(bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, font=Fonts.BODY)
            state = 'disabled'
        else:
            self.auto_btn.config(bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, font=Fonts.BODY)
            self.manual_btn.config(bg=Colors.PRIMARY, fg=Colors.WHITE, font=Fonts.BODY_BOLD)
            state = 'normal'

        # Update field states
        self.trans_entry.config(state=state)
        self.alt_trans_entry.config(state=state)
        self.freq_combo.config(state='readonly' if state == 'normal' else 'disabled')
        self.example_orig_entry.config(state=state)
        self.example_trans_entry.config(state=state)

    def add_word(self):
        """Add the word to the database."""
        word_text = self.word_entry.get().strip()

        if not word_text:
            messagebox.showerror("Error", "Word is required", parent=self.dialog)
            return

        if self.is_auto_mode:
            self.add_word_auto(word_text)
        else:
            self.add_word_manual(word_text)

    def add_word_auto(self, word_text):
        """Add word using GPT auto-fill."""
        # Get selected language
        selected_name = self.lang_var.get()
        language_from = get_code(selected_name)
        if not language_from:
            language_from = self.current_language

        # Get mother tongue - required, no fallback
        if not self.config:
            raise ValueError("ConfigManager is required for add_word_auto")
        language_to = self.config.get_mother_tongue()
        if not language_to:
            messagebox.showerror("Error", "Mother tongue not configured. Please set it in Settings.", parent=self.dialog)
            return

        # Get API key before starting thread
        api_key = self.config.get_api_key() if self.config else None
        if not api_key:
            messagebox.showerror("Error", "No API key configured. Please add your OpenAI API key in Settings.", parent=self.dialog)
            return

        # Show processing status
        self.status_label.config(text="Processing with GPT...")
        self.add_btn.config(state='disabled')
        self.dialog.update()

        import threading

        def worker():
            try:
                # Add word and let enhance_word fill the details
                word = self.db_manager.add_word(
                    word=word_text,
                    translation=word_text,  # Temporary, will be enhanced
                    language_from=language_from,
                    language_to=language_to
                )

                # Enhance the word (GPT translation, frequency, examples)
                from src.shared.database_models import Vocabulary
                with self.db_manager.session_scope() as session:
                    vocab = session.query(Vocabulary).filter(Vocabulary.id == word.id).first()
                    if vocab:
                        enhanced = self.db_manager.enhance_word(vocab, api_key=api_key)
                        for attr in ['word', 'primary_translation', 'secondary_translation',
                                   'translation', 'frequency_level', 'frequency_rank',
                                   'example_sentence_original', 'example_sentence_translation']:
                            if hasattr(enhanced, attr):
                                setattr(vocab, attr, getattr(enhanced, attr))

                self.dialog.after(0, self.on_add_success)
            except Exception as e:
                err_msg = str(e)
                self.dialog.after(0, lambda msg=err_msg: self.on_add_error(msg))

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def add_word_manual(self, word_text):
        """Add word with manual entries."""
        translation = self.trans_entry.get().strip()

        if not translation:
            messagebox.showerror("Error", "Translation is required", parent=self.dialog)
            return

        # Get selected language
        selected_name = self.lang_var.get()
        language_from = get_code(selected_name)
        if not language_from:
            language_from = self.current_language

        # Get mother tongue - default to first language alphabetically if not configured
        from .languages import LANGUAGES
        language_to = self.config.get_mother_tongue() if self.config else sorted(LANGUAGES.keys())[0]

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

    def on_add_success(self):
        """Handle successful word addition."""
        self.dialog.destroy()
        if self.on_success:
            self.on_success()

    def on_add_error(self, error_msg):
        """Handle error during word addition."""
        self.status_label.config(text="")
        self.add_btn.config(state='normal')
        messagebox.showerror("Error", f"Failed to add word: {error_msg}", parent=self.dialog)


class DatabaseView:
    """View for browsing and managing the vocabulary database."""

    def __init__(self, master, config=None, back_callback=None):
        """
        Initialize DatabaseView.

        Args:
            master: Tkinter root window
            config: ConfigManager instance
            back_callback: Function to call when back button is pressed
        """
        self.master = master
        self.config = config
        self.back_callback = back_callback
        self.db_manager = DatabaseManager()

        self.setup_window()
        self.create_widgets()
        self.load_words()

    def setup_window(self):
        """Configure the window."""
        self.master.title("My Database - InfiniLing")
        self.master.configure(bg=Colors.CONTENT_BG)
        center_top_window(self.master, width=900, height=600)

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

        # Table area (placeholder for now)
        self.create_table_area()

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

        self.tab_buttons = {}
        for lang_code, count in sorted_langs:
            lang_name = get_name(lang_code)
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

        # Save as last used language
        if self.config:
            self.config.save_last_language(language_code)

        # Update tab button styles
        for code, btn in self.tab_buttons.items():
            if code == language_code:
                btn.config(bg=Colors.PRIMARY, fg=Colors.WHITE, font=Fonts.BODY_BOLD)
            else:
                btn.config(bg=Colors.LIGHT_GRAY, fg=Colors.DARK_GRAY, font=Fonts.BODY)

        # Reload words with new filter
        self.load_words()

    def create_toolbar(self):
        """Create toolbar with Add button and stats."""
        toolbar_frame = Frame(self.main_frame, bg=Colors.CONTENT_BG)
        toolbar_frame.pack(fill='x', pady=(0, Spacing.MD))

        # Add Word button
        add_btn = Button(toolbar_frame, text="+ Add Word",
                        font=Fonts.BODY_BOLD, bg=Colors.SUCCESS, fg=Colors.WHITE,
                        activebackground='#218838', relief='flat', bd=0,
                        pady=Spacing.XS, padx=Spacing.MD,
                        command=self.show_add_dialog)
        add_btn.pack(side='left')

        # Add List button (secondary style)
        add_list_btn = Button(toolbar_frame, text="+ Add List",
                             font=Fonts.BODY, bg=Colors.CONTENT_BG, fg=Colors.PRIMARY,
                             activebackground=Colors.LIGHT_GRAY, relief='flat', bd=0,
                             pady=Spacing.XS, padx=Spacing.SM,
                             command=self.import_list)
        add_list_btn.pack(side='left', padx=(Spacing.SM, 0))

        # Word count label
        self.count_label = Label(toolbar_frame, text="Total: 0 words",
                                font=Fonts.BODY, bg=Colors.CONTENT_BG, fg=Colors.MEDIUM_GRAY)
        self.count_label.pack(side='right')

    def create_table_area(self):
        """Create the scrollable table display area."""
        # Container with border
        table_container = Frame(self.main_frame, bg=Colors.WHITE, relief='solid', bd=1)
        table_container.pack(fill='both', expand=True)

        # Header row
        self.create_table_header(table_container)

        # Canvas for scrolling
        self.canvas = Canvas(table_container, bg=Colors.WHITE, highlightthickness=0)
        scrollbar = Scrollbar(table_container, orient='vertical', command=self.canvas.yview)

        self.table_frame = Frame(self.canvas, bg=Colors.WHITE)

        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor='nw')

        # Bind events for scrolling
        self.table_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)

    def create_table_header(self, parent):
        """Create the table header row."""
        header_frame = Frame(parent, bg=Colors.BORDER_GRAY)
        header_frame.pack(fill='x')

        columns = [
            ("", 30),           # Expand indicator
            ("Word", 150),
            ("Translation", 200),
            ("Freq", 70),
            ("Added", 80),
            ("Next", 80),
            ("Actions", 90)
        ]

        for col_name, width in columns:
            col_frame = Frame(header_frame, bg=Colors.BORDER_GRAY, width=width)
            col_frame.pack(side='left', padx=1)
            col_frame.pack_propagate(False)

            label = Label(col_frame, text=col_name, font=Fonts.BODY_BOLD,
                         bg=Colors.BORDER_GRAY, fg=Colors.DARK_GRAY, anchor='w')
            label.pack(fill='x', padx=Spacing.XS, pady=Spacing.XS)

    def _on_frame_configure(self, event):
        """Update scroll region when frame size changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Update frame width when canvas size changes."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

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

    def create_word_row(self, word):
        """Create a single word row in the table."""
        row_frame = Frame(self.table_frame, bg=Colors.WHITE)
        row_frame.pack(fill='x', pady=1)

        # Store reference for expansion
        self.row_widgets[word.id] = {'frame': row_frame, 'word': word}

        # Main row content
        content_frame = Frame(row_frame, bg=Colors.WHITE)
        content_frame.pack(fill='x')

        # Expand indicator
        expand_label = Label(content_frame, text="▶", font=Fonts.SMALL,
                            bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY, width=3)
        expand_label.pack(side='left')
        self.row_widgets[word.id]['expand_label'] = expand_label

        # Word
        word_label = Label(content_frame, text=word.word or "", font=Fonts.BODY_BOLD,
                          bg=Colors.WHITE, fg=Colors.DARK_GRAY, width=18, anchor='w')
        word_label.pack(side='left', padx=Spacing.XS)

        # Translation with secondary
        translation_text = word.primary_translation or word.translation or ""
        if word.secondary_translation:
            translation_text += f" [& {word.secondary_translation}]"
        trans_label = Label(content_frame, text=translation_text, font=Fonts.BODY,
                           bg=Colors.WHITE, fg=Colors.PRIMARY, width=25, anchor='w')
        trans_label.pack(side='left', padx=Spacing.XS)

        # Frequency badge
        freq_text = word.frequency_level or "-"
        freq_color = self.get_frequency_color(word.frequency_level)
        freq_label = Label(content_frame, text=freq_text, font=Fonts.SMALL,
                          bg=freq_color, fg=Colors.WHITE, width=10)
        freq_label.pack(side='left', padx=Spacing.XS)

        # Date added
        added_text = word.date_added.strftime("%b %d") if word.date_added else "-"
        added_label = Label(content_frame, text=added_text, font=Fonts.SMALL,
                           bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY, width=10, anchor='w')
        added_label.pack(side='left', padx=Spacing.XS)

        # Next review
        due_days = self.db_manager.get_due_days(word.id)
        if due_days == 0:
            next_text = "Due!"
            next_color = Colors.ERROR
        else:
            next_text = f"in {due_days}d"
            next_color = Colors.MEDIUM_GRAY
        next_label = Label(content_frame, text=next_text, font=Fonts.SMALL,
                          bg=Colors.WHITE, fg=next_color, width=10, anchor='w')
        next_label.pack(side='left', padx=Spacing.XS)

        # Action buttons
        actions_frame = Frame(content_frame, bg=Colors.WHITE)
        actions_frame.pack(side='left', padx=Spacing.XS)

        edit_btn = Button(actions_frame, text="Edit", font=Fonts.SMALL,
                         bg=Colors.WHITE, fg=Colors.PRIMARY, relief='flat', bd=0,
                         command=lambda w=word: self.start_edit(w.id))
        edit_btn.pack(side='left', padx=2)

        delete_btn = Button(actions_frame, text="🗑️", font=Fonts.SMALL,
                           bg=Colors.WHITE, fg=Colors.ERROR, relief='flat', bd=0,
                           command=lambda w=word: self.confirm_delete(w.id))
        delete_btn.pack(side='left', padx=2)

        # Bind click for expansion (on row, not buttons)
        for widget in [content_frame, expand_label, word_label, trans_label,
                       freq_label, added_label, next_label]:
            widget.bind('<Button-1>', lambda e, wid=word.id: self.toggle_expand(wid))

        # Hover effect
        for widget in [content_frame, expand_label, word_label, trans_label,
                       freq_label, added_label, next_label]:
            widget.bind('<Enter>', lambda e, f=content_frame: self.on_row_enter(f))
            widget.bind('<Leave>', lambda e, f=content_frame: self.on_row_leave(f))

    def get_frequency_color(self, level):
        """Get color for frequency level."""
        colors = {
            "Top 100": "#1B5E20",
            "Top 1,000": "#2E7D32",
            "Top 5,000": "#388E3C",
            "Top 10,000": "#689F38",
            "Top 20,000": "#FBC02D",
            "Top 50,000": "#FF8F00",
            "Top 100,000": "#F57C00",
            "Rare": "#D32F2F",
        }
        return colors.get(level, Colors.MEDIUM_GRAY)

    def on_row_enter(self, frame):
        """Handle mouse enter on row."""
        frame.configure(bg=Colors.HOVER)
        for widget in frame.winfo_children():
            if isinstance(widget, (Label, Frame)):
                # Skip frequency badge (has colored background)
                current_bg = str(widget.cget('bg'))
                if current_bg in (Colors.WHITE, Colors.HOVER):
                    widget.configure(bg=Colors.HOVER)

    def on_row_leave(self, frame):
        """Handle mouse leave on row."""
        frame.configure(bg=Colors.WHITE)
        for widget in frame.winfo_children():
            if isinstance(widget, (Label, Frame)):
                # Skip frequency badge (has colored background)
                current_bg = str(widget.cget('bg'))
                if current_bg in (Colors.WHITE, Colors.HOVER):
                    widget.configure(bg=Colors.WHITE)

    def toggle_expand(self, word_id):
        """Toggle row expansion to show example sentences."""
        if word_id in self.expanded_rows:
            self.collapse_row(word_id)
        else:
            self.expand_row(word_id)

    def expand_row(self, word_id):
        """Expand a row to show example sentences."""
        if word_id not in self.row_widgets:
            return

        self.expanded_rows.add(word_id)
        row_data = self.row_widgets[word_id]
        word = row_data['word']

        # Update expand indicator
        row_data['expand_label'].config(text="▼")

        # Create expanded content
        expanded_frame = Frame(row_data['frame'], bg=Colors.LIGHT_GRAY)
        expanded_frame.pack(fill='x', padx=(30, 0), pady=(0, Spacing.XS))
        row_data['expanded_frame'] = expanded_frame

        # Example sentence
        if word.example_sentence_original:
            example_label = Label(expanded_frame,
                                 text=f"📝 {word.example_sentence_original}",
                                 font=Fonts.SMALL_ITALIC, bg=Colors.LIGHT_GRAY,
                                 fg=Colors.TEXT_GRAY, anchor='w', wraplength=600)
            example_label.pack(fill='x', padx=Spacing.SM, pady=(Spacing.XS, 0))

            if word.example_sentence_translation:
                trans_example = Label(expanded_frame,
                                     text=f"   {word.example_sentence_translation}",
                                     font=Fonts.SMALL, bg=Colors.LIGHT_GRAY,
                                     fg=Colors.MEDIUM_GRAY, anchor='w', wraplength=600)
                trans_example.pack(fill='x', padx=Spacing.SM, pady=(0, Spacing.XS))
        else:
            no_example = Label(expanded_frame, text="No example sentence",
                              font=Fonts.SMALL_ITALIC, bg=Colors.LIGHT_GRAY,
                              fg=Colors.MEDIUM_GRAY)
            no_example.pack(padx=Spacing.SM, pady=Spacing.XS)

    def collapse_row(self, word_id):
        """Collapse an expanded row."""
        if word_id not in self.row_widgets:
            return

        self.expanded_rows.discard(word_id)
        row_data = self.row_widgets[word_id]

        # Update expand indicator
        row_data['expand_label'].config(text="▶")

        # Remove expanded content
        if 'expanded_frame' in row_data:
            row_data['expanded_frame'].destroy()
            del row_data['expanded_frame']

    def start_edit(self, word_id):
        """Start editing a word row - replace display with input fields."""
        if word_id not in self.row_widgets:
            return

        row_data = self.row_widgets[word_id]
        word = row_data['word']

        # Collapse if expanded
        if word_id in self.expanded_rows:
            self.collapse_row(word_id)

        # Clear the row frame
        for widget in row_data['frame'].winfo_children():
            widget.destroy()

        # Create edit mode content
        edit_frame = Frame(row_data['frame'], bg=Colors.TILE_SELECTED)
        edit_frame.pack(fill='x', pady=1)
        row_data['edit_frame'] = edit_frame

        # Word entry
        word_entry = Entry(edit_frame, font=Fonts.BODY, width=15)
        word_entry.insert(0, word.word or "")
        word_entry.pack(side='left', padx=Spacing.XS, pady=Spacing.XS)
        row_data['word_entry'] = word_entry

        # Primary translation entry
        trans_entry = Entry(edit_frame, font=Fonts.BODY, width=15)
        trans_entry.insert(0, word.primary_translation or word.translation or "")
        trans_entry.pack(side='left', padx=Spacing.XS, pady=Spacing.XS)
        row_data['trans_entry'] = trans_entry

        # Secondary translation entry
        sec_trans_entry = Entry(edit_frame, font=Fonts.BODY, width=12)
        sec_trans_entry.insert(0, word.secondary_translation or "")
        sec_trans_entry.pack(side='left', padx=Spacing.XS, pady=Spacing.XS)
        row_data['sec_trans_entry'] = sec_trans_entry

        # Frequency dropdown
        freq_options = ["Top 100", "Top 1,000", "Top 5,000", "Top 10,000",
                       "Top 20,000", "Top 50,000", "Top 100,000", "Rare"]
        freq_var = tk.StringVar(value=word.frequency_level or "")
        freq_combo = ttk.Combobox(edit_frame, textvariable=freq_var,
                                  values=freq_options, width=10, state='readonly')
        freq_combo.pack(side='left', padx=Spacing.XS, pady=Spacing.XS)
        row_data['freq_var'] = freq_var

        # Save/Cancel buttons
        btn_frame = Frame(edit_frame, bg=Colors.TILE_SELECTED)
        btn_frame.pack(side='right', padx=Spacing.XS)

        save_btn = Button(btn_frame, text="✅", font=Fonts.SMALL,
                         bg=Colors.SUCCESS, fg=Colors.WHITE, relief='flat', bd=0,
                         command=lambda: self.save_edit(word_id))
        save_btn.pack(side='left', padx=2)

        cancel_btn = Button(btn_frame, text="❌", font=Fonts.SMALL,
                           bg=Colors.ERROR, fg=Colors.WHITE, relief='flat', bd=0,
                           command=lambda: self.cancel_edit(word_id))
        cancel_btn.pack(side='left', padx=2)

        # Focus on word entry
        word_entry.focus_set()

    def save_edit(self, word_id):
        """Save edited word data."""
        if word_id not in self.row_widgets:
            return

        row_data = self.row_widgets[word_id]

        # Get values from entries
        new_word = row_data['word_entry'].get().strip()
        new_trans = row_data['trans_entry'].get().strip()
        new_sec_trans = row_data['sec_trans_entry'].get().strip()
        new_freq = row_data['freq_var'].get()

        # Validate required fields
        if not new_word or not new_trans:
            messagebox.showerror("Error", "Word and Translation are required")
            return

        # Update in database
        success = self.db_manager.update_word(
            word_id,
            word=new_word,
            primary_translation=new_trans,
            translation=new_trans,  # Keep translation in sync
            secondary_translation=new_sec_trans or None,
            frequency_level=new_freq or None
        )

        if success:
            self.load_words()  # Refresh table
        else:
            messagebox.showerror("Error", "Failed to update word")

    def cancel_edit(self, word_id):
        """Cancel editing and restore row display."""
        self.load_words()  # Simply reload to restore original state

    def confirm_delete(self, word_id):
        """Show delete confirmation dialog."""
        word = self.row_widgets.get(word_id, {}).get('word')
        if not word:
            return

        result = messagebox.askyesno(
            "Delete Word?",
            f"Are you sure you want to delete \"{word.word}\" from your database?\n\nThis action cannot be undone.",
            icon='warning'
        )

        if result:
            self.delete_word(word_id)

    def delete_word(self, word_id):
        """Delete a word from the database."""
        success = self.db_manager.delete_word(word_id)
        if success:
            self.load_words()  # Refresh the table
        else:
            messagebox.showerror("Error", "Failed to delete word")

    def show_add_dialog(self):
        """Show the Add Word dialog."""
        AddWordDialog(
            self.master,
            self.db_manager,
            config=self.config,
            current_language=self.current_language,
            on_success=self.on_word_added
        )

    def import_list(self):
        """Import vocabulary from a CSV file."""
        filetypes = [
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Select Vocabulary File to Import",
            filetypes=filetypes
        )

        if not file_path:
            return  # User canceled

        try:
            # Use current language or last used language
            language_from = self.current_language or (self.config.get_last_language() if self.config else None)
            language_to = self.config.get_mother_tongue() if self.config else None

            if not language_from or not language_to:
                messagebox.showerror("Error", "Language not configured. Please set up languages first.")
                return

            results = self.db_manager.import_vocabulary_from_csv(
                file_path,
                language_from=language_from,
                language_to=language_to
            )

            if results['imported'] > 0:
                messagebox.showinfo("Import Successful",
                                  f"Total rows: {results['total_rows']}\n"
                                  f"Imported: {results['imported']} new words!\n\n"
                                  f"Skipped the rest (already exist).")
            else:
                messagebox.showinfo("Import Complete",
                                  f"No new words to import.\n\n"
                                  f"Total rows: {results['total_rows']}\n"
                                  f"All words already exist in database.")

            # Refresh the view
            self.on_word_added()

        except Exception as e:
            messagebox.showerror("Import Error", f"Import failed: {str(e)}")

    def on_word_added(self):
        """Handle word added - refresh tabs and words."""
        # Recreate tabs in case a new language was added
        if hasattr(self, 'tab_frame'):
            self.tab_frame.destroy()
        self.create_language_tabs()
        self.load_words()

    def go_back(self):
        """Return to main menu."""
        if self.back_callback:
            self.back_callback()

    def show_settings(self):
        """Show settings dialog."""
        SettingsDialog(self.master, self.config)
