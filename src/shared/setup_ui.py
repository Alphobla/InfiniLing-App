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
