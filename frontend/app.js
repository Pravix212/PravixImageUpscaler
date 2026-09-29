// Application State
let selectedFile = null;
let isGif = false;
let selectedModel = "ultrasharp-4x";
let selectedScale = 2;
let selectedFormat = "png";
let selectedOutputDir = null;
let selectedDiscordBudget = 10;
let isProcessing = false;

// Zoom & Pan State
let currentZoom = 1.0;
let isSliderDragging = false;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let panX = 0;
let panY = 0;
let currentSplitPct = 50;

// DOM Elements
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const dropzoneEmpty = document.getElementById("dropzoneEmpty");
const dropzonePreview = document.getElementById("dropzonePreview");
const thumbImg = document.getElementById("thumbImg");
const previewFilename = document.getElementById("previewFilename");
const previewTag = document.getElementById("previewTag");
const previewDims = document.getElementById("previewDims");
const btnRemoveFile = document.getElementById("btnRemoveFile");

const modelsContainer = document.getElementById("modelsContainer");
const scaleButtons = document.querySelectorAll(".scale-btn");
const outputFolderPath = document.getElementById("outputFolderPath");
const btnBrowseFolder = document.getElementById("btnBrowseFolder");
const formatSelector = document.getElementById("formatSelector");
const formatHint = document.getElementById("formatHint");
const btnUpscale = document.getElementById("btnUpscale");
const btnUpscaleText = document.getElementById("btnUpscaleText");

const viewIdle = document.getElementById("viewIdle");
const viewProcessing = document.getElementById("viewProcessing");
const viewResultImage = document.getElementById("viewResultImage");
const viewResultGif = document.getElementById("viewResultGif");

const progressBarFill = document.getElementById("progressBarFill");
const progressPctText = document.getElementById("progressPctText");
const consoleBox = document.getElementById("consoleBox");

const canvasToolbar = document.getElementById("canvasToolbar");
const btnZoomIn = document.getElementById("btnZoomIn");
const btnZoomOut = document.getElementById("btnZoomOut");
const btnZoomFit = document.getElementById("btnZoomFit");
const zoomLevelText = document.getElementById("zoomLevelText");

const statBefore = document.getElementById("statBefore");
const statAfter = document.getElementById("statAfter");
const statTime = document.getElementById("statTime");
const btnDownload = document.getElementById("btnDownload");

// Comparison Slider Elements
const comparisonContainer = document.getElementById("comparisonContainer");
const afterWrapper = document.getElementById("afterWrapper");
const sliderHandle = document.getElementById("sliderHandle");
const imgBefore = document.getElementById("imgBefore");
const imgAfter = document.getElementById("imgAfter");

// GIF Player Elements
const gifBefore = document.getElementById("gifBefore");
const gifAfter = document.getElementById("gifAfter");
const btnSyncReplay = document.getElementById("btnSyncReplay");

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  fetchSystemInfo();
  fetchModels();
  setupEventListeners();
  setupSliderEvents();
  setupZoomPanEvents();
  checkPreloadParam();
});

async function checkPreloadParam() {
  const params = new URLSearchParams(window.location.search);
  const preloadPath = params.get("preload");
  if (!preloadPath) return;

  try {
    const filename = preloadPath.replace(/\\/g, "/").split("/").pop();
    const res = await fetch(`/api/preload-file?path=${encodeURIComponent(preloadPath)}`);
    if (!res.ok) return;
    const blob = await res.blob();
    const file = new File([blob], filename, { type: blob.type || "image/png" });
    handleFileSelected(file);
  } catch (err) {
    console.warn("Failed to preload image from arguments:", err);
  }
}

// 1. Fetch System Info (GPU)
async function fetchSystemInfo() {
  try {
    const res = await fetch("/api/system");
    const data = await res.json();
    document.getElementById("gpuNameText").textContent = data.gpu || "RTX 5070 Ready";
    if (data.output_dir && !selectedOutputDir) {
      outputFolderPath.value = data.output_dir;
    }
  } catch (err) {
    document.getElementById("gpuNameText").textContent = "RTX 5070 (Vulkan Ready)";
  }
}

// 2. Fetch Available Models
async function fetchModels() {
  try {
    const res = await fetch("/api/models");
    const data = await res.json();
    renderModelCards(data.models);
  } catch (err) {
    console.error("Error fetching models:", err);
  }
}

