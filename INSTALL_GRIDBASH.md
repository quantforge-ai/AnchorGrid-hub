# Grid Bash Installation Guide

## Quick Start (Conda Environment: QuantGrid-core)

### 1. Activate Your Environment

```bash
conda activate QuantGrid-core
```

### 2. Install Dependencies

```bash
# Core dependencies for Grid Bash
pip install prompt_toolkit rich psutil requests

# Optional: If you want full QuantGrid functionality
pip install -e .
```

Or use the requirements file:

```bash
pip install -r requirements-shell.txt
```

### 3. Test the Boot Animation

```bash
# Test the standalone demo
python demo_gridbash.py
```

You should see the Matrix Glitch logo with:
- Gradient rendering (blue to cyan)
- "INITIALIZING HIVE MIND CONNECTION..."
- System diagnostics progress bar
- Then the shell prompt: `(grid) guest@QuantGrid-core $`

### 4. Try Commands

Once in Grid Bash:
- `help` - See all commands
- `status` - System diagnostics
- `login` - Mock authentication
- `ls` - List files
- `cd <dir>` - Change directory
- `exit` - Quit

---

## Full Installation (All QuantGrid Features)

If you want the complete package with ML training capabilities:

```bash
conda activate QuantGrid-core

# Install base package
pip install -e .

# Install ML dependencies (for training adapters)
pip install -e ".[ml]"

# Install dev dependencies (for building)
pip install -e ".[dev]"
```

---

## Building Standalone Executable

### Windows

```bash
# Install PyInstaller
pip install pyinstaller

# Run build script
build.bat

# Output: dist\GridBash.exe
```

### Linux/macOS

```bash
# Install PyInstaller
pip install pyinstaller

# Make script executable
chmod +x build.sh

# Run build
./build.sh

# Output: dist/gridbash
```

---

## Troubleshooting

### "Module not found" errors

Make sure you've activated the conda environment:
```bash
conda activate QuantGrid-core
```

### Grid Bash won't start

Check if all dependencies are installed:
```bash
pip list | grep -E "(prompt_toolkit|rich|psutil)"
```

Should show:
- prompt_toolkit >= 3.0.43
- rich >= 13.7.0
- psutil >= 5.9.0

### Import errors from quantgrid package

The standalone demo (`demo_gridbash.py`) doesn't need the full package. But if you're running `python -m quantgrid.shell.main`, you need:

```bash
pip install -e .
```

---

## Environment Info

- **Python Version**: 3.12
- **Conda Env**: QuantGrid-core
- **Platform**: Windows/Linux/macOS

---

## Next Steps

1. Test the demo: `python demo_gridbash.py`
2. Try building: `build.bat` (Windows) or `./build.sh` (Linux/Mac)
3. Create installer: Open `installers/windows/setup.iss` in Inno Setup (Windows only)

**Questions?** Check `docs/GRIDBASH_BUILD.md` for full build documentation.
