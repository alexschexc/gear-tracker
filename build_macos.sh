#!/bin/bash
# Build script for GearTracker macOS executable
# Run on macOS (or macOS VM/Hackintosh)

set -e

echo "=== GearTracker macOS Build Script ==="

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "Warning: This script is designed for macOS."
    echo "Building macOS executables requires a macOS system."
    echo "For Linux CI/CD, use GitHub Actions instead."
    exit 1
fi

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Check for Pillow (for icon conversion if needed)
if ! python -c "from PIL import Image" 2>/dev/null; then
    echo "Installing Pillow..."
    pip install pillow
fi

# Convert icon to icns if needed
if [ ! -f "icon.icns" ]; then
    if [ -f "icon.png" ]; then
        echo "Converting icon.png to icon.icns..."
        python -c "
from PIL import Image
import subprocess
import tempfile
import os

img = Image.open('icon.png')
sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]

# Create temp directory for icons
with tempfile.TemporaryDirectory() as tmpdir:
    # Generate PNG files at each size
    for size in sizes:
        icon_name = f'icon_{size[0]}x{size[1]}.png'
        resized = img.resize(size, Image.LANCZOS)
        resized.save(os.path.join(tmpdir, icon_name))
    
    # Use sips (macOS built-in) to ensure proper format
    for size in sizes:
        icon_name = f'icon_{size[0]}x{size[1]}.png'
        subprocess.run(['sips', '-s', 'format', 'png', os.path.join(tmpdir, icon_name)], check=True)
    
    # Convert to ICNS using sips and iconutil
    iconset_dir = os.path.join(tmpdir, 'GearTracker.iconset')
    os.makedirs(iconset_dir, exist_ok=True)
    
    # Create standard icon set files
    icon_map = {
        'icon_16x16.png': 'icon_16x16.png',
        'icon_32x32.png': 'icon_32x32.png',
        'icon_64x64.png': 'icon_64x64.png',
        'icon_128x128.png': 'icon_128x128.png',
        'icon_256x256.png': 'icon_256x256.png',
        'icon_512x512.png': 'icon_512x512.png',
        'icon_1024x1024.png': 'icon_1024x1024.png',
    }
    
    for src, dst in icon_map.items():
        # Standard resolution
        subprocess.run(['cp', os.path.join(tmpdir, src), os.path.join(iconset_dir, dst)], check=True)
        # High resolution (@2x)
        src_2x = src.replace('.png', '@2x.png')
        if os.path.exists(os.path.join(tmpdir, src_2x)):
            subprocess.run(['cp', os.path.join(tmpdir, src_2x), os.path.join(iconset_dir, dst.replace('.png', '@2x.png'))], check=True)
    
    # Create @2x versions for Retina displays
    for size in [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)]:
        src = f'icon_{size[0]}x{size[1]}.png'
        dst = f'icon_{size[0]}x{size[1]}@2x.png'
        resized = img.resize((size[0]*2, size[1]*2), Image.LANCZOS)
        resized.save(os.path.join(tmpdir, dst))
        subprocess.run(['cp', os.path.join(tmpdir, dst), os.path.join(iconset_dir, dst)], check=True)
    
    # Convert to ICNS using iconutil
    subprocess.run(['iconutil', '-c', 'icns', '-o', 'icon.icns', iconset_dir], check=True)
    print('icon.icns created successfully')
"
    else
        echo "Error: icon.png not found. Cannot create icon.icns"
        exit 1
    fi
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.spec

# Build the macOS app
echo "Building macOS executable..."
pyinstaller geartracker_macos.spec --clean

# Verify the build
if [ -d "dist/GearTracker.app" ]; then
    echo ""
    echo "=== Build Complete ==="
    echo "macOS app: dist/GearTracker.app"
    echo ""
    echo "File size: $(du -sh dist/GearTracker.app | cut -f1)"
    echo ""
    echo "To test: open dist/GearTracker.app"
    echo "To create DMG: use create-dmg or manually copy to a disk image"
else
    echo "Error: Build failed, GearTracker.app not found"
    exit 1
fi
