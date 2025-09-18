#!/usr/bin/env python3
"""
Simple File Organizer - Automatically organize files by type
"""

import os
import shutil
from pathlib import Path
import logging
from datetime import datetime


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
        
        return True


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python file_organizer.py <directory> [--dry-run]")
        print("Example: python file_organizer.py ~/Downloads --dry-run")
        return
    
    directory = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    organizer = SimpleFileOrganizer(directory)
    
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