import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
from datetime import datetime, timedelta
import json
import os
import threading
import time
from tkinter import font
import sys
import calendar
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import system tray functionality
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    # Fallback for Windows without external dependencies
    try:
        import win32gui
        import win32con
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False

import shutil

class ReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Reminders")
        self.root.geometry("900x500")  # Increased width for side panel
        self.root.minsize(800, 400)    # Increased minimum size
        
        # Configure the app to run in system tray when closed
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Create a small tray-like window (initially hidden)
        self.tray_window = None
        self.is_hidden = False
        
        # Side panel state
        self.side_panel_visible = True
        
        # Data file path
        self.data_file = "reminders.json"
        self.backup_file = "reminders_backup.json"
        self.logs_file = "reminder_logs.json"
        self.settings_file = "app_settings.json"
        self.reminders = []
        self.logs = []
        
        # Default settings
        self.settings = {
            "notification_minutes_before": 15,
            "email_settings": {
                "smtp_server": "",
                "smtp_port": 587,
                "email": "",
                "password": ""
            },
            "custom_themes": {}
        }
        
        # Theme colors
        self.themes = {
            "light": {"bg": "#ffffff", "fg": "#000000", "select_bg": "#0078d4"},
            "dark": {"bg": "#2d2d2d", "fg": "#ffffff", "select_bg": "#404040"},
            "blue": {"bg": "#e6f3ff", "fg": "#003366", "select_bg": "#0066cc"},
            "green": {"bg": "#e6ffe6", "fg": "#003300", "select_bg": "#00cc00"}
        }
        
        # Load custom themes from settings
        custom_themes = self.settings.get("custom_themes", {})
        self.themes.update(custom_themes)
        
        self.current_theme = "light"
        
        # Load existing reminders
        self.load_reminders()
        self.load_logs()
        self.load_settings()
        
        # Create GUI
        self.create_widgets()
        
        # Start background reminder checker
        self.start_reminder_checker()
        
        # Center the window
        self.center_window()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Create menu bar
        self.create_menu()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)  # Main content gets more space
        main_frame.columnconfigure(1, weight=1)  # Side panel gets less space
        main_frame.rowconfigure(1, weight=1)
        
        # Title and toggle button frame
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=(tk.W, tk.E))
        title_frame.columnconfigure(0, weight=1)
        
        title_font = font.Font(size=16, weight="bold")
        title_label = ttk.Label(title_frame, text="Reminders", font=title_font)
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Toggle side panel button
        self.toggle_button = ttk.Button(title_frame, text="◀ Hide History", 
                                      command=self.toggle_side_panel, width=14)
        self.toggle_button.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # Create horizontal paned window to split main content and side panel
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel - Reminders list frame
        list_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(list_frame, weight=2)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Right panel - Progress history side window
        self.side_frame = ttk.LabelFrame(self.paned_window, text="📊 Progress History", padding="10")
        self.paned_window.add(self.side_frame, weight=1)
        self.side_frame.columnconfigure(0, weight=1)
        self.side_frame.rowconfigure(1, weight=1)
        
        # Create treeview for reminders
        columns = ("S.No", "Title", "Due Date", "Due Time", "Status", "Progress")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        self.tree.heading("S.No", text="S.No")
        self.tree.heading("Title", text="Reminder")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Due Time", text="Due Time")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Progress", text="Progress")
        
        self.tree.column("S.No", width=50, minwidth=40)
        self.tree.column("Title", width=200, minwidth=150)
        self.tree.column("Due Date", width=100, minwidth=80)
        self.tree.column("Due Time", width=100, minwidth=80)
        self.tree.column("Status", width=80, minwidth=60)
        self.tree.column("Progress", width=70, minwidth=60)
        
        # Bind tree selection to update side panel
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid treeview and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Create side panel content
        self.create_side_panel()
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Info label
        info_label = ttk.Label(buttons_frame, text="💡 Select a task and click Update to track progress", 
                              font=("Arial", 8), foreground="gray")
        info_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Buttons
        ttk.Button(buttons_frame, text="✅ Mark Complete", command=self.mark_complete).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="📝 Update Progress", command=self.update_task_progress).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🗑️ Delete", command=self.delete_reminder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="🔄 Refresh", command=self.refresh_list).pack(side=tk.LEFT)
        
        # Restore/Show button (for when running in background)
        ttk.Button(buttons_frame, text="Hide to Background", command=self.hide_window).pack(side=tk.RIGHT)
        
        # Populate the list
        self.refresh_list()
        
        # Set up keyboard shortcuts
        self.root.bind('<Control-p>', lambda e: self.toggle_side_panel())
    
    def toggle_side_panel(self):
        """Toggle visibility of the progress history side panel"""
        if self.side_panel_visible:
            # Hide the side panel
            self.paned_window.forget(self.side_frame)
            self.toggle_button.config(text="▶ Show History")
            self.side_panel_visible = False
            
            # Adjust window size for better experience when panel is hidden
            current_geometry = self.root.geometry()
            width, height = current_geometry.split('x')[0], current_geometry.split('x')[1].split('+')[0]
            if int(width) > 700:  # Only adjust if window is large enough
                new_width = max(600, int(width) - 200)  # Reduce width but keep minimum
                self.root.geometry(f"{new_width}x{height}")
        else:
            # Show the side panel
            self.paned_window.add(self.side_frame, weight=1)
            self.toggle_button.config(text="◀ Hide History")
            self.side_panel_visible = True
            
            # Restore wider window when panel is shown
            current_geometry = self.root.geometry()
            width, height = current_geometry.split('x')[0], current_geometry.split('x')[1].split('+')[0]
            if int(width) < 800:  # Only adjust if window is narrow
                new_width = max(900, int(width) + 200)  # Increase width
                self.root.geometry(f"{new_width}x{height}")
            
            # Update the side panel content if a task is selected
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                index = self.tree.index(item)
                if index < len(self.reminders):
                    sorted_reminders = sorted(self.reminders, key=lambda x: f"{x['due_date']} {x['due_time']}")
                    self.update_history_panel(sorted_reminders[index])
    
    def create_side_panel(self):
        """Create the progress history side panel"""
        # Header for selected task
        self.selected_task_label = ttk.Label(self.side_frame, text="Select a task to view progress history", 
                                           font=("Arial", 10), foreground="gray")
        self.selected_task_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress history tree
        history_columns = ("Date", "Progress", "Comments")
        self.history_tree = ttk.Treeview(self.side_frame, columns=history_columns, 
                                       show="tree headings", height=12)
        
        # Configure column headings
        self.history_tree.heading("#0", text="Timeline")
        self.history_tree.heading("Date", text="Date/Time")
        self.history_tree.heading("Progress", text="Progress")
        self.history_tree.heading("Comments", text="Comments")
        
        # Configure column widths
        self.history_tree.column("#0", width=30, minwidth=30)
        self.history_tree.column("Date", width=120, minwidth=100)
        self.history_tree.column("Progress", width=60, minwidth=50)
        self.history_tree.column("Comments", width=200, minwidth=150)
        
        # History tree scrollbar
        history_scrollbar = ttk.Scrollbar(self.side_frame, orient=tk.VERTICAL, 
                                        command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Grid history tree and scrollbar
        self.history_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # Configure tree tags for styling
        self.history_tree.tag_configure("date_group", background="#f0f8ff", foreground="darkblue")
        self.history_tree.tag_configure("update_item", background="white", foreground="darkgreen")
        self.history_tree.tag_configure("high_progress", foreground="green", font=("Arial", 9, "bold"))
        self.history_tree.tag_configure("medium_progress", foreground="orange")
        self.history_tree.tag_configure("low_progress", foreground="red")
        
        # Progress summary
        self.progress_summary = ttk.Label(self.side_frame, text="", font=("Arial", 9), 
                                        foreground="darkblue")
        self.progress_summary.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W))
        
    def update_history_panel(self, reminder=None):
        """Update the progress history side panel"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        if not reminder:
            self.selected_task_label.config(text="Select a task to view progress history", 
                                          foreground="gray")
            self.progress_summary.config(text="")
            return
            
        # Update header
        task_title = reminder["title"][:30] + "..." if len(reminder["title"]) > 30 else reminder["title"]
        self.selected_task_label.config(text=f"📋 {task_title}", foreground="black")
        
        # Update progress summary
        current_progress = reminder.get("progress", 0)
        updates_count = len(reminder.get("updates", []))
        created_date = datetime.fromisoformat(reminder["created"]).strftime("%m/%d/%Y")
        
        summary_text = f"Progress: {current_progress}/10 • Updates: {updates_count} • Created: {created_date}"
        self.progress_summary.config(text=summary_text)
        
        # Add progress history to tree
        updates = reminder.get("updates", [])
        if not updates:
            # Show creation entry
            creation_item = self.history_tree.insert("", tk.END, 
                                                    text="📝", 
                                                    values=(created_date, "0/10", "Task created"))
            return
            
        # Group updates by date
        updates_by_date = {}
        for update in updates:
            try:
                timestamp = datetime.fromisoformat(update["timestamp"])
                date_key = timestamp.strftime("%Y-%m-%d")
                
                if date_key not in updates_by_date:
                    updates_by_date[date_key] = []
                    
                updates_by_date[date_key].append({
                    "time": timestamp.strftime("%H:%M"),
                    "full_datetime": timestamp.strftime("%m/%d %H:%M"),
                    "progress": update.get("progress", 0),
                    "comment": update.get("comment", "").strip() or "Progress updated",
                    "timestamp": timestamp
                })
            except:
                continue
        
        # Sort dates and add to tree
        for date_key in sorted(updates_by_date.keys(), reverse=True):
            date_display = datetime.strptime(date_key, "%Y-%m-%d").strftime("%m/%d/%Y")
            date_item = self.history_tree.insert("", tk.END, 
                                                text="📅", 
                                                values=(date_display, "", f"{len(updates_by_date[date_key])} updates"),
                                                tags=("date_group",))
            
            # Sort updates by time (most recent first)
            day_updates = sorted(updates_by_date[date_key], 
                               key=lambda x: x["timestamp"], reverse=True)
            
            for update in day_updates:
                comment_display = update["comment"][:50] + "..." if len(update["comment"]) > 50 else update["comment"]
                
                # Determine progress tag
                progress_val = update["progress"]
                progress_tag = "low_progress"
                if progress_val >= 7:
                    progress_tag = "high_progress"
                elif progress_val >= 4:
                    progress_tag = "medium_progress"
                    
                self.history_tree.insert(date_item, tk.END, 
                                       text="🔄", 
                                       values=(update["time"], 
                                             f"{update['progress']}/10", 
                                             comment_display),
                                       tags=("update_item", progress_tag))
            
            # Expand today's updates by default
            if date_key == datetime.now().strftime("%Y-%m-%d"):
                self.history_tree.item(date_item, open=True)
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Reminder", command=self.new_reminder)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Data", command=self.manual_backup)
        file_menu.add_command(label="Restore from Backup", command=self.restore_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Show Window", command=self.show_window)
        file_menu.add_command(label="Hide to Background", command=self.hide_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Logs", command=self.show_logs)
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Progress Panel", command=self.toggle_side_panel, accelerator="Ctrl+P")
        view_menu.add_separator()
        theme_submenu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_submenu)
        theme_submenu.add_command(label="Light Theme", command=lambda: self.change_theme("light"))
        theme_submenu.add_command(label="Dark Theme", command=lambda: self.change_theme("dark"))
        theme_submenu.add_command(label="Blue Theme", command=lambda: self.change_theme("blue"))
        theme_submenu.add_command(label="Green Theme", command=lambda: self.change_theme("green"))
        # Add custom themes to menu
        for theme_name in self.settings.get("custom_themes", {}):
            theme_submenu.add_command(label=f"{theme_name.title()} Theme", 
                                    command=lambda t=theme_name: self.change_theme(t))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self.show_settings)
        tools_menu.add_command(label="Export Logs to Email", command=self.export_logs_to_email)
        tools_menu.add_separator()
        tools_menu.add_command(label="Create Custom Theme", command=self.create_custom_theme)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📧 Email Setup Guide", command=self.add_email_setup_guide)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
    def new_reminder(self):
        """Create a new reminder dialog"""
        dialog = ReminderDialog(self.root, self.add_reminder)
        
    def add_reminder(self, title, due_date, due_time):
        """Add a new reminder"""
        reminder = {
            "title": title,
            "due_date": due_date,
            "due_time": due_time,
            "status": "Pending",
            "created": datetime.now().isoformat(),
            "comments": "",
            "progress": 0,
            "updates": []  # Thread-like update history
        }
        self.reminders.append(reminder)
        self.save_reminders()
        self.refresh_list()
        
    def mark_complete(self):
        """Mark selected reminder as complete and remove from list"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a reminder to mark as complete.")
            return
            
        item = selection[0]
        index = self.tree.index(item)
        
        if index < len(self.reminders):
            # Get the reminder before removing it
            completed_reminder = self.reminders[index].copy()
            completed_reminder["status"] = "Completed"
            completed_reminder["completed_at"] = datetime.now().isoformat()
            
            # Add to logs
            self.logs.append(completed_reminder)
            
            # Remove from reminders list
            del self.reminders[index]
            
            # Save both files
            self.save_reminders()
            self.save_logs()
            self.refresh_list()
            
            # Show confirmation message
            messagebox.showinfo("Task Completed", 
                f"'{completed_reminder['title']}' has been marked as complete and removed from the list.\n\n"
                "You can view completed tasks in View → Logs.")
            
    def delete_reminder(self):
        """Delete selected reminder"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a reminder to delete.")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this reminder?"):
            item = selection[0]
            index = self.tree.index(item)
            
            if index < len(self.reminders):
                del self.reminders[index]
                self.save_reminders()
                self.refresh_list()
                
    def refresh_list(self):
        """Refresh the reminders list"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Sort reminders by due date/time
        sorted_reminders = sorted(self.reminders, key=lambda x: f"{x['due_date']} {x['due_time']}")
        
        # Add reminders to tree with serial numbers
        for index, reminder in enumerate(sorted_reminders, 1):
            # Color code based on status and due date
            tags = []
            if self.is_overdue(reminder):
                tags.append("overdue")
            elif self.is_due_soon(reminder):
                tags.append("due_soon")
            elif reminder["status"] == "Pending":
                tags.append("pending")
            elif reminder["status"] == "Notified":
                tags.append("notified")
            
            # Get progress with default value for existing reminders
            progress = reminder.get("progress", 0)
            progress_text = f"{progress}/10" if progress > 0 else "0/10"
                
            self.tree.insert("", tk.END, values=(
                index,  # Serial number
                reminder["title"],
                reminder["due_date"],
                reminder["due_time"],
                reminder["status"],
                progress_text
            ), tags=tags)
            
        # Configure tags
        self.tree.tag_configure("overdue", foreground="red", background="#ffe6e6")
        self.tree.tag_configure("due_soon", foreground="orange", background="#fff3cd")
        self.tree.tag_configure("pending", foreground="darkred", background="#ffe6f0")
        self.tree.tag_configure("notified", foreground="purple", background="#f0e6ff")
        
    def on_tree_select(self, event):
        """Handle tree selection changes and update side panel"""
        selection = self.tree.selection()
        if not selection:
            self.update_history_panel()  # Clear side panel
            return
            
        item = selection[0]
        index = self.tree.index(item)
        
        if index < len(self.reminders):
            # Sort reminders the same way as in refresh_list to get correct reminder
            sorted_reminders = sorted(self.reminders, key=lambda x: f"{x['due_date']} {x['due_time']}")
            reminder = sorted_reminders[index]
            self.update_history_panel(reminder)
        
    def update_task_progress(self):
        """Open update dialog for selected task"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to update.")
            return
            
        item = selection[0]
        index = self.tree.index(item)
        
        if index < len(self.reminders):
            reminder = self.reminders[index]
            # Open update dialog
            UpdateProgressDialog(self.root, reminder, self.on_progress_updated)
            
    def on_progress_updated(self, updated_reminder):
        """Callback when progress is updated from dialog"""
        # Find and update the reminder in our list
        for i, reminder in enumerate(self.reminders):
            if (reminder["title"] == updated_reminder["title"] and 
                reminder["due_date"] == updated_reminder["due_date"] and
                reminder["due_time"] == updated_reminder["due_time"]):
                
                # Update the reminder
                self.reminders[i] = updated_reminder
                break
                
        # Save and refresh
        self.save_reminders()
        self.refresh_list()
        
        # Update side panel with new data
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.reminders):
                sorted_reminders = sorted(self.reminders, key=lambda x: f"{x['due_date']} {x['due_time']}")
                self.update_history_panel(sorted_reminders[index])
        
        # Show confirmation
        progress = updated_reminder.get("progress", 0)
        messagebox.showinfo("Updated!", 
                           f"Progress updated to {progress}/10 for '{updated_reminder['title']}'")
    
        
    def is_overdue(self, reminder):
        """Check if reminder is overdue"""
        try:
            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
            return datetime.now() > due_datetime and reminder["status"] not in ["Completed", "Notified"]
        except:
            return False
            
    def is_due_soon(self, reminder):
        """Check if reminder is due within configured notification time"""
        try:
            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            notification_time = self.settings.get("notification_minutes_before", 15)
            warning_time = now + timedelta(minutes=notification_time)
            return now <= due_datetime <= warning_time and reminder["status"] not in ["Completed", "Notified"]
        except:
            return False
            
    def load_reminders(self):
        """Load reminders from JSON file with backup recovery"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.reminders = json.load(f)
            elif os.path.exists(self.backup_file):
                # Try to recover from backup if main file is missing
                with open(self.backup_file, 'r') as f:
                    self.reminders = json.load(f)
                # Restore main file from backup
                import shutil
                shutil.copy2(self.backup_file, self.data_file)
                messagebox.showinfo("Data Recovery", "Your reminders have been recovered from backup!")
                
            # Update existing reminders with new fields if they don't exist
            for reminder in self.reminders:
                if "comments" not in reminder:
                    reminder["comments"] = ""
                if "progress" not in reminder:
                    reminder["progress"] = 0
                if "updates" not in reminder:
                    reminder["updates"] = []
                    
        except Exception:
            self.reminders = []
            
    def save_reminders(self):
        """Save reminders to JSON file"""
        try:
            # Create backup before saving
            if os.path.exists(self.data_file):
                import shutil
                shutil.copy2(self.data_file, self.backup_file)
            
            with open(self.data_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception:
            pass
            
    def load_logs(self):
        """Load completed task logs from JSON file"""
        try:
            if os.path.exists(self.logs_file):
                with open(self.logs_file, 'r') as f:
                    self.logs = json.load(f)
        except Exception:
            self.logs = []
            
    def save_logs(self):
        """Save logs to JSON file"""
        try:
            with open(self.logs_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception:
            pass
            
    def load_settings(self):
        """Load application settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    # Merge custom themes with default themes
                    if "custom_themes" in loaded_settings:
                        for name, theme in loaded_settings["custom_themes"].items():
                            self.themes[name] = theme
        except Exception:
            pass
            
    def save_settings(self):
        """Save application settings to JSON file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
            
    def show_logs(self):
        """Show completed task logs window"""
        logs_window = tk.Toplevel(self.root)
        logs_window.title("Completed Tasks Log")
        logs_window.geometry("700x400")
        logs_window.transient(self.root)
        
        # Center the logs window
        logs_window.update_idletasks()
        x = (logs_window.winfo_screenwidth() // 2) - (logs_window.winfo_width() // 2)
        y = (logs_window.winfo_screenheight() // 2) - (logs_window.winfo_height() // 2)
        logs_window.geometry(f"+{x}+{y}")
        
        # Create frame and treeview for logs
        main_frame = ttk.Frame(logs_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Completed Tasks", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Treeview for logs
        columns = ("S.No", "Title", "Due Date", "Due Time", "Completed At")
        logs_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        logs_tree.heading("S.No", text="S.No")
        logs_tree.heading("Title", text="Task")
        logs_tree.heading("Due Date", text="Due Date")
        logs_tree.heading("Due Time", text="Due Time") 
        logs_tree.heading("Completed At", text="Completed At")
        
        logs_tree.column("S.No", width=50)
        logs_tree.column("Title", width=180)
        logs_tree.column("Due Date", width=100)
        logs_tree.column("Due Time", width=100)
        logs_tree.column("Completed At", width=150)
        
        # Scrollbar
        logs_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=logs_tree.yview)
        logs_tree.configure(yscrollcommand=logs_scrollbar.set)
        
        logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        logs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate logs
        for index, log in enumerate(reversed(self.logs), 1):  # Show newest first with serial numbers
            completed_at = log.get("completed_at", "Unknown")
            if completed_at != "Unknown":
                try:
                    dt = datetime.fromisoformat(completed_at)
                    completed_at = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            logs_tree.insert("", tk.END, values=(
                index,  # Serial number
                log.get("title", ""),
                log.get("due_date", ""),
                log.get("due_time", ""),
                completed_at
            ))
            
        # Close button
        ttk.Button(main_frame, text="Close", command=logs_window.destroy).pack(pady=(10, 0))
        
    def change_theme(self, theme_name):
        """Change the application theme"""
        if theme_name not in self.themes:
            return
            
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Apply theme to main window
        try:
            self.root.configure(bg=theme["bg"])
            
            # Update tree colors
            style = ttk.Style()
            style.theme_use('clam')  # Use clam theme for better customization
            
            # Configure treeview colors
            style.configure("Treeview", 
                           background=theme["bg"],
                           foreground=theme["fg"],
                           fieldbackground=theme["bg"])
            style.configure("Treeview.Heading", 
                           background=theme["select_bg"],
                           foreground="white")
                           
        except Exception:
            pass  # Ignore theme errors
            
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center the settings window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notification Settings Tab
        notif_frame = ttk.Frame(notebook)
        notebook.add(notif_frame, text="Notifications")
        
        ttk.Label(notif_frame, text="Notification Settings", font=("Arial", 12, "bold")).pack(pady=(10, 20))
        
        notif_inner_frame = ttk.Frame(notif_frame)
        notif_inner_frame.pack(pady=10)
        
        ttk.Label(notif_inner_frame, text="Show notification before due time:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.notification_var = tk.IntVar(value=self.settings.get("notification_minutes_before", 15))
        notification_spinbox = tk.Spinbox(notif_inner_frame, from_=1, to=120, width=10, textvariable=self.notification_var)
        notification_spinbox.grid(row=0, column=1, padx=(10, 5), pady=5)
        
        ttk.Label(notif_inner_frame, text="minutes").grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Email Settings Tab
        email_frame = ttk.Frame(notebook)
        notebook.add(email_frame, text="Email Export")
        
        ttk.Label(email_frame, text="Email Export Settings", font=("Arial", 12, "bold")).pack(pady=(10, 20))
        
        email_inner_frame = ttk.Frame(email_frame)
        email_inner_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Email settings variables
        email_settings = self.settings.get("email_settings", {})
        
        ttk.Label(email_inner_frame, text="SMTP Server:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.smtp_server_var = tk.StringVar(value=email_settings.get("smtp_server", "smtp.gmail.com"))
        ttk.Entry(email_inner_frame, textvariable=self.smtp_server_var, width=30).grid(row=0, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        
        ttk.Label(email_inner_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.smtp_port_var = tk.IntVar(value=email_settings.get("smtp_port", 587))
        ttk.Entry(email_inner_frame, textvariable=self.smtp_port_var, width=10).grid(row=1, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        
        ttk.Label(email_inner_frame, text="Your Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar(value=email_settings.get("email", ""))
        ttk.Entry(email_inner_frame, textvariable=self.email_var, width=30).grid(row=2, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        
        ttk.Label(email_inner_frame, text="App Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar(value=email_settings.get("password", ""))
        ttk.Entry(email_inner_frame, textvariable=self.password_var, width=30, show="*").grid(row=3, column=1, padx=(10, 0), pady=5, sticky=tk.W)
        
        ttk.Label(email_inner_frame, text="Note: Use app-specific password for Gmail", font=("Arial", 8)).grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # Email setup help button
        ttk.Button(email_inner_frame, text="📧 Email Setup Guide", command=self.add_email_setup_guide).grid(row=5, column=0, columnspan=2, pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=lambda: self.save_settings_dialog(settings_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.LEFT)
        
    def save_settings_dialog(self, window):
        """Save settings from dialog"""
        try:
            self.settings["notification_minutes_before"] = self.notification_var.get()
            self.settings["email_settings"] = {
                "smtp_server": self.smtp_server_var.get(),
                "smtp_port": self.smtp_port_var.get(),
                "email": self.email_var.get(),
                "password": self.password_var.get()
            }
            self.save_settings()
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully!")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def export_logs_to_email(self):
        """Export logs to email"""
        try:
            # Check if email settings are configured
            email_settings = self.settings.get("email_settings", {})
            if not all([email_settings.get("smtp_server"), email_settings.get("email"), email_settings.get("password")]):
                if messagebox.askyesno("Email Settings", "Email settings are not configured. Would you like to configure them now?"):
                    self.show_settings()
                return
                
            # Load logs
            if not os.path.exists(self.logs_file):
                messagebox.showwarning("No Logs", "No logs available to export.")
                return
                
            with open(self.logs_file, 'r') as f:
                logs_data = json.load(f)
                
            if not logs_data:
                messagebox.showwarning("No Logs", "No logs available to export.")
                return
                
            # Create email content
            subject = f"Reminder App Logs - {datetime.now().strftime('%Y-%m-%d')}"
            body = "Reminder Application - Completed Tasks Log\n\n"
            body += "=" * 60 + "\n\n"
            
            for index, log in enumerate(logs_data, 1):
                body += f"#{index} - {log.get('title', 'Unknown Task')}\n"
                body += f"Due Date: {log.get('due_date', 'N/A')}\n"
                body += f"Due Time: {log.get('due_time', 'N/A')}\n"
                
                completed_at = log.get('completed_at', 'Unknown')
                if completed_at != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(completed_at)
                        completed_at = dt.strftime('%Y-%m-%d at %H:%M')
                    except:
                        pass
                body += f"Completed: {completed_at}\n"
                body += "-" * 40 + "\n\n"
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = email_settings['email']
            msg['To'] = email_settings['email']  # Send to self
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_settings['smtp_server'], email_settings['smtp_port'])
            server.starttls()
            server.login(email_settings['email'], email_settings['password'])
            text = msg.as_string()
            server.sendmail(email_settings['email'], email_settings['email'], text)
            server.quit()
            
            messagebox.showinfo("Success", "Logs have been sent to your email successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {str(e)}")
            
    def create_custom_theme(self):
        """Create custom theme dialog"""
        theme_window = tk.Toplevel(self.root)
        theme_window.title("Create Custom Theme")
        theme_window.geometry("450x350")
        theme_window.transient(self.root)
        theme_window.grab_set()
        
        # Center the window
        theme_window.update_idletasks()
        x = (theme_window.winfo_screenwidth() // 2) - (theme_window.winfo_width() // 2)
        y = (theme_window.winfo_screenheight() // 2) - (theme_window.winfo_height() // 2)
        theme_window.geometry(f"+{x}+{y}")
        
        ttk.Label(theme_window, text="Create Custom Theme", font=("Arial", 14, "bold")).pack(pady=(10, 20))
        
        # Theme name
        name_frame = ttk.Frame(theme_window)
        name_frame.pack(pady=5, padx=20, fill=tk.X)
        ttk.Label(name_frame, text="Theme Name:").pack(side=tk.LEFT)
        theme_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=theme_name_var, width=25).pack(side=tk.RIGHT)
        
        # Color selections
        colors_frame = ttk.LabelFrame(theme_window, text="Colors", padding=10)
        colors_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Color variables
        self.custom_colors = {
            'bg': tk.StringVar(value="#FFFFFF"),
            'fg': tk.StringVar(value="#000000"),
            'select_bg': tk.StringVar(value="#0078D4"),
            'select_fg': tk.StringVar(value="#FFFFFF"),
            'button_bg': tk.StringVar(value="#F0F0F0"),
            'button_fg': tk.StringVar(value="#000000")
        }
        
        color_labels = {
            'bg': 'Background Color:',
            'fg': 'Text Color:',
            'select_bg': 'Selection Background:',
            'select_fg': 'Selection Text:',
            'button_bg': 'Button Background:',
            'button_fg': 'Button Text:'
        }
        
        row = 0
        for key, label in color_labels.items():
            ttk.Label(colors_frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
            
            color_frame = ttk.Frame(colors_frame)
            color_frame.grid(row=row, column=1, padx=(10, 0), pady=2, sticky=tk.E)
            
            color_entry = ttk.Entry(color_frame, textvariable=self.custom_colors[key], width=10)
            color_entry.pack(side=tk.LEFT)
            
            color_button = tk.Button(color_frame, text="Pick", 
                                   command=lambda k=key: self.pick_color(k),
                                   width=5)
            color_button.pack(side=tk.LEFT, padx=(5, 0))
            
            row += 1
        
        # Preview frame
        preview_frame = ttk.LabelFrame(theme_window, text="Preview", padding=10)
        preview_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.preview_label = tk.Label(preview_frame, text="Sample text with this theme", 
                                    relief=tk.RAISED, padx=20, pady=10)
        self.preview_label.pack()
        
        # Update preview initially
        self.update_theme_preview()
        
        # Buttons
        button_frame = ttk.Frame(theme_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Preview", command=self.update_theme_preview).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Save Theme", 
                  command=lambda: self.save_custom_theme(theme_name_var.get(), theme_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=theme_window.destroy).pack(side=tk.LEFT)
        
    def pick_color(self, color_key):
        """Open color picker"""
        try:
            color = colorchooser.askcolor(color=self.custom_colors[color_key].get())
            if color[1]:  # If user didn't cancel
                self.custom_colors[color_key].set(color[1])
                self.update_theme_preview()
        except:
            messagebox.showerror("Error", "Color picker not available")
            
    def update_theme_preview(self):
        """Update theme preview"""
        try:
            self.preview_label.configure(
                bg=self.custom_colors['bg'].get(),
                fg=self.custom_colors['fg'].get()
            )
        except:
            pass
            
    def save_custom_theme(self, theme_name, window):
        """Save custom theme"""
        if not theme_name:
            messagebox.showerror("Error", "Please enter a theme name")
            return
            
        try:
            custom_theme = {
                'bg': self.custom_colors['bg'].get(),
                'fg': self.custom_colors['fg'].get(),
                'selectbackground': self.custom_colors['select_bg'].get(),
                'selectforeground': self.custom_colors['select_fg'].get(),
                'button_bg': self.custom_colors['button_bg'].get(),
                'button_fg': self.custom_colors['button_fg'].get()
            }
            
            # Add to themes
            self.themes[theme_name] = custom_theme
            
            # Save to settings
            custom_themes = self.settings.get("custom_themes", {})
            custom_themes[theme_name] = custom_theme
            self.settings["custom_themes"] = custom_themes
            self.save_settings()
            
            # Update theme menu
            self.create_menu()
            
            messagebox.showinfo("Success", f"Custom theme '{theme_name}' has been created and saved!")
            window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save custom theme: {str(e)}")
            
    def manual_backup(self):
        """Create manual backup of data"""
        try:
            import shutil
            from tkinter import filedialog
            
            # Ask user where to save backup
            backup_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Backup As"
            )
            
            if backup_path and os.path.exists(self.data_file):
                shutil.copy2(self.data_file, backup_path)
                messagebox.showinfo("Backup Created", f"Data backed up to:\n{backup_path}")
            else:
                messagebox.showwarning("Backup Failed", "No data to backup or operation cancelled.")
        except Exception as e:
            messagebox.showerror("Backup Error", f"Failed to create backup: {str(e)}")
            
    def restore_backup(self):
        """Restore data from backup file"""
        try:
            from tkinter import filedialog
            
            # Ask user to select backup file
            backup_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Select Backup File to Restore"
            )
            
            if backup_path and os.path.exists(backup_path):
                if messagebox.askyesno("Confirm Restore", 
                    "This will replace your current reminders with the backup data. Continue?"):
                    
                    import shutil
                    shutil.copy2(backup_path, self.data_file)
                    self.load_reminders()
                    self.refresh_list()
                    messagebox.showinfo("Restore Complete", "Data restored from backup successfully!")
        except Exception as e:
            messagebox.showerror("Restore Error", f"Failed to restore backup: {str(e)}")
            
    def start_reminder_checker(self):
        """Start background thread to check for due reminders"""
        def check_reminders():
            while True:
                try:
                    current_time = datetime.now()
                    notification_minutes = self.settings.get("notification_minutes_before", 15)
                    
                    for reminder in self.reminders:
                        if reminder["status"] == "Pending":
                            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
                            # Check for early notification
                            time_until_due = (due_datetime - current_time).total_seconds() / 60
                            
                            if 0 <= time_until_due <= notification_minutes and not reminder.get("early_notified", False):
                                self.show_early_notification(reminder, int(time_until_due))
                                reminder["early_notified"] = True
                                self.save_reminders()
                            elif current_time >= due_datetime:
                                self.show_reminder_notification(reminder)
                                reminder["status"] = "Notified"
                                self.save_reminders()
                                # Update GUI if window is visible
                                if self.root.state() != 'withdrawn':
                                    self.root.after(0, self.refresh_list)
                except Exception as e:
                    # Silently handle errors in background mode
                    pass
                    
                time.sleep(30)  # Check every 30 seconds for early notifications
                
        thread = threading.Thread(target=check_reminders, daemon=True)
        thread.start()
        
    def show_reminder_notification(self, reminder):
        """Show notification for due reminder"""
        # Show message box notification
        self.root.after(0, lambda: messagebox.showinfo(
            "Reminder Due!",
            f"Reminder: {reminder['title']}\nDue: {reminder['due_date']} at {reminder['due_time']}"
        ))
        
        # Bring window to front if hidden
        self.root.after(0, self.show_window)
        
    def show_early_notification(self, reminder, minutes_left):
        """Show early notification before reminder is due"""
        # Show message box notification
        self.root.after(0, lambda: messagebox.showinfo(
            "Reminder Coming Up!",
            f"Reminder: {reminder['title']}\nDue in {minutes_left} minutes\nDue: {reminder['due_date']} at {reminder['due_time']}"
        ))
        
        # Bring window to front if hidden
        self.root.after(0, self.show_window)
        
    def hide_window(self):
        """Hide window to system tray"""
        self.root.withdraw()
        self.is_hidden = True
        
        # Try to use system tray first, fallback to taskbar minimization
        if TRAY_AVAILABLE:
            try:
                self.create_system_tray()
            except Exception as e:
                # If system tray fails, use taskbar minimization
                print(f"System tray failed: {e}")
                self.minimize_to_taskbar()
        else:
            # Use Windows taskbar minimization
            self.minimize_to_taskbar()
        
    def minimize_to_taskbar(self):
        """Minimize to Windows taskbar"""
        # Create a minimal taskbar presence
        if not hasattr(self, 'taskbar_window'):
            self.taskbar_window = tk.Tk()
            self.taskbar_window.title("📋 Reminders (Hidden)")
            self.taskbar_window.geometry("1x1")  # Minimal size
            self.taskbar_window.withdraw()  # Hide immediately
            
            # Create a context menu for taskbar icon
            def on_taskbar_click():
                self.show_window()
                
            def create_taskbar_menu():
                menu = tk.Menu(self.taskbar_window, tearoff=0)
                menu.add_command(label="🔍 Show Reminders", command=self.show_window)
                menu.add_command(label="➕ New Reminder", command=self.new_reminder)
                menu.add_separator()
                menu.add_command(label="⚙️ Settings", command=self.show_settings)
                menu.add_command(label="📊 View Logs", command=self.show_logs)
                menu.add_separator()
                menu.add_command(label="❌ Quit", command=self.quit_app)
                return menu
            
            self.taskbar_menu = create_taskbar_menu()
            
            # Show the taskbar window
            self.taskbar_window.deiconify()
            self.taskbar_window.iconify()  # Minimize to taskbar
        
        # Show notification about being in taskbar
        self.show_taskbar_message()
        
    def create_system_tray(self):
        """Create system tray icon (requires pystray)"""
        def create_image():
            # Create a simple icon
            image = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(image)
            draw.rectangle([16, 16, 48, 48], fill='blue', outline='darkblue', width=2)
            draw.text((20, 20), "R", fill='white')
            return image
        
        def show_app(icon, item_obj):
            self.show_window()
            
        def quit_app(icon, item_obj):
            self.quit_app()
            
        def new_reminder_tray(icon, item_obj):
            self.root.after(0, self.new_reminder)
            
        # Create menu items
        menu_items = [
            item('Show Reminders', show_app, default=True),
            item('New Reminder', new_reminder_tray),
            pystray.Menu.SEPARATOR,
            item('Settings', lambda icon, item_obj: self.root.after(0, self.show_settings)),
            item('View Logs', lambda icon, item_obj: self.root.after(0, self.show_logs)),
            pystray.Menu.SEPARATOR,
            item('Quit', quit_app)
        ]
        
        # Create and run system tray
        self.tray_icon = pystray.Icon(
            name="Reminders",
            icon=create_image(),
            title="Reminder App",
            menu=pystray.Menu(*menu_items)
        )
        
        # Run tray in separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
    def show_taskbar_message(self):
        """Show message about taskbar minimization"""
        if not self.is_hidden:
            return
            
        # Create a temporary notification window
        taskbar_msg_window = tk.Toplevel()
        taskbar_msg_window.title("Reminder App - Background Mode")
        taskbar_msg_window.geometry("400x250")
        taskbar_msg_window.resizable(False, False)
        
        # Center the message window
        x = (taskbar_msg_window.winfo_screenwidth() // 2) - 200
        y = (taskbar_msg_window.winfo_screenheight() // 2) - 125
        taskbar_msg_window.geometry(f"+{x}+{y}")
        
        # Make it always on top
        taskbar_msg_window.attributes('-topmost', True)
        
        main_frame = ttk.Frame(taskbar_msg_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title with icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(pady=(0, 15))
        
        ttk.Label(title_frame, text="📋", font=("Arial", 20)).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="App is now running in background!", 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=(10, 0))
        
        # Instructions
        ttk.Label(main_frame, text="✅ You'll receive notifications for due reminders", 
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        ttk.Label(main_frame, text="✅ App is minimized to Windows taskbar", 
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        ttk.Label(main_frame, text="✅ Look for '📋 Reminders (Hidden)' in taskbar", 
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        ttk.Label(main_frame, text="✅ Click taskbar icon to restore window", 
                 font=("Arial", 9)).pack(anchor=tk.W, pady=2)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=(15, 10))
        
        # System tray info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_frame, text="💡 Want a system tray icon instead?", 
                 font=("Arial", 9, "bold")).pack()
        ttk.Label(info_frame, text="Install: pip install pystray Pillow", 
                 font=("Arial", 8)).pack()
        ttk.Label(info_frame, text="Then restart the app for full system tray support!", 
                 font=("Arial", 8)).pack()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="Show App Now", 
                  command=lambda: [self.show_window(), taskbar_msg_window.destroy()]).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Got It!", command=taskbar_msg_window.destroy).pack(side=tk.LEFT)
        
        # Auto close after 8 seconds
        taskbar_msg_window.after(8000, taskbar_msg_window.destroy)
        
    def add_email_setup_guide(self):
        """Show email setup guide"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Email Setup Guide")
        guide_window.geometry("600x500")
        guide_window.transient(self.root)
        guide_window.grab_set()
        
        # Center the window
        guide_window.update_idletasks()
        x = (guide_window.winfo_screenwidth() // 2) - (guide_window.winfo_width() // 2)
        y = (guide_window.winfo_screenheight() // 2) - (guide_window.winfo_height() // 2)
        guide_window.geometry(f"+{x}+{y}")
        
        # Create scrollable text widget
        main_frame = ttk.Frame(guide_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(main_frame, text="📧 Email Server Setup Guide", 
                 font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, width=70, height=25, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        guide_text = """📧 EMAIL SERVER SETUP GUIDE

═══════════════════════════════════════════════════════

🔹 GMAIL SETUP (Most Common)
═══════════════════════════════════════════════════════

1️⃣ ENABLE 2-FACTOR AUTHENTICATION:
   • Go to myaccount.google.com
   • Click "Security" → "2-Step Verification"
   • Follow the setup process

2️⃣ CREATE APP PASSWORD:
   • Go to myaccount.google.com
   • Security → 2-Step Verification → App passwords
   • Select "Mail" and "Windows Computer"
   • Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

3️⃣ SETTINGS IN REMINDER APP:
   • SMTP Server: smtp.gmail.com
   • SMTP Port: 587
   • Your Email: your-email@gmail.com
   • App Password: [paste the 16-char password from step 2]

═══════════════════════════════════════════════════════

🔹 OUTLOOK/HOTMAIL SETUP
═══════════════════════════════════════════════════════

1️⃣ ENABLE APP PASSWORDS:
   • Go to account.microsoft.com
   • Security → Advanced security options
   • Turn on "App passwords"

2️⃣ CREATE APP PASSWORD:
   • Generate new app password
   • Copy the password

3️⃣ SETTINGS IN REMINDER APP:
   • SMTP Server: smtp-mail.outlook.com
   • SMTP Port: 587
   • Your Email: your-email@outlook.com (or @hotmail.com)
   • App Password: [paste the app password from step 2]

═══════════════════════════════════════════════════════

🔹 YAHOO MAIL SETUP
═══════════════════════════════════════════════════════

1️⃣ ENABLE APP PASSWORDS:
   • Go to login.yahoo.com
   • Account Security → Generate app password

2️⃣ SETTINGS IN REMINDER APP:
   • SMTP Server: smtp.mail.yahoo.com
   • SMTP Port: 587
   • Your Email: your-email@yahoo.com
   • App Password: [your generated app password]

═══════════════════════════════════════════════════════

🔹 OTHER EMAIL PROVIDERS
═══════════════════════════════════════════════════════

For other email providers, you'll need:
• SMTP server address (usually smtp.yourprovider.com)
• Port number (usually 587 for TLS or 465 for SSL)
• Your email address
• App password or regular password (if app passwords not required)

═══════════════════════════════════════════════════════

⚠️  IMPORTANT SECURITY NOTES:

• NEVER use your regular email password
• Always use app-specific passwords when available
• App passwords are safer than regular passwords
• If you can't create app passwords, contact your email provider

═══════════════════════════════════════════════════════

🔧 TROUBLESHOOTING:

❌ "Authentication failed":
   → Check if you're using app password, not regular password
   → Verify 2FA is enabled (for Gmail)

❌ "Connection refused":
   → Check SMTP server address and port number
   → Try port 465 instead of 587

❌ "SSL/TLS error":
   → Make sure you're using the correct port (587 for TLS)

═══════════════════════════════════════════════════════

Need help? The most common setup is Gmail with app passwords!
"""
        
        text_widget.insert(tk.END, guide_text)
        text_widget.configure(state=tk.DISABLED)  # Make read-only
        
        # Close button
        ttk.Button(main_frame, text="Close", command=guide_window.destroy).pack(pady=(10, 0))
        
    def show_window(self):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False
        
        # Clean up taskbar window if it exists
        if hasattr(self, 'taskbar_window'):
            try:
                self.taskbar_window.destroy()
                delattr(self, 'taskbar_window')
            except:
                pass
            
        # Stop system tray if it exists
        if TRAY_AVAILABLE and hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except:
                pass
            
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Reminder App",
            "Lightweight Reminder Application\n\n"
            "Features:\n"
            "• Create and manage reminders\n"
            "• Background notifications\n"
            "• Lightweight and efficient\n"
            "• Runs in system tray\n\n"
            "Built with Python & Tkinter\n\n"
            "Made by Swapnil Shandilya"
        )
        
    def quit_app(self):
        """Quit the application completely"""
        if messagebox.askyesno("Quit Application", "Are you sure you want to quit the Reminder App?"):
            self.root.quit()
            sys.exit()
            
    def run(self):
        """Run the application"""
        self.root.mainloop()


class ReminderDialog:
    def __init__(self, parent, callback):
        self.callback = callback
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("New Reminder")
        self.dialog.geometry("700x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Create widgets
        self.create_dialog_widgets()
        
        # Focus on title entry
        self.title_entry.focus()
        
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        parent = self.dialog.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_dialog_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Form
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right side - Calendar
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === LEFT SIDE - FORM ===
        
        # Title
        ttk.Label(left_frame, text="Reminder Title:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.title_entry = ttk.Entry(left_frame, width=40)
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Due date
        ttk.Label(left_frame, text="Due Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        date_frame = ttk.Frame(left_frame)
        date_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Date selection
        today = datetime.now()
        self.date_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(date_frame, text="Today", command=self.set_today).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(date_frame, text="Tomorrow", command=self.set_tomorrow).grid(row=0, column=2)
        
        # Due time
        ttk.Label(left_frame, text="Due Time:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        time_frame = ttk.Frame(left_frame)
        time_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Time selection
        current_time = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.time_var = tk.StringVar(value=current_time.strftime("%H:%M"))
        self.time_entry = ttk.Entry(time_frame, textvariable=self.time_var, width=10)
        self.time_entry.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Label(time_frame, text="(HH:MM format)").grid(row=0, column=1)
        
        # Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Create Reminder", command=self.create_reminder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # === RIGHT SIDE - CALENDAR ===
        
        ttk.Label(right_frame, text="Calendar", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Calendar navigation
        nav_frame = ttk.Frame(right_frame)
        nav_frame.pack(pady=(0, 10))
        
        self.current_month = today.month
        self.current_year = today.year
        
        ttk.Button(nav_frame, text="<", width=3, command=self.prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(nav_frame, text="", font=("Arial", 10, "bold"))
        self.month_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text=">", width=3, command=self.next_month).pack(side=tk.LEFT)
        
        # Calendar display
        self.cal_frame = ttk.Frame(right_frame)
        self.cal_frame.pack()
        
        self.create_calendar()
        
        # Bind Enter key to create reminder
        self.dialog.bind('<Return>', lambda e: self.create_reminder())
        
    def create_calendar(self):
        """Create calendar display"""
        # Clear existing calendar
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
            
        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.config(text=f"{month_name} {self.current_year}")
        
        # Days of week headers
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            ttk.Label(self.cal_frame, text=day, font=("Arial", 8, "bold")).grid(row=0, column=i, padx=1, pady=1)
        
        # Get calendar for current month
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        today = datetime.now()
        
        for week_num, week in enumerate(cal, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.cal_frame, text="").grid(row=week_num, column=day_num, padx=1, pady=1)
                else:
                    # Highlight today
                    if (day == today.day and 
                        self.current_month == today.month and 
                        self.current_year == today.year):
                        btn = tk.Button(self.cal_frame, text=str(day), width=3, height=1,
                                      bg="#0078d4", fg="white", font=("Arial", 8, "bold"),
                                      command=lambda d=day: self.select_date(d))
                    else:
                        btn = tk.Button(self.cal_frame, text=str(day), width=3, height=1,
                                      bg="#f0f0f0", font=("Arial", 8),
                                      command=lambda d=day: self.select_date(d))
                    btn.grid(row=week_num, column=day_num, padx=1, pady=1)
    
    def prev_month(self):
        """Navigate to previous month"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.create_calendar()
    
    def next_month(self):
        """Navigate to next month"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.create_calendar()
    
    def select_date(self, day):
        """Select a date from calendar"""
        selected_date = datetime(self.current_year, self.current_month, day)
        self.date_var.set(selected_date.strftime("%Y-%m-%d"))
        self.create_calendar()  # Refresh calendar to show selection
        
    def set_today(self):
        """Set date to today"""
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        
    def set_tomorrow(self):
        """Set date to tomorrow"""
        tomorrow = datetime.now() + timedelta(days=1)
        self.date_var.set(tomorrow.strftime("%Y-%m-%d"))
        
    def create_reminder(self):
        """Create the reminder"""
        title = self.title_entry.get().strip()
        due_date = self.date_var.get().strip()
        due_time = self.time_var.get().strip()
        
        # Validation
        if not title:
            messagebox.showerror("Error", "Please enter a reminder title.")
            return
            
        try:
            # Validate date format
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Please enter date in YYYY-MM-DD format.")
            return
            
        try:
            # Validate time format
            datetime.strptime(due_time, "%H:%M")
        except ValueError:
            messagebox.showerror("Error", "Please enter time in HH:MM format.")
            return
            
        # Check if the due date/time is not in the past
        try:
            due_datetime = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
            if due_datetime <= datetime.now():
                if not messagebox.askyesno("Past Date/Time", "The specified date/time is in the past. Do you want to continue?"):
                    return
        except ValueError:
            messagebox.showerror("Error", "Invalid date/time combination.")
            return
            
        # Create reminder
        self.callback(title, due_date, due_time)
        self.dialog.destroy()


class UpdateProgressDialog:
    def __init__(self, parent, reminder, callback):
        self.callback = callback
        self.reminder = reminder.copy()  # Work with a copy
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Update Progress - {reminder['title']}")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Create widgets
        self.create_dialog_widgets()
        
        # Focus on comments
        self.comments_text.focus()
        
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        parent = self.dialog.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_dialog_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_container = ttk.Frame(self.dialog, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title section
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="📋 Update Task Progress", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"Task: {self.reminder['title']}", 
                 font=("Arial", 10)).pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(title_frame, text=f"Due: {self.reminder['due_date']} at {self.reminder['due_time']}", 
                 font=("Arial", 9), foreground="gray").pack(anchor=tk.W)
        
        # Comments section
        comments_frame = ttk.LabelFrame(main_container, text="💬 Comments & Notes", padding="10")
        comments_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Comments text widget with scrollbar
        text_frame = ttk.Frame(comments_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.comments_text = tk.Text(text_frame, height=6, font=("Arial", 10), 
                                    wrap=tk.WORD, bg="white")
        comments_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                          command=self.comments_text.yview)
        self.comments_text.configure(yscrollcommand=comments_scrollbar.set)
        
        self.comments_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        comments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load existing comments
        existing_comments = self.reminder.get("comments", "")
        if existing_comments:
            self.comments_text.insert(tk.END, existing_comments)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_container, text="📊 Progress Level", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Progress slider
        slider_frame = ttk.Frame(progress_frame)
        slider_frame.pack(fill=tk.X)
        
        ttk.Label(slider_frame, text="Completion Level:").pack(anchor=tk.W)
        
        self.progress_var = tk.IntVar(value=self.reminder.get("progress", 0))
        
        progress_container = ttk.Frame(slider_frame)
        progress_container.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_slider = tk.Scale(progress_container, from_=0, to=10, 
                                       orient=tk.HORIZONTAL, variable=self.progress_var, 
                                       length=300, font=("Arial", 9))
        self.progress_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_label = ttk.Label(progress_container, text=f"{self.progress_var.get()}/10", 
                                       font=("Arial", 11, "bold"))
        self.progress_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Update progress label when slider changes
        def update_progress_label(val):
            self.progress_label.config(text=f"{val}/10")
        self.progress_slider.config(command=update_progress_label)
        
        # History section
        if self.reminder.get("updates"):
            history_frame = ttk.LabelFrame(main_container, text="📜 Recent Updates", padding="10")
            history_frame.pack(fill=tk.X, pady=(0, 15))
            
            history_text = tk.Text(history_frame, height=3, font=("Arial", 9), 
                                  state=tk.DISABLED, bg="#f8f8f8")
            history_text.pack(fill=tk.X)
            
            # Load update history
            updates = self.reminder.get("updates", [])[-3:]  # Last 3 updates
            if updates:
                history_text.config(state=tk.NORMAL)
                for update in updates:
                    timestamp = datetime.fromisoformat(update["timestamp"]).strftime("%m/%d %H:%M")
                    comment_snippet = update["comment"][:50] + "..." if len(update["comment"]) > 50 else update["comment"]
                    history_text.insert(tk.END, f"🕒 {timestamp}: Progress {update['progress']}/10 - {comment_snippet}\n")
                history_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="📝 Update Progress", 
                  command=self.update_progress).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # Bind Enter key to update
        self.dialog.bind('<Return>', lambda e: self.update_progress())
        
    def update_progress(self):
        """Update the reminder progress and comments"""
        # Get current values
        comments = self.comments_text.get("1.0", tk.END).strip()
        progress = self.progress_var.get()
        
        # Update reminder data
        self.reminder["comments"] = comments
        self.reminder["progress"] = progress
        
        # Add to updates history (threading system)
        if "updates" not in self.reminder:
            self.reminder["updates"] = []
        
        update_entry = {
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "comment": comments[:100] + "..." if len(comments) > 100 else comments,
            "action": "progress_update"
        }
        self.reminder["updates"].append(update_entry)
        
        # Keep only last 10 updates
        if len(self.reminder["updates"]) > 10:
            self.reminder["updates"] = self.reminder["updates"][-10:]
        
        # Call callback with updated reminder
        self.callback(self.reminder)
        
        # Close dialog
        self.dialog.destroy()


if __name__ == "__main__":
    app = ReminderApp()
    app.run()
