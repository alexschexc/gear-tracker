# PR Description: Windows Support - Standalone Executable

## Summary
Added Windows standalone executable support with cross-platform build infrastructure.

## Changes

### New Files
- **`icon.ico`** - Multi-resolution Windows icon (16x16, 32x32, 48x48, 256x256)
- **`geartracker_windows.spec`** - PyInstaller spec file for Windows builds
- **`build_windows.sh`** - Build script for cross-compilation via Wine
- **`dist/GearTracker.exe`** - Pre-built Windows executable (39MB)

### Modified Files
- **`README.md`** - Updated platform support status: ✅ Windows now supported
  - Added "Running from Source" section
  - Added Standalone Executables section with download links
  - Updated single-binary binary section

## Build Requirements
- Python 3.14+
- PyQt6
- For cross-compilation: Wine + Python 3.14 for Windows

## Testing
- Executable tested via Wine during build process
- Ready for Windows VM / real Windows machine validation
