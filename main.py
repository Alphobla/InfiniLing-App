import tkinter as tk
from tkinter import messagebox
import sys

try:
    from src.shared.menu import MainMenu
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    """Main application entry point"""
    root = tk.Tk()
    
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