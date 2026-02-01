#!/bin/bash
# ====================================================================
# Grid Bash Build Script (Linux/macOS)
# ====================================================================
# This script freezes the Python shell into a standalone executable
# using PyInstaller.
# ====================================================================

echo ""
echo "🏗️  Building Grid Bash Executable..."
echo ""

# 1. Clean previous builds
rm -rf build dist

# 2. Run PyInstaller
pyinstaller --noconfirm --onefile --console \
    --name "gridbash" \
    --hidden-import "torch" \
    --hidden-import "rich" \
    --hidden-import "prompt_toolkit" \
    --hidden-import "quantgrid.hub" \
    --hidden-import "quantgrid.ml" \
    --hidden-import "quantgrid.core" \
    quantgrid/shell/main.py

echo ""
echo "✅ Build Complete!"
echo "📁 Output: dist/gridbash"
echo "💡 Test it: ./dist/gridbash"
echo ""

# Make executable
chmod +x dist/gridbash

# Optional: Install to /usr/local/bin
read -p "Install to /usr/local/bin? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo cp dist/gridbash /usr/local/bin/
    echo "✅ Installed! Type 'gridbash' anywhere to launch."
fi
