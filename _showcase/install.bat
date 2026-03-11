@echo off
setlocal

echo.
echo  ============================================
echo   BPE-SVD Embedder Demo — Environment Setup
echo  ============================================
echo.

:: Resolve to _showcase directory regardless of where the script is called from
cd /d "%~dp0"

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.11+ and add it to PATH.
    pause
    exit /b 1
)

:: Create isolated virtual environment
if not exist ".venv" (
    echo  [1/3] Creating isolated virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo        Done.
) else (
    echo  [1/3] Virtual environment already exists — skipping.
)

:: Activate and install dependencies
echo  [2/3] Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Vendor the bpe_svd package (inference + training) into this venv.
:: The showcase stubs (core.py) do NOT import from it yet — this just
:: makes the package available so wiring it up requires no reinstall.
pip install -e ..\packages\bpe_svd --quiet
if errorlevel 1 (
    echo  [WARN] Could not install bpe_svd package. Demo stubs will still work.
)
echo        Done.

echo  [3/3] Verifying installation...
python -c "import numpy; print(f'        numpy {numpy.__version__}')"
python -c "import tkinter; print('        tkinter OK')"
python -c "import bpe_svd; print(f'        bpe_svd {bpe_svd.__version__} (vendored)')" 2>nul || echo         bpe_svd not installed (optional)

echo.
echo  ============================================
echo   Setup complete.
echo.
echo   Run the demo:
echo     run_ui.bat        (graphical interface)
echo     run_cli.bat       (command line)
echo  ============================================
echo.

endlocal
