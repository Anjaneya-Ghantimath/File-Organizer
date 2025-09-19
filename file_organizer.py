#!/usr/bin/env python3
"""
Simple File Organizer - Automatically organize files by type
"""

import os
import shutil
from pathlib import Path
import logging
from datetime import datetime
import json
import threading
import queue

# Optional GUI imports (loaded when GUI is used)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
except Exception:
    # Tkinter might not be available in some environments; CLI will still work
    tk = None


class SimpleFileOrganizer:
    """A simple class to organize files in a directory based on their file types."""
    
    def __init__(self, target_directory):
        """Initialize with target directory."""
        self.target_directory = Path(target_directory)
        # Initialize logging
        self.setup_logging("INFO")
        
        # Define file categories
        self.file_categories = {
            "Documents": {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'},
            "Images": {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'},
            "Videos": {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.mpg', '.mpeg'},
            "Audio": {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'},
            "Archives": {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
            "Code": {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb'}
        }
        
        self.stats = {"moved": 0, "errors": 0}
        self.undo_data = []
        self.undo_file = self.target_directory / ".file_organizer_undo.json"

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
        self.logger.info(f"File Organizer initialized. Log file: {log_filename}")
    
    def save_undo_data(self):
        """Save undo data to JSON file."""
        try:
            undo_info = {
                "timestamp": datetime.now().isoformat(),
                "target_directory": str(self.target_directory),
                "moves": self.undo_data
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
                    self.logger.info(f"Loaded {len(self.undo_data)} undo entries")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to load undo data: {e}")
        return False
    
    def clear_undo_data(self):
        """Clear undo data and remove undo file."""
        try:
            self.undo_data = []
            if self.undo_file.exists():
                self.undo_file.unlink()
            self.logger.info("Undo data cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear undo data: {e}")
    
    def get_file_category(self, file_extension):
        """Get category for file extension."""
        file_extension = file_extension.lower()
        for category, extensions in self.file_categories.items():
            if file_extension in extensions:
                return category
        return "Others"
    
    def _sort_files(self, files, sort_by='name', sort_order='asc'):
        """Sort files based on specified criteria and order.
        
        Args:
            files (list): List of Path objects to sort
            sort_by (str): Sort criteria - 'name', 'date', or 'size'
            sort_order (str): Sort order - 'asc' for ascending, 'desc' for descending
            
        Returns:
            list: Sorted list of files
        """
        try:
            if sort_by == 'name':
                key_func = lambda f: f.name.lower()
            elif sort_by == 'date':
                key_func = lambda f: f.stat().st_mtime
            elif sort_by == 'size':
                key_func = lambda f: f.stat().st_size
            else:
                # Default to name if invalid sort_by
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
    
    def create_folders(self):
        """Create category folders."""
        for category in list(self.file_categories.keys()) + ["Others"]:
            folder_path = self.target_directory / category
            folder_path.mkdir(exist_ok=True)
            # Debug log for folder verification/creation
            if hasattr(self, 'logger'):
                self.logger.debug(f"Created/verified folder: {folder_path}")
        if hasattr(self, 'logger'):
            self.logger.info("Category folders created/verified")
    
    def organize_files(self, dry_run=False, sort_by='name', sort_order='asc'):
        """Organize all files in the directory.
        
        Args:
            dry_run (bool): If True, only preview changes without moving files
            sort_by (str): Sort criteria - 'name', 'date', or 'size'
            sort_order (str): Sort order - 'asc' for ascending, 'desc' for descending
        """
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting file organization{' (DRY RUN)' if dry_run else ''}")
            self.logger.info(f"Target directory: {self.target_directory}")
            self.logger.info(f"Sort by: {sort_by}, Order: {sort_order}")
        if not self.target_directory.exists():
            print(f"Error: Directory '{self.target_directory}' does not exist!")
            if hasattr(self, 'logger'):
                self.logger.error(f"Directory does not exist: {self.target_directory}")
            return False
        
        # Create folders
        if not dry_run:
            self.create_folders()
        
        # Get all files
        files = [f for f in self.target_directory.iterdir() if f.is_file() and not f.name.startswith('.')]
        
        # Sort files based on criteria
        files = self._sort_files(files, sort_by, sort_order)
        
        if not files:
            print("No files found to organize.")
            if hasattr(self, 'logger'):
                self.logger.info("No files found to organize")
            return True
        
        print(f"Found {len(files)} files to organize")
        print("-" * 40)
        if hasattr(self, 'logger'):
            self.logger.info(f"Found {len(files)} files to organize")
        
        # Process each file
        for file_path in files:
            try:
                category = self.get_file_category(file_path.suffix)
                destination = self.target_directory / category / file_path.name
                
                if dry_run:
                    print(f"[DRY RUN] {file_path.name} -> {category}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"[DRY RUN] Would move: {file_path.name} -> {category}/")
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
                    print(f"Moved: {file_path.name} -> {category}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"Moved: {file_path.name} -> {category}/{destination.name}")
                    
                    # Track for undo
                    self.undo_data.append({
                        "original_path": str(file_path),
                        "new_path": str(destination),
                        "filename": file_path.name,
                        "category": category
                    })
                    self.stats["moved"] += 1
                    
            except Exception as e:
                print(f"Error moving {file_path.name}: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error moving {file_path.name}: {e}")
                self.stats["errors"] += 1
        
        # Show summary
        if not dry_run:
            print("-" * 40)
            print(f"Summary: {self.stats['moved']} files moved, {self.stats['errors']} errors")
            if hasattr(self, 'logger'):
                self.logger.info("-" * 40)
                self.logger.info(f"Summary: {self.stats['moved']} files moved, {self.stats['errors']} errors")
            
            # Save undo data if files were moved
            if self.stats["moved"] > 0:
                self.save_undo_data()
                print(f"Undo data saved. Use --undo to reverse these changes.")
        
        return True
    
    def undo_organization(self, dry_run=False):
        """Undo the last file organization."""
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting undo operation{' (DRY RUN)' if dry_run else ''}")
        
        # Load undo data
        if not self.load_undo_data():
            print("No undo data found. Nothing to undo.")
            return False
        
        if not self.undo_data:
            print("No undo data available. Nothing to undo.")
            return False
        
        print(f"Found {len(self.undo_data)} files to undo")
        print("-" * 40)
        
        undo_stats = {"moved": 0, "errors": 0}
        
        # Process each undo entry
        for move_info in self.undo_data:
            try:
                original_path = Path(move_info["original_path"])
                new_path = Path(move_info["new_path"])
                
                if dry_run:
                    print(f"[DRY RUN] {new_path.name} -> {original_path.parent.name}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"[DRY RUN] Would undo: {new_path.name} -> {original_path.parent.name}/")
                else:
                    # Check if the file still exists in the new location
                    if not new_path.exists():
                        print(f"Warning: {new_path.name} not found in {move_info['category']}/ - skipping")
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"File not found for undo: {new_path}")
                        continue
                    
                    # Check if original location is available
                    if original_path.exists():
                        print(f"Warning: {original_path.name} already exists in original location - skipping")
                        if hasattr(self, 'logger'):
                            self.logger.warning(f"Original location occupied: {original_path}")
                        continue
                    
                    # Move file back
                    shutil.move(str(new_path), str(original_path))
                    print(f"Undone: {new_path.name} -> {original_path.parent.name}/")
                    if hasattr(self, 'logger'):
                        self.logger.info(f"Undone: {new_path.name} -> {original_path.parent.name}/")
                    undo_stats["moved"] += 1
                    
            except Exception as e:
                print(f"Error undoing {move_info.get('filename', 'unknown')}: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error undoing {move_info.get('filename', 'unknown')}: {e}")
                undo_stats["errors"] += 1
        
        # Show summary
        if not dry_run:
            print("-" * 40)
            print(f"Undo Summary: {undo_stats['moved']} files moved back, {undo_stats['errors']} errors")
            if hasattr(self, 'logger'):
                self.logger.info("-" * 40)
                self.logger.info(f"Undo Summary: {undo_stats['moved']} files moved back, {undo_stats['errors']} errors")
            
            # Clear undo data after successful undo
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
    """Tkinter-based GUI for SimpleFileOrganizer."""
    def __init__(self):
        if tk is None:
            raise RuntimeError("Tkinter is not available in this environment.")

        self.root = tk.Tk()
        self.root.title("Simple File Organizer")
        self.root.geometry("780x520")
        try:
            self.root.iconbitmap(default='')
        except Exception:
            pass

        self.message_queue: "queue.Queue[str]" = queue.Queue()
        self.gui_handler = TkTextHandler(self.message_queue)
        self.gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.worker_thread: threading.Thread | None = None
        self.worker_running = False

        self._build_widgets()
        self._poll_log_queue()

    def _build_widgets(self):
        padding = {"padx": 8, "pady": 6}

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, **padding)

        ttk.Label(top_frame, text="Target directory:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(top_frame, textvariable=self.dir_var)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(top_frame, text="Browse...", command=self._choose_directory).pack(side=tk.LEFT)

        options_frame = ttk.Frame(self.root)
        options_frame.pack(fill=tk.X, **padding)

        self.dry_run_var = tk.BooleanVar(value=False)
        self.undo_var = tk.BooleanVar(value=False)
        dry_cb = ttk.Checkbutton(options_frame, text="Dry run (no changes)", variable=self.dry_run_var)
        undo_cb = ttk.Checkbutton(options_frame, text="Undo last organization", variable=self.undo_var, command=self._ensure_mutual_exclusive)
        dry_cb.pack(side=tk.LEFT)
        undo_cb.pack(side=tk.LEFT, padx=16)

        # Sorting options
        sort_frame = ttk.LabelFrame(self.root, text="Sorting Options")
        sort_frame.pack(fill=tk.X, **padding)
        
        ttk.Label(sort_frame, text="Sort by:").pack(side=tk.LEFT)
        self.sort_by_var = tk.StringVar(value="name")
        sort_by_combo = ttk.Combobox(sort_frame, textvariable=self.sort_by_var, 
                                   values=["name", "date", "size"], state="readonly", width=8)
        sort_by_combo.pack(side=tk.LEFT, padx=(8, 16))
        
        ttk.Label(sort_frame, text="Order:").pack(side=tk.LEFT)
        self.sort_order_var = tk.StringVar(value="asc")
        sort_order_combo = ttk.Combobox(sort_frame, textvariable=self.sort_order_var,
                                      values=["asc", "desc"], state="readonly", width=8)
        sort_order_combo.pack(side=tk.LEFT, padx=(8, 0))

        actions_frame = ttk.Frame(self.root)
        actions_frame.pack(fill=tk.X, **padding)

        self.run_button = ttk.Button(actions_frame, text="Run", command=self._on_run)
        self.run_button.pack(side=tk.LEFT)
        self.stop_button = ttk.Button(actions_frame, text="Stop", command=self._on_stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=8)
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(actions_frame, textvariable=self.status_var).pack(side=tk.RIGHT)

        log_frame = ttk.LabelFrame(self.root, text="Logs")
        log_frame.pack(fill=tk.BOTH, expand=True, **padding)
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, height=18)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

    def _choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_var.set(path)

    def _ensure_mutual_exclusive(self):
        if self.undo_var.get():
            self.dry_run_var.set(False)

    def _append_log(self, text: str):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.message_queue.get_nowait()
                self._append_log(msg)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_log_queue)

    def _on_run(self):
        if self.worker_running:
            return
        directory = self.dir_var.get().strip()
        if not directory:
            messagebox.showwarning("Missing directory", "Please choose a target directory.")
            return

        do_undo = self.undo_var.get()
        dry_run = self.dry_run_var.get()

        # Clear previous logs
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        self.run_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.status_var.set("Running...")
        self.worker_running = True

        def _work():
            try:
                organizer = SimpleFileOrganizer(directory)
                # Attach GUI logging handler
                logger = logging.getLogger(__name__)
                logger.addHandler(self.gui_handler)
                try:
                    if do_undo:
                        organizer.undo_organization(dry_run=dry_run)
                    else:
                        # Get sorting options from GUI
                        sort_by = self.sort_by_var.get()
                        sort_order = self.sort_order_var.get()
                        organizer.organize_files(dry_run=dry_run, sort_by=sort_by, sort_order=sort_order)
                finally:
                    logger.removeHandler(self.gui_handler)
            except Exception as e:
                self.message_queue.put(f"ERROR: {e}\n")
            finally:
                self.root.after(0, self._on_worker_done)

        self.worker_thread = threading.Thread(target=_work, daemon=True)
        self.worker_thread.start()

    def _on_stop(self):
        # Cooperative stop flag; we don't have an internal cancel in organizer, so we just inform user
        messagebox.showinfo("Stop", "Safe stop is not supported mid-run. Please wait for completion.")

    def _on_worker_done(self):
        self.worker_running = False
        self.run_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.status_var.set("Done")

    def run(self):
        self.root.mainloop()

def main():
    """Main function."""
    import sys
    
    # If no CLI args and Tkinter is available, launch GUI
    if len(sys.argv) < 2 and tk is not None:
        try:
            app = FileOrganizerGUI()
            app.run()
            return
        except Exception as e:
            print(f"Failed to launch GUI: {e}")
            # Fallback to CLI usage text
    
    if len(sys.argv) < 2:
        print("Usage: python file_organizer.py <directory> [--dry-run] [--undo] [--sort-by name|date|size] [--sort-order asc|desc]")
        print("Example: python file_organizer.py ~/Downloads --dry-run")
        print("         python file_organizer.py ~/Downloads --undo")
        print("         python file_organizer.py ~/Downloads --sort-by date --sort-order desc")
        return
    
    directory = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    undo_mode = "--undo" in sys.argv
    
    # Parse sorting options
    sort_by = "name"  # default
    sort_order = "asc"  # default
    
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
    
    organizer = SimpleFileOrganizer(directory)
    
    if undo_mode:
        print(f"File Organizer - UNDO MODE")
        print(f"Target: {directory}")
        print(f"Mode: {'DRY RUN' if dry_run else 'UNDO ORGANIZATION'}")
        print("=" * 40)
        
        if not dry_run:
            confirm = input("Proceed with undoing file organization? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        
        organizer.undo_organization(dry_run)
    else:
        print(f"File Organizer")
        print(f"Target: {directory}")
        print(f"Mode: {'DRY RUN' if dry_run else 'ORGANIZE FILES'}")
        print(f"Sort by: {sort_by}, Order: {sort_order}")
        print("=" * 40)
        
        if not dry_run:
            confirm = input("Proceed with organizing files? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        
        organizer.organize_files(dry_run, sort_by, sort_order)


if __name__ == "__main__":
    main()