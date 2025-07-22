# Lightweight Reminder App

A simple, lightweight Python GUI application built with tkinter for managing reminders.

## Features

- **Lightweight Design**: Minimal resource usage, perfect for running in the background
- **Background Operation**: Runs in system tray when window is closed
- **Smart Notifications**: Automatic notifications when reminders are due
- **Easy Management**: Create, complete, and delete reminders with a simple interface
- **Visual Indicators**: Color-coded reminders (overdue in red, due soon in orange)
- **Persistent Storage**: Reminders are saved in JSON format and persist between sessions

## How to Use

### Running the Application

1. **Using Python directly**:
   ```
   python reminder_app.py
   ```

2. **Using the batch file** (Windows):
   ```
   run_reminder_app.bat
   ```

### Creating Reminders

1. Click on **File → New Reminder** or use the menu
2. Enter the reminder title
3. Set the due date (YYYY-MM-DD format)
4. Set the due time (HH:MM format)
5. Click "Create Reminder"

### Managing Reminders

- **Mark Complete**: Select a reminder and click "Mark Complete"
- **Delete**: Select a reminder and click "Delete"
- **Refresh**: Click "Refresh" to update the list

### Background Operation

- Click the **X** button or **File → Hide to Tray** to run in background
- The app will show notifications for due reminders
- Use **File → Show Window** to restore the window
- Use **File → Exit** to completely quit the application

## File Structure

```
reminder_app/
├── reminder_app.py          # Main application file
├── run_reminder_app.bat     # Windows batch file to run the app
├── reminders.json          # Data file (created automatically)
└── README.md              # This file
```

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)
- No additional dependencies required!

## Data Storage

Reminders are automatically saved to `reminders.json` in the same directory as the application. This file is created automatically when you add your first reminder.

## Color Coding

- **Gray text**: Completed reminders
- **Red background**: Overdue reminders
- **Orange background**: Reminders due within the next hour
- **Normal**: Upcoming reminders

## Keyboard Shortcuts

- **Enter**: Create reminder (when in New Reminder dialog)
- **Alt+F4**: Close application completely

## Tips

- The application checks for due reminders every 30 seconds
- Reminders are sorted by due date and time
- You can set reminders for past dates (with confirmation)
- The app is designed to be lightweight and use minimal system resources

## Troubleshooting

If you encounter any issues:

1. Make sure Python is installed and accessible from command line
2. Ensure you have write permissions in the application directory
3. Check that the `reminders.json` file isn't corrupted (delete it to reset)

## About

This lightweight reminder application is built with Python's tkinter library, making it cross-platform compatible and requiring no additional installations beyond Python itself.
