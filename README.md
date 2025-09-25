# Enhanced File Organizer Pro

A Python tool and GUI application that organizes files in a target directory with advanced features like multiple organization modes, malware-suspicious file detection, comprehensive logging, and safe undo.

## Key Features

- **Multiple Organization Modes**: Organize by `type`, `date`, `size`, or file `extension`
- **Malware-Suspicious Detection**: Flags and quarantines suspicious files to a `Suspicious/` folder
- **Professional GUI**: Modern Tkinter GUI with progress, logs, and notifications
- **Dry Run Mode**: Preview all moves without changing files
- **Undo Support**: Safely revert the last organization
- **Sorting Options**: Sort processing order by `name`, `date`, or `size`, asc/desc
- **Smart Conflict Resolution**: Auto-renames with numeric suffixes to avoid overwrites
- **Comprehensive Logging**: Timestamped logs in `logs/` with INFO/WARNING/ERROR

## Organization Modes

- **type**: Groups by categories like `Documents`, `Images`, `Videos`, `Audio`, `Archives`, `Code`, `Executables`, `Fonts`, `Data`, `Others`
- **date**: Groups by recency buckets: `This Week`, `This Month`, `This Year`, or year folders; falls back to `Unknown Date`
- **size**: Groups by size: `Small (< 1MB)`, `Medium (1-10MB)`, `Large (10-100MB)`, `Very Large (> 100MB)`, or `Unknown Size`
- **extension**: Creates a folder named after the file extension (e.g., `pdf/`, `png/`); `No Extension` if none

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

## GUI Usage

Just run without CLI arguments to launch the GUI (if Tkinter is available):

```bash
python file_organizer.py
```

In the GUI you can:
- Pick a target directory
- Choose organization mode and sorting
- Toggle Dry Run or Undo
- View colored logs and progress
- Get completion notifications

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
- Duplicate handling with numeric suffixes
- Undo saves a `.file_organizer_undo.json` in the target directory
- Skips dotfiles in the root of the target during processing

## Troubleshooting

- Ensure the selected directory exists and is accessible
- If GUI fails to launch, use the CLI
- Review the latest file in `logs/` for details

## License

This project is open source. Feel free to modify and distribute.

## Changelog

- **v2.0** (2025): Enhanced Organizer Pro
  - Advanced GUI, organization modes, suspicious detection, improved CLI
- **v1.0** (2024): Initial release with basic organizing