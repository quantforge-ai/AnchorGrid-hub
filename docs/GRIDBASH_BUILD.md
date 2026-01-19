# Grid Bash Installation & Build Guide

## What is Grid Bash?

Grid Bash is a **standalone terminal environment** for QuantGrid - inspired by Git Bash but purpose-built for financial intelligence. When developers open Grid Bash, they enter a curated environment where QuantGrid commands (`train`, `push`, `pull`) work seamlessly alongside standard commands (`git`, `ls`, `python`).

---

## For End Users: Installation

### Windows

**Option 1: Installer (Recommended)**
1. Download `QuantGrid_Setup_v1.0.exe`
2. Run the installer
3. Click "Next" through the wizard
4. Launch from Desktop shortcut or right-click any folder → "Open Grid Bash Here"

**Option 2: Portable**
1. Download `GridBash.exe`
2. Place anywhere (e.g., `C:\Tools\`)
3. Double-click to run

### Linux / macOS

```bash
# Download and install
curl -O https://quantgrid.dev/downloads/gridbash
chmod +x gridbash
sudo mv gridbash /usr/local/bin/

# Launch
gridbash
```

---

## For Developers: Building from Source

### Prerequisites

**Required**:
- Python 3.11+
- Git

**Install Dependencies**:
```bash
pip install -r requirements-shell.txt
# Or manually:
pip install prompt_toolkit rich psutil requests torch
pip install pyinstaller  # For building
```

### Step 1: Test the Shell Locally

```bash
# From project root
python -m quantgrid.shell.main
```

You should see:
```
QUANTGRID TERMINAL v1.0
The Operating System for Financial Intelligence

(grid) guest@QuantGrid-core $
```

Try commands:
- `help` - See all commands
- `status` - Check system
- `ls` - List files
- `exit` - Quit

### Step 2: Build Standalone Executable

#### Windows

```batch
# Run the build script
build.bat

# Output: dist\GridBash.exe (~80MB)
```

#### Linux/macOS

```bash
# Make build script executable
chmod +x build.sh

# Run it
./build.sh

# Output: dist/gridbash
```

**What PyInstaller Does**:
- Bundles Python interpreter + all dependencies
- Creates single executable file
- No Python installation required on target machine

### Step 3: Create Installer (Windows Only)

**Requirements**:
- [Inno Setup](https://jrsoftware.org/isdl.php) (free download)

**Steps**:
1. Open `installers/windows/setup.iss` in Inno Setup Compiler
2. Click **Compile** (Ctrl+F9)
3. Output: `installers/windows/Output/QuantGrid_Setup_v1.0.exe`

**What the Installer Does**:
- Installs to `C:\Program Files\QuantGrid\`
- Adds to system PATH (type `gridbash` anywhere)
- Creates desktop shortcut
- Adds right-click menu: "Open Grid Bash Here"
- Professional uninstaller

---

## File Structure

```
QuantGrid-core/
├── quantgrid/
│   └── shell/
│       ├── __init__.py
│       └── main.py              # The shell engine
├── installers/
│   └── windows/
│       └── setup.iss            # Inno Setup config
├── assets/
│   └── grid.ico                 # Application icon
├── build.bat                    # Windows build script
├── build.sh                     # Linux/Mac build script
└── requirements-shell.txt       # Shell dependencies
```

---

## Testing Checklist

Before releasing, test:

- `help` command shows all commands
- `status` displays GPU info
- `ls` works (system pass-through)
- `ls models` shows Grid-specific listing
- `cd` changes directory and updates prompt
- `login` / `logout` work
- `init` creates `.quantgrid/` folder
- `exit` cleanly closes shell
- Command history persists (up arrow)
- Auto-completion works (type `tr` + Tab)
- Colors render correctly
- Windows installer adds to PATH
- Right-click menu appears

---

## Customization

### Change Color Theme

Edit `quantgrid/shell/main.py`:

```python
style = Style.from_dict({
    'env': '#00ff00 bold',       # Green
    'user': '#00ffff bold',      # Cyan
    'at': '#ffffff',             # White
    'path': '#ff00ff italic',    # Magenta
})
```

### Add Custom Commands

Add to `GRID_COMMANDS` list and create handler in `execute()` method.

---

## Troubleshooting

**"Module not found" errors when frozen**:
- Add to `--hidden-import` in build scripts

**Large .exe file**:
- PyTorch is ~500MB. For lighter build, exclude ML dependencies

**Right-click menu doesn't appear**:
- Run installer as Administrator
- May need to restart Explorer.exe

**Icon not showing**:
- Ensure `assets/grid.ico` exists
- Rebuild with PyInstaller

---

## Distribution

### Release Checklist

1. **Test Build**: Run on clean Windows VM
2. **Version Bump**: Update version in `setup.iss` and `main.py`
3. **Changelog**: Document new features
4. **Build Installer**: Compile with Inno Setup
5. **Upload**: Host on GitHub Releases or quantgrid.dev
6. **Announce**: Blog post, Twitter, Discord

### Download Links

Structure:
```
https://quantgrid.dev/downloads/
  ├── windows/QuantGrid_Setup_v1.0.exe
  ├── linux/gridbash
  └── macos/gridbash.dmg
```

---

## Future Enhancements

- Live market data in prompt
- Desktop notifications
- Plugin system
- macOS DMG installer
- Linux AppImage
- Themes (dark/light/cyberpunk)
- Multiplayer mode (see team activity)

---

**Built with pride by the QuantGrid Team**
