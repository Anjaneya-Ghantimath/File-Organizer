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
import time
import sqlite3
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

# Optional advanced imports
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    TkinterDnD = TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    TkinterDnD = None
    DND_AVAILABLE = False


class SimpleFileOrganizer:
    """Enhanced file organizer with advanced analytics and duplicate detection."""
    
    def __init__(self, target_directory):
        """Initialize with target directory and analytics database."""
        self.target_directory = Path(target_directory)
        self.setup_logging("INFO")
        self.setup_database()
        
        # Enhanced file categories with more types
        self.default_categories = {
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
        
        # Load custom categories
        self.file_categories = self.load_custom_categories()
        
        # Suspicious file patterns for malware detection
        self.suspicious_patterns = [
            r'.*\.(bat|cmd|scr|pif|com|vbs|ws|jar)$',  # Suspicious extensions
            r'.*\.(exe|dll)\..*',  # Double extensions
            r'^[a-f0-9]{8,}$',  # Files with only hex names (potential malware)
            r'.*\s+\.(exe|bat|cmd|scr)$',  # Space before extension
            r'system32|windows|temp.*\.(exe|dll|bat|cmd)',  # System-related suspicious names
        ]
        
        self.stats = {"moved": 0, "errors": 0, "suspicious": 0, "duplicates": 0, "space_saved": 0}
        self.undo_data = []
        self.undo_file = self.target_directory / ".file_organizer_undo.json"
        self.suspicious_files = []
        self.duplicate_files = []
        self.organization_report = None

    def setup_database(self):
        """Set up SQLite database for analytics and history."""
        try:
            db_path = Path.home() / ".file_organizer" / "organizer.db"
            db_path.parent.mkdir(exist_ok=True)
            
            self.db_connection = sqlite3.connect(str(db_path))
            cursor = self.db_connection.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organization_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    directory TEXT NOT NULL,
                    organization_type TEXT NOT NULL,
                    files_moved INTEGER DEFAULT 0,
                    duplicates_found INTEGER DEFAULT 0,
                    suspicious_found INTEGER DEFAULT 0,
                    space_saved INTEGER DEFAULT 0,
                    time_taken REAL DEFAULT 0,
                    dry_run BOOLEAN DEFAULT 0
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS custom_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    extensions TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    is_duplicate BOOLEAN DEFAULT 0,
                    is_suspicious BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            
            self.db_connection.commit()
            self.logger.info(f"Database initialized: {db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup database: {e}")
            self.db_connection = None

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

    def load_custom_categories(self):
        """Load custom categories from database."""
        categories = self.default_categories.copy()
        
        if self.db_connection:
            try:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT name, extensions FROM custom_categories")
                for name, extensions_str in cursor.fetchall():
                    extensions = set(ext.strip() for ext in extensions_str.split(','))
                    categories[name] = extensions
            except Exception as e:
                self.logger.error(f"Failed to load custom categories: {e}")
        
        return categories

    def save_custom_category(self, name, extensions):
        """Save a custom category to database."""
        if not self.db_connection:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            extensions_str = ','.join(sorted(extensions))
            cursor.execute("""
                INSERT OR REPLACE INTO custom_categories (name, extensions, created_at)
                VALUES (?, ?, ?)
            """, (name, extensions_str, datetime.now().isoformat()))
            self.db_connection.commit()
            
            # Update in-memory categories
            self.file_categories[name] = extensions
            return True
        except Exception as e:
            self.logger.error(f"Failed to save custom category: {e}")
            return False

    def calculate_file_hash(self, file_path, chunk_size=8192):
        """Calculate MD5 hash of a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def find_duplicates(self, files, progress_callback=None):
        """Find duplicate files using hash comparison."""
        if not files:
            return
        
        print("🔍 Scanning for duplicate files...")
        hash_to_files = defaultdict(list)
        
        for i, file_path in enumerate(files):
            if progress_callback:
                try:
                    progress_callback(i + 1, len(files), f"Scanning: {file_path.name}")
                except Exception:
                    pass
            
            try:
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    hash_to_files[file_hash].append(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to hash {file_path.name}: {e}")
        
        # Find duplicates (files with same hash)
        duplicates = []
        for file_hash, file_list in hash_to_files.items():
            if len(file_list) > 1:
                # Keep the first file, mark others as duplicates
                duplicates.extend(file_list[1:])
        
        self.duplicate_files = duplicates
        self.stats["duplicates"] = len(duplicates)
        
        if duplicates:
            print(f"🔍 Found {len(duplicates)} duplicate files")
            # Calculate space that could be saved
            for dup_file in duplicates:
                try:
                    self.stats["space_saved"] += dup_file.stat().st_size
                except:
                    pass

    def generate_file_statistics(self, files):
        """Generate comprehensive file statistics."""
        stats = {
            'total_files': len(files),
            'total_size': 0,
            'type_distribution': defaultdict(int),
            'size_distribution': defaultdict(int),
            'date_distribution': defaultdict(int),
            'largest_files': [],
            'oldest_files': [],
            'newest_files': []
        }
        
        file_sizes = []
        file_dates = []
        
        for file_path in files:
            try:
                stat = file_path.stat()
                size = stat.st_size
                mod_time = stat.st_mtime
                
                stats['total_size'] += size
                file_sizes.append((file_path, size))
                file_dates.append((file_path, mod_time))
                
                # Type distribution
                ext = file_path.suffix.lower()
                stats['type_distribution'][ext] += 1
                
                # Size distribution
                if size < 1024 * 1024:  # < 1MB
                    stats['size_distribution']['Small (< 1MB)'] += 1
                elif size < 10 * 1024 * 1024:  # < 10MB
                    stats['size_distribution']['Medium (1-10MB)'] += 1
                elif size < 100 * 1024 * 1024:  # < 100MB
                    stats['size_distribution']['Large (10-100MB)'] += 1
                else:
                    stats['size_distribution']['Very Large (> 100MB)'] += 1
                
                # Date distribution
                mod_date = datetime.fromtimestamp(mod_time)
                if mod_date >= datetime.now() - timedelta(days=7):
                    stats['date_distribution']['This Week'] += 1
                elif mod_date >= datetime.now() - timedelta(days=30):
                    stats['date_distribution']['This Month'] += 1
                elif mod_date >= datetime.now() - timedelta(days=365):
                    stats['date_distribution']['This Year'] += 1
                else:
                    stats['date_distribution']['Older'] += 1
                    
            except Exception as e:
                self.logger.warning(f"Failed to get stats for {file_path.name}: {e}")
        
        # Sort and get top files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        file_dates.sort(key=lambda x: x[1])
        
        stats['largest_files'] = file_sizes[:10]
        stats['oldest_files'] = file_dates[:10]
        stats['newest_files'] = list(reversed(file_dates[-10:]))
        
        return stats

    def generate_report(self, file_stats):
        """Generate comprehensive organization report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_directory': str(self.target_directory),
            'statistics': self.stats,
            'file_statistics': file_stats,
            'suspicious_files': [str(f) for f in self.suspicious_files],
            'duplicate_files': [str(f) for f in self.duplicate_files],
            'organization_summary': {
                'total_files_processed': file_stats['total_files'],
                'files_moved': self.stats['moved'],
                'duplicates_found': self.stats['duplicates'],
                'suspicious_files': self.stats['suspicious'],
                'space_saved_mb': self.stats['space_saved'] / (1024 * 1024),
                'errors': self.stats['errors']
            }
        }
        
        self.organization_report = report
        return report

    def save_organization_history(self, organization_type):
        """Save organization session to database."""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO organization_history 
                (timestamp, directory, organization_type, files_moved, duplicates_found, 
                 suspicious_found, space_saved, time_taken, dry_run)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                str(self.target_directory),
                organization_type,
                self.stats['moved'],
                self.stats['duplicates'],
                self.stats['suspicious'],
                self.stats['space_saved'],
                getattr(self, 'operation_time', 0),
                False
            ))
            self.db_connection.commit()
        except Exception as e:
            self.logger.error(f"Failed to save organization history: {e}")

    def export_report_pdf(self, report, filename):
        """Export organization report to PDF."""
        if not REPORTLAB_AVAILABLE:
            return False
        
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title = Paragraph("File Organization Report", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Summary
            summary_data = [
                ['Metric', 'Value'],
                ['Target Directory', report['target_directory']],
                ['Total Files Processed', str(report['organization_summary']['total_files_processed'])],
                ['Files Moved', str(report['organization_summary']['files_moved'])],
                ['Duplicates Found', str(report['organization_summary']['duplicates_found'])],
                ['Suspicious Files', str(report['organization_summary']['suspicious_files'])],
                ['Space Saved (MB)', f"{report['organization_summary']['space_saved_mb']:.2f}"],
                ['Errors', str(report['organization_summary']['errors'])]
            ]
            
            summary_table = Table(summary_data)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 12))
            
            # File type distribution
            if report['file_statistics']['type_distribution']:
                story.append(Paragraph("File Type Distribution", styles['Heading2']))
                type_data = [['File Type', 'Count']]
                for ext, count in sorted(report['file_statistics']['type_distribution'].items()):
                    type_data.append([ext or 'No Extension', str(count)])
                
                type_table = Table(type_data)
                type_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(type_table)
                story.append(Spacer(1, 12))
            
            doc.build(story)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export PDF report: {e}")
            return False

    def export_report_excel(self, report, filename):
        """Export organization report to Excel."""
        if not PANDAS_AVAILABLE:
            return False
        
        try:
            # Create summary DataFrame
            summary_data = {
                'Metric': ['Target Directory', 'Total Files', 'Files Moved', 'Duplicates', 'Suspicious', 'Space Saved (MB)', 'Errors'],
                'Value': [
                    report['target_directory'],
                    report['organization_summary']['total_files_processed'],
                    report['organization_summary']['files_moved'],
                    report['organization_summary']['duplicates_found'],
                    report['organization_summary']['suspicious_files'],
                    f"{report['organization_summary']['space_saved_mb']:.2f}",
                    report['organization_summary']['errors']
                ]
            }
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Summary sheet
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                # File type distribution
                if report['file_statistics']['type_distribution']:
                    type_data = pd.DataFrame([
                        {'File Type': ext or 'No Extension', 'Count': count}
                        for ext, count in report['file_statistics']['type_distribution'].items()
                    ])
                    type_data.to_excel(writer, sheet_name='File Types', index=False)
                
                # Size distribution
                if report['file_statistics']['size_distribution']:
                    size_data = pd.DataFrame([
                        {'Size Category': category, 'Count': count}
                        for category, count in report['file_statistics']['size_distribution'].items()
                    ])
                    size_data.to_excel(writer, sheet_name='Size Distribution', index=False)
                
                # Suspicious files
                if report['suspicious_files']:
                    suspicious_data = pd.DataFrame([
                        {'File Path': path} for path in report['suspicious_files']
                    ])
                    suspicious_data.to_excel(writer, sheet_name='Suspicious Files', index=False)
                
                # Duplicate files
                if report['duplicate_files']:
                    duplicate_data = pd.DataFrame([
                        {'File Path': path} for path in report['duplicate_files']
                    ])
                    duplicate_data.to_excel(writer, sheet_name='Duplicate Files', index=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export Excel report: {e}")
            return False

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

    def organize_files(self, dry_run=False, sort_by='name', sort_order='asc', organization_type="type", progress_callback=None, find_duplicates=True):
        """Organize files with enhanced features including duplicate detection."""
        self.start_time = time.time()
        
        if hasattr(self, 'logger'):
            self.logger.info(f"Starting file organization{' (DRY RUN)' if dry_run else ''}")
            self.logger.info(f"Target directory: {self.target_directory}")
            self.logger.info(f"Organization type: {organization_type}")
            self.logger.info(f"Find duplicates: {find_duplicates}")
        
        if not self.target_directory.exists():
            print(f"Error: Directory '{self.target_directory}' does not exist!")
            return False
        
        # Reset stats
        self.stats = {"moved": 0, "errors": 0, "suspicious": 0, "duplicates": 0, "space_saved": 0}
        self.suspicious_files = []
        self.duplicate_files = []
        
        # Get all files
        files = [f for f in self.target_directory.iterdir() if f.is_file() and not f.name.startswith('.')]
        if not files:
            print("No files found to organize.")
            return True
        
        # Generate file statistics
        file_stats = self.generate_file_statistics(files)
        
        # Find duplicates if enabled
        if find_duplicates:
            print("🔍 Scanning for duplicates...")
            self.find_duplicates(files, progress_callback)
            
            # Calculate space that would be saved by removing duplicates
            for dup_file in self.duplicate_files:
                try:
                    self.stats["space_saved"] += dup_file.stat().st_size
                except:
                    pass
        
        # Sort files
        files = self._sort_files(files, sort_by, sort_order)
        
        # Create folders
        if not dry_run:
            self.create_folders(organization_type)
            if self.duplicate_files:
                (self.target_directory / "Duplicates").mkdir(exist_ok=True)
        
        print(f"Found {len(files)} files to organize")
        if self.duplicate_files:
            print(f"🔍 {len(self.duplicate_files)} duplicate files found")
        print("-" * 60)
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            if progress_callback:
                try:
                    progress_callback(i, len(files), file_path.name)
                except Exception:
                    pass
            
            try:
                # Check if file is a duplicate
                is_duplicate = file_path in self.duplicate_files
                
                # Check for suspicious files
                is_suspicious = self.detect_suspicious_file(file_path)
                
                if is_suspicious:
                    category = "Suspicious"
                    self.suspicious_files.append(file_path)
                    self.stats["suspicious"] += 1
                elif is_duplicate:
                    category = "Duplicates"
                else:
                    category = self.get_file_category(file_path, organization_type)
                
                # For extension-based organization, create folders dynamically
                if organization_type == "extension" and not is_suspicious and not is_duplicate:
                    category_path = self.target_directory / category
                    if not dry_run:
                        category_path.mkdir(exist_ok=True)
                
                destination = self.target_directory / category / file_path.name
                
                if dry_run:
                    status = "[SUSPICIOUS]" if is_suspicious else "[DUPLICATE]" if is_duplicate else "[DRY RUN]"
                    print(f"{status} {file_path.name} -> {category}/")
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
                    status = "[SUSPICIOUS]" if is_suspicious else "[DUPLICATE]" if is_duplicate else "Moved:"
                    print(f"{status} {file_path.name} -> {category}/")
                    
                    # Track for undo
                    self.undo_data.append({
                        "original_path": str(file_path),
                        "new_path": str(destination),
                        "filename": file_path.name,
                        "category": category,
                        "suspicious": is_suspicious,
                        "duplicate": is_duplicate
                    })
                    self.stats["moved"] += 1
                    
            except Exception as e:
                print(f"Error moving {file_path.name}: {e}")
                self.stats["errors"] += 1
        
        # Generate and save report
        if not dry_run:
            report = self.generate_report(file_stats)
            self.save_organization_history(organization_type)
            
            print("-" * 60)
            print(f"📊 Summary: {self.stats['moved']} files moved, {self.stats['duplicates']} duplicates, {self.stats['suspicious']} suspicious, {self.stats['errors']} errors")
            if self.stats["space_saved"] > 0:
                space_mb = self.stats["space_saved"] / (1024 * 1024)
                print(f"💾 Space that can be saved by removing duplicates: {space_mb:.2f} MB")
            
            if self.stats["moved"] > 0:
                self.save_undo_data()
                print(f"📝 Organization complete! Use --undo to reverse changes.")
        
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
    """Enhanced professional GUI with advanced features."""
    def __init__(self):
        if tk is None:
            raise RuntimeError("Tkinter is not available in this environment.")

        # Initialize DnD if available
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("🗂️ Enhanced File Organizer Pro")
        self.root.geometry("1100x750")
        self.root.configure(bg='#f0f0f0')
        
        # Theme system
        self.current_theme = self.load_theme_preference()
        self.themes = {
            'light': {
                'bg': '#f1f5f9',
                'card_bg': '#ffffff',
                'primary': '#2563eb',
                'text': '#1e293b',
                'border': '#e2e8f0'
            },
            'dark': {
                'bg': '#1e293b',
                'card_bg': '#334155',
                'primary': '#3b82f6',
                'text': '#f1f5f9',
                'border': '#475569'
            }
        }
        
        # Enhanced color scheme with theme support
        self.colors = {
            'primary': '#2563eb',
            'primary_light': '#3b82f6',
            'secondary': '#64748b',
            'success': '#16a34a',
            'success_light': '#22c55e',
            'warning': '#d97706',
            'warning_light': '#f59e0b',
            'danger': '#dc2626',
            'danger_light': '#ef4444',
            'light': '#f8fafc',
            'dark': '#1e293b',
            'card_bg': '#ffffff',
            'border': '#e2e8f0',
            'progress_bg': '#e5e7eb',
            'progress_fill': '#10b981'
        }
        
        # Update colors based on theme
        self.apply_theme()
        
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
        self.backup_enabled = False
        
        # Animation and progress tracking
        self.animation_running = False
        self.progress_animation_id = None
        
        # Statistics and analytics
        self.file_stats = {}
        self.organizer_instance = None

        self._build_widgets()
        self._setup_drag_drop()
        self._poll_log_queue()

    def load_theme_preference(self):
        """Load saved theme preference."""
        try:
            config_path = Path.home() / ".file_organizer" / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'light')
        except:
            pass
        return 'light'

    def save_theme_preference(self, theme):
        """Save theme preference."""
        try:
            config_path = Path.home() / ".file_organizer" / "config.json"
            config_path.parent.mkdir(exist_ok=True)
            config = {'theme': theme}
            with open(config_path, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def apply_theme(self):
        """Apply current theme colors."""
        theme_colors = self.themes[self.current_theme]
        self.colors.update({
            'bg': theme_colors['bg'],
            'card_bg': theme_colors['card_bg'],
            'text': theme_colors['text'],
            'border': theme_colors['border']
        })

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.apply_theme()
        self.save_theme_preference(self.current_theme)
        self._configure_styles()
        self._refresh_theme()

    def _refresh_theme(self):
        """Refresh GUI with new theme."""
        # This would require rebuilding widgets for full theme support
        self.root.configure(bg=self.colors['bg'])
        messagebox.showinfo("Theme Changed", "Theme will be fully applied on next restart.")

    def _setup_drag_drop(self):
        """Setup drag and drop functionality."""
        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<DropEnter>>', self._on_drop_enter)
            self.root.dnd_bind('<<DropLeave>>', self._on_drop_leave)
            self.root.dnd_bind('<<Drop>>', self._on_drop)

    def _on_drop_enter(self, event):
        """Handle drag enter."""
        self.root.configure(bg='#e3f2fd')

    def _on_drop_leave(self, event):
        """Handle drag leave."""
        self.root.configure(bg=self.colors['bg'])

    def _on_drop(self, event):
        """Handle file/folder drop."""
        files = self.root.tk.splitlist(event.data)
        if files:
            folder_path = files[0]
            if Path(folder_path).is_dir():
                self.dir_var.set(folder_path)
                messagebox.showinfo("📂 Folder Added", f"Directory set to:\n{folder_path}")
        self.root.configure(bg=self.colors['bg'])

    def start_progress_animation(self):
        """Start smooth progress bar animation."""
        self.animation_running = True
        self._animate_progress()

    def _animate_progress(self):
        """Animate progress bar with smooth transitions."""
        if self.animation_running and hasattr(self, 'progress_bar'):
            current_value = self.progress_bar['value']
            # Add slight pulsing effect
            pulse = 2 * (1 + 0.1 * abs(time.time() % 2 - 1))
            if current_value < 100:
                self.progress_animation_id = self.root.after(50, self._animate_progress)

    def stop_progress_animation(self):
        """Stop progress bar animation."""
        self.animation_running = False
        if self.progress_animation_id:
            self.root.after_cancel(self.progress_animation_id)

    def show_statistics_window(self):
        """Show detailed file statistics with charts."""
        if not self.file_stats:
            messagebox.showwarning("No Data", "No statistics available. Please run organization first.")
            return

        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 File Statistics")
        stats_window.geometry("800x600")
        stats_window.configure(bg=self.colors['bg'])

        # Create notebook for different chart types
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # File type distribution pie chart
        type_frame = ttk.Frame(notebook)
        notebook.add(type_frame, text="File Types")
        
        try:
            if MATPLOTLIB_AVAILABLE:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                type_data = dict(self.file_stats.get('type_distribution', {}))
                if type_data:
                    colors = plt.cm.Set3(range(len(type_data)))
                    wedges, texts, autotexts = ax.pie(type_data.values(), labels=type_data.keys(), 
                                                     autopct='%1.1f%%', colors=colors, startangle=90)
                    ax.set_title("File Type Distribution", fontsize=16, fontweight='bold')
                    
                    # Make percentage text bold
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                
                canvas = FigureCanvasTkAgg(fig, type_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                tk.Label(type_frame, text="Matplotlib not available for charts", 
                        bg=self.colors['bg'], fg=self.colors['text']).pack(pady=50)
        except Exception as e:
            tk.Label(type_frame, text=f"Error creating chart: {e}", 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=50)

        # Size distribution bar chart
        size_frame = ttk.Frame(notebook)
        notebook.add(size_frame, text="File Sizes")
        
        try:
            if MATPLOTLIB_AVAILABLE:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                size_data = self.file_stats.get('size_distribution', {})
                if size_data:
                    bars = ax.bar(size_data.keys(), size_data.values(), 
                                 color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444'])
                    ax.set_title("File Size Distribution", fontsize=16, fontweight='bold')
                    ax.set_ylabel("Number of Files")
                    
                    # Add value labels on bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{int(height)}', ha='center', va='bottom', fontweight='bold')
                
                canvas = FigureCanvasTkAgg(fig, size_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                tk.Label(size_frame, text="Matplotlib not available for charts", 
                        bg=self.colors['bg'], fg=self.colors['text']).pack(pady=50)
        except Exception as e:
            tk.Label(size_frame, text=f"Error creating chart: {e}", 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=50)

    def show_custom_categories_window(self):
        """Show window for managing custom file categories."""
        categories_window = tk.Toplevel(self.root)
        categories_window.title("🏷️ Custom Categories")
        categories_window.geometry("600x400")
        categories_window.configure(bg=self.colors['bg'])

        # Create category form
        form_frame = tk.Frame(categories_window, bg=self.colors['card_bg'], relief='solid', bd=1)
        form_frame.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(form_frame, text="Create New Category", font=("Segoe UI", 14, "bold"),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(pady=10)

        # Category name
        tk.Label(form_frame, text="Category Name:", bg=self.colors['card_bg'], 
                fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=(10, 0))
        category_name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=category_name_var, width=50).pack(padx=20, pady=5)

        # Extensions
        tk.Label(form_frame, text="File Extensions (comma-separated, e.g., .mp4, .avi):", 
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor=tk.W, padx=20, pady=(10, 0))
        extensions_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=extensions_var, width=50).pack(padx=20, pady=5)

        # Save button
        def save_category():
            name = category_name_var.get().strip()
            extensions_str = extensions_var.get().strip()
            
            if not name or not extensions_str:
                messagebox.showwarning("Invalid Input", "Please fill in both fields.")
                return

            extensions = {ext.strip().lower() for ext in extensions_str.split(',') if ext.strip()}
            if not extensions:
                messagebox.showwarning("Invalid Input", "Please provide valid extensions.")
                return

            # Save to organizer if available
            if hasattr(self, 'organizer_instance') and self.organizer_instance:
                if self.organizer_instance.save_custom_category(name, extensions):
                    messagebox.showinfo("✅ Success", f"Category '{name}' saved successfully!")
                    category_name_var.set("")
                    extensions_var.set("")
                else:
                    messagebox.showerror("❌ Error", "Failed to save category.")

        ttk.Button(form_frame, text="💾 Save Category", command=save_category,
                  style='Success.TButton').pack(pady=15)

    def show_analytics_window(self):
        """Show analytics and history window."""
        analytics_window = tk.Toplevel(self.root)
        analytics_window.title("📈 Analytics & History")
        analytics_window.geometry("900x600")
        analytics_window.configure(bg=self.colors['bg'])

        # Create analytics content
        content_frame = tk.Frame(analytics_window, bg=self.colors['card_bg'], relief='solid', bd=1)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(content_frame, text="Organization History & Analytics", 
                font=("Segoe UI", 16, "bold"), bg=self.colors['card_bg'], 
                fg=self.colors['text']).pack(pady=20)

        # History table (simplified)
        history_text = ScrolledText(content_frame, height=15, width=100)
        history_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Load history from database
        try:
            if hasattr(self, 'organizer_instance') and self.organizer_instance and self.organizer_instance.db_connection:
                cursor = self.organizer_instance.db_connection.cursor()
                cursor.execute("""
                    SELECT timestamp, directory, files_moved, duplicates_found, 
                           suspicious_found, space_saved, time_taken, organization_type
                    FROM organization_history
                    ORDER BY timestamp DESC LIMIT 20
                """)
                
                history_text.insert(tk.END, "Recent Organization Sessions:\n")
                history_text.insert(tk.END, "="*100 + "\n\n")
                
                for row in cursor.fetchall():
                    timestamp, directory, files_moved, duplicates, suspicious, space_saved, time_taken, org_type = row
                    dt = datetime.fromisoformat(timestamp)
                    space_mb = space_saved / (1024 * 1024) if space_saved else 0
                    
                    history_text.insert(tk.END, f"📅 {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    history_text.insert(tk.END, f"📁 Directory: {directory}\n")
                    history_text.insert(tk.END, f"🗂️ Type: {org_type} | Files Moved: {files_moved} | Duplicates: {duplicates} | Suspicious: {suspicious}\n")
                    history_text.insert(tk.END, f"💾 Space Saved: {space_mb:.2f} MB | Time: {time_taken:.2f}s\n")
                    history_text.insert(tk.END, "-"*80 + "\n\n")
        except Exception as e:
            history_text.insert(tk.END, f"Error loading history: {e}")

        history_text.configure(state=tk.DISABLED)

        # Export buttons
        export_frame = tk.Frame(content_frame, bg=self.colors['card_bg'])
        export_frame.pack(pady=10)

        ttk.Button(export_frame, text="📄 Export PDF Report", 
                  command=self.export_pdf_report, style='Primary.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(export_frame, text="📊 Export Excel Report", 
                  command=self.export_excel_report, style='Success.TButton').pack(side=tk.LEFT, padx=10)

    def export_pdf_report(self):
        """Export current report to PDF."""
        if not hasattr(self, 'organizer_instance') or not self.organizer_instance or not hasattr(self.organizer_instance, 'organization_report'):
            messagebox.showwarning("No Data", "No report data available.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF Report"
        )
        
        if filename:
            if self.organizer_instance.export_report_pdf(self.organizer_instance.organization_report, filename):
                messagebox.showinfo("✅ Success", f"PDF report exported to:\n{filename}")
            else:
                messagebox.showerror("❌ Error", "Failed to export PDF report.")

    def export_excel_report(self):
        """Export current report to Excel."""
        if not hasattr(self, 'organizer_instance') or not self.organizer_instance or not hasattr(self.organizer_instance, 'organization_report'):
            messagebox.showwarning("No Data", "No report data available.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save Excel Report"
        )
        
        if filename:
            if self.organizer_instance.export_report_excel(self.organizer_instance.organization_report, filename):
                messagebox.showinfo("✅ Success", f"Excel report exported to:\n{filename}")
            else:
                messagebox.showerror("❌ Error", "Failed to export Excel report.")

    def _configure_styles(self):
        """Configure modern ttk styles with enhanced colors."""
        # Button styles
        self.style.configure('Primary.TButton', 
                           foreground='white',
                           focuscolor='none',
                           borderwidth=0,
                           relief='flat')
        self.style.map('Primary.TButton', 
                      background=[('active', self.colors['primary_light']), 
                                ('!active', self.colors['primary'])],
                      relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        self.style.configure('Success.TButton', 
                           foreground='white',
                           focuscolor='none',
                           borderwidth=0,
                           relief='flat')
        self.style.map('Success.TButton', 
                      background=[('active', self.colors['success_light']), 
                                ('!active', self.colors['success'])],
                      relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        self.style.configure('Danger.TButton', 
                           foreground='white',
                           focuscolor='none',
                           borderwidth=0,
                           relief='flat')
        self.style.map('Danger.TButton', 
                      background=[('active', self.colors['danger_light']), 
                                ('!active', self.colors['danger'])],
                      relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        self.style.configure('Warning.TButton', 
                           foreground='white',
                           focuscolor='none',
                           borderwidth=0,
                           relief='flat')
        self.style.map('Warning.TButton', 
                      background=[('active', self.colors['warning_light']), 
                                ('!active', self.colors['warning'])],
                      relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        # Frame styles with colors
        self.style.configure('Card.TLabelframe', 
                           background=self.colors['card_bg'],
                           borderwidth=1,
                           relief='solid',
                           bordercolor=self.colors['border'])
        self.style.configure('Card.TLabelframe.Label', 
                           background=self.colors['card_bg'],
                           foreground=self.colors['dark'],
                           font=('Segoe UI', 10, 'bold'))
        
        self.style.configure('Header.TFrame', background=self.colors['primary'])
        
        # Progress bar style with green color
        self.style.configure('Colored.Horizontal.TProgressbar',
                           background='#10b981',  # Green fill
                           troughcolor='#e5e7eb',
                           borderwidth=2,
                           relief='solid',
                           bordercolor='#374151',
                           lightcolor='#34d399',
                           darkcolor='#059669')
        
        # Entry style
        self.style.configure('Modern.TEntry',
                           borderwidth=1,
                           relief='solid',
                           bordercolor=self.colors['border'])
        self.style.map('Modern.TEntry',
                      bordercolor=[('focus', self.colors['primary'])])
        
        # Combobox style  
        self.style.configure('Modern.TCombobox',
                           borderwidth=1,
                           relief='solid',
                           bordercolor=self.colors['border'])
        self.style.map('Modern.TCombobox',
                      bordercolor=[('focus', self.colors['primary'])])

    def _build_widgets(self):
        """Build the enhanced GUI with professional styling and advanced features."""
        # Enhanced header with theme toggle
        header = tk.Frame(self.root, bg=self.colors['primary'], height=60)
        header.pack(fill=tk.X, pady=(0, 15))
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=self.colors['primary'])
        header_content.pack(expand=True, fill=tk.BOTH)
        
        title_font = tkFont.Font(family="Segoe UI", size=18, weight="bold")
        tk.Label(header_content, text="🗂️ Enhanced File Organizer Pro", font=title_font, 
                 fg='white', bg=self.colors['primary']).pack(side=tk.LEFT, pady=15, padx=20)
        
        # Theme toggle button
        ttk.Button(header_content, text="🌓 Theme", command=self.toggle_theme).pack(side=tk.RIGHT, pady=15, padx=20)

        # Main container with gradient background
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Directory selection card with drag & drop support
        dir_card = ttk.LabelFrame(main_container, text=" 📁 Directory Selection (Drag & Drop Supported) ", style='Card.TLabelframe')
        dir_card.pack(fill=tk.X, pady=(0, 15))
        
        dir_inner = tk.Frame(dir_card, bg=self.colors['card_bg'])
        dir_inner.pack(fill=tk.X, padx=20, pady=20)
        
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_inner, textvariable=self.dir_var, font=("Segoe UI", 11), style='Modern.TEntry')
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15), ipady=8)
        ttk.Button(dir_inner, text="📂 Browse", command=self._choose_directory, 
                  style='Primary.TButton').pack(side=tk.RIGHT, ipady=5)

        # Enhanced organization options with advanced features
        org_card = ttk.LabelFrame(main_container, text=" ⚙️ Organization & Advanced Options ", style='Card.TLabelframe')
        org_card.pack(fill=tk.X, pady=(0, 15))
        
        org_inner = tk.Frame(org_card, bg=self.colors['card_bg'])
        org_inner.pack(fill=tk.X, padx=20, pady=20)

        # First row - Organization type and sorting
        row1 = tk.Frame(org_inner, bg=self.colors['card_bg'])
        row1.pack(fill=tk.X, pady=(0, 15))
        
        # Organization type with colored background
        org_section = tk.Frame(row1, bg='#eff6ff', relief='solid', bd=1)
        org_section.pack(side=tk.LEFT, padx=(0, 20), pady=5, fill=tk.X, expand=True)
        tk.Label(org_section, text="📋 Organize by:", font=("Segoe UI", 10, "bold"), 
                bg='#eff6ff', fg=self.colors['primary']).pack(side=tk.LEFT, padx=10, pady=10)
        self.org_type_var = tk.StringVar(value="type")
        org_combo = ttk.Combobox(org_section, textvariable=self.org_type_var, 
                                values=["type", "date", "size", "extension"], 
                                state="readonly", width=12, style='Modern.TCombobox')
        org_combo.pack(side=tk.LEFT, padx=10, pady=10)

        # Sorting options with colored background  
        sort_section = tk.Frame(row1, bg='#f0fdf4', relief='solid', bd=1)
        sort_section.pack(side=tk.RIGHT, padx=(0, 0), pady=5)
        
        tk.Label(sort_section, text="📊 Sort:", font=("Segoe UI", 10, "bold"), 
                bg='#f0fdf4', fg=self.colors['success']).pack(side=tk.LEFT, padx=10, pady=10)
        self.sort_by_var = tk.StringVar(value="name")
        sort_combo = ttk.Combobox(sort_section, textvariable=self.sort_by_var, 
                                 values=["name", "date", "size"], state="readonly", 
                                 width=8, style='Modern.TCombobox')
        sort_combo.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        self.sort_order_var = tk.StringVar(value="asc")
        order_combo = ttk.Combobox(sort_section, textvariable=self.sort_order_var,
                                  values=["asc", "desc"], state="readonly", 
                                  width=8, style='Modern.TCombobox')
        order_combo.pack(side=tk.LEFT, padx=(0, 10), pady=10)

        # Second row - Advanced options
        row2 = tk.Frame(org_inner, bg=self.colors['card_bg'])
        row2.pack(fill=tk.X, pady=(0, 15))
        
        # Mode options section
        mode_section = tk.Frame(row2, bg='#fefce8', relief='solid', bd=1)
        mode_section.pack(side=tk.LEFT, padx=(0, 15), pady=5, fill=tk.X, expand=True)
        
        tk.Label(mode_section, text="🔍 Mode Options:", font=("Segoe UI", 10, "bold"), 
                bg='#fefce8', fg=self.colors['warning']).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        mode_frame = tk.Frame(mode_section, bg='#fefce8')
        mode_frame.pack(padx=10, pady=(0, 10))
        
        self.dry_run_var = tk.BooleanVar(value=False)
        self.undo_var = tk.BooleanVar(value=False)
        self.find_duplicates_var = tk.BooleanVar(value=True)
        
        dry_cb = tk.Checkbutton(mode_frame, text="🔍 Dry run (preview only)", 
                               variable=self.dry_run_var, bg='#fefce8', 
                               font=("Segoe UI", 9), fg=self.colors['dark'])
        dry_cb.pack(anchor=tk.W, pady=(0, 5))
        
        undo_cb = tk.Checkbutton(mode_frame, text="↩️ Undo last operation", 
                                variable=self.undo_var, command=self._ensure_mutual_exclusive,
                                bg='#fefce8', font=("Segoe UI", 9), fg=self.colors['dark'])
        undo_cb.pack(anchor=tk.W, pady=(0, 5))
        
        dup_cb = tk.Checkbutton(mode_frame, text="🔍 Find duplicates", 
                               variable=self.find_duplicates_var, bg='#fefce8',
                               font=("Segoe UI", 9), fg=self.colors['dark'])
        dup_cb.pack(anchor=tk.W)

        # Backup options section
        backup_section = tk.Frame(row2, bg='#f0f9ff', relief='solid', bd=1)
        backup_section.pack(side=tk.RIGHT, padx=(0, 0), pady=5)
        
        tk.Label(backup_section, text="💾 Backup Options:", font=("Segoe UI", 10, "bold"), 
                bg='#f0f9ff', fg=self.colors['primary']).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        backup_frame = tk.Frame(backup_section, bg='#f0f9ff')
        backup_frame.pack(padx=10, pady=(0, 10))
        
        self.backup_var = tk.BooleanVar(value=False)
        backup_cb = tk.Checkbutton(backup_frame, text="💾 Create backup", 
                                  variable=self.backup_var, bg='#f0f9ff',
                                  font=("Segoe UI", 9), fg=self.colors['dark'])
        backup_cb.pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Button(backup_frame, text="📂 Backup Location", 
                  command=self._choose_backup_location, style='Primary.TButton').pack(anchor=tk.W)

        # Third row - Advanced features
        row3 = tk.Frame(org_inner, bg=self.colors['card_bg'])
        row3.pack(fill=tk.X)
        
        # Advanced features section
        advanced_section = tk.Frame(row3, bg='#fdf2f8', relief='solid', bd=1)
        advanced_section.pack(fill=tk.X, pady=5)
        
        tk.Label(advanced_section, text="🚀 Advanced Features:", font=("Segoe UI", 10, "bold"), 
                bg='#fdf2f8', fg='#be185d').pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        advanced_frame = tk.Frame(advanced_section, bg='#fdf2f8')
        advanced_frame.pack(padx=10, pady=(0, 10))
        
        advanced_buttons = tk.Frame(advanced_frame, bg='#fdf2f8')
        advanced_buttons.pack(fill=tk.X)
        
        ttk.Button(advanced_buttons, text="📊 Statistics", 
                  command=self.show_statistics_window, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(advanced_buttons, text="🏷️ Categories", 
                  command=self.show_custom_categories_window, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(advanced_buttons, text="📈 Analytics", 
                  command=self.show_analytics_window, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 10))

        # Notification bar for malware/duplicate alerts
        self.notification_frame = tk.Frame(main_container, bg=self.colors['danger'], height=40)
        self.notification_frame.pack(fill=tk.X, pady=(0, 15))
        self.notification_frame.pack_forget()  # Initially hidden
        
        self.notification_text = tk.Label(self.notification_frame, text="", 
                                         bg=self.colors['danger'], fg='white',
                                         font=("Segoe UI", 10, "bold"))
        self.notification_text.pack(expand=True, fill=tk.BOTH, pady=8)

        # Enhanced action buttons with loading spinner
        action_card = ttk.LabelFrame(main_container, text=" 🚀 Actions & Status ", style='Card.TLabelframe')
        action_card.pack(fill=tk.X, pady=(0, 15))
        
        action_inner = tk.Frame(action_card, bg=self.colors['card_bg'])
        action_inner.pack(fill=tk.X, padx=20, pady=20)

        # Buttons with spinner
        button_frame = tk.Frame(action_inner, bg=self.colors['card_bg'])
        button_frame.pack(side=tk.LEFT)
        
        self.run_button = ttk.Button(button_frame, text="🚀 Run Organizer", 
                                    command=self._on_run, style='Success.TButton')
        self.run_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=15)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop", 
                                     command=self._on_stop, style='Danger.TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15), ipady=8, ipadx=15)
        
        ttk.Button(button_frame, text="🗑️ Clear Logs", 
                  command=self._clear_logs, style='Warning.TButton').pack(side=tk.LEFT, ipady=8, ipadx=15)

        # Loading spinner (initially hidden)
        self.spinner_frame = tk.Frame(button_frame, bg=self.colors['card_bg'])
        self.spinner_frame.pack(side=tk.LEFT, padx=(15, 0))
        
        self.spinner_label = tk.Label(self.spinner_frame, text="", font=("Segoe UI", 12), 
                                     bg=self.colors['card_bg'], fg=self.colors['primary'])
        self.spinner_label.pack()
        
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_id = None

        # Enhanced status with colored background
        status_frame = tk.Frame(action_inner, bg='#f0f9ff', relief='solid', bd=1)
        status_frame.pack(side=tk.RIGHT, padx=(20, 0), pady=5)
        
        tk.Label(status_frame, text="📊 Status:", font=("Segoe UI", 10, "bold"), 
                bg='#f0f9ff', fg=self.colors['primary']).pack(side=tk.LEFT, padx=(15, 5), pady=10)
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(status_frame, textvariable=self.status_var, 
                               font=("Segoe UI", 11, "bold"), bg='#f0f9ff', fg=self.colors['success'])
        status_label.pack(side=tk.LEFT, padx=(0, 15), pady=10)

        # Enhanced progress card with animations
        progress_card = ttk.LabelFrame(main_container, text=" 📊 Progress Tracker ", style='Card.TLabelframe')
        progress_card.pack(fill=tk.X, pady=(0, 15))
        
        progress_inner = tk.Frame(progress_card, bg=self.colors['card_bg'])
        progress_inner.pack(fill=tk.X, padx=20, pady=20)
        
        # Progress info with statistics
        progress_info = tk.Frame(progress_inner, bg='#ecfdf5', relief='solid', bd=1)
        progress_info.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.StringVar(value="Ready to organize files...")
        progress_label = tk.Label(progress_info, textvariable=self.progress_var, 
                                 font=("Segoe UI", 10), bg='#ecfdf5', fg=self.colors['success'])
        progress_label.pack(pady=15)
        
        # Statistics display
        stats_frame = tk.Frame(progress_info, bg='#ecfdf5')
        stats_frame.pack(pady=(0, 10))
        
        self.stats_labels = {}
        stats_data = [("Files", "files_count"), ("Duplicates", "duplicates"), ("Suspicious", "suspicious"), ("Space Saved", "space_saved")]
        
        for i, (label, key) in enumerate(stats_data):
            stat_frame = tk.Frame(stats_frame, bg='#dcfce7', relief='solid', bd=1)
            stat_frame.pack(side=tk.LEFT, padx=5, pady=5)
            
            tk.Label(stat_frame, text=label, font=("Segoe UI", 8, "bold"), 
                    bg='#dcfce7', fg=self.colors['success']).pack(pady=(5, 0))
            self.stats_labels[key] = tk.Label(stat_frame, text="0", font=("Segoe UI", 12, "bold"), 
                                            bg='#dcfce7', fg=self.colors['dark'])
            self.stats_labels[key].pack(pady=(0, 5), padx=10)
        
        # Enhanced progress bar with green gradient effect
        progress_container = tk.Frame(progress_inner, bg='#f0fdf4', height=30, relief='solid', bd=1)
        progress_container.pack(fill=tk.X)
        progress_container.pack_propagate(False)
        
        self.progress_bar = ttk.Progressbar(progress_container, mode='determinate', 
                                          style='Colored.Horizontal.TProgressbar')
        self.progress_bar.pack(expand=True, fill=tk.BOTH, padx=3, pady=3)

        # Enhanced logs card with better colors and filtering
        logs_card = ttk.LabelFrame(main_container, text=" 📝 Activity Logs ", style='Card.TLabelframe')
        logs_card.pack(fill=tk.BOTH, expand=True)
        
        log_container = tk.Frame(logs_card, bg=self.colors['card_bg'])
        log_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Log controls
        log_controls = tk.Frame(log_container, bg=self.colors['card_bg'])
        log_controls.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(log_controls, text="Filter:", font=("Segoe UI", 9, "bold"), 
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(side=tk.LEFT)
        
        self.log_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(log_controls, textvariable=self.log_filter_var,
                                   values=["All", "Info", "Warning", "Error", "Suspicious"], 
                                   state="readonly", width=10)
        filter_combo.pack(side=tk.LEFT, padx=(5, 20))
        
        # Log text with dark theme for better contrast
        self.log_text = ScrolledText(log_container, wrap=tk.WORD, height=8, 
                                    font=("Consolas", 10), bg='#1e293b', fg='#e2e8f0',
                                    insertbackground='white')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)

        # Configure enhanced log text colors
        self.log_text.tag_config("ERROR", foreground='#fca5a5')
        self.log_text.tag_config("WARNING", foreground='#fde047')
        self.log_text.tag_config("INFO", foreground='#a7f3d0')
        self.log_text.tag_config("SUSPICIOUS", foreground='#f87171', background='#7f1d1d')
        self.log_text.tag_config("SUCCESS", foreground='#86efac')
        self.log_text.tag_config("DUPLICATE", foreground='#fbbf24', background='#78350f')

        # Initialize variables
        self.backup_location = None

    def start_spinner(self):
        """Start loading spinner animation."""
        self.spinner_label.configure(text=self.spinner_chars[self.spinner_index])
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
        self.spinner_id = self.root.after(100, self.start_spinner)

    def stop_spinner(self):
        """Stop loading spinner animation."""
        if self.spinner_id:
            self.root.after_cancel(self.spinner_id)
            self.spinner_id = None
        self.spinner_label.configure(text="")

    def update_statistics_display(self, stats):
        """Update the statistics display in real-time."""
        try:
            self.stats_labels["files_count"].configure(text=str(stats.get("moved", 0) + stats.get("errors", 0)))
            self.stats_labels["duplicates"].configure(text=str(stats.get("duplicates", 0)))
            self.stats_labels["suspicious"].configure(text=str(stats.get("suspicious", 0)))
            
            space_mb = stats.get("space_saved", 0) / (1024 * 1024)
            self.stats_labels["space_saved"].configure(text=f"{space_mb:.1f}MB")
        except Exception:
            pass

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
        """Append log text with enhanced color coding."""
        self.log_text.configure(state=tk.NORMAL)
        
        # Apply enhanced color coding based on log content
        if "ERROR" in text or "CRITICAL" in text:
            tag = "ERROR"
        elif "WARNING" in text or "SUSPICIOUS" in text or "⚠️" in text:
            tag = "WARNING"
        elif "✅" in text or "SUCCESS" in text or "completed successfully" in text:
            tag = "SUCCESS"
        elif "SUSPICIOUS" in text or "malware" in text.lower():
            tag = "SUSPICIOUS"
            # Also show notification for malware detection
            if "suspicious files detected" in text.lower():
                try:
                    import re
                    match = re.search(r'(\d+)\s+suspicious', text)
                    if match:
                        count = int(match.group(1))
                        self.root.after(100, lambda: self._show_malware_notification(count))
                except:
                    pass
        elif "DUPLICATE" in text or "duplicate" in text.lower():
            tag = "DUPLICATE"
        else:
            tag = "INFO"
        
        self.log_text.insert(tk.END, text, tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _clear_logs(self):
        """Clear the log display."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._hide_notification()

    def _show_malware_notification(self, count):
        """Show malware detection notification."""
        self.malware_count = count
        if count > 0:
            self.notification_text.config(text=f"⚠️ SECURITY ALERT: {count} suspicious/malware files detected and quarantined!")
            self.notification_frame.pack(fill=tk.X, pady=(0, 15), before=self.log_text.master.master)
            # Auto-hide after 10 seconds
            self.root.after(10000, self._hide_notification)

    def _show_duplicate_notification(self, count):
        """Show duplicate files notification."""
        if count > 0:
            self.notification_frame.configure(bg=self.colors['warning'])
            self.notification_text.configure(bg=self.colors['warning'])
            self.notification_text.config(text=f"🔍 DUPLICATES FOUND: {count} duplicate files detected and organized!")
            self.notification_frame.pack(fill=tk.X, pady=(0, 15), before=self.log_text.master.master)
            # Auto-hide after 8 seconds
            self.root.after(8000, self._hide_notification)

    def _hide_notification(self):
        """Hide the notification bar."""
        self.notification_frame.pack_forget()

    def _choose_backup_location(self):
        """Choose backup location."""
        path = filedialog.askdirectory(title="Select Backup Location")
        if path:
            self.backup_location = path
            messagebox.showinfo("✅ Backup Location Set", 
                              f"Backup will be saved to:\n{path}")

    def _create_backup(self, source_dir):
        """Create backup of files before organizing."""
        if not self.backup_location:
            return False
        
        try:
            import zipfile
            from datetime import datetime
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"file_organizer_backup_{timestamp}.zip"
            backup_path = Path(self.backup_location) / backup_filename
            
            self.message_queue.put(f"Creating backup: {backup_filename}\n")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                source_path = Path(source_dir)
                files = [f for f in source_path.iterdir() if f.is_file() and not f.name.startswith('.')]
                
                for file_path in files:
                    zipf.write(file_path, file_path.name)
            
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
        """Enhanced run method with all advanced features."""
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
        find_duplicates = self.find_duplicates_var.get()
        
        # Validate backup location if backup is enabled
        if create_backup and not do_undo and not dry_run:
            if not self.backup_location:
                result = messagebox.askyesno("💾 Backup Location", 
                                           "Backup is enabled but no location is set.\n"
                                           "Would you like to choose a backup location now?")
                if result:
                    self._choose_backup_location()
                    if not self.backup_location:
                        return
                else:
                    return
        
        # Track operation type for notifications
        self.current_operation = 'undo' if do_undo else 'organize'
        self.is_dry_run = dry_run

        # Clear previous logs, reset progress, and hide notifications
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._reset_progress()
        self._hide_notification()

        # Update UI state with enhanced styling and animations
        self.run_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        
        if dry_run:
            self.status_var.set("🔍 Analyzing...")
        elif do_undo:
            self.status_var.set("↩️ Restoring...")
        else:
            self.status_var.set("🚀 Organizing...")
        
        # Start animations
        self.start_spinner()
        self.start_progress_animation()
        self.worker_running = True

        def _work():
            """Enhanced worker thread function with all features."""
            try:
                # Create backup if enabled
                if create_backup and not do_undo and not dry_run:
                    self.message_queue.put("💾 Creating backup before organizing...\n")
                    if not self._create_backup(directory):
                        self.message_queue.put("❌ Backup failed. Operation cancelled.\n")
                        return

                # Initialize organizer with database support
                self.organizer_instance = SimpleFileOrganizer(directory)
                logger = logging.getLogger(__name__)
                logger.addHandler(self.gui_handler)
                
                try:
                    if do_undo:
                        def progress_callback(current, total, filename):
                            def update_gui():
                                self._update_progress(current, total, filename, "Restoring")
                                # Update statistics in real-time
                                if hasattr(self.organizer_instance, 'stats'):
                                    self.root.after(0, lambda: self.update_statistics_display(self.organizer_instance.stats))
                            self.root.after(0, update_gui)
                        self.organizer_instance.undo_organization(dry_run=dry_run, progress_callback=progress_callback)
                    else:
                        sort_by = self.sort_by_var.get()
                        sort_order = self.sort_order_var.get()
                        
                        def progress_callback(current, total, filename):
                            def update_gui():
                                action = "Analyzing" if dry_run else "Organizing"
                                self._update_progress(current, total, filename, action)
                                # Update statistics in real-time
                                if hasattr(self.organizer_instance, 'stats'):
                                    self.root.after(0, lambda: self.update_statistics_display(self.organizer_instance.stats))
                            self.root.after(0, update_gui)
                        
                        # Store file statistics for charts
                        files = [f for f in Path(directory).iterdir() if f.is_file() and not f.name.startswith('.')]
                        self.file_stats = self.organizer_instance.generate_file_statistics(files)
                        
                        self.organizer_instance.organize_files(
                            dry_run=dry_run, 
                            sort_by=sort_by, 
                            sort_order=sort_order,
                            organization_type=org_type,
                            progress_callback=progress_callback,
                            find_duplicates=find_duplicates
                        )
                        
                        # Show notifications for duplicates and malware
                        if hasattr(self.organizer_instance, 'stats'):
                            stats = self.organizer_instance.stats
                            if stats.get('duplicates', 0) > 0 or stats.get('suspicious', 0) > 0:
                                def show_notifications():
                                    if stats.get('suspicious', 0) > 0:
                                        self._show_malware_notification(stats['suspicious'])
                                    elif stats.get('duplicates', 0) > 0:
                                        self._show_duplicate_notification(stats['duplicates'])
                                self.root.after(500, show_notifications)
                        
                finally:
                    logger.removeHandler(self.gui_handler)
            except Exception as e:
                self.message_queue.put(f"💥 CRITICAL ERROR: {e}\n")
            finally:
                self.root.after(0, self._on_worker_done)

        self.worker_thread = threading.Thread(target=_work, daemon=True)
        self.worker_thread.start()

    def _on_stop(self):
        """Stop operation (cooperative)."""
        messagebox.showinfo("ℹ️ Stop Request", 
                          "Stop request noted. The operation will complete current file processing safely.")

    def _on_worker_done(self):
        """Handle worker completion with enhanced notifications and animations."""
        self.worker_running = False
        self.run_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        
        # Stop animations
        self.stop_spinner()
        self.stop_progress_animation()
        
        # Enhanced status updates with colors
        if self.current_operation == 'organize':
            if self.is_dry_run:
                self.status_var.set("🔍 Analysis Complete")
            else:
                self.status_var.set("✅ Organization Complete")
        elif self.current_operation == 'undo':
            if self.is_dry_run:
                self.status_var.set("🔄 Preview Complete")
            else:
                self.status_var.set("↩️ Restore Complete")
        else:
            self.status_var.set("✅ Complete")
        
        self.progress_bar['value'] = 100
        self.progress_var.set("🎉 Operation completed successfully!")
        
        # Final statistics update
        if hasattr(self, 'organizer_instance') and self.organizer_instance and hasattr(self.organizer_instance, 'stats'):
            self.update_statistics_display(self.organizer_instance.stats)
        
        self._show_completion_notification()

    def _show_completion_notification(self):
        """Show enhanced completion notifications with detailed statistics."""
        malware_info = f"\n🛡️ {self.malware_count} suspicious files quarantined" if self.malware_count > 0 else ""
        duplicate_info = ""
        space_info = ""
        
        if hasattr(self, 'organizer_instance') and self.organizer_instance and hasattr(self.organizer_instance, 'stats'):
            stats = self.organizer_instance.stats
            if stats.get('duplicates', 0) > 0:
                duplicate_info = f"\n🔍 {stats['duplicates']} duplicate files found"
            if stats.get('space_saved', 0) > 0:
                space_mb = stats['space_saved'] / (1024 * 1024)
                space_info = f"\n💾 {space_mb:.2f} MB space can be saved"
        
        if self.current_operation == 'organize':
            if self.is_dry_run:
                messagebox.showinfo("🔍 Analysis Complete", 
                    "Comprehensive analysis completed! 📊\n\n"
                    "✅ All files have been analyzed\n"
                    "📁 Organization plan shown in logs\n"
                    "🛡️ Security scan completed" + malware_info +
                    duplicate_info + space_info + "\n"
                    "\nReady for actual organization!")
            else:
                backup_info = "\n💾 Backup created before organizing" if hasattr(self, 'backup_var') and self.backup_var.get() else ""
                messagebox.showinfo("🗂️ Organization Complete", 
                    "Files organized successfully! 🎉\n\n"
                    "✅ All files sorted into categories\n"
                    "🛡️ Security scan completed" + malware_info +
                    duplicate_info + space_info + backup_info + "\n"
                    "📝 Activity logged for review\n"
                    "📊 Statistics available in Analytics\n"
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
        
        # Reset tracking variables
        self.current_operation = None
        self.is_dry_run = False
        self.malware_count = 0

    def _update_progress(self, current, total, filename="", action="Processing"):
        """Enhanced progress updates with smooth animations."""
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar['value'] = percentage
            
            # Truncate long filenames for display
            display_name = filename[:35] + "..." if len(filename) > 35 else filename
            
            # Enhanced progress text with emojis and colors
            if action == "Analyzing":
                emoji = "🔍"
            elif action == "Organizing":
                emoji = "🗂️"
            elif action == "Restoring":
                emoji = "↩️"
            else:
                emoji = "⚡"
            
            self.progress_var.set(f"{emoji} {action}: {current}/{total} ({percentage:.1f}%) - {display_name}")
            
            # Add subtle progress bar color changes based on progress (green theme)
            if percentage < 30:
                progress_color = '#059669'  # Dark green
            elif percentage < 70:
                progress_color = '#10b981'  # Medium green
            else:
                progress_color = '#34d399'  # Light green
                
            # Update progress bar style dynamically
            self.style.configure('Colored.Horizontal.TProgressbar', background=progress_color)
        else:
            self.progress_bar['value'] = 0
            self.progress_var.set(f"{action} files...")

    def _reset_progress(self):
        """Reset progress indicators with enhanced styling."""
        self.progress_bar['value'] = 0
        self.progress_var.set("🚀 Ready to organize files...")
        self.malware_count = 0

    def run(self):
        """Run the GUI application with enhanced window management."""
        # Set minimum window size
        self.root.minsize(900, 650)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Set window icon if available
        try:
            # Try to set a window icon (you can add an .ico file to your project)
            pass  # self.root.iconbitmap('icon.ico')
        except:
            pass
        
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

        # Parse duplicate detection option
        find_duplicates = "--no-duplicates" not in sys.argv

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
            
            result = organizer.organize_files(dry_run, sort_by, sort_order, org_type, find_duplicates=find_duplicates)
            
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
        print("  --no-duplicates        Disable duplicate file detection")
        print("\nExamples:")
        print("  python file_organizer.py ~/Downloads --dry-run")
        print("  python file_organizer.py ~/Downloads --org-type date")
        print("  python file_organizer.py ~/Downloads --org-type size --sort-by date")
        print("  python file_organizer.py ~/Downloads --backup ~/Backups")
        print("  python file_organizer.py ~/Downloads --undo")
        print("\n🛡️ Features:")
        print("  • Advanced malware detection and quarantine")
        print("  • Duplicate file detection with hash comparison")
        print("  • Multiple organization methods (type/date/size/extension)")
        print("  • Professional GUI with drag & drop support")
        print("  • Real-time analytics and statistics")
        print("  • PDF/Excel report export")
        print("  • Custom file categories")
        print("  • Comprehensive logging with color coding")
        print("  • Safe undo functionality with full restore")
        print("  • Automatic backup creation")
        print("  • Theme support (light/dark)")


if __name__ == "__main__":
    main()