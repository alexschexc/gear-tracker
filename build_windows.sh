#!/bin/bash
# Build script for GearTracker Windows executable
# Requires Wine with Python 3.14 installed

set -e

echo "=== GearTracker Windows Build Script ==="

# Check for Wine
if ! command -v wine &> /dev/null; then
    echo "Error: Wine is not installed."
    echo "Install Wine first, then Python 3.14 for Windows:"
    echo "  1. Download Python 3.14 Windows installer from python.org"
    echo "  2. Install under Wine: wine python-3.14.0-amd64.exe"
    exit 1
fi

# Check if Python exists in Wine
if ! wine python --version &> /dev/null; then
    echo "Python not found in Wine. Install it first:"
    echo "  wget https://www.python.org/ftp/python/3.14.0/python-3.14.0-amd64.exe"
    echo "  wine python-3.14.0-amd64.exe"
    exit 1
fi

echo "Python version: $(wine python --version 2>&1 | tail -1)"

# Install dependencies in Wine if needed
echo "Ensuring dependencies installed in Wine..."
wine python -m pip install pyinstaller pillow pyqt6 -q 2>/dev/null || true

# Convert icon if needed
if [ ! -f "icon.ico" ]; then
    echo "Converting icon.png to icon.ico..."
    python -c "from PIL import Image; sizes = [(16,16), (32,32), (48,48), (256,256)]; img = Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=sizes)"
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.spec

# Build with Wine
echo "Building Windows executable..."
WINEPREFIX=/home/alexander/.wine wine python -m PyInstaller geartracker_windows.spec --clean

echo ""
echo "=== Build Complete ==="
echo "Windows executable: dist/GearTracker.exe"
echo ""
echo "File size: $(ls -lh dist/GearTracker.exe | awk '{print $5}')"
echo ""
echo "Transfer GearTracker.exe to Windows for testing."
