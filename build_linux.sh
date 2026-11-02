#!/usr/bin/env bash
set -e

# ==============================================================================
# SwiffyGiffy Linux Build Script (Ubuntu, Linux Mint, Debian)
# Builds standalone executable & desktop bundle into dist/
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  SwiffyGiffy — Building for Linux (Ubuntu / Mint)"
echo "============================================================"

# Ensure Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is not installed. Run: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "[2/4] Installing / verifying dependencies..."
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

echo "[3/4] Running PyInstaller build..."
./.venv/bin/python build_exe.py

echo "[4/4] Done! Linux executable & desktop bundle generated in dist/"
echo "  - Standalone binary: dist/SwiffyGiffy"
echo "  - Desktop launcher : dist/SwiffyGiffy.desktop"
echo "  - Tarball bundle   : dist/SwiffyGiffy-linux-x86_64.tar.gz"
echo "============================================================"

