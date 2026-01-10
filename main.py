import tkinter as tk
from tkinter import messagebox
import sys
import os
from src.shared.menu import MainMenu
from src.shared.config import initialize_config
from src.gentexter_mode.orchestrator_updated import VocabularyApp


# sys and os are still needed for start_app logic

from src.shared.setup_ui import SetupWindow

def main():
    """Main application entry point with dependency injection"""
    # Initialize configuration system
    # We use a temporary ConfigManager just to resolve its own file path
    from src.shared.config import ConfigManager
    temp_config = ConfigManager()
    config_path = temp_config.resolve_path('config.json')
    config = initialize_config(config_path)
    print("✅ Configuration system initialized")

    # Initialize main window
    root = tk.Tk()
    
    # Check for API Key
    api_key = config.get_api_key()
    
    def start_app():
        # Set icon on Windows only
        try:
            if sys.platform.startswith('win'):
                icon_path = config.resolve_path("data/icon.ico")
                if os.path.exists(icon_path):
                    root.iconbitmap(icon_path)
        except Exception:
            pass
        
        # Initialize vocabulary service with config
        database_url = config.get('vocabulary.database_url')
        vocab_service = VocabularyApp(database_url, config=config)
        print("✅ Vocabulary service initialized")
        
        # Initialize main menu with dependency injection
        MainMenu(root, config=config, vocab_service=vocab_service)

    if not api_key:
        # Launch setup if no key found
        SetupWindow(root, config, start_app)
    else:
        # Update environment for immediate use
        os.environ['OPENAI_API_KEY'] = api_key
        start_app()

    root.mainloop()

if __name__ == "__main__":
    print("Starting InfiniLing...")
    print("=" * 50)
    main()