function renderModelCards(models) {
  modelsContainer.innerHTML = "";
  models.forEach((m) => {
    const card = document.createElement("div");
    card.className = `model-card ${m.id === selectedModel ? "active" : ""}`;
    card.dataset.id = m.id;
    card.innerHTML = `
      <div class="model-header">
        <span class="model-title">${m.name}</span>
        <span class="model-badge">${m.category}</span>
      </div>
      <p class="model-desc">${m.description}</p>
    `;
    card.addEventListener("click", () => {
      document.querySelectorAll(".model-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      selectedModel = m.id;
    });
    modelsContainer.appendChild(card);
  });
}

// 3. Setup General Events
function setupEventListeners() {
  // Dropzone click & drag
  dropzone.addEventListener("click", (e) => {
    if (e.target !== fileInput) {
      fileInput.click();
    }
  });

  fileInput.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  // Global window drop & dropzone drop
  ["dragenter", "dragover"].forEach((eventName) => {
    window.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = "copy";
      dropzone.classList.add("dragover");
    });
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = "copy";
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "dragend"].forEach((eventName) => {
    window.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.clientX === 0 || e.clientY === 0) {
        dropzone.classList.remove("dragover");
      }
    });
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  window.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  // Global Paste from clipboard (Ctrl+V)
  window.addEventListener("paste", (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const blob = items[i].getAsFile();
        handleFileSelected(blob);
        break;
      }
    }
  });

  btnRemoveFile.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  // Scale buttons
  scaleButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      scaleButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedScale = parseInt(btn.dataset.scale);
    });
  });

  // Face Restoration Toggle & Slider
  const chkRestoreFaces = document.getElementById("chkRestoreFaces");
  const faceFidelityBox = document.getElementById("faceFidelityBox");
  const sliderFaceFidelity = document.getElementById("sliderFaceFidelity");
  const faceFidelityVal = document.getElementById("faceFidelityVal");

  if (chkRestoreFaces && faceFidelityBox) {
    chkRestoreFaces.addEventListener("change", () => {
      if (chkRestoreFaces.checked) {
        faceFidelityBox.classList.remove("hidden");
      } else {
        faceFidelityBox.classList.add("hidden");
      }
    });
  }

  if (sliderFaceFidelity && faceFidelityVal) {
    sliderFaceFidelity.addEventListener("input", () => {
      faceFidelityVal.textContent = sliderFaceFidelity.value + "%";
    });
  }

  // Discord Optimizer Toggle & Budget Selection
  const chkDiscordOpt = document.getElementById("chkDiscordOpt");
  const discordBudgetBox = document.getElementById("discordBudgetBox");
  const budgetPills = document.querySelectorAll(".budget-pill");

  if (chkDiscordOpt && discordBudgetBox) {
    chkDiscordOpt.addEventListener("change", () => {
      if (chkDiscordOpt.checked) {
        discordBudgetBox.classList.remove("hidden");
      } else {
        discordBudgetBox.classList.add("hidden");
      }
    });
  }

  budgetPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      budgetPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      selectedDiscordBudget = parseFloat(pill.dataset.mb) || 10;
    });
  });

  // Step 4: Browse Output Folder
  btnBrowseFolder.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/browse-folder", { method: "POST" });
      const data = await res.json();
      if (data.folder) {
        selectedOutputDir = data.folder;
        outputFolderPath.value = data.folder;
      }
    } catch (err) {
      console.error("Folder browse error:", err);
    }
  });

  // Action Button
  btnUpscale.addEventListener("click", startUpscaling);

  // Open Output Folder in Explorer
  document.getElementById("btnOpenFolder").addEventListener("click", async () => {
    await fetch("/api/open-output", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ folder: selectedOutputDir }),
    });
  });

  // Donate via PayPal (Opens in default system browser once)
  const btnDonate = document.getElementById("btnDonate");
  if (btnDonate) {
    btnDonate.addEventListener("click", async (e) => {
      e.preventDefault();
      const donateUrl = "https://www.paypal.com/ncp/payment/HT8PSWCS898LU";
      try {
        const resp = await fetch("/api/open-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: donateUrl }),
        });
        if (!resp.ok) {
          window.open(donateUrl, "_blank");
        }
      } catch (_) {
        window.open(donateUrl, "_blank");
      }
    });
  }

  // Resync GIF
  if (btnSyncReplay) {
    btnSyncReplay.addEventListener("click", () => {
      const bSrc = gifBefore.src;
      const aSrc = gifAfter.src;
      gifBefore.src = "";
      gifAfter.src = "";
      setTimeout(() => {
        gifBefore.src = bSrc;
        gifAfter.src = aSrc;
      }, 50);
    });
  }
}

