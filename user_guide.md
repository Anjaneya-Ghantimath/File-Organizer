# Simple File Organizer - User Guide

## Quick Start Guide

![0](https://github.com/user-attachments/assets/ea9ef1bd-6e16-4d75-9e81-45edf54eb3f1)


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
![1](https://github.com/user-attachments/assets/534ad597-f68b-4e1f-8f14-8ef98c83bb12)

##Actual Organization Example

![3](https://github.com/user-attachments/assets/4c9df09a-640c-40b4-9a6a-d7fd3b326e88)

###if we want to undone the previous organization we can go with the following command in CLI

![2](https://github.com/user-attachments/assets/5fb64754-2915-4a1f-b08e-d6caf5aca67e)



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


##GUI Working Example

![4](https://github.com/user-attachments/assets/2a12aafc-64ed-46bf-b4bc-09ac7f1f4062)
![4 1](https://github.com/user-attachments/assets/123d61cc-0738-4391-8e44-a715049adad5)


##for uploading or selecting the files we have two options as following
![5](https://github.com/user-attachments/assets/826c3e47-3aae-40a1-8c13-3447bad81b58)


##when we select the browse option we will get a pop like following for selecting the file
![1 1](https://github.com/user-attachments/assets/3784c365-5395-4619-b536-43e820d6691a)


##Advanced Features
![7](https://github.com/user-attachments/assets/0764d6b6-950c-47fc-9a60-51e032397bb5)

![7 1](https://github.com/user-attachments/assets/6132bb6e-2e7a-4579-a3fe-859f1bbf252e)


##mode options
![8](https://github.com/user-attachments/assets/2a591baf-67a7-4659-a9e2-ee908a38c3f5)


##Backup option , first we need to select the backup folder for storing the files

![9](https://github.com/user-attachments/assets/0faf2649-95ad-4876-bf35-7b282cc32657)


##Advanced features
![10](https://github.com/user-attachments/assets/cdd15b00-f549-4b8d-b669-58811a1000ea)

##the following exampole will depict that which types of files are present in the folder which we orgamnized
![11](https://github.com/user-attachments/assets/8e29eef0-9afa-4077-b86d-ad02573befc5)

##the following picture will show the size of the files present in the folder
![12](https://github.com/user-attachments/assets/3d11cf7d-4ddb-4b23-a019-cb5452349933)

##If we want to add new categories and new extention we can add(shown below) it will help to directly add files , it will save the effort to add the categories into the code
![13](https://github.com/user-attachments/assets/f3f4c0c7-143f-411c-a23d-d227bfb4c954)

##file categories supported
![14](https://github.com/user-attachments/assets/b7a05b22-e05f-45a1-aba7-27ea4dd280f8)

##workflow
![00](https://github.com/user-attachments/assets/b241320a-1be6-46f0-bc0a-1742d82ac447)

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
