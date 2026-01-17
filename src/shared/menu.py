from tkinter import Tk, Frame, Button, Label, messagebox, ttk
from src.transcriber_mode.ui import WhisperInterface
from src.gentexter_mode.gentexter_config_ui import GentexterConfig
from src.shared.styles import Spacing, Colors, center_top_window
from src.shared.style_utils import CommonPatterns
from src.shared.database_ui import DatabaseView


class MainMenu:
    def __init__(self, master, config=None, vocab_service=None):
        """
        Initialize MainMenu with dependency injection.
        
        Args:
            master: Tkinter root window
            config: ConfigManager instance
            vocab_service: VocabularyApp service instance
        """
        self.master = master
        self.config = config
        self.vocab_service = vocab_service
        self.show_main_menu()

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.master.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        """Show the main menu"""
        self.clear_window()
        
        # Use config for window settings if available
        app_name = self.config.get('app.name')
        window_width, window_height = self.config.get_window_size('main_menu')
        bg_color = self.config.get('ui.colors.background')

        self.master.title(app_name)
        self.master.configure(bg=bg_color)
        self.master.resizable(False, False)
        center_top_window(self.master, width=window_width, height=window_height)

        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = Frame(self.master, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=Spacing.XL, pady=Spacing.XL)

        # Title
        title_label = Label(main_frame, text="🌍 InfiniLing", 
                           font=("Segoe UI", 24, "bold"), 
                           bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=(0, Spacing.XL))

        # Button container - horizontal layout
        button_frame = Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(expand=True)

        # Whisper Mode Button
        whisper_button = CommonPatterns.create_main_action_button(
            button_frame, 
            text="🎤\nTranscriber\nMode", 
            command=self.open_whisper_mode,
            button_type='large_square',
            bg=Colors.BUTTON_PAUSE,
            active_bg=Colors.BUTTON_PAUSE_HOVER,
            center=False
        )
        whisper_button.master.pack(side='left', padx=15, pady=10)

        # Wordstory Mode Button
        wordstory_button = CommonPatterns.create_main_action_button(
            button_frame,
            text="📚\nGentexter\nMode",
            command=self.open_wordstory_mode,
            button_type='large_square',
            bg=Colors.BUTTON_STOP,
            active_bg=Colors.BUTTON_STOP_HOVER,
            center=False
        )
        wordstory_button.master.pack(side='left', padx=15, pady=10)

        # Database Mode Button
        database_button = CommonPatterns.create_main_action_button(
            button_frame,
            text="📖\nMy\nDatabase",
            command=self.open_database_mode,
            button_type='large_square',
            bg=Colors.BUTTON_JUMP,  # Blue
            active_bg=Colors.BUTTON_JUMP_HOVER,
            center=False
        )
        database_button.master.pack(side='left', padx=15, pady=10)

        # Footer
        footer_label = Label(main_frame, text="© 2025 InfiniLing", 
                            font=("Segoe UI", 9), 
                            bg='#f0f0f0', fg='#bdc3c7')
        footer_label.pack(side='bottom', pady=(40, 0))

    def open_whisper_mode(self):
        """Open the Whisper interface in the same window"""
        try:
            self.clear_window()
            # Inject dependencies into WhisperInterface
            WhisperInterface(
                self.master, 
                config=self.config,
                back_callback=self.show_main_menu
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Whisper Mode: {e}")
            self.show_main_menu()

    def open_wordstory_mode(self):
        """Open the Vocabulary interface in the same window"""
        try:
            self.clear_window()
            # Inject dependencies into GentexterConfig
            GentexterConfig(
                self.master,
                config=self.config,
                vocab_service=self.vocab_service,
                back_callback=self.show_main_menu
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Wordstory Mode: {e}")
            self.show_main_menu()

    def open_database_mode(self):
        """Open the Database view in the same window"""
        try:
            self.clear_window()
            DatabaseView(
                self.master,
                config=self.config,
                back_callback=self.show_main_menu
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Database Mode: {e}")
            self.show_main_menu()

if __name__ == "__main__":
    root = Tk()
    app = MainMenu(root)
    root.mainloop()