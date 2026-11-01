# SwiffyGiffy — Local YouTube & Video to GIF Studio

**SwiffyGiffy** is a self-contained local web application for creating high-quality GIFs from YouTube links (or local video files). It packages Python, Flask, `yt-dlp`, Pillow, and a static `FFmpeg` binary into a single portable **`SwiffyGiffy.exe`** executable that anyone can double-click to start the studio in their browser—with zero external setup required.

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
  - Customize font family (`Impact`, `Sans-Serif Bold`, `Comic`, `Monospace`, `Serif`), font size, text color, outline color & thickness, background box color & opacity, and per-layer start/end timing within the clip.
- **Speed, Loop Modes & Color Filters**:
  - Playback speed control (`0.5x` slow-mo to `2.0x` double speed).
  - Loop modes: **Infinite Loop**, **Boomerang (Forward + Reverse)**, **Reverse Playback**, or **Play Once**.
  - Live-previewed color adjustments (Brightness, Contrast, Saturation, Grayscale, Sepia) and quick filter presets (`Vivid Pop`, `Noir B&W`, `Vintage Sepia`, `High Contrast`).
- **2-Pass 256-Color Palette Optimization**:
  - Uses FFmpeg `palettegen` + `paletteuse` with Sierra dithering for crisp, vibrant GIFs.

---

## 🚀 Running the Standalone `.exe`

1. Locate **`dist/SwiffyGiffy.exe`**.
2. Share **`SwiffyGiffy.exe`** with anyone on Windows (no Python or FFmpeg installation needed on their PC).
3. Double-click **`SwiffyGiffy.exe`** — it starts the local server and automatically opens `http://127.0.0.1:5175` in your default web browser.
4. Generated GIFs are saved to `swiffygiffy_data/output_gifs` next to the `.exe` (and can also be downloaded directly from the web UI or opened via the **📁 Output Folder** button).

---

## 🛠️ Running from Source or Rebuilding the `.exe`

### Run from Python source
```powershell
.\.venv\Scripts\python.exe app.py
```

### Rebuild `dist/SwiffyGiffy.exe`
```powershell
.\.venv\Scripts\python.exe build_exe.py
```
Or double-click [`build_exe.bat`](build_exe.bat).
