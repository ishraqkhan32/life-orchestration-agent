import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import json
import uuid
from datetime import datetime, date
import base64
import os
from PIL import Image, ImageTk
import requests
from typing import Optional, List, Dict
import tkinter.simpledialog as simpledialog
import platform

class LifeManagementApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Orchestration Agent")
        
        # Set application icon
        self.set_app_icon()

        # set the window to full screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.configure(bg='#f8fafc')
        
        # Initialize autosave variables
        self.autosave_enabled = True
        self.autosave_delay = 2000  # milliseconds
        self.autosave_jobs = {}
        
        # Initialize database
        self.init_database()
        
        # Create main interface
        self.create_interface()
        
        # Load data
        self.load_data()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        self.conn = sqlite3.connect('life_management.db')
        self.cursor = self.conn.cursor()
        
        # Life priorities table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS priorities (
                category TEXT PRIMARY KEY,
                description TEXT
            )
        ''')
        
        # Affirmations table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS affirmations (
                id INTEGER PRIMARY KEY,
                content TEXT,
                date_updated TEXT
            )
        ''')
        
        # Vision board images table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vision_images (
                id TEXT PRIMARY KEY,
                name TEXT,
                image_data TEXT
            )
        ''')
        
        # Tasks table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT,
                category TEXT,
                priority INTEGER,
                status TEXT,
                is_daily BOOLEAN,
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Journal entries table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                date TEXT PRIMARY KEY,
                content TEXT,
                feedback TEXT
            )
        ''')
        
        self.conn.commit()
    
    def set_app_icon(self):
        """Set the application icon (window and Dock)"""
        try:
            # Set Tkinter window icon (cross-platform)
            icon_png_path = os.path.join("assets", "icon.png")
            if os.path.exists(icon_png_path):
                icon_image = Image.open(icon_png_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
                self.icon_image = icon_photo  # Prevent garbage collection

            # Set Dock icon on macOS using .icns file and pyobjc
            if platform.system() == "Darwin":
                icns_path = os.path.join(os.path.dirname(__file__), "assets", "icon.icns")
                if os.path.exists(icns_path):
                    try:
                        from AppKit import NSApplication, NSImage
                        from Foundation import NSURL
                        app = NSApplication.sharedApplication()
                        nsimage = NSImage.alloc().initByReferencingFile_(icns_path)
                        if nsimage:
                            app.setApplicationIconImage_(nsimage)
                    except Exception as e:
                        print(f"Could not set Dock icon: {e}")

            # Optionally set icon name
            self.root.iconname("Orchestration Agent")
        except Exception as e:
            print(f"Could not set app icon: {e}")
            pass
    
    def schedule_autosave(self, widget_name: str, save_function):
        """Schedule an autosave operation for a specific widget"""
        if not self.autosave_enabled:
            return
            
        # Cancel existing job for this widget
        if widget_name in self.autosave_jobs:
            self.root.after_cancel(self.autosave_jobs[widget_name])
        
        # Schedule new job using Tkinter's after method
        job_id = self.root.after(self.autosave_delay, save_function)
        self.autosave_jobs[widget_name] = job_id
    
    def on_text_change(self, widget_name: str, save_function):
        """Handle text change events and schedule autosave"""
        def callback(event=None):
            self.schedule_autosave(widget_name, save_function)
        return callback
    
    def create_interface(self):
        """Create the main interface with tabs"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_tasks_tab()
        self.create_weekly_planning_tab()
        self.create_journal_tab()
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with priorities, affirmations, and vision board"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        dashboard_content = ttk.Frame(dashboard_frame)
        dashboard_content.pack(fill=tk.BOTH, expand=True)

        dashboard_content.rowconfigure(0, weight=1)
        dashboard_content.rowconfigure(1, weight=1)
        dashboard_content.columnconfigure(0, weight=1)

        # Life Priorities Section
        priorities_frame = ttk.LabelFrame(dashboard_content, text="Life Priorities", padding=20)
        priorities_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))

        # Make each column take up 1/3 of the space
        for col in range(3):
            priorities_frame.grid_columnconfigure(col, weight=1)

        self.priority_vars = {}
        priorities = ['career', 'health', 'finances', 'religion', 'relationships', 'hobbies']
        
        for i, priority in enumerate(priorities):
            row = i // 3
            col = i % 3
            
            ttk.Label(priorities_frame, text=priority.capitalize() + ":").grid(
                row=row*2, column=col, sticky="w", padx=5, pady=(5, 0)
            )
            
            text_widget = tk.Text(priorities_frame, height=4, width=1, wrap=tk.WORD, undo=True)
            text_widget.grid(row=row*2+1, column=col, padx=5, pady=(0, 10), sticky="nsew")
            priorities_frame.grid_rowconfigure(row*2+1, weight=1)
            
            # Bind autosave to text changes
            text_widget.bind('<KeyRelease>', self.on_text_change(f'priority_{priority}', self.save_priorities))
            
            self.priority_vars[priority] = text_widget
        
        # Save priorities button
        save_button = ttk.Button(priorities_frame, text="Save Priorities", command=self.save_priorities)
        save_button.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Affirmations Section
        affirmations_frame = ttk.LabelFrame(dashboard_content, text="Daily Affirmations", padding=20)
        affirmations_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        
        self.affirmations_text = scrolledtext.ScrolledText(affirmations_frame, height=6, wrap=tk.WORD, undo=True)
        self.affirmations_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Bind autosave to text changes
        self.affirmations_text.bind('<KeyRelease>', self.on_text_change('affirmations', self.save_affirmations))
        
        ttk.Button(affirmations_frame, text="Save Affirmations", 
                  command=self.save_affirmations).pack(pady=5)
        
        # Vision Board Section
        # vision_frame = ttk.LabelFrame(scrollable_frame, text="Vision Board", padding=20)
        # vision_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # ttk.Button(vision_frame, text="Upload Images", 
        #           command=self.upload_vision_images).pack(pady=5)
        
        # # Vision board display frame
        # self.vision_display_frame = ttk.Frame(vision_frame)
        # self.vision_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def create_tasks_tab(self):
        """Create the tasks tab with daily and massive backlogs"""
        tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(tasks_frame, text="Tasks")

        # Create two columns for daily and massive backlog
        daily_frame = ttk.LabelFrame(tasks_frame, text="Today's Tasks", padding=10)
        daily_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)

        backlog_frame = ttk.LabelFrame(tasks_frame, text="Task Backlog", padding=10)
        backlog_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        # Daily tasks section
        daily_input_frame = ttk.Frame(daily_frame)
        daily_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.daily_task_entry = ttk.Entry(daily_input_frame)
        self.daily_task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.daily_task_entry.bind('<Return>', lambda e: self.add_task(True))

        ttk.Button(daily_input_frame, text="Add Task", 
                  command=lambda: self.add_task(True)).pack(side=tk.RIGHT)

        # Daily tasks listbox with scrollbar
        daily_list_frame = ttk.Frame(daily_frame)
        daily_list_frame.pack(fill=tk.BOTH, expand=True)

        self.daily_tasks_listbox = tk.Listbox(daily_list_frame, selectmode=tk.SINGLE)
        daily_scrollbar = ttk.Scrollbar(daily_list_frame, orient=tk.VERTICAL)
        self.daily_tasks_listbox.config(yscrollcommand=daily_scrollbar.set)
        daily_scrollbar.config(command=self.daily_tasks_listbox.yview)

        self.daily_tasks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        daily_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Daily tasks buttons
        daily_buttons_frame = ttk.Frame(daily_frame)
        daily_buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(daily_buttons_frame, text="Complete", 
                  command=lambda: self.toggle_task(True)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(daily_buttons_frame, text="Delete", 
                  command=lambda: self.delete_task(True)).pack(side=tk.LEFT)

        # Massive backlog section
        backlog_input_frame = ttk.Frame(backlog_frame)
        backlog_input_frame.pack(fill=tk.X, pady=(0, 10))

        self.backlog_task_entry = ttk.Entry(backlog_input_frame)
        self.backlog_task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.backlog_task_entry.bind('<Return>', lambda e: self.add_task(False))

        ttk.Button(backlog_input_frame, text="Add Task", 
                  command=lambda: self.add_task(False)).pack(side=tk.RIGHT)

        # Backlog tasks listbox with scrollbar
        backlog_list_frame = ttk.Frame(backlog_frame)
        backlog_list_frame.pack(fill=tk.BOTH, expand=True)

        self.backlog_tasks_listbox = tk.Listbox(backlog_list_frame, selectmode=tk.SINGLE)
        backlog_scrollbar = ttk.Scrollbar(backlog_list_frame, orient=tk.VERTICAL)
        self.backlog_tasks_listbox.config(yscrollcommand=backlog_scrollbar.set)
        backlog_scrollbar.config(command=self.backlog_tasks_listbox.yview)

        self.backlog_tasks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backlog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Backlog tasks buttons
        backlog_buttons_frame = ttk.Frame(backlog_frame)
        backlog_buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(backlog_buttons_frame, text="Move to Daily", 
                  command=self.move_to_daily).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(backlog_buttons_frame, text="Complete", 
                  command=lambda: self.toggle_task(False)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(backlog_buttons_frame, text="Delete", 
                  command=lambda: self.delete_task(False)).pack(side=tk.LEFT)

        # Bind double-click to edit_task for both listboxes
        self.daily_tasks_listbox.bind('<Double-Button-1>', self.edit_task)
        self.backlog_tasks_listbox.bind('<Double-Button-1>', self.edit_task)

    def create_journal_tab(self):
        """Create the journal tab with reflection input and history"""
        journal_frame = ttk.Frame(self.notebook)
        self.notebook.add(journal_frame, text="Journal")

        # Use grid for full control
        journal_frame.columnconfigure(0, weight=3)
        journal_frame.columnconfigure(1, weight=2)
        journal_frame.rowconfigure(0, weight=1)

        # Left side - Journal input and feedback
        left_frame = ttk.Frame(journal_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)

        # Right side - Journal history
        right_frame = ttk.LabelFrame(journal_frame, text="Journal History", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)

        # Date selection
        date_frame = ttk.Frame(left_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 5))
        self.journal_date = tk.StringVar(value=date.today().isoformat())
        self.date_entry = ttk.Entry(date_frame, textvariable=self.journal_date, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.date_entry.bind('<Return>', self.load_journal_entry)
        
        ttk.Button(date_frame, text="Load Entry", 
                  command=self.load_journal_entry).pack(side=tk.LEFT)
        
        # Journal input
        ttk.Label(left_frame, text="Journal Reflection:").pack(anchor=tk.W, pady=(0, 5))
        self.journal_text = scrolledtext.ScrolledText(left_frame, height=15, wrap=tk.WORD, undo=True)
        self.journal_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Bind autosave to text changes
        self.journal_text.bind('<KeyRelease>', self.on_text_change('journal', self.auto_save_journal))
        
        ttk.Button(left_frame, text="Submit Reflection", 
                  command=self.submit_journal).pack(pady=5)
        
        # Feedback section
        feedback_frame = ttk.LabelFrame(left_frame, text="AI Feedback", padding=10)
        feedback_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.feedback_text = scrolledtext.ScrolledText(feedback_frame, height=8, wrap=tk.WORD, 
                                                      state=tk.DISABLED, undo=True)
        self.feedback_text.pack(fill=tk.BOTH, expand=True)
        
        # History listbox with scrollbar
        history_list_frame = ttk.Frame(right_frame)
        history_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_listbox = tk.Listbox(history_list_frame, selectmode=tk.SINGLE)
        history_scrollbar = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL)
        self.history_listbox.config(yscrollcommand=history_scrollbar.set)
        history_scrollbar.config(command=self.history_listbox.yview)
        
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox.bind('<Double-Button-1>', self.load_selected_entry)
    
    def create_weekly_planning_tab(self):
        """Create the weekly planning tab with 7 columns for each day of the week"""
        import calendar
        from datetime import timedelta, date

        weekly_frame = ttk.Frame(self.notebook)
        self.notebook.add(weekly_frame, text="Weekly Planning")

        # Top frame for week start selection
        top_frame = ttk.Frame(weekly_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top_frame, text="Start of Week (YYYY-MM-DD):").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(top_frame, text="⟵", command=self.goto_previous_week, width=0.25).pack(side=tk.LEFT)

        
        self.week_start_var = tk.StringVar()
        # Set week_start_var to Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        self.week_start_var.set(monday.isoformat())
        self.week_start_entry = ttk.Entry(top_frame, textvariable=self.week_start_var, width=12)
        self.week_start_entry.pack(side=tk.LEFT)

        # Add Previous and Next Week buttons
        
        ttk.Button(top_frame, text="⟶", command=self.goto_next_week, width=0.25).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(top_frame, text="Set Week", command=self.update_week_dates).pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Save Week", command=self.save_weekly_planning).pack(side=tk.LEFT, padx=(10, 0))

        # Frame for the 7 columns
        days_frame = ttk.Frame(weekly_frame)
        days_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        days_frame.grid_rowconfigure(0, weight=0)
        days_frame.grid_rowconfigure(1, weight=0)
        days_frame.grid_rowconfigure(2, weight=1)
        for col in range(7):
            days_frame.grid_columnconfigure(col, weight=1)

        self.weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.weekday_date_vars = []
        self.weekday_text_widgets = []

        # Create headers and text widgets for each day
        for col, day_name in enumerate(self.weekday_names):
            ttk.Label(days_frame, text=day_name, anchor="center").grid(row=0, column=col, padx=0, pady=0, sticky="ew")
            date_var = tk.StringVar()
            date_entry = ttk.Entry(days_frame, textvariable=date_var, width=10, justify="center")
            date_entry.grid(row=1, column=col, padx=0, pady=0, sticky="ew")
            self.weekday_date_vars.append(date_var)
            text_widget = tk.Text(days_frame, height=15, wrap=tk.WORD, undo=True, insertbackground="grey")
            text_widget.grid(row=2, column=col, padx=0, pady=0, sticky="nsew")
            # Bind autosave to text changes
            text_widget.bind('<KeyRelease>', self.on_text_change(f'weekly_{col}', self.save_weekly_planning))
            self.weekday_text_widgets.append(text_widget)

        # Create table for weekly planning if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_planning (
                week_start TEXT,
                day_index INTEGER,
                content TEXT,
                PRIMARY KEY (week_start, day_index)
            )
        ''')
        self.conn.commit()

        # Initialize the week dates and load data
        self.update_week_dates()

    def update_week_dates(self):
        """Update the date entries for each day of the week based on the start date and load saved data"""
        from datetime import datetime, timedelta
        try:
            input_date = datetime.strptime(self.week_start_var.get(), "%Y-%m-%d").date()
            # Find the previous Monday (or the same day if it's Monday)
            monday = input_date - timedelta(days=input_date.weekday())
            self.week_start_var.set(monday.isoformat())
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid start date in YYYY-MM-DD format.")
            return
        for i, (date_var, text_widget) in enumerate(zip(self.weekday_date_vars, self.weekday_text_widgets)):
            day_date = monday + timedelta(days=i)
            date_var.set(day_date.isoformat())
            if day_date < date.today():
                text_widget.config(background="#f5f5f5", foreground="#555555")
        self.load_weekly_planning()

    def save_weekly_planning(self):
        """Save the weekly planning text for each day into the database"""
        week_start = self.week_start_var.get()
        for i, text_widget in enumerate(self.weekday_text_widgets):
            content = text_widget.get(1.0, tk.END).strip()
            self.cursor.execute(
                "INSERT OR REPLACE INTO weekly_planning (week_start, day_index, content) VALUES (?, ?, ?)",
                (week_start, i, content)
            )
        self.conn.commit()

    def load_weekly_planning(self):
        """Load the weekly planning text for each day from the database"""
        week_start = self.week_start_var.get()
        self.cursor.execute(
            "SELECT day_index, content FROM weekly_planning WHERE week_start = ?",
            (week_start,)
        )
        data = {row[0]: row[1] for row in self.cursor.fetchall()}
        for i, text_widget in enumerate(self.weekday_text_widgets):
            text_widget.delete(1.0, tk.END)
            if i in data:
                text_widget.insert(1.0, data[i])

    def goto_previous_week(self):
        """Go to the previous week (Monday) and update the view"""
        from datetime import datetime, timedelta
        try:
            current_monday = datetime.strptime(self.week_start_var.get(), "%Y-%m-%d").date()
            prev_monday = current_monday - timedelta(days=7)
            self.week_start_var.set(prev_monday.isoformat())
            self.update_week_dates()
        except Exception as e:
            messagebox.showerror("Error", f"Could not go to previous week: {e}")

    def goto_next_week(self):
        """Go to the next week (Monday) and update the view"""
        from datetime import datetime, timedelta
        try:
            current_monday = datetime.strptime(self.week_start_var.get(), "%Y-%m-%d").date()
            next_monday = current_monday + timedelta(days=7)
            self.week_start_var.set(next_monday.isoformat())
            self.update_week_dates()
        except Exception as e:
            messagebox.showerror("Error", f"Could not go to next week: {e}")

    def load_data(self):
        """Load all data from database"""
        self.load_priorities()
        self.load_affirmations()
        self.load_tasks()
        self.load_journal_history()
    
    def load_priorities(self):
        """Load life priorities from database"""
        self.cursor.execute("SELECT category, description FROM priorities")
        priorities = self.cursor.fetchall()
        
        for category, description in priorities:
            if category in self.priority_vars:
                self.priority_vars[category].delete(1.0, tk.END)
                self.priority_vars[category].insert(1.0, description or "")
    
    def save_priorities(self):
        """Save life priorities to database"""
        for category, text_widget in self.priority_vars.items():
            description = text_widget.get(1.0, tk.END).strip()
            self.cursor.execute(
                "INSERT OR REPLACE INTO priorities (category, description) VALUES (?, ?)",
                (category, description)
            )
        self.conn.commit()
    
    def load_affirmations(self):
        """Load affirmations from database"""
        self.cursor.execute("SELECT content FROM affirmations ORDER BY date_updated DESC LIMIT 1")
        result = self.cursor.fetchone()
        if result:
            self.affirmations_text.delete(1.0, tk.END)
            self.affirmations_text.insert(1.0, result[0])
    
    def save_affirmations(self):
        """Save affirmations to database"""
        content = self.affirmations_text.get(1.0, tk.END).strip()
        self.cursor.execute(
            "INSERT OR REPLACE INTO affirmations (id, content, date_updated) VALUES (1, ?, ?)",
            (content, datetime.now().isoformat())
        )
        self.conn.commit()
    
    def add_task(self, is_daily: bool):
        """Add a new task"""
        entry_widget = self.daily_task_entry if is_daily else self.backlog_task_entry
        description = entry_widget.get().strip()
        
        if not description:
            return
        
        task_id = str(uuid.uuid4())
        self.cursor.execute(
            """INSERT INTO tasks 
               (id, description, category, priority, status, is_daily, created_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, description, 'general', 1, 'pending', is_daily, 
             datetime.now().isoformat(), None)
        )
        self.conn.commit()
        
        entry_widget.delete(0, tk.END)
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from database"""
        # Load daily tasks
        self.daily_tasks_listbox.delete(0, tk.END)
        self.cursor.execute(
            "SELECT id, description, status FROM tasks WHERE is_daily = ? ORDER BY created_at",
            (True,)
        )
        self.daily_tasks = self.cursor.fetchall()

        for task_id, description, status in self.daily_tasks:
            display_text = f"{'✓' if status == 'completed' else '○'} {description}"
            self.daily_tasks_listbox.insert(tk.END, display_text)

        # Load backlog tasks (no filtering)
        self.backlog_tasks_listbox.delete(0, tk.END)
        self.cursor.execute(
            "SELECT id, description, status FROM tasks WHERE is_daily = ? ORDER BY created_at",
            (False,)
        )
        self.backlog_tasks = self.cursor.fetchall()

        for task_id, description, status in self.backlog_tasks:
            display_text = f"{'✓' if status == 'completed' else '○'} {description}"
            self.backlog_tasks_listbox.insert(tk.END, display_text)

    def toggle_task(self, is_daily: bool):
        """Toggle task completion status"""
        listbox = self.daily_tasks_listbox if is_daily else self.backlog_tasks_listbox
        tasks = self.daily_tasks if is_daily else self.backlog_tasks
        
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task first.")
            return
        
        task_index = selection[0]
        if task_index >= len(tasks):
            return
        
        task_id, description, current_status = tasks[task_index]
        new_status = 'completed' if current_status == 'pending' else 'pending'
        completed_at = datetime.now().isoformat() if new_status == 'completed' else None
        
        self.cursor.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (new_status, completed_at, task_id)
        )
        self.conn.commit()
        self.load_tasks()
    
    def delete_task(self, is_daily: bool):
        """Delete a task"""
        listbox = self.daily_tasks_listbox if is_daily else self.backlog_tasks_listbox
        tasks = self.daily_tasks if is_daily else self.backlog_tasks
        
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task first.")
            return
        
        task_index = selection[0]
        if task_index >= len(tasks):
            return
        
        task_id = tasks[task_index][0]
    
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()
    
    def move_to_daily(self):
        """Move a task from backlog to daily"""
        selection = self.backlog_tasks_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task first.")
            return
        
        task_index = selection[0]
        tasks = self.backlog_tasks
        if task_index >= len(tasks):
            return
        
        task_id = tasks[task_index][0]
        
        self.cursor.execute(
            "UPDATE tasks SET is_daily = ? WHERE id = ?",
            (True, task_id)
        )
        self.conn.commit()
        self.load_tasks()
    
    def auto_save_journal(self):
        """Auto-save journal content without generating feedback"""
        journal_date = self.journal_date.get()
        content = self.journal_text.get(1.0, tk.END).strip()
        
        if content:
            # Save content without feedback (feedback will be generated on manual submit)
            self.cursor.execute(
                "INSERT OR REPLACE INTO journal_entries (date, content) VALUES (?, ?)",
                (journal_date, content)
            )
            self.conn.commit()
    
    def submit_journal(self):
        """Submit journal reflection and get AI feedback"""
        journal_date = self.journal_date.get()
        content = self.journal_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("Warning", "Please write a reflection first.")
            return
        
        # Generate feedback
        feedback = self.generate_feedback(content)
        
        # Save to database
        self.cursor.execute(
            "INSERT OR REPLACE INTO journal_entries (date, content, feedback) VALUES (?, ?, ?)",
            (journal_date, content, feedback)
        )
        self.conn.commit()
        
        # Display feedback
        self.feedback_text.config(state=tk.NORMAL)
        self.feedback_text.delete(1.0, tk.END)
        self.feedback_text.insert(1.0, feedback)
        self.feedback_text.config(state=tk.DISABLED)
        
        # Refresh history
        self.load_journal_history()
        messagebox.showinfo("Success", "Journal reflection submitted successfully!")
    
    def generate_feedback(self, reflection: str) -> str:
        """Generate AI feedback for journal reflection"""
        # Get user's priorities for context
        self.cursor.execute("SELECT category, description FROM priorities WHERE description IS NOT NULL AND description != ''")
        priorities = self.cursor.fetchall()
        
        goal_context = ", ".join([f"{cat}: {desc}" for cat, desc in priorities])
        
        # This is a simplified feedback generator
        # In production, you would call Ollama API here
        positive_keywords = ['grateful', 'accomplished', 'progress', 'success', 'happy', 'achieved', 'proud']
        challenge_keywords = ['difficult', 'struggle', 'failed', 'worried', 'stressed', 'behind', 'overwhelmed']
        
        reflection_lower = reflection.lower()
        has_positive = any(word in reflection_lower for word in positive_keywords)
        has_challenges = any(word in reflection_lower for word in challenge_keywords)
        
        feedback = "**Reflection Analysis:**\n\n"
        
        if has_positive:
            feedback += "✅ Great to see positive momentum! Your reflection shows growth and accomplishment.\n\n"
        
        if has_challenges:
            feedback += "🎯 I notice some challenges mentioned. Remember that obstacles are opportunities for growth.\n\n"
        
        feedback += "**Alignment Check:**\n"
        if goal_context:
            feedback += f"Your current goals ({goal_context}) provide a strong foundation. Consider how today's experiences connect to these priorities.\n\n"
        else:
            feedback += "Consider setting clear life priorities to better align your daily actions with your long-term goals.\n\n"
        
        feedback += "**Actionable Suggestions:**\n"
        feedback += "• Identify one small win from today to build momentum\n"
        feedback += "• Choose one area from your priorities to focus on tomorrow\n"
        feedback += "• Practice gratitude for progress made, however small\n"
        feedback += "• Reflect on lessons learned from today's challenges"
        
        return feedback
    
    def load_journal_entry(self, event=None):
        """Load journal entry for selected date"""
        journal_date = self.journal_date.get()
        
        self.cursor.execute(
            "SELECT content, feedback FROM journal_entries WHERE date = ?",
            (journal_date,)
        )
        result = self.cursor.fetchone()
        
        if result:
            content, feedback = result
            self.journal_text.delete(1.0, tk.END)
            self.journal_text.insert(1.0, content)
            
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete(1.0, tk.END)
            self.feedback_text.insert(1.0, feedback or "")
            self.feedback_text.config(state=tk.DISABLED)
        else:
            self.journal_text.delete(1.0, tk.END)
            self.feedback_text.config(state=tk.NORMAL)
            self.feedback_text.delete(1.0, tk.END)
            self.feedback_text.config(state=tk.DISABLED)
    
    def load_journal_history(self):
        """Load journal history in the sidebar"""
        self.history_listbox.delete(0, tk.END)
        
        self.cursor.execute(
            "SELECT date, content FROM journal_entries ORDER BY date DESC"
        )
        entries = self.cursor.fetchall()
        
        for entry_date, content in entries:
            preview = content[:50] + "..." if len(content) > 50 else content
            display_text = f"{entry_date}: {preview}"
            self.history_listbox.insert(tk.END, display_text)
    
    def load_selected_entry(self, event):
        """Load selected journal entry from history"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        # Get the date from the selected item
        selected_text = self.history_listbox.get(selection[0])
        entry_date = selected_text.split(":")[0]
        
        self.journal_date.set(entry_date)
        self.load_journal_entry()
    
    def edit_task(self, event):
        # Get the index of the clicked item
        widget = event.widget
        try:
            index = widget.curselection()[0]
        except IndexError:
            return  # No item selected

        # Get current text
        current_text = widget.get(index)

        # Ask user for new text
        new_text = simpledialog.askstring("Edit Task", "Edit the task:", initialvalue=current_text, parent=self.root)
        if new_text and new_text.strip():
            # Update the Listbox
            widget.delete(index)
            widget.insert(index, new_text)
            # TODO: Update your database or data structure here as well!
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        finally:
            # Cancel all autosave jobs
            for job_id in self.autosave_jobs.values():
                self.root.after_cancel(job_id)
            self.conn.close()

# Add import for IO operations
import io

def main():
    """Main function to run"""
    app = LifeManagementApp()
    app.run()

if __name__ == "__main__":
    main()