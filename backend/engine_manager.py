import os
import sys
import subprocess
import urllib.request
import threading
import time
import tempfile
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent
    BUNDLE_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parent.parent
    BUNDLE_ROOT = APP_ROOT

# Check possible binary locations (BUNDLE_ROOT first for --onefile compatibility)
possible_bins = [
    BUNDLE_ROOT / "backend" / "bin" / "upscayl-bin.exe",
    BUNDLE_ROOT / "bin" / "upscayl-bin.exe",
    APP_ROOT / "backend" / "bin" / "upscayl-bin.exe",
    APP_ROOT / "bin" / "upscayl-bin.exe",
    Path(__file__).resolve().parent / "bin" / "upscayl-bin.exe"
]
BIN_PATH = next((p for p in possible_bins if p.exists()), possible_bins[0])
BIN_DIR = BIN_PATH.parent

possible_models = [
    BUNDLE_ROOT / "backend" / "models",
    BUNDLE_ROOT / "models",
    APP_ROOT / "backend" / "models",
    APP_ROOT / "models",
    Path(__file__).resolve().parent / "models"
]
MODELS_DIR = next((p for p in possible_models if p.exists()), possible_models[0])
TEMP_DIR = Path(tempfile.gettempdir()) / "PravixUpscaler" / "temp"

GITHUB_MODELS_BASE = "https://raw.githubusercontent.com/upscayl/upscayl/main/resources/models"

AVAILABLE_MODELS = {
    "upscayl-standard-4x": {
        "name": "Universal Standard",
        "description": "Best general-purpose model for natural photos and real-world images.",
        "category": "Photo",
        "scale": 4,
        "files": ["upscayl-standard-4x.bin", "upscayl-standard-4x.param"]
    },
    "ultrasharp-4x": {
        "name": "UltraSharp",
        "description": "Enhances extreme clarity and removes blur/compression artifacts.",
        "category": "Enhance",
        "scale": 4,
        "files": ["ultrasharp-4x.bin", "ultrasharp-4x.param"]
    },
    "digital-art-4x": {
        "name": "Digital Art",
        "description": "Specially trained for anime, manga, 2D art, and vector-style graphics.",
        "category": "Anime / Art",
        "scale": 4,
        "files": ["digital-art-4x.bin", "digital-art-4x.param"]
    },
    "upscayl-lite-4x": {
        "name": "Fast Lite",
        "description": "Ultra-lightweight and fast. Perfect for long GIFs and rapid batch processing.",
        "category": "Fast",
        "scale": 4,
        "files": ["upscayl-lite-4x.bin", "upscayl-lite-4x.param"]
    },
    "remacri-4x": {
        "name": "Remacri",
        "description": "Excels at fine textured details, fabric, landscapes, and architectural surfaces.",
        "category": "Texture",
        "scale": 4,
        "files": ["remacri-4x.bin", "remacri-4x.param"]
    },
    "high-fidelity-4x": {
        "name": "High Fidelity",
        "description": "Subtle, faithful upscaling that preserves authentic grain and original character.",
        "category": "Photo",
        "scale": 4,
        "files": ["high-fidelity-4x.bin", "high-fidelity-4x.param"]
    }
}


def is_model_installed(model_id: str) -> bool:
    if model_id not in AVAILABLE_MODELS:
        return False
    files = AVAILABLE_MODELS[model_id]["files"]
    return all((MODELS_DIR / f).exists() and (MODELS_DIR / f).stat().st_size > 0 for f in files)


def download_model(model_id: str, progress_callback=None) -> bool:
    """Download model .param and .bin files from Upscayl repository."""
    if model_id not in AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_id}")
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    files = AVAILABLE_MODELS[model_id]["files"]
    
    for filename in files:
        target_path = MODELS_DIR / filename
        if target_path.exists() and target_path.stat().st_size > 0:
            continue
            
        url = f"{GITHUB_MODELS_BASE}/{filename}"
        print(f"Downloading model file: {filename} from {url}...")
        if progress_callback:
            progress_callback(f"Downloading {filename}...")
            
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10; Win64; x64)"})
        with urllib.request.urlopen(req) as resp, open(target_path, "wb") as f:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB blocks
            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size and progress_callback:
                    pct = int((downloaded / total_size) * 100)
                    progress_callback(f"Downloading {filename}: {pct}%")

    return True


def ensure_model(model_id: str, progress_callback=None, on_log=None):
    cb = on_log or progress_callback
    if not is_model_installed(model_id):
        download_model(model_id, cb)


def get_models_catalog():
    models = []
    for mid, info in AVAILABLE_MODELS.items():
        models.append({
            "id": mid,
            "name": info["name"],
            "description": info["description"],
            "category": info["category"],
            "scale": info["scale"],
            "is_installed": is_model_installed(mid)
        })
    return models


def run_engine_command(input_path: str, output_path: str, model_id: str, 
                       scale: int = 4, tile_size: int = 0, gpu_id: int = 0,
                       custom_width: int = None, format_out: str = "png",
                       verbose: bool = True, on_log=None):
    """
    Executes upscayl-bin.exe with given arguments.
    Works for both single image and directory inputs.
    """
    if not BIN_PATH.exists():
        raise RuntimeError(f"Engine binary not found at {BIN_PATH}")

    ensure_model(model_id, on_log)
    
    model_scale = AVAILABLE_MODELS.get(model_id, {}).get("scale", 4)

    cmd = [
        str(BIN_PATH),
        "-i", str(input_path),
        "-o", str(output_path),
        "-m", str(MODELS_DIR),
        "-n", model_id,
        "-z", str(model_scale),
        "-s", str(scale),
        "-t", str(tile_size),
        "-g", str(gpu_id),
        "-f", format_out
    ]
    
    if custom_width:
        cmd.extend(["-w", str(custom_width)])
        
    if verbose:
        cmd.append("-v")

    print(f"Executing: {' '.join(cmd)}")
    if on_log:
        on_log("Starting AI engine...")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1
    )

    full_log = []
    for line in iter(process.stdout.readline, ""):
        clean_line = line.strip()
        if clean_line:
            full_log.append(clean_line)
            try:
                print(f"[Engine] {clean_line}")
            except UnicodeEncodeError:
                safe_line = clean_line.encode("ascii", errors="replace").decode("ascii")
                print(f"[Engine] {safe_line}")
            if on_log:
                try:
                    on_log(clean_line)
                except Exception:
                    pass

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Upscaling engine failed with code {process.returncode}:\n" + "\n".join(full_log[-10:]))
        
    return True