// 4. File Ingestion Logic
function handleFileSelected(file) {
  selectedFile = file;
  const filename = file.name || "pasted_image.png";
  const ext = filename.split(".").pop().toLowerCase();
  isGif = ext === "gif";

  dropzoneEmpty.classList.add("hidden");
  dropzonePreview.classList.remove("hidden");
  previewFilename.textContent = filename;

  if (isGif) {
    previewTag.textContent = "ANIMATED GIF";
    previewTag.className = "preview-tag gif-tag";
  } else {
    previewTag.textContent = "STATIC IMAGE";
    previewTag.className = "preview-tag";
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    thumbImg.src = e.target.result;
    const imgTest = new Image();
    imgTest.onload = () => {
      previewDims.textContent = `${imgTest.width} x ${imgTest.height}`;
    };
    imgTest.src = e.target.result;
  };
  reader.readAsDataURL(file);

  updateFormatSelector(isGif);
  btnUpscale.disabled = false;
}

function clearSelectedFile(resetView = false) {
  selectedFile = null;
  fileInput.value = "";
  dropzoneEmpty.classList.remove("hidden");
  dropzonePreview.classList.add("hidden");
  btnUpscale.disabled = true;
  if (resetView) {
    canvasToolbar.classList.add("hidden");
    switchView("idle");
  }
}

function updateFormatSelector(isAnimatedGif) {
  formatSelector.innerHTML = "";
  if (isAnimatedGif) {
    formatSelector.innerHTML = `
      <button class="format-btn active" data-fmt="gif">GIF</button>
      <button class="format-btn" data-fmt="webp">Animated WebP</button>
    `;
    selectedFormat = "gif";
    formatHint.textContent = "Standard Animated GIF (optimized adaptive palette)";
  } else {
    formatSelector.innerHTML = `
      <button class="format-btn active" data-fmt="png">PNG</button>
      <button class="format-btn" data-fmt="jpg">JPG</button>
      <button class="format-btn" data-fmt="webp">WEBP</button>
    `;
    selectedFormat = "png";
    formatHint.textContent = "Lossless high-quality PNG";
  }

  formatSelector.querySelectorAll(".format-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      formatSelector.querySelectorAll(".format-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedFormat = btn.dataset.fmt;
      if (selectedFormat === "webp" && isAnimatedGif) {
        formatHint.textContent = "Animated WebP: True 24-bit color, no 256-color banding!";
      } else if (selectedFormat === "gif") {
        formatHint.textContent = "Standard Animated GIF (optimized 256-color palette)";
      } else if (selectedFormat === "png") {
        formatHint.textContent = "Lossless crisp PNG";
      } else if (selectedFormat === "jpg") {
        formatHint.textContent = "Standard compressed JPG";
      } else {
        formatHint.textContent = "Modern compact WEBP";
      }
    });
  });
}

// 5. Start Upscaling Task
async function startUpscaling() {
  if (!selectedFile || isProcessing) return;

  isProcessing = true;
  btnUpscale.disabled = true;
  btnUpscaleText.textContent = "UPSCALING...";

  canvasToolbar.classList.add("hidden");
  switchView("processing");
  progressBarFill.style.width = "5%";
  progressPctText.textContent = "5%";
  consoleBox.innerHTML = `<div class="console-line">[System] Initializing engine with model ${selectedModel} (${selectedScale}x)...</div>`;

  const formData = new FormData();
  formData.append("file", selectedFile);
  formData.append("model_id", selectedModel);
  formData.append("scale", selectedScale);
  formData.append("output_format", selectedFormat);
  if (selectedOutputDir) {
    formData.append("output_dir", selectedOutputDir);
  }
  const chkEnhance = document.getElementById("chkEnhanceQuality");
  formData.append("enhance_quality", chkEnhance ? chkEnhance.checked : true);

  const chkFaces = document.getElementById("chkRestoreFaces");
  const sliderFidelity = document.getElementById("sliderFaceFidelity");
  const restoreFaces = chkFaces ? chkFaces.checked : false;
  const faceFidelity = sliderFidelity ? (parseInt(sliderFidelity.value) / 100.0) : 0.75;
  formData.append("restore_faces", restoreFaces);
  formData.append("face_fidelity", faceFidelity);

  const chkDiscord = document.getElementById("chkDiscordOpt");
  const discordOpt = chkDiscord ? chkDiscord.checked : false;
  formData.append("discord_optimize", discordOpt);
  formData.append("discord_target_mb", selectedDiscordBudget);

  try {
    const res = await fetch("/api/upscale", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!data.task_id) {
      throw new Error(data.error || "Failed to start upscale task");
    }

    listenTaskProgress(data.task_id);
  } catch (err) {
    alert("Error starting upscale: " + err.message);
    resetProcessingState();
    switchView("idle");
  }
}

