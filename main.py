import tkinter as tk
from tkinter import messagebox
import sys
import os
from src.shared.menu import MainMenu
from src.shared.config import initialize_config
from src.gentexter_mode.orchestrator_updated import VocabularyApp


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    """Main application entry point with dependency injection"""
    # Initialize configuration system
    config = initialize_config(resource_path('config.json'))
    print("✅ Configuration system initialized")

    # Initialize main window
    root = tk.Tk()
    
    # Set icon on Windows only
    try:
        if sys.platform.startswith('win'):
            icon_path = resource_path("data/icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
    except Exception:
        # Icon setting failed, continue without icon
        pass
    
    # Initialize vocabulary service with config
    database_url = config.get('vocabulary.database_url')
    vocab_service = VocabularyApp(database_url, config=config)
    print("✅ Vocabulary service initialized")

    
    # Initialize main menu with dependency injection
    main_menu = MainMenu(root, config=config, vocab_service=vocab_service)
    root.mainloop()

if __name__ == "__main__":
    print("Starting InfiniLing...")
    print("=" * 50)
    main()