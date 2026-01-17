"""
Database View UI for browsing and managing vocabulary words.
"""

from tkinter import Frame, Label, Button, messagebox
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
        """Create the table display area."""
        # Placeholder - will be implemented in Task 4
        self.table_frame = Frame(self.main_frame, bg=Colors.WHITE, relief='solid', bd=1)
        self.table_frame.pack(fill='both', expand=True)

        placeholder = Label(self.table_frame, text="Table will appear here",
                           font=Fonts.BODY, bg=Colors.WHITE, fg=Colors.MEDIUM_GRAY)
        placeholder.pack(expand=True)

    def load_words(self):
        """Load words from database and update display."""
        words = self.db_manager.get_all_words()
        self.count_label.config(text=f"Total: {len(words)} words")

    def show_add_dialog(self):
        """Show the Add Word dialog."""
        # Placeholder - will be implemented in Task 6
        messagebox.showinfo("Add Word", "Add Word dialog coming soon")

    def go_back(self):
        """Return to main menu."""
        if self.back_callback:
            self.back_callback()
