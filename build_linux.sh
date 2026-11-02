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
    echo "ERROR: python3 is not installed."
    echo "Run: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    exit 1
fi

# 1. Verify existing .venv (delete and recreate if pip is missing / broken)
if [ -d ".venv" ]; then
    if ! ./.venv/bin/python -m pip --version &>/dev/null; then
        echo "[!] Existing .venv is missing pip. Cleaning up .venv to recreate it..."
        rm -rf .venv
    fi
fi

# 2. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtual environment (.venv)..."
    python3 -m venv .venv 2>/dev/null || {
        echo "python3 -m venv failed. Trying virtualenv or fallback..."
        if command -v virtualenv &>/dev/null; then
            virtualenv -p python3 .venv
        else
            echo "ERROR: Failed to create virtual environment."
            echo "Please run: sudo apt update && sudo apt install -y python3-venv python3-full"
            exit 1
        fi
    }
fi

# 3. Ensure pip exists inside .venv (bootstrap if Debian/Ubuntu stripped ensurepip)
if ! ./.venv/bin/python -m pip --version &>/dev/null; then
    echo "[!] Bootstrapping pip into .venv..."
    ./.venv/bin/python -m ensurepip --upgrade 2>/dev/null || {
        echo "[!] ensurepip failed; fetching get-pip.py..."
        curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
        ./.venv/bin/python /tmp/get-pip.py
        rm -f /tmp/get-pip.py
    }
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
