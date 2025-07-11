import tkinter as tk
from tkinter import messagebox
import sys
import os

try:
    from src.shared.menu import MainMenu
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Set icon on Windows only
    if sys.platform.startswith('win'):
        icon_path = resource_path("data/icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    
    try:
        main_menu = MainMenu(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Application Error", 
                           f"Failed to start the application:\n\n{str(e)}\n\n"
                           f"Please check that all required packages are installed.")
        print(f"Detailed error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting InfiniLing...")
    print("=" * 50)
    main()