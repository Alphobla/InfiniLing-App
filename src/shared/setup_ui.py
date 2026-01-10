import tkinter as tk
from tkinter import messagebox
import base64
from .styles import Colors, Fonts, Spacing, center_top_window

class SetupWindow:
    def __init__(self, master, config, on_success):
        self.master = master
        self.config = config
        self.on_success = on_success
        
        self.setup_ui()

    def setup_ui(self):
        self.master.title("InfiniLing - Setup")
        window_width, window_height = 450, 280
        self.master.configure(bg=Colors.BACKGROUND)
        center_top_window(self.master, width=window_width, height=window_height)
        
        main_frame = tk.Frame(self.master, bg=Colors.BACKGROUND, padx=30, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        # Title
        tk.Label(main_frame, text="🔑 API Setup", font=("Segoe UI", 18, "bold"), 
                 bg=Colors.BACKGROUND, fg=Colors.PRIMARY).pack(pady=(0, 20))
        
        tk.Label(main_frame, text="To use the AI features, please enter your\nOpenAI API Key.", 
                 font=Fonts.BODY, bg=Colors.BACKGROUND, justify="center").pack(pady=(0, 20))

        # API Key Section
        tk.Label(main_frame, text="OpenAI API Key", font=Fonts.BODY_BOLD, 
                 bg=Colors.BACKGROUND).pack(anchor='w')
        self.key_entry = tk.Entry(main_frame, font=Fonts.BODY, width=40, show="*")
        self.key_entry.pack(pady=(5, 20), ipady=3)
        
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
        
        # Validate and Save
        if user_key.startswith("sk-") and len(user_key) > 20:
            self.config.save_api_key(user_key)
            messagebox.showinfo("Success", "API Key saved successfully!")
            self.on_success()
            return

        messagebox.showerror("Error", "Please provide a valid OpenAI API Key (starting with 'sk-').")
