# Simple File Organizer - User Guide

## Quick Start Guide

### Step 1: Download and Test
1. Save `file_organizer.py` to your computer
2. Open terminal/command prompt
3. Test with dry run first:
   ```bash
   python file_organizer.py ~/Downloads --dry-run
   ```

### Step 2: Organize Files
If the preview looks good:
```bash
python file_organizer.py ~/Downloads
```
Type `y` and press Enter to confirm.

## Understanding the Output

### Dry Run Example
```
File Organizer
Target: /Users/john/Downloads  
Mode: DRY RUN
========================================
Found 8 files to organize
----------------------------------------
[DRY RUN] report.pdf -> Documents/
[DRY RUN] vacation.jpg -> Images/
[DRY RUN] song.mp3 -> Audio/
[DRY RUN] backup.zip -> Archives/
```

### Actual Organization Example
```
File Organizer
Target: /Users/john/Downloads
Mode: ORGANIZE FILES
========================================
Proceed with organizing files? (y/N): y
Found 8 files to organize
----------------------------------------
Moved: report.pdf -> Documents/
Moved: vacation.jpg -> Images/
Moved: song.mp3 -> Audio/
Moved: backup.zip -> Archives/
----------------------------------------
Summary: 8 files moved, 0 errors
```

## File Categories Explained

| Category | File Types | Examples |
|----------|------------|----------|
| **Documents** | Text, PDF, Office files | `.pdf`, `.docx`, `.txt`, `.xlsx` |
| **Images** | Pictures and graphics | `.jpg`, `.png`, `.gif`, `.svg` |
| **Videos** | Movie and video files | `.mp4`, `.avi`, `.mkv`, `.mov` |
| **Audio** | Music and sound files | `.mp3`, `.wav`, `.flac`, `.aac` |
| **Archives** | Compressed files | `.zip`, `.rar`, `.7z`, `.tar` |
| **Code** | Programming files | `.py`, `.html`, `.css`, `.js` |
| **Others** | Anything else | `.xyz`, `.unknown` |

## Common Scenarios

### Scenario 1: Messy Downloads Folder
**Problem**: Downloads folder has 50+ mixed files
**Solution**: 
```bash
python file_organizer.py ~/Downloads --dry-run
python file_organizer.py ~/Downloads
```

### Scenario 2: Project Files
**Problem**: Project folder has mixed code, docs, and media
**Solution**:
```bash
python file_organizer.py /path/to/project --dry-run
python file_organizer.py /path/to/project
```

### Scenario 3: USB Drive Cleanup
**Problem**: USB drive with various file types
**Solution**:
```bash
python file_organizer.py /Volumes/USB_DRIVE --dry-run
python file_organizer.py /Volumes/USB_DRIVE
```

## Troubleshooting

### Common Issues

**"Directory does not exist"**
- Check the path is correct
- Use quotes around paths with spaces: `"~/My Downloads"`

**"Permission denied"**
- Close any programs using the files
- Run as administrator (Windows) or with sudo (Mac/Linux)

**Files not moving**
- Ensure files aren't currently open
- Check available disk space

### Getting Help
```bash
python file_organizer.py
# Shows usage instructions

python file_organizer.py ~/Downloads --dry-run
# Always test first!
```

## Tips and Best Practices

### Before You Start
1. **Always use dry run first** (`--dry-run`)
2. **Close any open files** in the target directory
3. **Backup important files** if unsure
4. **Start with a small test folder** to get familiar

### Best Results
- Use on folders with mixed file types (Downloads, Desktop, etc.)
- Perfect for cleaning up project folders
- Great for organizing USB drives and external storage
- Ideal for sorting through old archive folders

### What Gets Organized
✅ Regular files with recognized extensions  
✅ Files in the root of the target directory  
❌ Files in subdirectories (they stay put)  
❌ Hidden files (starting with '.')  
❌ System files  

### File Naming Conflicts
If a file with the same name already exists in the destination folder:
- `document.pdf` becomes `document_1.pdf`
- `document_1.pdf` becomes `document_2.pdf`
- And so on...

## Platform-Specific Notes

### Windows
```cmd
python file_organizer.py C:\Users\Username\Downloads --dry-run
python file_organizer.py "C:\Path With Spaces" --dry-run
```

### macOS
```bash
python3 file_organizer.py ~/Downloads --dry-run
python3 file_organizer.py /Users/username/Desktop --dry-run
```

### Linux
```bash
python3 file_organizer.py ~/Downloads --dry-run
python3 file_organizer.py /home/username/Documents --dry-run
```

## Summary

This simple file organizer helps you quickly clean up messy folders by sorting files into logical categories. Always test with `--dry-run` first, then run the actual organization when you're satisfied with the preview.