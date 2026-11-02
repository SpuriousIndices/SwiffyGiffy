import sys
import shutil
import tarfile
import subprocess
from pathlib import Path


def create_linux_desktop_helpers(root: Path, dist_dir: Path, bin_path: Path):
    """Create .desktop launcher, run.sh, desktop installer, and tarball for Linux Mint / Ubuntu."""
    bin_name = bin_path.name

    # 1. Ensure executable permissions
    try:
        bin_path.chmod(bin_path.stat().st_mode | 0o755)
    except Exception:
        pass

    # 2. Copy app icon
    icon_src = root / "static" / "icon.png"
    icon_dst = dist_dir / "swiffygiffy.png"
    if icon_src.exists():
        shutil.copy2(icon_src, icon_dst)

    # 3. Create double-clickable .desktop launcher file
    desktop_file = dist_dir / "SwiffyGiffy.desktop"
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SwiffyGiffy
Comment=Local YouTube & Video to GIF Studio
Exec=sh -c 'DIR="$(dirname "$(readlink -f "%k")")"; cd "$DIR" && ./{bin_name}'
Icon=swiffygiffy
Terminal=true
Categories=AudioVideo;Video;Graphics;
StartupNotify=true
"""
    desktop_file.write_text(desktop_content, encoding="utf-8")
    try:
        desktop_file.chmod(desktop_file.stat().st_mode | 0o755)
    except Exception:
        pass

    # 4. Create simple run.sh script
    run_sh = dist_dir / "run.sh"
    run_sh_content = f"""#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$DIR"
chmod +x ./{bin_name}
exec ./{bin_name} "$@"
"""
    run_sh.write_text(run_sh_content, encoding="utf-8")
    try:
        run_sh.chmod(run_sh.stat().st_mode | 0o755)
    except Exception:
        pass

    # 5. Create 1-click desktop/menu installer for Ubuntu & Linux Mint
    install_sh = dist_dir / "install-desktop-launcher.sh"
    install_content = f"""#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
chmod +x "$DIR/{bin_name}" "$DIR/run.sh"

APPS_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$APPS_DIR" "$ICONS_DIR"

if [ -f "$DIR/swiffygiffy.png" ]; then
    cp "$DIR/swiffygiffy.png" "$ICONS_DIR/swiffygiffy.png"
fi

cat > "$APPS_DIR/swiffygiffy.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SwiffyGiffy
Comment=Local YouTube & Video to GIF Studio
Exec="$DIR/{bin_name}"
Icon=swiffygiffy
Terminal=true
Categories=AudioVideo;Video;Graphics;
StartupNotify=true
EOF

chmod +x "$APPS_DIR/swiffygiffy.desktop"

# If Desktop folder exists (standard in Ubuntu/Mint), optionally add icon to Desktop
if [ -d "$HOME/Desktop" ]; then
    cp "$APPS_DIR/swiffygiffy.desktop" "$HOME/Desktop/SwiffyGiffy.desktop"
    chmod +x "$HOME/Desktop/SwiffyGiffy.desktop"
    # Ubuntu GNOME requires marking desktop files as trusted
    gio set "$HOME/Desktop/SwiffyGiffy.desktop" metadata::trusted true 2>/dev/null || true
fi

echo "============================================================"
echo "  SwiffyGiffy has been added to your Applications Menu & Desktop!"
echo "============================================================"
"""
    install_sh.write_text(install_content, encoding="utf-8")
    try:
        install_sh.chmod(install_sh.stat().st_mode | 0o755)
    except Exception:
        pass

    # 6. Package a portable .tar.gz bundle for easy distribution
    archive_path = dist_dir / "SwiffyGiffy-linux-x86_64.tar.gz"
    bundle_files = [bin_name, "SwiffyGiffy.desktop", "run.sh", "install-desktop-launcher.sh"]
    if icon_dst.exists():
        bundle_files.append("swiffygiffy.png")

    with tarfile.open(archive_path, "w:gz") as tar:
        for fname in bundle_files:
            fpath = dist_dir / fname
            if fpath.exists():
                tar.add(fpath, arcname=f"SwiffyGiffy/{fname}")

    print(f"  [Linux Package] Created {archive_path.name} ({archive_path.stat().st_size / (1024*1024):.1f} MB)")


def build():
    root = Path(__file__).resolve().parent
    spec_path = root / "SwiffyGiffy.spec"

    print(f"[SwiffyGiffy Build] Building with {spec_path.name} on {sys.platform}...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_path),
    ]

    result = subprocess.run(cmd, cwd=str(root))
    if result.returncode != 0:
        sys.exit(result.returncode)

    dist_dir = root / "dist"
    exe_name = "SwiffyGiffy.exe" if sys.platform == "win32" else "SwiffyGiffy"
    bin_path = dist_dir / exe_name

    if bin_path.exists():
        size_mb = bin_path.stat().st_size / (1024 * 1024)
        print("=" * 64)
        print("  SUCCESS! Standalone executable created:")
        print(f"  {bin_path} ({size_mb:.1f} MB)")

        if sys.platform != "win32":
            create_linux_desktop_helpers(root, dist_dir, bin_path)

        print("=" * 64)
    else:
        print(f"ERROR: {dist_dir / exe_name} was not found after build.")
        sys.exit(1)


if __name__ == "__main__":
    build()
