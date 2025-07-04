import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.main_menu import MainMenu
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)

def main():
    """Main application entry point"""
    root = tk.Tk()
    root.title("🌍 InfiniLing")
    root.geometry("600x450")
    root.configure(bg='#f0f0f0')
    
    # Set window icon if available
    try:
        # You can add an icon file later
        pass
    except:
        pass
    
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
    print("Starting Unified Language App...")
    print("=" * 50)
    main()