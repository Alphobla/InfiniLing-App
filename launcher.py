#!/usr/bin/env python3
"""
Simple launcher script for the Unified Language App
"""

import os
import sys
import subprocess
import platform

def main():
    print("🌍 Unified Language App Launcher")
    print("=" * 40)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if we're on Windows
    is_windows = platform.system() == "Windows"
    
    try:
        # Check if Python is available
        result = subprocess.run([sys.executable, "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Python is not available")
            return False
        
        print(f"✅ Python version: {result.stdout.strip()}")
        
        # Install requirements if needed
        print("📦 Checking requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
                      check=True)
        print("✅ Requirements satisfied")
        
        # Launch the application
        print("🚀 Starting Unified Language App...")
        print("-" * 40)
        
        # Change to src directory and run main.py
        src_path = os.path.join(script_dir, "src")
        os.chdir(src_path)
        
        # Run the application
        subprocess.run([sys.executable, "main.py"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False
    except FileNotFoundError:
        print("❌ Python not found. Please install Python 3.7 or later.")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application closed by user")
        return True
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        input("Press Enter to exit...")
