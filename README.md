# Lightweight Reminder App

A feature-rich, lightweight Python GUI application built with tkinter for managing reminders with advanced functionality.

## Features

### Core Features
- **Lightweight Design**: Minimal resource usage, perfect for running in the background
- **Background Operation**: Runs in system tray when window is closed
- **Smart Notifications**: Automatic notifications when reminders are due
- **Easy Management**: Create, complete, and delete reminders with a simple interface
- **Persistent Storage**: Reminders are saved in JSON format and persist between sessions

### Advanced Features
- **Interactive Calendar**: Built-in calendar widget for easy date selection
- **Color-Coded Status**: Visual indicators for different reminder states
- **Task History Logs**: View completed tasks with completion timestamps  
- **Multiple Themes**: Choose from Light, Dark, Blue, and Green themes
- **Data Backup & Recovery**: Automatic and manual backup with recovery options
- **Enhanced UI**: Improved interface with better organization and visual feedback

### Visual Status Indicators
- **Pending**: Light red background - tasks waiting to be completed
- **Completed**: Green background - successfully finished tasks
- **Overdue**: Red background - tasks past their due time
- **Due Soon**: Orange background - tasks due within the next hour

## How to Use

### Running the Application (Multiple Options)

**Option 1: Silent VBS Launcher (Recommended - No Console)**:
   ```
   Double-click: run_reminder_silent.vbs
   ```

**Option 2: Optimized Python Launcher**:
   ```
   Double-click: start_reminder_silent.bat
   ```

**Option 3: Using Python directly**:
   ```
   python reminder_app.py
   ```

**Option 4: Using pythonw (No Console)**:
   ```
   pythonw reminder_app.py
   ```

**Option 5: Create Standalone Executable**:
   See `CREATE_EXECUTABLE.md` for instructions to create a standalone .exe file

### Creating Reminders

1. Click on **File → New Reminder** or use the menu
2. Enter the reminder title
3. Set the due date using:
   - **Manual entry** (YYYY-MM-DD format)
   - **Quick buttons** (Today/Tomorrow)
   - **Interactive calendar** (click dates on the right side)
4. Set the due time (HH:MM format)
5. Click "Create Reminder"

### Managing Reminders

- **Mark Complete**: Select a reminder and click "Mark Complete"
- **Delete**: Select a reminder and click "Delete"  
- **Refresh**: Click "Refresh" to update the list
- **View Logs**: Go to **View → Logs** to see completed task history

### Themes & Customization

- **Change Theme**: Go to **View → Theme** and choose from:
  - Light Theme (default)
  - Dark Theme  
  - Blue Theme
  - Green Theme

### Data Management & Backup

- **Automatic Backup**: App creates backup copies automatically
- **Manual Backup**: **File → Backup Data** to save to custom location
- **Restore Data**: **File → Restore from Backup** to recover from backup
- **Auto-Recovery**: If main data file is lost, automatically recovers from backup

### Background Operation

- Click the **X** button or **File → Hide to Tray** to run in background
- The app will show notifications for due reminders
- Use **File → Show Window** to restore the window
- Use **File → Exit** to completely quit the application

## File Structure

```
reminder_app/
├── reminder_app.py              # Main application file
├── run_reminder_app.bat         # Basic batch file to run the app
├── run_reminder_silent.vbs      # Silent VBS launcher (no console)
├── start_reminder_silent.bat    # Optimized batch launcher
├── launcher.py                  # Optimized Python launcher
├── reminders.json              # Main data file (created automatically)
├── reminders_backup.json       # Automatic backup file
├── reminder_logs.json          # Completed tasks log
├── CREATE_EXECUTABLE.md        # Instructions for creating .exe
├── packaging_understanding.txt  # Technical documentation
├── setup.py                    # Configuration for executable creation
└── README.md                   # This file
```

## Requirements

- Python 3.6 or higher
- tkinter (usually included with Python)
- Standard library modules: json, datetime, threading, calendar, os
- No additional dependencies required!

## Data Storage & Safety

### Multiple Data Files
- **reminders.json**: Main storage for active reminders
- **reminders_backup.json**: Automatic backup created before each save
- **reminder_logs.json**: History of completed tasks

### Data Safety Features
- **Automatic Backup**: Every save operation creates a backup
- **Auto-Recovery**: Detects missing main file and restores from backup
- **Manual Backup**: Save backups to any location (external drives, cloud folders)
- **Manual Restore**: Restore from any backup file
- **Completion Logs**: Permanent record of completed tasks with timestamps

## Color Coding

- **Light Red**: Pending reminders waiting for completion
- **Green**: Successfully completed reminders
- **Red**: Overdue reminders (past due date/time)
- **Orange**: Reminders due within the next hour

## Menu Structure

### File Menu
- New Reminder
- Backup Data
- Restore from Backup
- Show/Hide Window
- Exit

### View Menu  
- Logs (completed tasks history)
- Theme (Light, Dark, Blue, Green)

### Help Menu
- About (includes developer credit)

## Keyboard Shortcuts

- **Enter**: Create reminder (when in New Reminder dialog)
- **Calendar Navigation**: Use < > buttons or click dates directly
- **Alt+F4**: Close application completely

## New Features Highlights

### Interactive Calendar
- **Visual Date Selection**: Click any date on the calendar to select it
- **Month Navigation**: Browse previous and next months easily  
- **Today Highlighting**: Current date is highlighted in blue
- **Larger Dialog**: Expanded New Reminder window (700x500) to accommodate calendar

### Enhanced Themes
- **4 Theme Options**: Light, Dark, Blue, and Green color schemes
- **Complete UI Theming**: Changes background, text, and selection colors
- **Persistent**: Theme selection affects the entire application interface

### Task History & Logs
- **Completion Tracking**: All completed tasks are logged with timestamps
- **Searchable History**: View past completed tasks in dedicated window
- **Detailed Information**: Shows original due date/time and completion date/time

### Advanced Backup System
- **Triple Protection**: Main file + automatic backup + manual backup options
- **Smart Recovery**: Automatically detects and recovers from data loss
- **User Control**: Manual backup/restore with file dialog selection
- **Cloud-Friendly**: Easy to backup to cloud storage or external drives

## Tips

- The application checks for due reminders every 60 seconds (optimized for performance)
- Reminders are sorted automatically by due date and time
- You can set reminders for past dates (with confirmation dialog)
- The app is designed to be lightweight and use minimal system resources
- Use the VBS launcher for completely silent operation
- Backup your data regularly using **File → Backup Data**

## Troubleshooting

### Common Issues
1. **Missing reminders**: Check **File → Restore from Backup**
2. **Theme not applying**: Restart the application
3. **Calendar not working**: Ensure Python has calendar module (standard library)
4. **Performance issues**: Reduce number of active reminders or restart app

### Data Recovery
- If `reminders.json` is deleted, the app will automatically restore from backup
- Use **File → Restore from Backup** to manually recover from any backup file
- Check for `reminders_backup.json` in the same directory as the app

## About

This lightweight reminder application is built with Python's tkinter library, making it cross-platform compatible and requiring no additional installations beyond Python itself.

**Created by: Swapnil Shandilya**

### Technical Features
- Multi-threaded background processing
- JSON-based data storage with backup redundancy
- Event-driven GUI with responsive design
- Cross-platform compatibility (Windows, macOS, Linux)
- Memory-efficient operation suitable for continuous background use
