#!/usr/bin/env bash
set -e

# ==============================================================================
# SwiffyGiffy AppImage Packaging Script (Ubuntu / Linux Mint)
# Creates a 100% self-contained, double-clickable .AppImage
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DIST_BIN="$SCRIPT_DIR/dist/SwiffyGiffy"

if [ ! -f "$DIST_BIN" ]; then
    echo "Executable $DIST_BIN not found. Running build_linux.sh first..."
    ./build_linux.sh
fi

echo "============================================================"
echo "  Packaging SwiffyGiffy as an AppImage..."
echo "============================================================"

APPDIR="$SCRIPT_DIR/build/SwiffyGiffy.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# 1. Copy binary and icon
cp "$DIST_BIN" "$APPDIR/usr/bin/SwiffyGiffy"
chmod +x "$APPDIR/usr/bin/SwiffyGiffy"

if [ -f "$SCRIPT_DIR/static/icon.png" ]; then
    cp "$SCRIPT_DIR/static/icon.png" "$APPDIR/swiffygiffy.png"
    cp "$SCRIPT_DIR/static/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/swiffygiffy.png"
fi

# 2. Desktop entry in AppDir
cat > "$APPDIR/swiffygiffy.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SwiffyGiffy
Comment=Local YouTube & Video to GIF Studio
Exec=SwiffyGiffy
Icon=swiffygiffy
Terminal=true
Categories=AudioVideo;Video;Graphics;
StartupNotify=true
EOF

# 3. AppRun script
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/usr/bin:$PATH"
exec "$APPDIR/usr/bin/SwiffyGiffy" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 4. Download appimagetool if not already present
APPIMAGETOOL="$SCRIPT_DIR/build/appimagetool-x86_64.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    curl -sSL -o "$APPIMAGETOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

# 5. Build AppImage
mkdir -p "$SCRIPT_DIR/dist"
OUTPUT_APPIMAGE="$SCRIPT_DIR/dist/SwiffyGiffy-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run "$APPDIR" "$OUTPUT_APPIMAGE"

echo "============================================================"
echo "  SUCCESS! Double-clickable AppImage generated:"
echo "  $OUTPUT_APPIMAGE"
echo "  On Ubuntu & Linux Mint: right click -> Properties -> Permissions"
echo "  -> check 'Allow executing file as program', then double-click!"
echo "============================================================"