function listenTaskProgress(taskId) {
  const evtSource = new EventSource(`/api/tasks/${taskId}/progress`);

  evtSource.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.log) {
      const line = document.createElement("div");
      line.className = "console-line";
      line.textContent = data.log;
      consoleBox.appendChild(line);
      consoleBox.scrollTop = consoleBox.scrollHeight;
    }

    if (data.progress !== undefined) {
      const p = Math.max(5, data.progress);
      progressBarFill.style.width = `${p}%`;
      progressPctText.textContent = `${p}%`;
    }

    if (data.status === "completed") {
      evtSource.close();
      progressBarFill.style.width = "100%";
      progressPctText.textContent = "100%";
      setTimeout(() => {
        try {
          if (data.result) {
            showResult(data.result);
          } else {
            console.warn("No result payload in completed task event");
          }
        } catch (err) {
          console.error("Error displaying result:", err);
        } finally {
          resetProcessingState();
        }
      }, 300);
    } else if (data.status === "failed") {
      evtSource.close();
      alert("Upscaling failed: " + (data.error || "Unknown error"));
      resetProcessingState();
      switchView("idle");
    }
  };

  evtSource.onerror = () => {
    evtSource.close();
    resetProcessingState();
  };
}

function resetProcessingState() {
  isProcessing = false;
  btnUpscaleText.textContent = "UPSCALE";
  btnUpscale.disabled = !selectedFile;
}

// 6. Show Results
function showResult(res) {
  if (!res) return;
  canvasToolbar.classList.remove("hidden");

  statBefore.textContent = `${res.width_before} x ${res.height_before}`;
  statAfter.textContent = `${res.width_after} x ${res.height_after}`;
  if (res.discord_final_mb) {
    statTime.textContent = `⏱️ ${res.elapsed_seconds}s • 🎮 ${res.discord_final_mb} MB (Discord Ready 🚀)`;
  } else {
    statTime.textContent = `⏱️ ${res.elapsed_seconds}s`;
  }

  btnDownload.href = res.output_preview_url;
  btnDownload.setAttribute("download", res.filename);

  if (res.is_gif) {
    switchView("resultGif");

    const origEl = document.getElementById("gifOrigDim");
    if (origEl) origEl.textContent = `${res.width_before} x ${res.height_before}`;
    const upEl = document.getElementById("gifUpscaledDim");
    if (upEl) upEl.textContent = `${res.width_after} x ${res.height_after} (${res.total_frames || "?"} frames)`;

    gifBefore.src = res.input_preview_url + "?t=" + Date.now();
    gifAfter.src = res.output_preview_url + "?t=" + Date.now();
  } else {
    switchView("resultImage");

    imgBefore.src = res.input_preview_url + "?t=" + Date.now();
    imgAfter.src = res.output_preview_url + "?t=" + Date.now();

    resetZoom();
    setSliderPosition(50);
  }

  // Clear sidebar queue so the user can immediately select/drop the next file!
  clearSelectedFile();
}

function switchView(viewName) {
  viewIdle.classList.add("hidden");
  viewProcessing.classList.add("hidden");
  viewResultImage.classList.add("hidden");
  viewResultGif.classList.add("hidden");

  if (viewName === "idle") viewIdle.classList.remove("hidden");
  else if (viewName === "processing") viewProcessing.classList.remove("hidden");
  else if (viewName === "resultImage") viewResultImage.classList.remove("hidden");
  else if (viewName === "resultGif") viewResultGif.classList.remove("hidden");
}

