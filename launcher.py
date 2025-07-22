#!/usr/bin/env python
"""
Lightweight Reminder App Launcher
This script runs the reminder app with minimal resource usage
"""
import sys
import os

# Suppress all console output for truly silent operation
if sys.platform == "win32":
    import ctypes
    # Hide console window on Windows
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Import and run the app
from reminder_app import ReminderApp

if __name__ == "__main__":
    app = ReminderApp()
    app.run()
