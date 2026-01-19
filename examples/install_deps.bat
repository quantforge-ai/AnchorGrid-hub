@echo off
REM ====================================================================
REM Grid Bash Dependencies Installer (Windows)
REM ====================================================================
REM This script installs all necessary dependencies for Grid Bash
REM in the QuantGrid-core conda environment
REM ====================================================================

echo.
echo 🔧 Installing Grid Bash Dependencies...
echo.

REM Check if in conda env
if "%CONDA_DEFAULT_ENV%"=="QuantGrid-core" (
    echo ✅ Detected conda environment: QuantGrid-core
) else (
    echo ⚠️  Warning: Not in QuantGrid-core environment
    echo 💡 Run: conda activate QuantGrid-core
    echo.
    pause
    exit /b 1
)

echo.
echo 📦 Installing core dependencies...
pip install prompt_toolkit rich psutil requests

echo.
echo ✅ Installation complete!
echo.
echo 🚀 Test Grid Bash with: python demo_gridbash.py
echo.
pause