// 7. Interactive Before/After Split Slider & Panning
function setupSliderEvents() {
  const isNearHandle = (clientX) => {
    const rect = comparisonContainer.getBoundingClientRect();
    const handleX = rect.left + (rect.width * currentSplitPct) / 100;
    return Math.abs(clientX - handleX) < 32;
  };

  const onDown = (clientX, clientY, button = 0) => {
    if (button !== 0) return;
    if (isNearHandle(clientX) || currentZoom === 1.0) {
      isSliderDragging = true;
      updateSliderFromClientX(clientX);
    } else if (currentZoom > 1.0) {
      isPanning = true;
      panStartX = clientX - panX;
      panStartY = clientY - panY;
      comparisonContainer.style.cursor = "grabbing";
    }
  };

  const onMove = (clientX, clientY) => {
    if (isSliderDragging) {
      updateSliderFromClientX(clientX);
    } else if (isPanning) {
      panX = clientX - panStartX;
      panY = clientY - panStartY;
      updateImageTransforms();
    } else {
      if (currentZoom > 1.0) {
        comparisonContainer.style.cursor = isNearHandle(clientX) ? "ew-resize" : "grab";
      } else {
        comparisonContainer.style.cursor = "ew-resize";
      }
    }
  };

  const onUp = () => {
    isSliderDragging = false;
    if (isPanning) {
      isPanning = false;
      comparisonContainer.style.cursor = currentZoom > 1.0 ? "grab" : "ew-resize";
    }
  };

  comparisonContainer.addEventListener("mousedown", (e) => onDown(e.clientX, e.clientY, e.button));
  window.addEventListener("mousemove", (e) => onMove(e.clientX, e.clientY));
  window.addEventListener("mouseup", onUp);

  comparisonContainer.addEventListener("touchstart", (e) => {
    if (e.touches && e.touches[0]) onDown(e.touches[0].clientX, e.touches[0].clientY, 0);
  }, { passive: true });

  window.addEventListener("touchmove", (e) => {
    if (e.touches && e.touches[0]) onMove(e.touches[0].clientX, e.touches[0].clientY);
  }, { passive: true });

  window.addEventListener("touchend", onUp);

  // Double click toggles between 100% fit and 200% zoom
  comparisonContainer.addEventListener("dblclick", () => {
    if (currentZoom > 1.0) {
      resetZoom();
    } else {
      applyZoom(2.0);
    }
  });
}

function updateSliderFromClientX(clientX) {
  const rect = comparisonContainer.getBoundingClientRect();
  let offset = clientX - rect.left;
  let pct = (offset / rect.width) * 100;
  pct = Math.max(0, Math.min(100, pct));
  setSliderPosition(pct);
}

function setSliderPosition(pct) {
  currentSplitPct = pct;
  comparisonContainer.style.setProperty("--split", `${pct}%`);
  sliderHandle.style.left = `${pct}%`;
}

// 8. Zoom & Pan Controls
function setupZoomPanEvents() {
  btnZoomIn.addEventListener("click", () => applyZoom(currentZoom + 0.25));
  btnZoomOut.addEventListener("click", () => applyZoom(currentZoom - 0.25));
  btnZoomFit.addEventListener("click", resetZoom);

  // Mouse wheel zoom
  comparisonContainer.addEventListener("wheel", (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.2 : -0.2;
    applyZoom(currentZoom + delta);
  }, { passive: false });
}

function applyZoom(zoom) {
  currentZoom = Math.max(1.0, Math.min(5.0, Math.round(zoom * 100) / 100));
  zoomLevelText.textContent = `${Math.round(currentZoom * 100)}%`;
  if (currentZoom === 1.0) {
    panX = 0;
    panY = 0;
    comparisonContainer.style.cursor = "ew-resize";
  } else {
    comparisonContainer.style.cursor = "grab";
  }
  updateImageTransforms();
}

function resetZoom() {
  currentZoom = 1.0;
  panX = 0;
  panY = 0;
  zoomLevelText.textContent = "100%";
  updateImageTransforms();
  comparisonContainer.style.cursor = "ew-resize";
}

function updateImageTransforms() {
  const transform = `translate(${panX}px, ${panY}px) scale(${currentZoom})`;
  imgBefore.style.transform = transform;
  imgAfter.style.transform = transform;
}
