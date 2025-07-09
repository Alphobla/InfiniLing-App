from tkinter import Tk, Frame, Button, Label, messagebox, ttk
from src.transcriber_mode.ui import WhisperInterface
from src.gentexter_mode.ui import VocabularyInterface
from src.shared.styles import Spacing, Colors


class MainMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("InfiniLing")
        self.master.geometry("500x350")
        self.master.configure(bg='#f0f0f0')
        self.master.resizable(False, False)
        
        # Center the window
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

        self.current_interface = None
        self.create_widgets()

    def clear_window(self):
        """Clear all widgets from the window"""
        for widget in self.master.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        """Show the main menu"""
        self.clear_window()
        self.current_interface = None
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
        whisper_frame = Frame(button_frame, bg=Colors.BUTTON_PAUSE_HOVER, relief='raised', bd=2)
        whisper_frame.pack(side='left', padx=15, pady=10)
        whisper_frame.pack_propagate(False)
        whisper_frame.configure(width=150, height=150)
        
        whisper_button = Button(whisper_frame, text="🎤\nTranscriber\nMode", 
                               command=self.open_whisper_mode,
                               font=("Segoe UI", 12, "bold"),
                               bg=Colors.BUTTON_PAUSE, fg='white', 
                               activebackground=Colors.BUTTON_PAUSE_HOVER, activeforeground='white',
                               relief='flat', bd=0)
        whisper_button.pack(fill='both', expand=True)

        # Wordstory Mode Button
        wordstory_frame = Frame(button_frame, bg=Colors.BUTTON_SPEED_HOVER, relief='raised', bd=2)
        wordstory_frame.pack(side='left', padx=15, pady=10)
        wordstory_frame.pack_propagate(False)
        wordstory_frame.configure(width=150, height=150)
        
        wordstory_button = Button(wordstory_frame, text="📚\nGentexter\nMode", 
                                 command=self.open_wordstory_mode,
                                 font=("Segoe UI", 12, "bold"),
                                 bg=Colors.BUTTON_SPEED, fg='white',
                                 activebackground=Colors.BUTTON_SPEED_HOVER, activeforeground='white',
                                 relief='flat', bd=0)
        wordstory_button.pack(fill='both', expand=True)

        # Footer
        footer_label = Label(main_frame, text="© 2025 InfiniLing", 
                            font=("Segoe UI", 9), 
                            bg='#f0f0f0', fg='#bdc3c7')
        footer_label.pack(side='bottom', pady=(40, 0))

    def open_whisper_mode(self):
        """Open the Whisper interface in the same window"""
        try:
            self.clear_window()
            self.current_interface = WhisperInterface(self.master, self.show_main_menu)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Whisper Mode: {e}")
            self.show_main_menu()

    def open_wordstory_mode(self):
        """Open the Vocabulary interface in the same window"""
        try:
            self.clear_window()
            self.current_interface = VocabularyInterface(self.master, self.show_main_menu)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Wordstory Mode: {e}")
            self.show_main_menu()

if __name__ == "__main__":
    root = Tk()
    app = MainMenu(root)
    root.mainloop()