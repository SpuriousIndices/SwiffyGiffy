import sys
import subprocess
from pathlib import Path


def build():
    root = Path(__file__).resolve().parent
    spec_path = root / "SwiffyGiffy.spec"

    print(f"[SwiffyGiffy Build] Building with {spec_path.name}...")
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

    exe_path = root / "dist" / "SwiffyGiffy.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("=" * 64)
        print("  SUCCESS! Standalone executable created:")
        print(f"  {exe_path} ({size_mb:.1f} MB)")
        print("=" * 64)
    else:
        print("ERROR: dist/SwiffyGiffy.exe was not found after build.")
        sys.exit(1)


if __name__ == "__main__":
    build()
