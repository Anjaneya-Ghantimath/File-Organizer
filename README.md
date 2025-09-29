# Enhanced File Organizer Pro

A Python tool and GUI application that organizes files in a target directory with advanced features like multiple organization modes, malware-suspicious file detection, comprehensive logging, safe undo, and optional backups.

## Key Features

- **Multiple Organization Modes**: Organize by `type`, `date`, `size`, or file `extension`
- **Malware-Suspicious Detection**: Flags and quarantines suspicious files to a `Suspicious/` folder with summaries
- **Enhanced Backup System**: Create zip backups with metadata and full recovery capabilities
- **Professional GUI**: Modern Tkinter GUI with progress, logs, notifications, and backup controls
- **Dry Run Mode**: Preview all moves without changing files
- **Undo Support**: Safely revert the last organization
- **Backup Recovery**: Restore all files from backup with one-click recovery
- **Duplicate Detection**: Find and handle duplicate files automatically
- **Sorting Options**: Sort processing order by `name`, `date`, or `size`, asc/desc
- **Smart Conflict Resolution**: Auto-renames with numeric suffixes to avoid overwrites
- **Comprehensive Logging**: Timestamped logs in `logs/` with INFO/WARNING/ERROR
- **Quick Controls**: "Clear Logs" button and real-time security banner when suspicious files are found

## Organization Modes

- **type**: Groups by categories like `Documents`, `Images`, `Videos`, `Audio`, `Archives`, `Code`, `Executables`, `Fonts`, `Data`, `Others`
- **date**: Groups by recency buckets: `This Week`, `This Month`, `This Year`, or year folders; falls back to `Unknown Date`
- **size**: Groups by size: `Small (< 1MB)`, `Medium (1-10MB)`, `Large (10-100MB)`, `Very Large (> 100MB)`, or `Unknown Size`
- **extension**: Creates a folder named after the file extension (e.g., `pdf/`, `png/`); `No Extension` if none

## Enhanced Backup System

The backup system now provides comprehensive file protection:

- **Automatic Backup Creation**: Creates timestamped ZIP files with complete file inventory
- **Metadata Tracking**: Saves detailed JSON metadata including file information, timestamps, and operation history
- **One-Click Recovery**: Restore all files from backup to their original locations
- **File Safety**: All deleted files are preserved and can be fully recovered
- **Recovery Confirmation**: User confirmation dialogs before recovery operations
- **Progress Tracking**: Detailed progress messages during backup and recovery operations

## Suspicious File Handling

The organizer detects potentially suspicious files using patterns like:
- Executable/script extensions (e.g., `.bat`, `.cmd`, `.scr`, `.com`, `.vbs`, `.jar`)
- Double extensions (e.g., `invoice.pdf.exe`)
- Hex-only filenames
- Hidden executables (e.g., `.run`, `.exe`)
- System-related names (e.g., includes `system32`, `windows`, `temp` with executable extensions)

Suspicious files are moved to a dedicated `Suspicious/` folder and highlighted in logs. Counts are included in the summary. Undo will restore them back as well.

## Installation

- Requires Python 3.8+ (built-in libraries only)
- Clone/download this repository

```bash
git clone <repository-url>
cd pj1-zalimaa
```

(Optional) Make the script executable on Unix-like systems:

```bash
chmod +x file_organizer.py
```

## Usage (CLI)

Basic organization by type:

```bash
python file_organizer.py /path/to/folder
```

Dry run preview:

```bash
python file_organizer.py ~/Downloads --dry-run
```

Choose organization mode and sorting:

```bash
python file_organizer.py ~/Downloads --org-type date --sort-by size --sort-order desc
```

Create a backup before organizing:

```bash
python file_organizer.py ~/Downloads --backup ~/Backups
```

Undo last operation:

```bash
python file_organizer.py ~/Downloads --undo
```

### CLI Options

- `directory`: Path to the directory to organize (required)
- `--dry-run`: Preview changes without moving files
- `--undo`: Undo the last organization
- `--org-type TYPE`: `type|date|size|extension` (default: `type`)
- `--sort-by FIELD`: `name|date|size` (default: `name`)
- `--sort-order ORDER`: `asc|desc` (default: `asc`)
- `--backup LOCATION`: Create a zip backup to `LOCATION` before organizing

## GUI Usage

Just run without CLI arguments to launch the GUI (if Tkinter is available):

```bash
python file_organizer.py
```

In the GUI you can:
- Pick a target directory with drag & drop support
- Choose organization mode and sorting options
- Toggle Dry Run or Undo operations
- Enable backup and choose a destination directory
- Recover files from backup with one-click recovery
- Find and handle duplicate files
- View colored logs and progress tracking
- Get completion notifications, including security alerts showing number of suspicious files quarantined
- Access advanced features like Statistics and Custom Categories

## Output Structure (examples)

```
Target Directory/
├── Documents/
├── Images/
├── Videos/
├── Audio/
├── Archives/
├── Code/
├── Data/
├── Fonts/
├── Executables/
├── Suspicious/
├── Others/
└── logs/
    └── file_organizer_YYYYMMDD_HHMMSS.log
```

## Logging

- Logs are written to `logs/file_organizer_YYYYMMDD_HHMMSS.log`
- INFO for standard actions, WARNING for suspicious detections, ERROR for failures

## Safety & Reliability

- Dry Run mode for safe previews
- Duplicate detection and handling with numeric suffixes
- Undo saves a `.file_organizer_undo.json` in the target directory
- Skips dotfiles in the root of the target during processing
- Enhanced backup system with metadata and recovery capabilities
- One-click backup recovery for complete file restoration
- Comprehensive logging for all operations

## Customization

- Progress bar color can be changed in `FileOrganizerGUI._configure_styles` (style: `Green.Horizontal.TProgressbar`). Default is green `#10b981`. For light blue, use `#3b82f6`.
- Window title and labels are defined in the GUI header and can be adjusted.

## Troubleshooting

- Ensure the selected directory exists and is accessible
- If GUI fails to launch, use the CLI
- Review the latest file in `logs/` for details

## License

This project is open source. Feel free to modify and distribute.

## Changelog

- **v2.2** (2025): Enhanced Backup & Recovery System
  - Added comprehensive backup recovery functionality with one-click restoration
  - Enhanced backup creation with detailed metadata tracking
  - Improved GUI with backup recovery button and better user experience
  - Added duplicate detection and handling capabilities
  - Enhanced file safety with complete backup and recovery system
- **v2.1** (2025): Backups and Security Notifications
  - Added GUI backup toggle and location chooser, backup in CLI (`--backup`)
  - Security notification banner and completion summaries with suspicious counts
  - Green progress bar style in GUI
- **v2.0** (2025): Enhanced Organizer Pro
  - Advanced GUI, organization modes, suspicious detection, improved CLI
- **v1.0** (2024): Initial release with basic organizing