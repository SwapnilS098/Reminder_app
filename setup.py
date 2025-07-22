from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need fine-tuning
build_options = {
    'packages': ['tkinter', 'json', 'datetime', 'threading', 'os'],
    'excludes': ['unittest', 'test', 'distutils'],
    'include_files': []
}

# GUI applications require a different base on Windows
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('reminder_app.py', 
               base=base, 
               target_name='ReminderApp.exe',
               icon=None)  # You can add an icon file here
]

setup(
    name='Lightweight Reminder App',
    version='1.0',
    description='A lightweight reminder application',
    options={'build_exe': build_options},
    executables=executables
)
