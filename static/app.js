(() => {
  // Application State
  const state = {
    video: null, // { video_id, title, duration, width, height, ... }
    startTime: 0.0,
    endTime: 5.0,
    fps: 15,
    speed: 1.0,
    outputWidth: 480,
    loopMode: "normal",
    quality: "high",
    crop: {
      enabled: false,
      aspect: "free",
      x: 0.1, // normalized 0..1
      y: 0.1,
      w: 0.8,
      h: 0.8,
    },
    filters: {
      brightness: 0.0,
      contrast: 1.0,
      saturation: 1.0,
      grayscale: false,
      sepia: false,
    },
    textLayers: [],
    selectedTextId: null,
  };

  // DOM Elements
  const ytForm = document.getElementById("yt-form");
  const ytUrlInput = document.getElementById("yt-url-input");
  const loadYtBtn = document.getElementById("load-yt-btn");
  const localVideoInput = document.getElementById("local-video-input");
  const openFolderBtn = document.getElementById("open-folder-btn");

  const loadingBanner = document.getElementById("loading-banner");
  const loadingMessage = document.getElementById("loading-message");
  const loadingProgressBar = document.getElementById("loading-progress-bar");

  const videoTitleBadge = document.getElementById("video-title-badge");
  const videoMetaBadge = document.getElementById("video-meta-badge");
  const emptyStage = document.getElementById("empty-stage");
  const videoContainer = document.getElementById("video-container");
  const videoPlayer = document.getElementById("video-player");
  const interactiveOverlay = document.getElementById("interactive-overlay");

  const cropBox = document.getElementById("crop-box");
  const cropDimensionsTag = document.getElementById("crop-dimensions-tag");
  const textOverlaysStage = document.getElementById("text-overlays-stage");

  // Timeline DOM
  const playPauseBtn = document.getElementById("play-pause-btn");
  const restartClipBtn = document.getElementById("restart-clip-btn");
  const loopPreviewToggle = document.getElementById("loop-preview-toggle");
  const currentTimeLabel = document.getElementById("current-time-label");
  const clipDurationLabel = document.getElementById("clip-duration-label");
  const estFramesLabel = document.getElementById("est-frames-label");
  const setStartCurrentBtn = document.getElementById("set-start-current-btn");
  const setEndCurrentBtn = document.getElementById("set-end-current-btn");

  const timelineTrack = document.getElementById("timeline-track");
  const timelineUnselectedLeft = document.getElementById("timeline-unselected-left");
  const timelineSelectedRange = document.getElementById("timeline-selected-range");
  const timelineUnselectedRight = document.getElementById("timeline-unselected-right");
  const handleStart = document.getElementById("handle-start");
  const handleEnd = document.getElementById("handle-end");
  const timelinePlayhead = document.getElementById("timeline-playhead");
  const tickStart = document.getElementById("tick-start");
  const tickMid = document.getElementById("tick-mid");
  const tickEnd = document.getElementById("tick-end");

  // Tab 1: Length & Size
  const startTimeInput = document.getElementById("start-time-input");
  const endTimeInput = document.getElementById("end-time-input");
  const outputWidthSelect = document.getElementById("output-width-select");
  const fpsSelect = document.getElementById("fps-select");
  const speedSelect = document.getElementById("speed-select");
  const loopModeSelect = document.getElementById("loop-mode-select");
  const qualitySelect = document.getElementById("quality-select");

  // Tab 2: Crop
  const cropEnableToggle = document.getElementById("crop-enable-toggle");
  const cropXInput = document.getElementById("crop-x-input");
  const cropYInput = document.getElementById("crop-y-input");
  const cropWInput = document.getElementById("crop-w-input");
  const cropHInput = document.getElementById("crop-h-input");
  const centerCropBtn = document.getElementById("center-crop-btn");
  const resetCropBtn = document.getElementById("reset-crop-btn");

  // Tab 3: Text Layers
  const addTopTextBtn = document.getElementById("add-top-text-btn");
  const addBottomTextBtn = document.getElementById("add-bottom-text-btn");
  const textLayersList = document.getElementById("text-layers-list");
  const textEditorPanel = document.getElementById("text-editor-panel");
  const textContentInput = document.getElementById("text-content-input");
  const textFontSelect = document.getElementById("text-font-select");
  const textSizeInput = document.getElementById("text-size-input");
  const fontSizeVal = document.getElementById("font-size-val");
  const textColorInput = document.getElementById("text-color-input");
  const textStrokeColorInput = document.getElementById("text-stroke-color-input");
  const textStrokeWidthInput = document.getElementById("text-stroke-width-input");
  const textBgColorInput = document.getElementById("text-bg-color-input");
  const textBgOpacityInput = document.getElementById("text-bg-opacity-input");
  const bgOpacityVal = document.getElementById("bg-opacity-val");
  const textStartOffsetInput = document.getElementById("text-start-offset-input");
  const textEndOffsetInput = document.getElementById("text-end-offset-input");
  const textUppercaseInput = document.getElementById("text-uppercase-input");
  const deleteTextLayerBtn = document.getElementById("delete-text-layer-btn");

  // Tab 4: Filters
  const filterBrightness = document.getElementById("filter-brightness");
  const filterContrast = document.getElementById("filter-contrast");
  const filterSaturation = document.getElementById("filter-saturation");
  const filterGrayscale = document.getElementById("filter-grayscale");
  const filterSepia = document.getElementById("filter-sepia");
  const brightnessVal = document.getElementById("brightness-val");
  const contrastVal = document.getElementById("contrast-val");
  const saturationVal = document.getElementById("saturation-val");

  // Export & Gallery
  const generateGifBtn = document.getElementById("generate-gif-btn");
  const exportStatus = document.getElementById("export-status");
  const latestResultCard = document.getElementById("latest-result-card");
  const resultMetaBadge = document.getElementById("result-meta-badge");
  const resultGifImg = document.getElementById("result-gif-img");
  const resultDownloadBtn = document.getElementById("result-download-btn");
  const galleryGrid = document.getElementById("gallery-grid");
  const galleryCount = document.getElementById("gallery-count");

  // Helpers
  function formatTimeMMSS(sec) {
    const s = Math.max(0, Math.floor(sec));
    const mins = Math.floor(s / 60);
    const rem = s % 60;
    return `${mins}:${rem.toString().padStart(2, "0")}`;
  }

  function showLoading(msg, pct = 10) {
    loadingBanner.classList.remove("hidden");
    loadingMessage.textContent = msg;
    loadingProgressBar.style.width = `${pct}%`;
  }

  function hideLoading() {
    loadingBanner.classList.add("hidden");
  }

  // Tab Switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const pane = document.getElementById(btn.dataset.tab);
      if (pane) pane.classList.add("active");
    });
  });

  // Load YouTube Video
  ytForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = ytUrlInput.value.trim();
    if (!url) return;

    loadYtBtn.disabled = true;
    showLoading("Connecting to YouTube...", 8);

    try {
      const res = await fetch("/api/load-youtube", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Failed to load YouTube URL");
      }
      pollYoutubeJob(data.job_id);
    } catch (err) {
      hideLoading();
      loadYtBtn.disabled = false;
      alert(err.message);
    }
  });

  async function pollYoutubeJob(jobId) {
    try {
      const res = await fetch(`/api/job/${jobId}`);
      const job = await res.json();
      if (!res.ok || job.status === "error") {
        throw new Error(job.message || job.error || "Download failed");
      }
      showLoading(job.message || "Downloading...", job.progress || 25);

      if (job.status === "completed" && job.video) {
        hideLoading();
        loadYtBtn.disabled = false;
        onVideoLoaded(job.video);
      } else {
        setTimeout(() => pollYoutubeJob(jobId), 600);
      }
    } catch (err) {
      hideLoading();
      loadYtBtn.disabled = false;
      alert(err.message);
    }
  }

  // Upload Local Video File
  localVideoInput.addEventListener("change", async () => {
    const file = localVideoInput.files[0];
    if (!file) return;

    showLoading(`Uploading & preparing ${file.name}...`, 40);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-video", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      hideLoading();
      localVideoInput.value = "";
      if (!res.ok || data.error) {
        throw new Error(data.error || "Upload failed");
      }
      onVideoLoaded(data.video);
    } catch (err) {
      hideLoading();
      localVideoInput.value = "";
      alert(err.message);
    }
  });

  // Open Output Folder
  openFolderBtn.addEventListener("click", async () => {
    await fetch("/api/open-output-folder", { method: "POST" });
  });

  // Initialize Loaded Video in Studio
  function onVideoLoaded(videoMeta) {
    state.video = videoMeta;
    const dur = Math.max(0.5, Number(videoMeta.duration) || 10);

    state.startTime = 0.0;
    state.endTime = Math.min(dur, 5.0);

    videoTitleBadge.textContent = videoMeta.title || "Loaded Video";
    videoMetaBadge.textContent = `${videoMeta.width}×${videoMeta.height} • ${formatTimeMMSS(dur)}`;

    emptyStage.classList.add("hidden");
    videoContainer.classList.remove("hidden");

    videoPlayer.src = `/api/video/${videoMeta.video_id}`;
    videoPlayer.load();

    playPauseBtn.disabled = false;
    restartClipBtn.disabled = false;
    setStartCurrentBtn.disabled = false;
    setEndCurrentBtn.disabled = false;
    generateGifBtn.disabled = false;

    startTimeInput.max = dur.toFixed(1);
    endTimeInput.max = dur.toFixed(1);

    tickStart.textContent = "0:00";
    tickMid.textContent = formatTimeMMSS(dur / 2);
    tickEnd.textContent = formatTimeMMSS(dur);

    syncTimingUI();
    updateCropOverlayUI();
    renderStageTextOverlays();
  }

  // Video Player Events
  videoPlayer.addEventListener("loadedmetadata", () => {
    if (state.video && videoPlayer.duration && isFinite(videoPlayer.duration)) {
      state.video.duration = Number(videoPlayer.duration.toFixed(2));
      if (state.endTime > state.video.duration) {
        state.endTime = Math.min(state.video.duration, 5.0);
      }
      tickMid.textContent = formatTimeMMSS(state.video.duration / 2);
      tickEnd.textContent = formatTimeMMSS(state.video.duration);
      syncTimingUI();
    }
    videoPlayer.currentTime = state.startTime;
    videoPlayer.playbackRate = state.speed;
    updateCropOverlayUI();
    renderStageTextOverlays();
  });

  videoPlayer.addEventListener("play", () => {
    playPauseBtn.textContent = "⏸";
  });

  videoPlayer.addEventListener("pause", () => {
    playPauseBtn.textContent = "▶";
  });

  videoPlayer.addEventListener("timeupdate", () => {
    if (!state.video) return;
    const cur = videoPlayer.currentTime;
    currentTimeLabel.textContent = `${cur.toFixed(2)}s`;

    // Loop within [startTime, endTime] if Loop Trim Range is enabled
    if (loopPreviewToggle.checked && cur >= state.endTime) {
      videoPlayer.currentTime = state.startTime;
      if (!videoPlayer.paused) {
        videoPlayer.play().catch(() => {});
      }
    }

    updatePlayheadUI(cur);
    updateTextVisibilityByTime(cur);
  });

  playPauseBtn.addEventListener("click", () => {
    if (!state.video) return;
    if (videoPlayer.paused) {
      if (
        videoPlayer.currentTime < state.startTime ||
        videoPlayer.currentTime >= state.endTime
      ) {
        videoPlayer.currentTime = state.startTime;
      }
      videoPlayer.play();
    } else {
      videoPlayer.pause();
    }
  });

  restartClipBtn.addEventListener("click", () => {
    if (!state.video) return;
    videoPlayer.currentTime = state.startTime;
  });

  setStartCurrentBtn.addEventListener("click", () => {
    if (!state.video) return;
    const cur = Number(videoPlayer.currentTime.toFixed(2));
    state.startTime = Math.min(cur, state.endTime - 0.2);
    syncTimingUI();
  });

  setEndCurrentBtn.addEventListener("click", () => {
    if (!state.video) return;
    const cur = Number(videoPlayer.currentTime.toFixed(2));
    state.endTime = Math.max(cur, state.startTime + 0.2);
    syncTimingUI();
  });

  // Sync Timing Controls & Timeline Bar
  function syncTimingUI() {
    const dur = state.video ? state.video.duration : 10.0;
    state.startTime = Math.max(0, Math.min(state.startTime, dur - 0.2));
    state.endTime = Math.max(state.startTime + 0.2, Math.min(state.endTime, dur));

    startTimeInput.value = state.startTime.toFixed(1);
    endTimeInput.value = state.endTime.toFixed(1);

    const clipLen = Math.max(0.1, state.endTime - state.startTime);
    const effectiveLen = clipLen / state.speed;
    let frames = Math.max(1, Math.round(effectiveLen * state.fps));
    if (state.loopMode === "bounce" && frames > 2) {
      frames = frames * 2 - 2;
    }

    clipDurationLabel.textContent = `${clipLen.toFixed(2)}s`;
    estFramesLabel.textContent = `${frames}`;

    // Timeline bar percentages
    const startPct = (state.startTime / dur) * 100;
    const endPct = (state.endTime / dur) * 100;

    timelineUnselectedLeft.style.width = `${startPct}%`;
    timelineSelectedRange.style.left = `${startPct}%`;
    timelineSelectedRange.style.width = `${Math.max(0.5, endPct - startPct)}%`;
    timelineUnselectedRight.style.width = `${Math.max(0, 100 - endPct)}%`;

    handleStart.style.left = `${startPct}%`;
    handleEnd.style.left = `${endPct}%`;

    updatePlayheadUI(videoPlayer.currentTime || state.startTime);
  }

  function updatePlayheadUI(currentTime) {
    const dur = state.video ? state.video.duration : 10.0;
    const pct = Math.max(0, Math.min(100, (currentTime / dur) * 100));
    timelinePlayhead.style.left = `${pct}%`;
  }

  // Timeline Interactive Dragging (Start Handle, End Handle, or Track Scrub)
  let activeTimelineDrag = null; // "start" | "end" | "scrub"

  handleStart.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    activeTimelineDrag = "start";
  });

  handleEnd.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    activeTimelineDrag = "end";
  });

  timelineTrack.addEventListener("mousedown", (e) => {
    if (!state.video) return;
    activeTimelineDrag = "scrub";
    handleTimelineMouseMove(e);
  });

  window.addEventListener("mousemove", (e) => {
    if (activeTimelineDrag) {
      handleTimelineMouseMove(e);
    }
    if (activeCropDrag) {
      handleCropMouseMove(e);
    }
    if (activeTextDrag) {
      handleTextMouseMove(e);
    }
  });

  window.addEventListener("mouseup", () => {
    activeTimelineDrag = null;
    activeCropDrag = null;
    activeTextDrag = null;
  });

  function handleTimelineMouseMove(e) {
    if (!state.video) return;
    const rect = timelineTrack.getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const timeVal = Number((ratio * state.video.duration).toFixed(2));

    if (activeTimelineDrag === "start") {
      state.startTime = Math.min(timeVal, state.endTime - 0.2);
      videoPlayer.currentTime = state.startTime;
      syncTimingUI();
    } else if (activeTimelineDrag === "end") {
      state.endTime = Math.max(timeVal, state.startTime + 0.2);
      videoPlayer.currentTime = Math.max(state.startTime, state.endTime - 0.3);
      syncTimingUI();
    } else if (activeTimelineDrag === "scrub") {
      videoPlayer.currentTime = timeVal;
      updatePlayheadUI(timeVal);
    }
  }

  // Timing Inputs & Step Buttons
  startTimeInput.addEventListener("change", () => {
    state.startTime = parseFloat(startTimeInput.value) || 0;
    if (state.video) videoPlayer.currentTime = state.startTime;
    syncTimingUI();
  });

  endTimeInput.addEventListener("change", () => {
    state.endTime = parseFloat(endTimeInput.value) || state.startTime + 1;
    syncTimingUI();
  });

  document.querySelectorAll(".step-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.stepTarget;
      const step = parseFloat(btn.dataset.step);
      if (targetId === "start-time-input") {
        state.startTime = Math.max(0, state.startTime + step);
        if (state.video) videoPlayer.currentTime = state.startTime;
      } else {
        state.endTime = Math.max(state.startTime + 0.2, state.endTime + step);
      }
      syncTimingUI();
    });
  });

  document.querySelectorAll("[data-set-duration]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const len = parseFloat(btn.dataset.setDuration);
      const maxDur = state.video ? state.video.duration : 60;
      state.endTime = Math.min(maxDur, state.startTime + len);
      syncTimingUI();
    });
  });

  outputWidthSelect.addEventListener("change", () => {
    state.outputWidth = parseInt(outputWidthSelect.value, 10);
  });

  fpsSelect.addEventListener("change", () => {
    state.fps = parseInt(fpsSelect.value, 10);
    syncTimingUI();
  });

  speedSelect.addEventListener("change", () => {
    state.speed = parseFloat(speedSelect.value);
    if (videoPlayer) videoPlayer.playbackRate = state.speed;
    syncTimingUI();
  });

  loopModeSelect.addEventListener("change", () => {
    state.loopMode = loopModeSelect.value;
    syncTimingUI();
  });

  qualitySelect.addEventListener("change", () => {
    state.quality = qualitySelect.value;
  });

  // =========================================================================
  // INTERACTIVE CROP SYSTEM
  // =========================================================================
  let activeCropDrag = null; // { mode: 'move'|'nw'|..., startX, startY, origCrop }

  cropEnableToggle.addEventListener("change", () => {
    state.crop.enabled = cropEnableToggle.checked;
    updateCropOverlayUI();
  });

  document.querySelectorAll("[data-aspect]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-aspect]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.crop.aspect = btn.dataset.aspect;
      state.crop.enabled = true;
      cropEnableToggle.checked = true;
      applyAspectRatioToCrop(state.crop.aspect);
      updateCropOverlayUI();
    });
  });

  function applyAspectRatioToCrop(aspect) {
    if (aspect === "free" || !state.video) return;
    const [aw, ah] = aspect.split(":").map(Number);
    const targetRatio = aw / ah;
    const videoRatio = state.video.width / state.video.height;

    // Normalized w/h ratio relative to video dimensions
    const normRatio = targetRatio / videoRatio;
    let w = 0.75;
    let h = w / normRatio;
    if (h > 0.85) {
      h = 0.85;
      w = h * normRatio;
    }
    state.crop.w = Math.min(1, Math.max(0.1, w));
    state.crop.h = Math.min(1, Math.max(0.1, h));
    state.crop.x = (1 - state.crop.w) / 2;
    state.crop.y = (1 - state.crop.h) / 2;
  }

  centerCropBtn.addEventListener("click", () => {
    state.crop.x = (1 - state.crop.w) / 2;
    state.crop.y = (1 - state.crop.h) / 2;
    updateCropOverlayUI();
  });

  resetCropBtn.addEventListener("click", () => {
    state.crop.x = 0;
    state.crop.y = 0;
    state.crop.w = 1;
    state.crop.h = 1;
    updateCropOverlayUI();
  });

  [cropXInput, cropYInput, cropWInput, cropHInput].forEach((inp) => {
    inp.addEventListener("change", () => {
      state.crop.x = Math.max(0, Math.min(0.9, (parseFloat(cropXInput.value) || 0) / 100));
      state.crop.y = Math.max(0, Math.min(0.9, (parseFloat(cropYInput.value) || 0) / 100));
      state.crop.w = Math.max(0.05, Math.min(1 - state.crop.x, (parseFloat(cropWInput.value) || 80) / 100));
      state.crop.h = Math.max(0.05, Math.min(1 - state.crop.y, (parseFloat(cropHInput.value) || 80) / 100));
      state.crop.enabled = true;
      cropEnableToggle.checked = true;
      updateCropOverlayUI();
    });
  });

  function updateCropOverlayUI() {
    if (!state.crop.enabled) {
      cropBox.classList.add("hidden");
    } else {
      cropBox.classList.remove("hidden");
      cropBox.style.left = `${(state.crop.x * 100).toFixed(2)}%`;
      cropBox.style.top = `${(state.crop.y * 100).toFixed(2)}%`;
      cropBox.style.width = `${(state.crop.w * 100).toFixed(2)}%`;
      cropBox.style.height = `${(state.crop.h * 100).toFixed(2)}%`;

      if (state.video) {
        const pxW = Math.round(state.video.width * state.crop.w);
        const pxH = Math.round(state.video.height * state.crop.h);
        cropDimensionsTag.textContent = `${pxW} × ${pxH} px`;
      } else {
        cropDimensionsTag.textContent = `${Math.round(state.crop.w * 100)}% × ${Math.round(state.crop.h * 100)}%`;
      }
    }

    cropXInput.value = Math.round(state.crop.x * 100);
    cropYInput.value = Math.round(state.crop.y * 100);
    cropWInput.value = Math.round(state.crop.w * 100);
    cropHInput.value = Math.round(state.crop.h * 100);
  }

  cropBox.addEventListener("mousedown", (e) => {
    e.stopPropagation();
    const handle = e.target.dataset.handle;
    activeCropDrag = {
      mode: handle || "move",
      startX: e.clientX,
      startY: e.clientY,
      orig: { ...state.crop },
    };
  });

  function handleCropMouseMove(e) {
    const rect = interactiveOverlay.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const dx = (e.clientX - activeCropDrag.startX) / rect.width;
    const dy = (e.clientY - activeCropDrag.startY) / rect.height;
    const o = activeCropDrag.orig;
    const mode = activeCropDrag.mode;

    if (mode === "move") {
      state.crop.x = Math.max(0, Math.min(1 - o.w, o.x + dx));
      state.crop.y = Math.max(0, Math.min(1 - o.h, o.y + dy));
    } else {
      let x = o.x,
        y = o.y,
        w = o.w,
        h = o.h;
      if (mode.includes("e")) w = Math.max(0.08, Math.min(1 - x, o.w + dx));
      if (mode.includes("s")) h = Math.max(0.08, Math.min(1 - y, o.h + dy));
      if (mode.includes("w")) {
        const nx = Math.max(0, Math.min(o.x + o.w - 0.08, o.x + dx));
        w = o.w + (o.x - nx);
        x = nx;
      }
      if (mode.includes("n")) {
        const ny = Math.max(0, Math.min(o.y + o.h - 0.08, o.y + dy));
        h = o.h + (o.y - ny);
        y = ny;
      }
      state.crop.x = x;
      state.crop.y = y;
      state.crop.w = w;
      state.crop.h = h;
    }
    updateCropOverlayUI();
  }

  // =========================================================================
  // MULTI-LAYER DRAGGABLE TEXT OVERLAYS
  // =========================================================================
  let activeTextDrag = null; // { id, startX, startY, origX, origY }

  function createTextLayer(preset = "bottom") {
    const clipLen = Math.max(1, state.endTime - state.startTime);
    const newLayer = {
      id: "txt_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6),
      text: preset === "top" ? "TOP TEXT" : "BOTTOM TEXT",
      x: 0.5,
      y: preset === "top" ? 0.14 : 0.86,
      font_family: "impact",
      font_size: 42,
      color: "#ffffff",
      stroke_color: "#000000",
      stroke_width: 3,
      bg_color: "#000000",
      bg_opacity: 0,
      uppercase: true,
      start_offset: 0.0,
      end_offset: Number(clipLen.toFixed(1)),
    };
    state.textLayers.push(newLayer);
    state.selectedTextId = newLayer.id;
    renderTextInspectorList();
    populateTextEditorForm();
    renderStageTextOverlays();
  }

  addTopTextBtn.addEventListener("click", () => createTextLayer("top"));
  addBottomTextBtn.addEventListener("click", () => createTextLayer("bottom"));

  function getSelectedLayer() {
    return state.textLayers.find((l) => l.id === state.selectedTextId) || null;
  }

  function renderTextInspectorList() {
    textLayersList.innerHTML = "";
    if (state.textLayers.length === 0) {
      textEditorPanel.classList.add("hidden");
      return;
    }

    state.textLayers.forEach((layer, idx) => {
      const pill = document.createElement("div");
      pill.className = `text-layer-pill ${layer.id === state.selectedTextId ? "active" : ""}`;
      const label = (layer.text || "Empty Text").replace(/\n/g, " ").slice(0, 28);
      pill.innerHTML = `
        <span><strong>#${idx + 1}</strong> ${escapeHtml(label)}</span>
        <span class="hint">${layer.start_offset}s–${layer.end_offset}s</span>
      `;
      pill.addEventListener("click", () => {
        state.selectedTextId = layer.id;
        renderTextInspectorList();
        populateTextEditorForm();
        renderStageTextOverlays();
      });
      textLayersList.appendChild(pill);
    });
  }

  function populateTextEditorForm() {
    const layer = getSelectedLayer();
    if (!layer) {
      textEditorPanel.classList.add("hidden");
      return;
    }
    textEditorPanel.classList.remove("hidden");
    textContentInput.value = layer.text;
    textFontSelect.value = layer.font_family;
    textSizeInput.value = layer.font_size;
    fontSizeVal.textContent = layer.font_size;
    textColorInput.value = layer.color;
    textStrokeColorInput.value = layer.stroke_color;
    textStrokeWidthInput.value = layer.stroke_width;
    textBgColorInput.value = layer.bg_color;
    textBgOpacityInput.value = layer.bg_opacity;
    bgOpacityVal.textContent = `${Math.round(layer.bg_opacity * 100)}%`;
    textStartOffsetInput.value = layer.start_offset;
    textEndOffsetInput.value = layer.end_offset;
    textUppercaseInput.checked = layer.uppercase;
  }

  function onTextFormUpdated() {
    const layer = getSelectedLayer();
    if (!layer) return;
    layer.text = textContentInput.value;
    layer.font_family = textFontSelect.value;
    layer.font_size = parseInt(textSizeInput.value, 10) || 36;
    fontSizeVal.textContent = layer.font_size;
    layer.color = textColorInput.value;
    layer.stroke_color = textStrokeColorInput.value;
    layer.stroke_width = parseFloat(textStrokeWidthInput.value) || 0;
    layer.bg_color = textBgColorInput.value;
    layer.bg_opacity = parseFloat(textBgOpacityInput.value) || 0;
    bgOpacityVal.textContent = `${Math.round(layer.bg_opacity * 100)}%`;
    layer.start_offset = parseFloat(textStartOffsetInput.value) || 0;
    layer.end_offset = parseFloat(textEndOffsetInput.value) || 60;
    layer.uppercase = textUppercaseInput.checked;

    renderTextInspectorList();
    renderStageTextOverlays();
  }

  [
    textContentInput,
    textFontSelect,
    textSizeInput,
    textColorInput,
    textStrokeColorInput,
    textStrokeWidthInput,
    textBgColorInput,
    textBgOpacityInput,
    textStartOffsetInput,
    textEndOffsetInput,
    textUppercaseInput,
  ].forEach((el) => {
    el.addEventListener("input", onTextFormUpdated);
    el.addEventListener("change", onTextFormUpdated);
  });

  deleteTextLayerBtn.addEventListener("click", () => {
    state.textLayers = state.textLayers.filter((l) => l.id !== state.selectedTextId);
    state.selectedTextId = state.textLayers.length ? state.textLayers[0].id : null;
    renderTextInspectorList();
    populateTextEditorForm();
    renderStageTextOverlays();
  });

  function getCssFontStack(family) {
    switch (family) {
      case "impact":
        return "Impact, 'Arial Black', sans-serif";
      case "sans":
        return "'Segoe UI', Arial, sans-serif";
      case "comic":
        return "'Comic Sans MS', cursive, sans-serif";
      case "mono":
        return "Consolas, 'Courier New', monospace";
      case "serif":
        return "Georgia, 'Times New Roman', serif";
      default:
        return "Impact, sans-serif";
    }
  }

  function renderStageTextOverlays() {
    textOverlaysStage.innerHTML = "";
    const stageRect = interactiveOverlay.getBoundingClientRect();
    const scaleFactor = stageRect.height > 0 ? stageRect.height / 480.0 : 1.0;

    state.textLayers.forEach((layer) => {
      if (!layer.text.trim()) return;
      const div = document.createElement("div");
      div.className = `stage-text-item ${layer.id === state.selectedTextId ? "selected" : ""}`;
      div.dataset.layerId = layer.id;

      const displayText = layer.uppercase ? layer.text.toUpperCase() : layer.text;
      div.textContent = displayText;

      div.style.left = `${(layer.x * 100).toFixed(2)}%`;
      div.style.top = `${(layer.y * 100).toFixed(2)}%`;
      div.style.fontFamily = getCssFontStack(layer.font_family);
      div.style.fontWeight = "800";
      const pxSize = Math.max(10, Math.round(layer.font_size * scaleFactor));
      div.style.fontSize = `${pxSize}px`;
      div.style.color = layer.color;

      const sw = Math.max(0, layer.stroke_width * scaleFactor);
      if (sw > 0) {
        div.style.webkitTextStroke = `${sw.toFixed(1)}px ${layer.stroke_color}`;
        div.style.paintOrder = "stroke fill";
      }

      if (layer.bg_opacity > 0.01) {
        const rgb = hexToRgb(layer.bg_color);
        div.style.backgroundColor = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${layer.bg_opacity})`;
      } else {
        div.style.backgroundColor = "transparent";
      }

      div.addEventListener("mousedown", (e) => {
        e.stopPropagation();
        state.selectedTextId = layer.id;
        renderTextInspectorList();
        populateTextEditorForm();
        activeTextDrag = {
          id: layer.id,
          startX: e.clientX,
          startY: e.clientY,
          origX: layer.x,
          origY: layer.y,
        };
      });

      textOverlaysStage.appendChild(div);
    });

    if (videoPlayer) {
      updateTextVisibilityByTime(videoPlayer.currentTime || state.startTime);
    }
  }

  function updateTextVisibilityByTime(currentVideoTime) {
    const elapsedInClip = Math.max(0, currentVideoTime - state.startTime);
    state.textLayers.forEach((layer) => {
      const el = textOverlaysStage.querySelector(`[data-layer-id="${layer.id}"]`);
      if (!el) return;
      const visible =
        elapsedInClip >= layer.start_offset - 0.05 &&
        elapsedInClip <= layer.end_offset + 0.05;
      el.style.opacity = visible ? "1" : "0.2";
    });
  }

  function handleTextMouseMove(e) {
    const rect = interactiveOverlay.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const layer = state.textLayers.find((l) => l.id === activeTextDrag.id);
    if (!layer) return;

    const dx = (e.clientX - activeTextDrag.startX) / rect.width;
    const dy = (e.clientY - activeTextDrag.startY) / rect.height;
    layer.x = Math.max(0.05, Math.min(0.95, activeTextDrag.origX + dx));
    layer.y = Math.max(0.05, Math.min(0.95, activeTextDrag.origY + dy));
    renderStageTextOverlays();
  }

  window.addEventListener("resize", () => {
    renderStageTextOverlays();
  });

  // =========================================================================
  // COLOR FILTERS & LIVE CSS PREVIEW
  // =========================================================================
  function syncFiltersUI() {
    const f = state.filters;
    brightnessVal.textContent = f.brightness.toFixed(2);
    contrastVal.textContent = f.contrast.toFixed(2);
    saturationVal.textContent = f.saturation.toFixed(1);

    filterBrightness.value = f.brightness;
    filterContrast.value = f.contrast;
    filterSaturation.value = f.saturation;
    filterGrayscale.checked = f.grayscale;
    filterSepia.checked = f.sepia;

    // Apply live CSS filter preview to <video>
    const bCss = 1 + f.brightness;
    const cCss = f.contrast;
    const sCss = f.grayscale ? 0 : f.saturation;
    const sepiaCss = f.sepia ? 1 : 0;
    videoPlayer.style.filter = `brightness(${bCss}) contrast(${cCss}) saturate(${sCss}) sepia(${sepiaCss})`;
  }

  [filterBrightness, filterContrast, filterSaturation, filterGrayscale, filterSepia].forEach(
    (el) => {
      el.addEventListener("input", () => {
        state.filters.brightness = parseFloat(filterBrightness.value) || 0;
        state.filters.contrast = parseFloat(filterContrast.value) || 1;
        state.filters.saturation = parseFloat(filterSaturation.value) || 1;
        state.filters.grayscale = filterGrayscale.checked;
        state.filters.sepia = filterSepia.checked;
        syncFiltersUI();
      });
    }
  );

  document.querySelectorAll("[data-filter-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll("[data-filter-preset]")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const preset = btn.dataset.filterPreset;
      if (preset === "none") {
        state.filters = { brightness: 0, contrast: 1, saturation: 1, grayscale: false, sepia: false };
      } else if (preset === "vivid") {
        state.filters = { brightness: 0.05, contrast: 1.15, saturation: 1.6, grayscale: false, sepia: false };
      } else if (preset === "bw") {
        state.filters = { brightness: 0, contrast: 1.25, saturation: 0, grayscale: true, sepia: false };
      } else if (preset === "sepia") {
        state.filters = { brightness: 0.05, contrast: 1.05, saturation: 1, grayscale: false, sepia: true };
      } else if (preset === "punch") {
        state.filters = { brightness: -0.05, contrast: 1.45, saturation: 1.2, grayscale: false, sepia: false };
      }
      syncFiltersUI();
    });
  });

  // =========================================================================
  // GENERATE GIF & GALLERY
  // =========================================================================
  generateGifBtn.addEventListener("click", async () => {
    if (!state.video) return;

    generateGifBtn.disabled = true;
    generateGifBtn.textContent = "⏳ Rendering GIF...";
    exportStatus.classList.remove("hidden");
    exportStatus.textContent = "Extracting frames, applying text layers & optimizing 256-color palette...";

    const payload = {
      video_id: state.video.video_id,
      start_time: state.startTime,
      end_time: state.endTime,
      fps: state.fps,
      speed: state.speed,
      width: state.outputWidth,
      loop_mode: state.loopMode,
      quality: state.quality,
      crop: state.crop,
      filters: state.filters,
      text_layers: state.textLayers,
    };

    try {
      const res = await fetch("/api/generate-gif", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Failed to generate GIF");
      }

      // Show latest GIF preview card
      latestResultCard.classList.remove("hidden");
      resultGifImg.src = `${data.url}?t=${Date.now()}`;
      resultMetaBadge.textContent = `${data.width}×${data.height} • ${data.frames} frames • ${data.size_human}`;
      resultDownloadBtn.href = `${data.url}?download=1`;
      resultDownloadBtn.download = data.filename;

      exportStatus.textContent = `Done! Saved ${data.filename} (${data.size_human})`;
      loadGallery();
    } catch (err) {
      exportStatus.textContent = `Error: ${err.message}`;
      alert(err.message);
    } finally {
      generateGifBtn.disabled = false;
      generateGifBtn.textContent = "⚡ Create GIF";
    }
  });

  async function loadGallery() {
    try {
      const res = await fetch("/api/gifs");
      const data = await res.json();
      const gifs = data.gifs || [];
      galleryCount.textContent = gifs.length;

      if (gifs.length === 0) {
        galleryGrid.innerHTML = `<div class="gallery-empty">Generated GIFs will appear here for instant preview &amp; download.</div>`;
        return;
      }

      galleryGrid.innerHTML = "";
      gifs.forEach((g) => {
        const card = document.createElement("div");
        card.className = "gallery-item";
        card.innerHTML = `
          <img src="${g.url}" alt="${escapeHtml(g.filename)}" title="Click to preview in Result Panel" />
          <div class="gallery-item-info">
            <div class="gallery-item-meta">
              <span>${g.width}×${g.height}</span>
              <span>${g.size_human}</span>
            </div>
            <div class="gallery-item-actions">
              <a href="${g.url}?download=1" download="${escapeHtml(g.filename)}" class="btn btn-sm btn-primary">Download</a>
              <button type="button" class="btn btn-sm btn-danger" data-del="${escapeHtml(g.filename)}">Delete</button>
            </div>
          </div>
        `;
        card.querySelector("img").addEventListener("click", () => {
          latestResultCard.classList.remove("hidden");
          resultGifImg.src = g.url;
          resultMetaBadge.textContent = `${g.width}×${g.height} • ${g.frames} frames • ${g.size_human}`;
          resultDownloadBtn.href = `${g.url}?download=1`;
          resultDownloadBtn.download = g.filename;
        });
        card.querySelector("[data-del]").addEventListener("click", async () => {
          await fetch(`/api/output/${encodeURIComponent(g.filename)}`, { method: "DELETE" });
          loadGallery();
        });
        galleryGrid.appendChild(card);
      });
    } catch (e) {
      console.error("Failed to load gallery", e);
    }
  }

  function hexToRgb(hex) {
    const h = (hex || "#000000").replace("#", "");
    const num = parseInt(h, 16);
    return {
      r: (num >> 16) & 255,
      g: (num >> 8) & 255,
      b: num & 255,
    };
  }

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[m]);
  }

  // Initial load of gallery
  loadGallery();
})();

