import os
import sys
import json
import uuid
import time
import shutil
import socket
import tempfile
import threading
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    Response,
    abort,
)
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import yt_dlp
import imageio_ffmpeg


def get_base_dir() -> Path:
    """Return the path to bundled assets (works in dev and PyInstaller --onefile)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    """Return a writable runtime directory alongside the executable or script."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    runtime = base / "swiffygiffy_data"
    runtime.mkdir(parents=True, exist_ok=True)
    return runtime


BASE_DIR = get_base_dir()
RUNTIME_DIR = get_runtime_dir()
CACHE_DIR = RUNTIME_DIR / "video_cache"
OUTPUT_DIR = RUNTIME_DIR / "output_gifs"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_ffmpeg_path() -> str:
    """Locate the ffmpeg executable (bundled via imageio-ffmpeg or system PATH)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Check inside _MEIPASS/imageio_ffmpeg/binaries first
        meipass = Path(sys._MEIPASS)
        candidates = list(meipass.rglob("ffmpeg*.exe"))
        if candidates:
            return str(candidates[0])
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        found = shutil.which("ffmpeg")
        if found:
            return found
        raise RuntimeError("FFmpeg binary could not be located.")


app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB max upload

# In-memory registry of loaded videos & active jobs
VIDEOS_DB_FILE = CACHE_DIR / "videos_index.json"
JOBS = {}


def load_videos_db() -> dict:
    if VIDEOS_DB_FILE.exists():
        try:
            return json.loads(VIDEOS_DB_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_videos_db(db: dict):
    try:
        VIDEOS_DB_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")
    except Exception:
        pass


VIDEOS_DB = load_videos_db()


def probe_video_dimensions_and_duration(video_path: Path, ffmpeg_exe: str) -> dict:
    """Use ffmpeg -i stderr output to parse width, height, and duration."""
    cmd = [ffmpeg_exe, "-hide_banner", "-i", str(video_path)]
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    stderr = proc.stderr or ""
    import re

    width, height = 640, 360
    duration = 10.0

    dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", stderr)
    if dur_match:
        h, m, s = (
            int(dur_match.group(1)),
            int(dur_match.group(2)),
            float(dur_match.group(3)),
        )
        duration = h * 3600 + m * 60 + s

    # Match video stream resolution e.g. "Stream #0:0...: Video: ..., 1280x720"
    for line in stderr.splitlines():
        if "Video:" in line:
            res_match = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if res_match:
                width = int(res_match.group(1))
                height = int(res_match.group(2))
                break

    return {"width": width, "height": height, "duration": round(duration, 2)}


def resolve_windows_font(font_family: str, font_size: int) -> ImageFont.FreeTypeFont:
    """Resolve a TTF font on Windows (or fallback cleanly)."""
    font_map = {
        "impact": ["impact.ttf", "arialbd.ttf", "seguiemj.ttf"],
        "sans": ["arialbd.ttf", "segoeui.ttf", "arial.ttf", "calibri.ttf"],
        "meme": ["impact.ttf", "arialbd.ttf"],
        "mono": ["consolab.ttf", "consola.ttf", "courbd.ttf", "cour.ttf"],
        "serif": ["georgiab.ttf", "georgia.ttf", "timesbd.ttf", "times.ttf"],
        "comic": ["comicbd.ttf", "comic.ttf", "arialbd.ttf"],
    }
    candidates = font_map.get((font_family or "impact").lower(), font_map["impact"])
    win_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"

    for fname in candidates:
        fpath = win_fonts / fname
        if fpath.exists():
            try:
                return ImageFont.truetype(str(fpath), size=max(10, int(font_size)))
            except Exception:
                continue

    # Try direct name in Pillow
    for fname in candidates:
        try:
            return ImageFont.truetype(fname, size=max(10, int(font_size)))
        except Exception:
            continue

    try:
        return ImageFont.load_default(size=max(10, int(font_size)))
    except TypeError:
        return ImageFont.load_default()


def hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    h = (hex_color or "#FFFFFF").lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return (r, g, b, alpha)
    except Exception:
        return (255, 255, 255, alpha)


def render_text_layers_on_image(
    img: Image.Image, text_layers: list, elapsed_sec: float
) -> Image.Image:
    """Render all active text layers onto an RGBA copy of the frame."""
    if not text_layers:
        return img

    out = img.convert("RGBA")
    overlay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = out.size

    for layer in text_layers:
        raw_text = (layer.get("text") or "").strip()
        if not raw_text:
            continue

        # Check time visibility window relative to GIF clip start (in original clip seconds)
        start_offset = float(layer.get("start_offset", 0) or 0)
        end_offset = float(layer.get("end_offset", 999999) or 999999)
        if elapsed_sec < start_offset - 0.02 or elapsed_sec > end_offset + 0.02:
            continue

        uppercase = bool(layer.get("uppercase", False))
        text = raw_text.upper() if uppercase else raw_text

        # Font size is scaled relative to a reference height of 480px so it looks identical to the canvas preview
        base_font_size = float(layer.get("font_size", 36) or 36)
        scaled_font_size = max(10, int(round(base_font_size * (H / 480.0))))
        font_family = layer.get("font_family", "impact")
        font = resolve_windows_font(font_family, scaled_font_size)

        # Normalized center coordinates (0.0 to 1.0)
        norm_x = float(layer.get("x", 0.5))
        norm_y = float(layer.get("y", 0.85))
        cx = norm_x * W
        cy = norm_y * H

        stroke_width_base = float(layer.get("stroke_width", 3) or 0)
        stroke_width = max(0, int(round(stroke_width_base * (H / 480.0))))
        text_color = hex_to_rgba(layer.get("color", "#FFFFFF"), 255)
        stroke_color = hex_to_rgba(layer.get("stroke_color", "#000000"), 255)

        bg_opacity = float(layer.get("bg_opacity", 0) or 0)
        bg_color_hex = layer.get("bg_color", "#000000")

        # Measure multiline text bounding box
        bbox = draw.multiline_textbbox(
            (0, 0),
            text,
            font=font,
            stroke_width=stroke_width,
            align="center",
            spacing=4,
        )
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        tx = cx - tw / 2.0 - bbox[0]
        ty = cy - th / 2.0 - bbox[1]

        # Optional background box / pill
        if bg_opacity > 0.01:
            pad_x = max(6, int(scaled_font_size * 0.3))
            pad_y = max(4, int(scaled_font_size * 0.18))
            bg_rgba = hex_to_rgba(bg_color_hex, int(min(255, max(0, bg_opacity * 255))))
            rx0 = cx - tw / 2.0 - pad_x
            ry0 = cy - th / 2.0 - pad_y
            rx1 = cx + tw / 2.0 + pad_x
            ry1 = cy + th / 2.0 + pad_y
            draw.rounded_rectangle(
                [rx0, ry0, rx1, ry1],
                radius=max(4, int(scaled_font_size * 0.2)),
                fill=bg_rgba,
            )

        draw.multiline_text(
            (tx, ty),
            text,
            font=font,
            fill=text_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color if stroke_width > 0 else None,
            align="center",
            spacing=4,
        )

    combined = Image.alpha_composite(out, overlay)
    return combined.convert("RGB")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    try:
        ffmpeg_exe = get_ffmpeg_path()
        ffmpeg_ok = os.path.exists(ffmpeg_exe)
    except Exception as e:
        ffmpeg_exe = str(e)
        ffmpeg_ok = False
    return jsonify(
        {
            "status": "ok",
            "ffmpeg_ready": ffmpeg_ok,
            "ffmpeg_path": ffmpeg_exe,
            "output_dir": str(OUTPUT_DIR),
        }
    )


def download_youtube_worker(job_id: str, url: str):
    """Background worker to fetch and download a YouTube video for interactive editing."""
    try:
        JOBS[job_id]["status"] = "fetching_info"
        JOBS[job_id]["message"] = "Fetching video info from YouTube..."
        JOBS[job_id]["progress"] = 5

        ffmpeg_exe = get_ffmpeg_path()
        video_id = uuid.uuid4().hex[:12]
        out_template = str(CACHE_DIR / f"{video_id}.%(ext)s")

        def progress_hook(d):
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if total > 0:
                    pct = min(92, int(10 + (downloaded / total) * 80))
                else:
                    pct = 50
                speed_str = d.get("_speed_str", "").strip()
                JOBS[job_id]["status"] = "downloading"
                JOBS[job_id]["progress"] = pct
                JOBS[job_id]["message"] = (
                    f"Downloading video stream ({pct}%) {speed_str}".strip()
                )
            elif d.get("status") == "finished":
                JOBS[job_id]["status"] = "processing"
                JOBS[job_id]["progress"] = 95
                JOBS[job_id]["message"] = "Finalizing video container..."

        ydl_opts = {
            "format": (
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
                "best[height<=720][ext=mp4]/"
                "bestvideo[height<=720]+bestaudio/"
                "best[height<=720]/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": out_template,
            "ffmpeg_location": ffmpeg_exe,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = Path(ydl.prepare_filename(info))
            if not final_path.exists():
                mp4_candidate = CACHE_DIR / f"{video_id}.mp4"
                if mp4_candidate.exists():
                    final_path = mp4_candidate
                else:
                    matches = list(CACHE_DIR.glob(f"{video_id}.*"))
                    if matches:
                        final_path = matches[0]

        # Ensure browser-compatible H.264 MP4 container if needed
        probed = probe_video_dimensions_and_duration(final_path, ffmpeg_exe)
        duration = float(info.get("duration") or probed["duration"] or 10.0)
        width = int(info.get("width") or probed["width"] or 640)
        height = int(info.get("height") or probed["height"] or 360)

        meta = {
            "video_id": video_id,
            "title": info.get("title") or "YouTube Video",
            "uploader": info.get("uploader") or info.get("channel") or "YouTube",
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "thumbnail": info.get("thumbnail") or "",
            "webpage_url": url,
            "filepath": str(final_path),
            "created_at": datetime.now().isoformat(),
        }
        VIDEOS_DB[video_id] = meta
        save_videos_db(VIDEOS_DB)

        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["message"] = "Video ready!"
        JOBS[job_id]["video"] = meta

    except Exception as exc:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["message"] = f"Failed to load YouTube video: {str(exc)}"


@app.route("/api/load-youtube", methods=["POST"])
def api_load_youtube():
    data = request.get_json(force=True, silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Please enter a valid YouTube URL."}), 400

    # Check if this exact URL is already cached and file exists
    for vid, meta in list(VIDEOS_DB.items()):
        if meta.get("webpage_url") == url and Path(meta.get("filepath", "")).exists():
            job_id = uuid.uuid4().hex
            JOBS[job_id] = {
                "status": "completed",
                "progress": 100,
                "message": "Loaded from local cache!",
                "video": meta,
            }
            return jsonify({"job_id": job_id})

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "status": "starting",
        "progress": 2,
        "message": "Initializing YouTube downloader...",
    }
    thread = threading.Thread(
        target=download_youtube_worker, args=(job_id, url), daemon=True
    )
    thread.start()
    return jsonify({"job_id": job_id})


@app.route("/api/job/<job_id>")
def api_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/upload-video", methods=["POST"])
def api_upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No video file provided."}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename."}), 400

    ext = Path(f.filename).suffix.lower() or ".mp4"
    if ext not in {".mp4", ".webm", ".mkv", ".mov", ".avi", ".m4v"}:
        return jsonify({"error": f"Unsupported file extension: {ext}"}), 400

    video_id = uuid.uuid4().hex[:12]
    save_path = CACHE_DIR / f"{video_id}{ext}"
    f.save(str(save_path))

    ffmpeg_exe = get_ffmpeg_path()
    # If not mp4/webm, transcode to fast mp4 for smooth browser playback
    if ext not in {".mp4", ".webm"}:
        mp4_path = CACHE_DIR / f"{video_id}.mp4"
        cmd = [
            ffmpeg_exe,
            "-y",
            "-hide_banner",
            "-i",
            str(save_path),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(mp4_path),
        ]
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if mp4_path.exists():
            try:
                save_path.unlink()
            except Exception:
                pass
            save_path = mp4_path

    probed = probe_video_dimensions_and_duration(save_path, ffmpeg_exe)
    meta = {
        "video_id": video_id,
        "title": Path(f.filename).stem,
        "uploader": "Local File",
        "duration": probed["duration"],
        "width": probed["width"],
        "height": probed["height"],
        "thumbnail": "",
        "webpage_url": f"local://{f.filename}",
        "filepath": str(save_path),
        "created_at": datetime.now().isoformat(),
    }
    VIDEOS_DB[video_id] = meta
    save_videos_db(VIDEOS_DB)
    return jsonify({"video": meta})


@app.route("/api/video/<video_id>")
def stream_video(video_id: str):
    """Stream video file with HTTP Range Request support for instant scrubbing."""
    meta = VIDEOS_DB.get(video_id)
    if not meta:
        abort(404)
    video_path = Path(meta["filepath"])
    if not video_path.exists():
        abort(404)

    file_size = video_path.stat().st_size
    range_header = request.headers.get("Range", None)

    ext = video_path.suffix.lower()
    mime = "video/webm" if ext == ".webm" else "video/mp4"

    if not range_header:
        return send_file(str(video_path), mimetype=mime, conditional=True)

    import re

    m = re.search(r"bytes=(\d+)-(\d*)", range_header)
    if not m:
        return send_file(str(video_path), mimetype=mime, conditional=True)

    byte1 = int(m.group(1))
    byte2 = int(m.group(2)) if m.group(2) else file_size - 1
    byte2 = min(byte2, file_size - 1)
    length = byte2 - byte1 + 1

    with open(video_path, "rb") as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data, 206, mimetype=mime, direct_passthrough=True)
    rv.headers.add("Content-Range", f"bytes {byte1}-{byte2}/{file_size}")
    rv.headers.add("Accept-Ranges", "bytes")
    rv.headers.add("Content-Length", str(length))
    return rv


@app.route("/api/generate-gif", methods=["POST"])
def api_generate_gif():
    """
    Generate a high-quality GIF from the selected video segment with:
    - Start time & End time (trim)
    - Crop rectangle (normalized x, y, w, h)
    - Resolution scaling (width)
    - Frame rate (FPS) & Playback speed
    - Color filters (brightness, contrast, saturation, grayscale, sepia)
    - Multi-layer text overlays with outlines, fonts, background boxes, and time offsets
    - Loop modes (normal, bounce/boomerang, reverse, play-once)
    """
    data = request.get_json(force=True, silent=True) or {}
    video_id = data.get("video_id")
    meta = VIDEOS_DB.get(video_id)
    if not meta or not Path(meta.get("filepath", "")).exists():
        return jsonify({"error": "Source video not found. Please reload the video."}), 404

    video_path = Path(meta["filepath"])
    src_w = int(meta.get("width") or 640)
    src_h = int(meta.get("height") or 360)
    vid_duration = float(meta.get("duration") or 60.0)

    start_time = max(0.0, float(data.get("start_time", 0.0) or 0.0))
    end_time = float(data.get("end_time", min(5.0, vid_duration)) or min(5.0, vid_duration))
    if end_time <= start_time:
        end_time = min(vid_duration, start_time + 1.0)
    clip_duration = max(0.1, min(60.0, end_time - start_time))

    fps = max(4, min(30, int(data.get("fps", 15) or 15)))
    speed = max(0.25, min(4.0, float(data.get("speed", 1.0) or 1.0)))
    target_width = int(data.get("width", 480) or 480)
    loop_mode = (data.get("loop_mode") or "normal").lower()
    quality = (data.get("quality") or "high").lower()

    crop_cfg = data.get("crop") or {}
    crop_enabled = bool(crop_cfg.get("enabled", False))

    filters_cfg = data.get("filters") or {}
    brightness = float(filters_cfg.get("brightness", 0.0) or 0.0)  # -0.5 to 0.5
    contrast = float(filters_cfg.get("contrast", 1.0) or 1.0)  # 0.5 to 2.0
    saturation = float(filters_cfg.get("saturation", 1.0) or 1.0)  # 0.0 to 3.0
    grayscale = bool(filters_cfg.get("grayscale", False))
    sepia = bool(filters_cfg.get("sepia", False))

    text_layers = data.get("text_layers") or []

    ffmpeg_exe = get_ffmpeg_path()

    # Build FFmpeg filter chain for extracting processed frames
    vf_parts = []

    # 1. Speed adjustment
    if abs(speed - 1.0) > 0.01:
        vf_parts.append(f"setpts={1.0 / speed:.4f}*PTS")

    # 2. FPS
    vf_parts.append(f"fps={fps}")

    # 3. Crop
    if crop_enabled:
        nx = max(0.0, min(0.95, float(crop_cfg.get("x", 0.0))))
        ny = max(0.0, min(0.95, float(crop_cfg.get("y", 0.0))))
        nw = max(0.05, min(1.0 - nx, float(crop_cfg.get("w", 1.0))))
        nh = max(0.05, min(1.0 - ny, float(crop_cfg.get("h", 1.0))))
        cw = max(16, int(round(src_w * nw)) // 2 * 2)
        ch = max(16, int(round(src_h * nh)) // 2 * 2)
        cx = max(0, min(src_w - cw, int(round(src_w * nx))))
        cy = max(0, min(src_h - ch, int(round(src_h * ny))))
        vf_parts.append(f"crop={cw}:{ch}:{cx}:{cy}")

    # 4. Scale to target width preserving aspect ratio
    if target_width > 0:
        even_w = max(64, (target_width // 2) * 2)
        vf_parts.append(f"scale={even_w}:-2:flags=lanczos")

    # 5. Color adjustments
    if grayscale:
        saturation = 0.0
    if (
        abs(brightness) > 0.01
        or abs(contrast - 1.0) > 0.01
        or abs(saturation - 1.0) > 0.01
    ):
        vf_parts.append(
            f"eq=brightness={brightness:.2f}:contrast={contrast:.2f}:saturation={saturation:.2f}"
        )
    if sepia:
        vf_parts.append(
            "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        )

    vf_chain = ",".join(vf_parts)

    work_dir = Path(tempfile.mkdtemp(prefix="swiffygiffy_render_", dir=str(CACHE_DIR)))
    try:
        frames_pattern = str(work_dir / "frame_%05d.png")
        extract_cmd = [
            ffmpeg_exe,
            "-y",
            "-hide_banner",
            "-ss",
            f"{start_time:.3f}",
            "-t",
            f"{clip_duration:.3f}",
            "-i",
            str(video_path),
            "-vf",
            vf_chain,
            frames_pattern,
        ]
        proc = subprocess.run(
            extract_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        frame_files = sorted(work_dir.glob("frame_*.png"))
        if not frame_files:
            return (
                jsonify(
                    {
                        "error": "No frames could be extracted from the selected time range.",
                        "details": proc.stderr[-500:] if proc.stderr else "",
                    }
                ),
                400,
            )

        # Render text layers on each extracted frame using Pillow
        has_active_text = any((l.get("text") or "").strip() for l in text_layers)
        if has_active_text:
            for idx, fpath in enumerate(frame_files):
                # Elapsed original clip seconds corresponding to this frame
                elapsed_clip_sec = (idx / float(fps)) * speed
                with Image.open(fpath) as im:
                    rendered = render_text_layers_on_image(
                        im, text_layers, elapsed_clip_sec
                    )
                    rendered.save(fpath, format="PNG")

        # Handle loop modes (reverse, bounce/boomerang) by sequencing frame files
        sequenced_dir = work_dir / "seq"
        sequenced_dir.mkdir(exist_ok=True)

        if loop_mode == "reverse":
            ordered_frames = list(reversed(frame_files))
        elif loop_mode == "bounce" and len(frame_files) > 2:
            ordered_frames = list(frame_files) + list(reversed(frame_files[1:-1]))
        else:
            ordered_frames = list(frame_files)

        for idx, src_frame in enumerate(ordered_frames, start=1):
            dst_frame = sequenced_dir / f"seq_{idx:05d}.png"
            shutil.copy2(src_frame, dst_frame)

        # Assemble final high-quality GIF using FFmpeg 2-pass palettegen + paletteuse
        gif_id = uuid.uuid4().hex[:8]
        safe_stem = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in (meta.get("title") or "clip")
        )[:32].strip("_") or "clip"
        out_filename = f"{safe_stem}_{gif_id}.gif"
        out_gif_path = OUTPUT_DIR / out_filename

        dither_mode = (
            "sierra2_4a"
            if quality == "high"
            else ("bayer:bayer_scale=3" if quality == "medium" else "none")
        )
        max_colors = 256 if quality == "high" else (128 if quality == "medium" else 64)
        loop_flag = "-1" if loop_mode == "once" else "0"

        seq_pattern = str(sequenced_dir / "seq_%05d.png")
        palette_path = str(work_dir / "palette.png")

        # Pass 1: generate optimal color palette
        pal_cmd = [
            ffmpeg_exe,
            "-y",
            "-hide_banner",
            "-framerate",
            str(fps),
            "-i",
            seq_pattern,
            "-vf",
            f"palettegen=max_colors={max_colors}:stats_mode=diff",
            palette_path,
        ]
        subprocess.run(
            pal_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        # Pass 2: encode GIF using the generated palette
        gif_cmd = [
            ffmpeg_exe,
            "-y",
            "-hide_banner",
            "-framerate",
            str(fps),
            "-i",
            seq_pattern,
            "-i",
            palette_path,
            "-lavfi",
            f"paletteuse=dither={dither_mode}:diff_mode=rectangle",
            "-loop",
            loop_flag,
            str(out_gif_path),
        ]
        gif_proc = subprocess.run(
            gif_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if not out_gif_path.exists():
            return (
                jsonify(
                    {
                        "error": "Failed to encode final GIF.",
                        "details": gif_proc.stderr[-500:] if gif_proc.stderr else "",
                    }
                ),
                500,
            )

        with Image.open(out_gif_path) as gim:
            gw, gh = gim.size

        size_bytes = out_gif_path.stat().st_size
        return jsonify(
            {
                "filename": out_filename,
                "url": f"/api/output/{out_filename}",
                "width": gw,
                "height": gh,
                "frames": len(ordered_frames),
                "fps": fps,
                "duration": round(len(ordered_frames) / float(fps), 2),
                "size_bytes": size_bytes,
                "size_human": format_bytes(size_bytes),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"


@app.route("/api/gifs", methods=["GET"])
def api_list_gifs():
    items = []
    for p in sorted(
        OUTPUT_DIR.glob("*.gif"), key=lambda x: x.stat().st_mtime, reverse=True
    ):
        try:
            stat = p.stat()
            with Image.open(p) as im:
                w, h = im.size
                n_frames = getattr(im, "n_frames", 1)
            items.append(
                {
                    "filename": p.name,
                    "url": f"/api/output/{p.name}",
                    "width": w,
                    "height": h,
                    "frames": n_frames,
                    "size_bytes": stat.st_size,
                    "size_human": format_bytes(stat.st_size),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )
        except Exception:
            continue
    return jsonify({"gifs": items})


@app.route("/api/output/<filename>", methods=["GET"])
def serve_output_gif(filename: str):
    safe_name = Path(filename).name
    target = OUTPUT_DIR / safe_name
    if not target.exists():
        abort(404)
    download = request.args.get("download") == "1"
    return send_file(
        str(target),
        mimetype="image/gif",
        as_attachment=download,
        download_name=safe_name if download else None,
    )


@app.route("/api/output/<filename>", methods=["DELETE"])
def delete_output_gif(filename: str):
    safe_name = Path(filename).name
    target = OUTPUT_DIR / safe_name
    if target.exists():
        target.unlink()
    return jsonify({"deleted": safe_name})


@app.route("/api/open-output-folder", methods=["POST"])
def api_open_output_folder():
    try:
        if os.name == "nt":
            os.startfile(str(OUTPUT_DIR))
        return jsonify({"opened": str(OUTPUT_DIR)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def find_free_port(preferred: int = 5175) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    port = int(os.environ.get("SWIFFYGIFFY_PORT", find_free_port(5175)))
    url = f"http://127.0.0.1:{port}"
    no_browser = os.environ.get("SWIFFYGIFFY_NO_BROWSER") == "1"

    print("=" * 62)
    print("  SwiffyGiffy - Local YouTube to GIF Studio")
    print(f"  Server URL : {url}")
    print(f"  Output Dir : {OUTPUT_DIR}")
    print("  Press Ctrl+C in this window to stop the server.")
    print("=" * 62)

    if not no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()

