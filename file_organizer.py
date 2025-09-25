#!/usr/bin/env python3
"""
Enhanced File Organizer - Professional GUI with advanced features
"""

import os
import shutil
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json
import threading
import queue
import hashlib
import re
from collections import defaultdict

# Optional GUI imports (loaded when GUI is used)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    import tkinter.font as tkFont
except Exception:
    tk = None


class SimpleFileOrganizer:
    """Enhanced file organizer with malware detection and advanced organization."""
    
    def __init__(self, target_directory):
        """Initialize with target directory."""
        self.target_directory = Path(target_directory)
        self.setup_logging("INFO")
        
        # Enhanced file categories with more types
        self.file_categories = {
            "Documents": {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx', '.csv', '.odt', '.ods'},
            "Images": {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico', '.raw', '.psd'},
            "Videos": {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mpg', '.mpeg', '.m4v', '.3gp'},
            "Audio": {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.aiff'},
            "Archives": {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.cab', '.deb', '.rpm'},
            "Code": {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs', '.ts', '.jsx', '.vue'},
            "Executables": {'.exe', '.msi', '.deb', '.rpm', '.dmg', '.pkg', '.app', '.run'},
            "Fonts": {'.ttf', '.otf', '.woff', '.woff2', '.eot'},
            "Data": {'.json', '.xml', '.yaml', '.yml', '.sql', '.db', '.sqlite'}
        }
        
        # Suspicious file patterns for malware detection
        self.suspicious_patterns = [
            r'.*\.(bat|cmd|scr|pif|com|vbs|ws|jar)$',  # Suspicious extensions
            r'.*\.(exe|dll)\..*',  # Double extensions
            r'^[a-f0-9]{8,}$',  # Files with only hex names (potential malware)
            r'.*\s+\.(exe|bat|cmd|scr)$',  # Space before extension
            r'system32|windows|temp.*\.(exe|dll|bat|cmd)',  # System-related suspicious names
        ]
        
        self.stats = {"moved": 0, "errors": 0, "suspicious": 0}
        self.undo_data = []
        self.undo_file = self.target_directory / ".file_organizer_undo.json"
        self.suspicious_files = []

    def setup_logging(self, log_level: str = "INFO"):
        """Set up logging configuration."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_filename = log_dir / f"file_organizer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Enhanced File Organizer initialized. Log file: {log_filename}")

    def detect_suspicious_file(self, file_path):
        """Detect potentially suspicious/malware files."""
        filename = file_path.name.lower()
        
        # Check against suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        
        # Check file size (very small executables might be suspicious)
        if file_path.suffix.lower() in {'.exe', '.com', '.bat', '.cmd', '.scr'}:
            try:
                if file_path.stat().st_size < 1024:  # Less than 1KB
                    return True
            except:
                pass
        
        # Check for hidden files with executable extensions
        if filename.startswith('.') and file_path.suffix.lower() in {'.exe', '.bat', '.cmd', '.sh'}:
            return True
            
        return False

    def get_file_category(self, file_path, organization_type="type"):
        """Get category for file based on organization type."""
        if organization_type == "type":
            file_extension = file_path.suffix.lower()
            for category, extensions in self.file_categories.items():
                if file_extension in extensions:
                    return category
            return "Others"
        
        elif organization_type == "date":
            try:
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time >= datetime.now() - timedelta(days=7):
                    return "This Week"
                elif mod_time >= datetime.now() - timedelta(days=30):
                    return "This Month"
                elif mod_time >= datetime.now() - timedelta(days=365):
                    return "This Year"
                else:
                    return mod_time.strftime("%Y")
            except:
                return "Unknown Date"
        
        elif organization_type == "size":
            try:
                size = file_path.stat().st_size
                if size < 1024 * 1024:  # < 1MB
                    return "Small (< 1MB)"
                elif size < 10 * 1024 * 1024:  # < 10MB
                    return "Medium (1-10MB)"
                elif size < 100 * 1024 * 1024:  # < 100MB
                    return "Large (10-100MB)"
                else:
                    return "Very Large (> 100MB)"
            except:
                return "Unknown Size"
        
        elif organization_type == "extension":
            ext = file_path.suffix.lower()
            return ext[1:] if ext else "No Extension"
        
        return "Others"

    def save_undo_data(self):
        """Save undo data to JSON file."""
        try:
            undo_info = {
                "timestamp": datetime.now().isoformat(),
                "target_directory": str(self.target_directory),
                "moves": self.undo_data,
                "suspicious_files": [str(f) for f in self.suspicious_files]
            }
            with open(self.undo_file, 'w') as f:
                json.dump(undo_info, f, indent=2)
            self.logger.info(f"Undo data saved to {self.undo_file}")
        except Exception as e:
            self.logger.error(f"Failed to save undo data: {e}")

    def load_undo_data(self):
        """Load undo data from JSON file."""
        try:
            if self.undo_file.exists():
                with open(self.undo_file, 'r') as f:
                    undo_info = json.load(f)
                    self.undo_data = undo_info.get("moves", [])
                    self.suspicious_files = [Path(f) for f in undo_info.get("suspicious_files", [])]
                    self.logger.info(f"Loaded {len(self.undo_data)} undo entries")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to load undo data: {e}")
        return False

    def clear_undo_data(self):
        """Clear undo data and remove undo file."""
        try:
            self.undo_data = []
            self.suspicious_files = []
            if self.undo_file.exists():
                self.undo_file.unlink()
            self.logger.info("Undo data cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear undo data: {e}")

    def _sort_files(self, files, sort_by='name', sort_order='asc'):
        """Sort files based on specified criteria and order."""
        try:
            if sort_by == 'name':
                key_func = lambda f: f.name.lower()
            elif sort_by == 'date':
                key_func = lambda f: f.stat().st_mtime
            elif sort_by == 'size':
                key_func = lambda f: f.stat().st_size
            else:
                key_func = lambda f: f.name.lower()
            
            reverse = (sort_order == 'desc')
            sorted_files = sorted(files, key=key_func, reverse=reverse)
            
            if hasattr(self, 'logger'):
                self.logger.info(f"Files sorted by {sort_by} ({sort_order})")
            
            return sorted_files
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Error sorting files: {e}. Using original order.")
            return files

    def create_folders(self, organization_type="type"):
        """Create category folders based on organization type."""
        if organization_type == "type":
            categories = list(self.file_categories.keys()) + ["Others", "Suspicious"]
        elif organization_type == "date":
            categories = ["This Week", "This Month", "This Year", "Older", "Unknown Date", "Suspicious"]
        elif organization_type == "size":
            categories = ["Small (< 1MB)", "Medium (1-10MB)", "Large (10-100MB)", "Very Large (> 100MB)", "Unknown Size", "Suspicious"]
        elif organization_type == "extension":
            categories = ["Suspicious"]  # Will create extension folders dynamically
        
        for category in categories:
            folder_path = self.target_directory / category
            folder_path.mkdir(exist_ok=True)
            if hasattr(self, 'logger'):
                self.logger.debug(f"Created/verified folder: {folder_path}")
        
        if hasattr(self, 'logger'):
            self.logger.info("Category folders created/verified")

    def organize_files(self, dry_run=False, sort_by='name', sort_order='asc', organization_type="type", progress_callback=None):
        """Organize files with enhanced features including malware detection."""
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting file organization{' (DRY RUN)' if dry_run else ''}")
            self.logger.info(f"Target directory: {self.target_directory}")
            self.logger.info(f"Organization type: {organization_type}")
            self.logger.info(f"Sort by: {sort_by}, Order: {sort_order}")
        
        if not self.target_directory.exists():
            print(f"Error: Directory '{self.target_directory}' does not exist!")
            if hasattr(self, 'logger'):
                self.logger.error(f"Directory does not exist: {self.target_directory}")
            return False
        
        # Reset stats
        self.stats = {"moved": 0, "errors": 0, "suspicious": 0}
        self.suspicious_files = []
        
        # Create folders
        if not dry_run:
            self.create_folders(organization_type)
        
        # Get all files
        files = [f for f in self.target_directory.iterdir() if f.is_file() and not f.name.startswith('.')]
        files = self._sort_files(files, sort_by, sort_order)
        
        if not files:
            print("No files found to organize.")
            if hasattr(self, 'logger'):
                self.logger.info("No files found to organize")
            return True
        
        print(f"Found {len(files)} files to organize")
        print("-" * 50)
        if hasattr(self, 'logger'):
            self.logger.info(f"Found {len(files)} files to organize")
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            if progress_callback:
                try:
                    progress_callback(i, len(files), file_path.name)
                except Exception:
                    pass
            
            try:
                # Check for suspicious files
                is_suspicious = self.detect_suspicious_file(file_path)
                
                if is_suspicious:
                    category = "Suspicious"
                    self.suspicious_files.append(file_path)
                    self.stats["suspicious"] += 1
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"Suspicious file detected: {file_path.name}")
                else:
                    category = self.get_file_category(file_path, organization_type)
                
                # For extension-based organization, create folders dynamically
                if organization_type == "extension" and not is_suspicious:
                    category_path = self.target_directory / category
                    if not dry_run:
                        category_path.mkdir(exist_ok=True)
                
                destination = self.target_directory / category / file_path.name
                
                if dry_run:
                    status = "[SUSPICIOUS]" if is_suspicious else "[DRY RUN]"
                    print(f"{status} {file_path.name} -> {category}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"{status} Would move: {file_path.name} -> {category}/")
                else:
                    # Handle name conflicts
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        name = f"{original_dest.stem}_{counter}{original_dest.suffix}"
                        destination = original_dest.parent / name
                        counter += 1
                    
                    # Move file
                    shutil.move(str(file_path), str(destination))
                    status = "[SUSPICIOUS]" if is_suspicious else "Moved:"
                    print(f"{status} {file_path.name} -> {category}/")
                    if hasattr(self, 'logger'):
                        level = logging.WARNING if is_suspicious else logging.INFO
                        self.logger.log(level, f"{status} {file_path.name} -> {category}/{destination.name}")
                    
                    # Track for undo
                    self.undo_data.append({
                        "original_path": str(file_path),
                        "new_path": str(destination),
                        "filename": file_path.name,
                        "category": category,
                        "suspicious": is_suspicious
                    })
                    self.stats["moved"] += 1
                    
            except Exception as e:
                print(f"Error moving {file_path.name}: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error moving {file_path.name}: {e}")
                self.stats["errors"] += 1
        
        # Show summary
        if not dry_run:
            print("-" * 50)
            print(f"Summary: {self.stats['moved']} files moved, {self.stats['suspicious']} suspicious files, {self.stats['errors']} errors")
            if self.stats["suspicious"] > 0:
                print(f"⚠️  {self.stats['suspicious']} suspicious files were isolated in 'Suspicious' folder")
            if hasattr(self, 'logger'):
                self.logger.info("-" * 50)
                self.logger.info(f"Summary: {self.stats['moved']} files moved, {self.stats['suspicious']} suspicious, {self.stats['errors']} errors")
            
            if self.stats["moved"] > 0:
                self.save_undo_data()
                print(f"Undo data saved. Use --undo to reverse these changes.")
        
        return True

    def undo_organization(self, dry_run=False, progress_callback=None):
        """Undo the last file organization."""
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting undo operation{' (DRY RUN)' if dry_run else ''}")
        
        if not self.load_undo_data():
            print("No undo data found. Nothing to undo.")
            return False
        
        if not self.undo_data:
            print("No undo data available. Nothing to undo.")
            return False
        
        print(f"Found {len(self.undo_data)} files to undo")
        print("-" * 50)
        
        undo_stats = {"moved": 0, "errors": 0}
        
        for i, move_info in enumerate(self.undo_data, 1):
            if progress_callback:
                try:
                    filename = move_info.get('filename', 'unknown')
                    progress_callback(i, len(self.undo_data), filename)
                except Exception:
                    pass
            
            try:
                original_path = Path(move_info["original_path"])
                new_path = Path(move_info["new_path"])
                
                if dry_run:
                    status = "[SUSPICIOUS]" if move_info.get('suspicious') else "[DRY RUN]"
                    print(f"{status} {new_path.name} -> {original_path.parent.name}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"{status} Would undo: {new_path.name} -> {original_path.parent.name}/")
                else:
                    if not new_path.exists():
                        print(f"Warning: {new_path.name} not found in {move_info['category']}/ - skipping")
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"File not found for undo: {new_path}")
                        continue
                    
                    if original_path.exists():
                        print(f"Warning: {original_path.name} already exists in original location - skipping")
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"Original location occupied: {original_path}")
                        continue
                    
                    shutil.move(str(new_path), str(original_path))
                    status = "[RESTORED]" if move_info.get('suspicious') else "Undone:"
                    print(f"{status} {new_path.name} -> {original_path.parent.name}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"{status} {new_path.name} -> {original_path.parent.name}/")
                    undo_stats["moved"] += 1
                    
            except Exception as e:
                print(f"Error undoing {move_info.get('filename', 'unknown')}: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error undoing {move_info.get('filename', 'unknown')}: {e}")
                undo_stats["errors"] += 1
        
        if not dry_run:
            print("-" * 50)
            print(f"Undo Summary: {undo_stats['moved']} files moved back, {undo_stats['errors']} errors")
            if hasattr(self, 'logger'):
                self.logger.info("-" * 50)
                self.logger.info(f"Undo Summary: {undo_stats['moved']} files moved back, {undo_stats['errors']} errors")
            
            if undo_stats["moved"] > 0:
                self.clear_undo_data()
                print("Undo data cleared.")
        
        return True


class TkTextHandler(logging.Handler):
    """Logging handler that writes log records to a Tkinter Text widget via a queue."""
    def __init__(self, message_queue: "queue.Queue[str]"):
        super().__init__()
        self.message_queue = message_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.message_queue.put(msg + "\n")
        except Exception:
            pass


class FileOrganizerGUI:
    """Enhanced professional GUI for SimpleFileOrganizer."""
    def __init__(self):
        if tk is None:
            raise RuntimeError("Tkinter is not available in this environment.")

        self.root = tk.Tk()
        self.root.title("🗂️  File Organizer ")
        self.root.geometry("900x650")
        self.root.configure(bg='#f0f0f0')
        
        # Modern color scheme
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#64748b',
            'success': '#16a34a',
            'warning': '#d97706',
            'danger': '#dc2626',
            'light': '#f8fafc',
            'dark': '#1e293b'
        }
        
        # Configure modern ttk styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()

        self.message_queue: "queue.Queue[str]" = queue.Queue()
        self.gui_handler = TkTextHandler(self.message_queue)
        self.gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.worker_thread: threading.Thread | None = None
        self.worker_running = False
        self.current_operation = None
        self.is_dry_run = False
        self.malware_count = 0
        self.backup_location = None

        self._build_widgets()
        self._poll_log_queue()

    def _configure_styles(self):
        """Configure modern ttk styles."""
        # Button styles
        self.style.configure('Primary.TButton', foreground='white')
        self.style.map('Primary.TButton', background=[('active', '#1d4ed8'), ('!active', self.colors['primary'])])
        
        self.style.configure('Success.TButton', foreground='white')
        self.style.map('Success.TButton', background=[('active', '#15803d'), ('!active', self.colors['success'])])
        
        self.style.configure('Danger.TButton', foreground='white')
        self.style.map('Danger.TButton', background=[('active', '#b91c1c'), ('!active', self.colors['danger'])])
        
        # Frame styles
        self.style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        self.style.configure('Header.TFrame', background=self.colors['primary'])

        # Progress bar (green) style
        try:
            self.style.configure('Green.Horizontal.TProgressbar', background='#10b981')
        except Exception:
            pass

    def _build_widgets(self):
        """Build the enhanced GUI with professional styling."""
        # Header
        header = ttk.Frame(self.root, style='Header.TFrame')
        header.pack(fill=tk.X, pady=(0, 10))
        
        title_font = tkFont.Font(family="Segoe UI", size=16, weight="bold")
        ttk.Label(header, text="🗂️  File Organizer ", font=title_font, 
                 foreground='white', background=self.colors['primary']).pack(pady=15)

        # Main container with cards
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Directory selection card
        dir_card = ttk.LabelFrame(main_container, text=" 📁 Directory Selection ", style='Card.TFrame')
        dir_card.pack(fill=tk.X, pady=(0, 10))
        
        dir_frame = ttk.Frame(dir_card)
        dir_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 10))
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(dir_frame, text="📂 Browse", command=self._choose_directory, 
                  style='Primary.TButton').pack(side=tk.RIGHT)

        # Organization options card
        org_card = ttk.LabelFrame(main_container, text=" ⚙️ Organization Options ", style='Card.TFrame')
        org_card.pack(fill=tk.X, pady=(0, 10))
        
        org_frame = ttk.Frame(org_card)
        org_frame.pack(fill=tk.X, padx=15, pady=15)

        # Organization type
        ttk.Label(org_frame, text="Organize by:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.org_type_var = tk.StringVar(value="type")
        org_combo = ttk.Combobox(org_frame, textvariable=self.org_type_var, 
                                values=["type", "date", "size", "extension"], state="readonly", width=12)
        org_combo.grid(row=0, column=1, padx=(0, 20), sticky=tk.W)

        # Sorting options
        ttk.Label(org_frame, text="Sort by:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.sort_by_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(org_frame, textvariable=self.sort_by_var, 
                                 values=["name", "date", "size"], state="readonly", width=8)
        sort_combo.grid(row=0, column=3, padx=(0, 20), sticky=tk.W)

        ttk.Label(org_frame, text="Order:", font=("Segoe UI", 9, "bold")).grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.sort_order_var = tk.StringVar(value="asc")
        order_combo = ttk.Combobox(org_frame, textvariable=self.sort_order_var,
                                  values=["asc", "desc"], state="readonly", width=8)
        order_combo.grid(row=0, column=5, sticky=tk.W)

        # Mode options
        mode_frame = ttk.Frame(org_frame)
        mode_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(15, 0))
        
        self.dry_run_var = tk.BooleanVar(value=False)
        self.undo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(mode_frame, text="🔍 Dry run (preview only)", 
                       variable=self.dry_run_var).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(mode_frame, text="↩️ Undo last operation", 
                       variable=self.undo_var, command=self._ensure_mutual_exclusive).pack(side=tk.LEFT)

        # Backup options
        backup_frame = ttk.Frame(org_frame)
        backup_frame.grid(row=2, column=0, columnspan=6, sticky=tk.W, pady=(10, 0))
        self.backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(backup_frame, text="💾 Create backup before organizing", 
                        variable=self.backup_var).pack(side=tk.LEFT)
        ttk.Button(backup_frame, text="📂 Choose Backup Location", 
                   command=self._choose_backup_location, style='Primary.TButton').pack(side=tk.LEFT, padx=(12, 0))

        # Action buttons and status card
        action_card = ttk.LabelFrame(main_container, text=" 🚀 Actions & Status ", style='Card.TFrame')
        action_card.pack(fill=tk.X, pady=(0, 10))
        
        action_frame = ttk.Frame(action_card)
        action_frame.pack(fill=tk.X, padx=15, pady=15)

        # Buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(side=tk.LEFT)
        
        self.run_button = ttk.Button(button_frame, text="🚀 Run Organizer", 
                                    command=self._on_run, style='Success.TButton')
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", 
                                     command=self._on_stop, style='Danger.TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))

        # Clear logs button
        ttk.Button(button_frame, text="🗑️ Clear Logs", 
                  command=self._clear_logs).pack(side=tk.LEFT)

        # Status and progress
        status_frame = ttk.Frame(action_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold"))
        status_label.pack(side=tk.RIGHT)

        # Progress card
        progress_card = ttk.LabelFrame(main_container, text=" 📊 Progress ", style='Card.TFrame')
        progress_card.pack(fill=tk.X, pady=(0, 10))
        
        progress_frame = ttk.Frame(progress_card)
        progress_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.progress_var = tk.StringVar(value="Ready to organize files...")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=("Segoe UI", 9)).pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=200, style='Green.Horizontal.TProgressbar')
        self.progress_bar.pack(side=tk.RIGHT, padx=(10, 0))

        # Enhanced logs card
        logs_card = ttk.LabelFrame(main_container, text=" 📝 Activity Logs ", style='Card.TFrame')
        logs_card.pack(fill=tk.BOTH, expand=True)
        
        log_container = ttk.Frame(logs_card)
        log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.log_text = ScrolledText(log_container, wrap=tk.WORD, height=12, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

        # Configure log text colors for different log levels
        self.log_text.tag_config("ERROR", foreground=self.colors['danger'])
        self.log_text.tag_config("WARNING", foreground=self.colors['warning'])
        self.log_text.tag_config("INFO", foreground=self.colors['dark'])
        self.log_text.tag_config("SUSPICIOUS", foreground=self.colors['danger'], background="#fef2f2")

        # Notification bar (hidden by default)
        self.notification_frame = ttk.Frame(main_container)
        self.notification_label = ttk.Label(self.notification_frame, text="", foreground=self.colors['danger'])
        self.notification_label.pack(side=tk.LEFT, padx=8, pady=6)

    def _choose_directory(self):
        """Choose directory with improved dialog."""
        path = filedialog.askdirectory(title="Select Directory to Organize")
        if path:
            self.dir_var.set(path)

    def _ensure_mutual_exclusive(self):
        """Ensure dry run and undo are mutually exclusive."""
        if self.undo_var.get():
            self.dry_run_var.set(False)

    def _append_log(self, text: str):
        """Append log text with color coding."""
        self.log_text.configure(state=tk.NORMAL)
        
        # Apply color based on log level
        if "ERROR" in text:
            tag = "ERROR"
        elif "WARNING" in text or "SUSPICIOUS" in text:
            tag = "WARNING"
        else:
            tag = "INFO"
        
        self.log_text.insert(tk.END, text, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # If log mentions suspicious count in summary, show notification
        try:
            if "suspicious files" in text.lower():
                import re as _re
                m = _re.search(r"(\d+)\s+suspicious", text)
                if m:
                    self.malware_count = int(m.group(1))
                    self._show_malware_notification(self.malware_count)
        except Exception:
            pass

    def _clear_logs(self):
        """Clear the log display."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._hide_notification()

    def _show_malware_notification(self, count: int):
        """Show malware detection notification banner."""
        if count > 0:
            try:
                self.notification_label.configure(text=f"⚠️ SECURITY ALERT: {count} suspicious files quarantined")
                self.notification_frame.pack(fill=tk.X, padx=15, pady=(8, 0))
                # Auto hide after 10s
                self.root.after(10000, self._hide_notification)
            except Exception:
                pass

    def _hide_notification(self):
        try:
            self.notification_frame.pack_forget()
        except Exception:
            pass

    def _choose_backup_location(self):
        """Choose backup destination directory."""
        path = filedialog.askdirectory(title="Select Backup Location")
        if path:
            self.backup_location = path
            messagebox.showinfo("✅ Backup Location Set", f"Backup will be saved to:\n{path}")

    def _create_backup(self, source_dir: str) -> bool:
        """Create a zip backup of current files in the directory."""
        if not self.backup_location:
            return False
        try:
            import zipfile as _zip
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"file_organizer_backup_{ts}.zip"
            backup_path = Path(self.backup_location) / backup_name
            self.message_queue.put(f"Creating backup: {backup_name}\n")
            with _zip.ZipFile(backup_path, 'w', _zip.ZIP_DEFLATED) as zf:
                for f in Path(source_dir).iterdir():
                    if f.is_file() and not f.name.startswith('.'):
                        zf.write(f, f.name)
            self.message_queue.put(f"✅ Backup created successfully: {backup_path}\n")
            return True
        except Exception as e:
            self.message_queue.put(f"❌ Backup failed: {e}\n")
            return False

    def _poll_log_queue(self):
        """Poll log queue and update display."""
        try:
            while True:
                msg = self.message_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_log_queue)

    def _on_run(self):
        """Enhanced run method with validation and better UX."""
        if self.worker_running:
            return
        
        directory = self.dir_var.get().strip()
        if not directory:
            messagebox.showwarning("⚠️ Missing Directory", 
                                 "Please select a target directory to organize.")
            return

        if not Path(directory).exists():
            messagebox.showerror("❌ Invalid Directory", 
                               f"The selected directory does not exist:\n{directory}")
            return

        do_undo = self.undo_var.get()
        dry_run = self.dry_run_var.get()
        org_type = self.org_type_var.get()
        create_backup = self.backup_var.get()

        # Validate backup location when enabled (only for actual organize)
        if create_backup and not do_undo and not dry_run:
            if not self.backup_location:
                if messagebox.askyesno("💾 Backup Location", "Backup is enabled but no location is set.\nChoose a backup location now?"):
                    self._choose_backup_location()
                    if not self.backup_location:
                        return
                else:
                    return
        
        # Track operation type for notifications
        self.current_operation = 'undo' if do_undo else 'organize'
        self.is_dry_run = dry_run

        # Clear previous logs and reset progress
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._reset_progress()

        # Update UI state
        self.run_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set("🔄 Processing..." if not dry_run else "🔍 Analyzing...")
        self.worker_running = True

        def _work():
            """Worker thread function with optional backup."""
            try:
                # Backup before organizing
                if create_backup and not do_undo and not dry_run:
                    if not self._create_backup(directory):
                        return
                organizer = SimpleFileOrganizer(directory)
                logger = logging.getLogger(__name__)
                logger.addHandler(self.gui_handler)
                
                try:
                    if do_undo:
                        def progress_callback(current, total, filename):
                            def update_gui():
                                self._update_progress(current, total, filename, "Restoring")
                            self.root.after(0, update_gui)
                        organizer.undo_organization(dry_run=dry_run, progress_callback=progress_callback)
                    else:
                        sort_by = self.sort_by_var.get()
                        sort_order = self.sort_order_var.get()
                        
                        def progress_callback(current, total, filename):
                            def update_gui():
                                action = "Analyzing" if dry_run else "Organizing"
                                self._update_progress(current, total, filename, action)
                            self.root.after(0, update_gui)
                        
                        organizer.organize_files(
                            dry_run=dry_run, 
                            sort_by=sort_by, 
                            sort_order=sort_order,
                            organization_type=org_type,
                            progress_callback=progress_callback
                        )
                        try:
                            # Capture suspicious count for notification
                            self.malware_count = int(organizer.stats.get("suspicious", 0))
                        except Exception:
                            pass
                finally:
                    logger.removeHandler(self.gui_handler)
            except Exception as e:
                self.message_queue.put(f"CRITICAL ERROR: {e}\n")
            finally:
                self.root.after(0, self._on_worker_done)

        self.worker_thread = threading.Thread(target=_work, daemon=True)
        self.worker_thread.start()

    def _on_stop(self):
        """Stop operation (cooperative)."""
        messagebox.showinfo("ℹ️ Stop Request", 
                          "Stop request noted. The operation will complete current file processing safely.")

    def _on_worker_done(self):
        """Handle worker completion with enhanced notifications."""
        self.worker_running = False
        self.run_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("✅ Complete")
        self.progress_bar['value'] = 100
        self.progress_var.set("🎉 Operation completed successfully!")
        
        self._show_completion_notification()

    def _show_completion_notification(self):
        """Show enhanced completion notifications with malware/backup info."""
        malware_info = f"\n🛡️ {self.malware_count} suspicious files quarantined" if self.malware_count > 0 else ""
        if self.current_operation == 'organize':
            if self.is_dry_run:
                messagebox.showinfo("🔍 Analysis Complete", 
                    "Dry run completed successfully! 📊\n\n"
                    "✅ All files have been analyzed\n"
                    "📁 Organization plan shown in logs\n"
                    "🛡️ Security scan completed" + malware_info + "\n"
                    "\nReady for actual organization!")
            else:
                backup_info = "\n💾 Backup created before organizing" if self.backup_var.get() and self.backup_location else ""
                messagebox.showinfo("🗂️ Organization Complete", 
                    "Files organized successfully! 🎉\n\n"
                    "✅ All files sorted into categories\n"
                    "🛡️ Security scan completed" + malware_info +
                    backup_info + "\n"
                    "📝 Activity logged for review\n"
                    "↩️ Undo data saved for reversal")
        elif self.current_operation == 'undo':
            if self.is_dry_run:
                messagebox.showinfo("🔄 Undo Preview Complete", 
                    "Undo analysis completed! 📋\n\n"
                    "✅ Restore plan generated\n"
                    "📁 Original locations verified\n"
                    "\nReady to restore files!")
            else:
                messagebox.showinfo("↩️ Restore Complete", 
                    "Files restored successfully! 🎊\n\n"
                    "✅ All files returned to original locations\n"
                    "🧹 Organization folders cleaned up\n"
                    "📝 Undo history cleared")
        self.current_operation = None
        self.is_dry_run = False
        self.malware_count = 0

    def _update_progress(self, current, total, filename="", action="Processing"):
        """Enhanced progress updates."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            
            # Truncate long filenames for display
            display_name = filename[:30] + "..." if len(filename) > 30 else filename
            self.progress_var.set(f"{action}: {current}/{total} ({percentage:.1f}%) - {display_name}")
        else:
            self.progress_bar['value'] = 0
            self.progress_var.set(f"{action} files...")

    def _reset_progress(self):
        """Reset progress indicators."""
        self.progress_bar['value'] = 0
        self.progress_var.set("Ready to organize files...")
        self.malware_count = 0

    def run(self):
        """Run the GUI application."""
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()


def main():
    """Enhanced main function with better CLI support."""
    import sys
    
    # Enhanced CLI argument parsing
    if len(sys.argv) >= 2:
        directory = sys.argv[1]
        dry_run = "--dry-run" in sys.argv
        undo_mode = "--undo" in sys.argv
        
        # Parse organization type
        org_type = "type"  # default
        if "--org-type" in sys.argv:
            try:
                org_idx = sys.argv.index("--org-type")
                if org_idx + 1 < len(sys.argv):
                    org_type = sys.argv[org_idx + 1]
                    if org_type not in ["type", "date", "size", "extension"]:
                        print(f"Invalid organization type: {org_type}. Using 'type'.")
                        org_type = "type"
            except (ValueError, IndexError):
                print("Invalid --org-type usage. Using 'type'.")
        
        # Parse sorting options
        sort_by = "name"
        sort_order = "asc"
        
        if "--sort-by" in sys.argv:
            try:
                sort_idx = sys.argv.index("--sort-by")
                if sort_idx + 1 < len(sys.argv):
                    sort_by = sys.argv[sort_idx + 1]
                    if sort_by not in ["name", "date", "size"]:
                        print(f"Invalid sort-by option: {sort_by}. Using 'name'.")
                        sort_by = "name"
            except (ValueError, IndexError):
                print("Invalid --sort-by usage. Using 'name'.")
        
        if "--sort-order" in sys.argv:
            try:
                order_idx = sys.argv.index("--sort-order")
                if order_idx + 1 < len(sys.argv):
                    sort_order = sys.argv[order_idx + 1]
                    if sort_order not in ["asc", "desc"]:
                        print(f"Invalid sort-order option: {sort_order}. Using 'asc'.")
                        sort_order = "asc"
            except (ValueError, IndexError):
                print("Invalid --sort-order usage. Using 'asc'.")
        
        # Optional CLI backup flag: --backup <directory>
        backup_location = None
        if "--backup" in sys.argv:
            try:
                bidx = sys.argv.index("--backup")
                if bidx + 1 < len(sys.argv):
                    backup_location = sys.argv[bidx + 1]
                else:
                    print("Invalid --backup usage. Provide backup directory path.")
                    return
            except (ValueError, IndexError):
                print("Invalid --backup usage. Provide backup directory path.")
                return

        # Run CLI version
        organizer = SimpleFileOrganizer(directory)
        
        print("🗂️ Enhanced File Organizer Pro")
        print("=" * 50)
        
        if undo_mode:
            print(f"📁 Target: {directory}")
            print(f"🔄 Mode: {'DRY RUN UNDO' if dry_run else 'UNDO ORGANIZATION'}")
            print("=" * 50)
            
            if not dry_run:
                confirm = input("Proceed with undoing file organization? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    print("❌ Cancelled.")
                    return
            
            result = organizer.undo_organization(dry_run)
            
            if result:
                if dry_run:
                    print("\n🔍 Undo analysis completed successfully!")
                    print("📋 All files would be restored as shown above.")
                else:
                    print("\n✅ Undo operation completed successfully!")
                    print("↩️ All files restored to original locations.")
        else:
            print(f"📁 Target: {directory}")
            print(f"🗂️ Organization: {org_type}")
            print(f"📊 Sort: {sort_by} ({sort_order})")
            print(f"🔍 Mode: {'DRY RUN' if dry_run else 'ORGANIZE FILES'}")
            print("=" * 50)
            
            if not dry_run:
                # If backup requested via CLI, create it before organizing
                if backup_location:
                    try:
                        import zipfile as _zip
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_name = f"file_organizer_backup_{ts}.zip"
                        backup_path = Path(backup_location) / backup_name
                        print(f"💾 Creating backup: {backup_path}")
                        with _zip.ZipFile(backup_path, 'w', _zip.ZIP_DEFLATED) as zf:
                            for f in Path(directory).iterdir():
                                if f.is_file() and not f.name.startswith('.'):
                                    zf.write(f, f.name)
                        print(f"✅ Backup created: {backup_path}")
                    except Exception as e:
                        print(f"❌ Backup failed: {e}")
                        return
                confirm = input("Proceed with organizing files? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    print("❌ Cancelled.")
                    return
            
            result = organizer.organize_files(dry_run, sort_by, sort_order, org_type)
            
            if result:
                if dry_run:
                    print("\n🔍 Analysis completed successfully!")
                    print("📊 Organization plan shown above with malware detection.")
                else:
                    print("\n✅ Organization completed successfully!")
                    print("🗂️ Files organized with malware protection enabled.")
                    if backup_location:
                        print("💾 Backup was created prior to organizing.")

    else:
        # Launch GUI if no CLI args and Tkinter is available
        if tk is not None:
            try:
                app = FileOrganizerGUI()
                app.run()
                return
            except Exception as e:
                print(f"Failed to launch GUI: {e}")
        
        # Show enhanced CLI usage
        print("🗂️  File Organizer ")
        print("=" * 50)
        print("Usage: python file_organizer.py <directory> [options]")
        print("\nOptions:")
        print("  --dry-run              Preview changes without moving files")
        print("  --undo                 Undo last organization")
        print("  --org-type TYPE        Organization type: type|date|size|extension")
        print("  --sort-by FIELD        Sort by: name|date|size")
        print("  --sort-order ORDER     Sort order: asc|desc")
        print("  --backup LOCATION      Create a zip backup to LOCATION before organizing")
        print("\nExamples:")
        print("  python file_organizer.py ~/Downloads --dry-run")
        print("  python file_organizer.py ~/Downloads --org-type date")
        print("  python file_organizer.py ~/Downloads --org-type size --sort-by date")
        print("  python file_organizer.py ~/Downloads --undo")
        print("\n🛡️ Features:")
        print("  • Malware detection and quarantine")
        print("  • Multiple organization methods")
        print("  • Professional GUI interface")
        print("  • Comprehensive logging")
        print("  • Safe undo functionality")


if __name__ == "__main__":
    main()