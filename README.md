# SwiffyGiffy — Local YouTube & Video to GIF Studio

**SwiffyGiffy** is a self-contained local web application for creating high-quality GIFs from YouTube links (or local video files). It packages Python, Flask, `yt-dlp`, Pillow, and a static `FFmpeg` binary into a single portable executable for **Windows** (`.exe`) and **Linux** (`.AppImage` / standalone binary) that anyone can double-click to start the studio in their browser—with zero external setup required.

---

## ✨ Features

- **YouTube & Local Video Support**: Paste any YouTube video or Shorts URL (powered by `yt-dlp`) or upload a local video file (`.mp4`, `.webm`, `.mov`, `.mkv`).
- **Interactive Timeline & Length Control**:
  - Visual dual-handle trim bar to drag Start and End markers.
  - Fine-tune step buttons (`-0.1s` / `+0.1s`), quick duration chips (`2s`, `3s`, `5s`, `8s`, `10s`), and `Set Start` / `Set End` from current playhead position.
  - Real-time loop preview between Start and End markers.
- **Interactive On-Video Cropping**:
  - Drag and resize an 8-handle crop box with rule-of-thirds guides directly on the video preview.
  - Aspect ratio presets (`Freeform`, `1:1 Square`, `16:9 Wide`, `4:3 Classic`, `9:16 Vertical`) plus exact coordinate controls.
- **Draggable Multi-Layer Text Overlays**:
  - Add Top Meme Text, Bottom Meme Text, or multiple custom caption layers.
  - Drag text layers directly over the video stage to position them anywhere.
  - Cross-platform system font discovery (Windows, Ubuntu, Linux Mint fonts) with custom styling, colors, outlines, and visibility intervals.
- **Speed, Loop Modes & Color Filters**:
  - Playback speed control (`0.5x` slow-mo to `2.0x` double speed).
  - Loop modes: **Infinite Loop**, **Boomerang (Forward + Reverse)**, **Reverse Playback**, or **Play Once**.
  - Live-previewed color adjustments (Brightness, Contrast, Saturation, Grayscale, Sepia) and quick filter presets (`Vivid Pop`, `Noir B&W`, `Vintage Sepia`, `High Contrast`).
- **2-Pass 256-Color Palette Optimization**:
  - Uses FFmpeg `palettegen` + `paletteuse` with Sierra dithering for crisp, vibrant GIFs.

---

## 🚀 Running on Windows

1. Double-click **`SwiffyGiffy.exe`** (found in `dist/` or downloaded from GitHub Releases / Actions).
2. The local server starts and automatically opens `http://127.0.0.1:5175` in your default browser.
3. Generated GIFs are saved to `swiffygiffy_data/output_gifs` next to the `.exe`.

---

## 🐧 Running on Linux (Ubuntu, Linux Mint & Debian)

### Option A: AppImage (Recommended for Double-Click)
1. Download **`SwiffyGiffy-x86_64.AppImage`**.
2. Make it executable:
   - **Via GUI**: Right-click the `.AppImage` → **Properties** → **Permissions** tab → Check **"Allow executing file as program"**.
   - **Via Terminal**: `chmod +x SwiffyGiffy-x86_64.AppImage`
3. **Double-click** the file to launch!

### Option B: Tarball Bundle (`.tar.gz`)
1. Extract `SwiffyGiffy-linux-x86_64.tar.gz`.
2. Inside the extracted folder:
   - Double-click **`SwiffyGiffy.desktop`** (on Ubuntu GNOME, right-click and choose **"Allow Launching"** the first time).
   - Or double-click **`run.sh`**.
   - To add SwiffyGiffy directly into your Linux Mint or Ubuntu Applications menu & Desktop, run `./install-desktop-launcher.sh`.

---

## 🛠️ Building From Source

### Windows
```powershell
# Run from source
.\.venv\Scripts\python.exe app.py

# Build dist/SwiffyGiffy.exe
.\.venv\Scripts\python.exe build_exe.py
# Or double-click build_exe.bat
```

### Linux (Ubuntu / Mint)
```bash
# Run from source
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py

# Build standalone binary & desktop bundle (dist/SwiffyGiffy)
./build_linux.sh

# Package as single-file AppImage (dist/SwiffyGiffy-x86_64.AppImage)
./build_appimage.sh
```

---

## 🤖 Automated CI/CD Builds (GitHub Actions)

This repository includes a GitHub Actions workflow (`.github/workflows/build.yml`) that automatically builds both:
- **`SwiffyGiffy.exe`** (Windows x64)
- **`SwiffyGiffy-x86_64.AppImage`** and **`SwiffyGiffy-linux-x86_64.tar.gz`** (Linux x86_64, built on Ubuntu LTS)

Whenever you push commits or open a PR, download the ready-to-run executables from the GitHub Actions **Artifacts** section.
