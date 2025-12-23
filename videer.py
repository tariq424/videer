#!/usr/bin/env python3
"""
Videer Launcher - Main entry point for the application
"""
import sys
import os


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    if missing_deps:
        print("Error: Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install dependencies using:")
        print("  pip install -r requirements.txt")
        sys.exit(1)


def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        print("Error: tkinter is not available")
        print("\ntkinter is required for the GUI interface.")
        print("On Ubuntu/Debian: sudo apt-get install python3-tk")
        print("On Fedora: sudo dnf install python3-tkinter")
        print("On macOS: tkinter should be included with Python")
        return False


def main():
    """Main entry point"""
    print("Starting Videer - Video Generator from Pexels")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Check tkinter
    if not check_tkinter():
        sys.exit(1)
    
    # Import and run the GUI
    from videer_gui import main as gui_main
    
    print("Launching GUI...")
    gui_main()


if __name__ == "__main__":
    main()
