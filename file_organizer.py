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
    
    def organize_files(self, dry_run=False):
        """Organize all files in the directory."""
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting file organization{' (DRY RUN)' if dry_run else ''}")
            self.logger.info(f"Target directory: {self.target_directory}")
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


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python file_organizer.py <directory> [--dry-run] [--undo]")
        print("Example: python file_organizer.py ~/Downloads --dry-run")
        print("         python file_organizer.py ~/Downloads --undo")
        return
    
    directory = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    undo_mode = "--undo" in sys.argv
    
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
        print("=" * 40)
        
        if not dry_run:
            confirm = input("Proceed with organizing files? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        
        organizer.organize_files(dry_run)


if __name__ == "__main__":
    main()