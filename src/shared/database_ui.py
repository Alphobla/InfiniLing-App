"""
Database View UI for browsing and managing vocabulary words.
"""

from tkinter import Frame, Label, Button, Canvas, Scrollbar, messagebox
from .styles import Colors, Fonts, Spacing, center_top_window
from .style_utils import StyledWidgets, CommonPatterns
from .database_models import DatabaseManager


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

        # Get words sorted by date_added descending
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

        edit_btn = Button(actions_frame, text="✏️", font=Fonts.SMALL,
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
                widget.configure(bg=Colors.HOVER)

    def on_row_leave(self, frame):
        """Handle mouse leave on row."""
        frame.configure(bg=Colors.WHITE)
        for widget in frame.winfo_children():
            if isinstance(widget, (Label, Frame)):
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
        """Start editing a word row."""
        # Placeholder - will be implemented in Task 5
        messagebox.showinfo("Edit", f"Edit word {word_id} coming soon")

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
        # Placeholder - will be implemented in Task 6
        messagebox.showinfo("Add Word", "Add Word dialog coming soon")

    def go_back(self):
        """Return to main menu."""
        if self.back_callback:
            self.back_callback()
