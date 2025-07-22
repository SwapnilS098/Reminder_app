# Create Standalone Executable

## Quick Solution (No pip needed)

**Use the VBS launcher** - already included in your app:
- Double-click `run_reminder_silent.vbs`
- No installation required, runs silently

## Create .exe file (Optional)

### Method 1: PyInstaller
```
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name "ReminderApp" reminder_app.py
```

### Method 2: Auto-py-to-exe (GUI)
```
python -m pip install auto-py-to-exe
auto-py-to-exe
```

**If pip fails, try:**
- `python -m pip install --upgrade pip`
- `py -m pip install pyinstaller`
- `pip install --user pyinstaller`
