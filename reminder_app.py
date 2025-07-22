import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os
import threading
import time
from tkinter import font
import sys

class ReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Reminders")
        self.root.geometry("600x400")
        self.root.minsize(500, 300)
        
        # Configure the app to run in system tray when closed
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Data file path
        self.data_file = "reminders.json"
        self.reminders = []
        
        # Load existing reminders
        self.load_reminders()
        
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
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_font = font.Font(size=16, weight="bold")
        title_label = ttk.Label(main_frame, text="Reminders", font=title_font)
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Reminders list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Create treeview for reminders
        columns = ("Title", "Due Date", "Due Time", "Status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        self.tree.heading("Title", text="Reminder")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Due Time", text="Due Time")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Title", width=250, minwidth=150)
        self.tree.column("Due Date", width=100, minwidth=80)
        self.tree.column("Due Time", width=100, minwidth=80)
        self.tree.column("Status", width=80, minwidth=60)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid treeview and scrollbar
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Buttons
        ttk.Button(buttons_frame, text="Mark Complete", command=self.mark_complete).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Delete", command=self.delete_reminder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_list).pack(side=tk.LEFT)
        
        # Restore/Show button (for when running in background)
        ttk.Button(buttons_frame, text="Hide to Tray", command=self.hide_window).pack(side=tk.RIGHT)
        
        # Populate the list
        self.refresh_list()
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Reminder", command=self.new_reminder)
        file_menu.add_separator()
        file_menu.add_command(label="Show Window", command=self.show_window)
        file_menu.add_command(label="Hide to Tray", command=self.hide_window)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
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
            "created": datetime.now().isoformat()
        }
        self.reminders.append(reminder)
        self.save_reminders()
        self.refresh_list()
        
    def mark_complete(self):
        """Mark selected reminder as complete"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a reminder to mark as complete.")
            return
            
        item = selection[0]
        index = self.tree.index(item)
        
        if index < len(self.reminders):
            self.reminders[index]["status"] = "Completed"
            self.save_reminders()
            self.refresh_list()
            
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
        
        # Add reminders to tree
        for reminder in sorted_reminders:
            # Color code based on status and due date
            tags = []
            if reminder["status"] == "Completed":
                tags.append("completed")
            elif self.is_overdue(reminder):
                tags.append("overdue")
            elif self.is_due_soon(reminder):
                tags.append("due_soon")
                
            self.tree.insert("", tk.END, values=(
                reminder["title"],
                reminder["due_date"],
                reminder["due_time"],
                reminder["status"]
            ), tags=tags)
            
        # Configure tags
        self.tree.tag_configure("completed", foreground="gray")
        self.tree.tag_configure("overdue", foreground="red", background="#ffe6e6")
        self.tree.tag_configure("due_soon", foreground="orange", background="#fff3cd")
        
    def is_overdue(self, reminder):
        """Check if reminder is overdue"""
        try:
            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
            return datetime.now() > due_datetime and reminder["status"] != "Completed"
        except:
            return False
            
    def is_due_soon(self, reminder):
        """Check if reminder is due within next hour"""
        try:
            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            return now <= due_datetime <= now + timedelta(hours=1) and reminder["status"] != "Completed"
        except:
            return False
            
    def load_reminders(self):
        """Load reminders from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.reminders = json.load(f)
        except Exception as e:
            print(f"Error loading reminders: {e}")
            self.reminders = []
            
    def save_reminders(self):
        """Save reminders to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"Error saving reminders: {e}")
            
    def start_reminder_checker(self):
        """Start background thread to check for due reminders"""
        def check_reminders():
            while True:
                try:
                    current_time = datetime.now()
                    for reminder in self.reminders:
                        if reminder["status"] == "Pending":
                            due_datetime = datetime.strptime(f"{reminder['due_date']} {reminder['due_time']}", "%Y-%m-%d %H:%M")
                            if current_time >= due_datetime:
                                self.show_reminder_notification(reminder)
                                reminder["status"] = "Notified"
                                self.save_reminders()
                                # Update GUI if window is visible
                                if self.root.state() != 'withdrawn':
                                    self.root.after(0, self.refresh_list)
                except Exception as e:
                    print(f"Error in reminder checker: {e}")
                    
                time.sleep(30)  # Check every 30 seconds
                
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
        
    def hide_window(self):
        """Hide window to system tray"""
        self.root.withdraw()
        # Show tray icon notification
        self.show_tray_message()
        
    def show_window(self):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
    def show_tray_message(self):
        """Show message about running in background"""
        # Create a temporary window to show the message
        tray_window = tk.Toplevel()
        tray_window.title("Reminder App")
        tray_window.geometry("300x150")
        tray_window.resizable(False, False)
        
        # Center the tray message window
        x = (tray_window.winfo_screenwidth() // 2) - 150
        y = (tray_window.winfo_screenheight() // 2) - 75
        tray_window.geometry(f"+{x}+{y}")
        
        ttk.Label(tray_window, text="Reminder App is now running\nin the background.", 
                 font=("Arial", 10), justify=tk.CENTER).pack(pady=20)
        ttk.Label(tray_window, text="You will receive notifications\nfor due reminders.", 
                 font=("Arial", 9), justify=tk.CENTER).pack(pady=5)
        
        button_frame = ttk.Frame(tray_window)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="Show App", command=lambda: [self.show_window(), tray_window.destroy()]).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="OK", command=tray_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Auto close after 3 seconds
        tray_window.after(3000, tray_window.destroy)
        
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
            "Built with Python & Tkinter"
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
        self.dialog.geometry("400x300")
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
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        ttk.Label(main_frame, text="Reminder Title:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.title_entry = ttk.Entry(main_frame, width=40)
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Due date
        ttk.Label(main_frame, text="Due Date:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Date selection
        today = datetime.now()
        self.date_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(date_frame, text="Today", command=self.set_today).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(date_frame, text="Tomorrow", command=self.set_tomorrow).grid(row=0, column=2)
        
        # Due time
        ttk.Label(main_frame, text="Due Time:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Time selection
        current_time = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.time_var = tk.StringVar(value=current_time.strftime("%H:%M"))
        self.time_entry = ttk.Entry(time_frame, textvariable=self.time_var, width=10)
        self.time_entry.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Label(time_frame, text="(HH:MM format)").grid(row=0, column=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Create Reminder", command=self.create_reminder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # Bind Enter key to create reminder
        self.dialog.bind('<Return>', lambda e: self.create_reminder())
        
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


if __name__ == "__main__":
    app = ReminderApp()
    app.run()
