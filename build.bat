@echo off
REM ====================================================================
REM Grid Bash Build Script (Windows)
REM ====================================================================
REM This script freezes the Python shell into a standalone .exe
REM using PyInstaller. No Python installation required to run the output.
REM ====================================================================

echo.
echo 🏗️  Building Grid Bash Executable...
echo.

REM 1. Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 2. Run PyInstaller
REM --onefile: Bundles everything into one .exe
REM --name: Name of the output file
REM --icon: Your logo (make sure assets/grid.ico exists!)
REM --hidden-import: Ensures PyTorch and Rich are included
pyinstaller --noconfirm --onefile --console ^
    --name "GridBash" ^
    --icon "assets/grid.ico" ^
    --hidden-import "torch" ^
    --hidden-import "rich" ^
    --hidden-import "prompt_toolkit" ^
    --hidden-import "quantgrid.hub" ^
    --hidden-import "quantgrid.ml" ^
    --hidden-import "quantgrid.core" ^
    quantgrid/shell/main.py

echo.
echo ✅ Build Complete!
echo 📁 Output: dist\GridBash.exe
echo 💡 Test it: dist\GridBash.exe
echo.
pause
