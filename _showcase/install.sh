#!/usr/bin/env bash
set -euo pipefail

echo ""
echo " ============================================"
echo "  BPE-SVD Embedder Demo — Environment Setup"
echo " ============================================"
echo ""

# Resolve to _showcase directory regardless of where the script is called from
cd "$(dirname "$0")"

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo " [ERROR] python3 not found. Please install Python 3.11+."
    exit 1
fi

# Create isolated virtual environment
if [ ! -d ".venv" ]; then
    echo " [1/3] Creating isolated virtual environment..."
    python3 -m venv .venv
    echo "       Done."
else
    echo " [1/3] Virtual environment already exists — skipping."
fi

# Activate and install dependencies
echo " [2/3] Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt --quiet

# Vendor the bpe_svd package (inference + training) into this venv.
# The showcase stubs (core.py) do NOT import from it yet — this just
# makes the package available so wiring it up requires no reinstall.
pip install -e ../packages/bpe_svd --quiet || \
    echo " [WARN] Could not install bpe_svd package. Demo stubs will still work."
echo "       Done."

echo " [3/3] Verifying installation..."
python -c "import numpy; print(f'       numpy {numpy.__version__}')"
python -c "import tkinter; print('       tkinter OK')"
python -c "import bpe_svd; print(f'       bpe_svd {bpe_svd.__version__} (vendored)')" 2>/dev/null || \
    echo "       bpe_svd not installed (optional)"

echo ""
echo " ============================================"
echo "  Setup complete."
echo ""
echo "  Run the demo:"
echo "    ./run_ui.sh        (graphical interface)"
echo "    ./run_cli.sh       (command line)"
echo " ============================================"
echo ""
