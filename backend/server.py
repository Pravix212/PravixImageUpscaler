import os
import sys
import json
import time
import uuid
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, send_file
from flask_cors import CORS
from PIL import Image
# Disable Pillow decompression bomb check for ultra-high-resolution images
Image.MAX_IMAGE_PIXELS = None

# Ensure project root is in path
if getattr(sys, "frozen", False):
    APP_ROOT = Path(sys.executable).parent
    BUNDLE_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parent.parent
    BUNDLE_ROOT = APP_ROOT

sys.path.insert(0, str(BUNDLE_ROOT))

from backend.engine_manager import get_models_catalog, AVAILABLE_MODELS
from backend.image_processor import process_static_image
from backend.gif_processor import process_animated_gif

app = Flask(__name__, static_folder=str(BUNDLE_ROOT / "frontend"), static_url_path="")
CORS(app)

import tempfile

def get_desktop_dir() -> Path:
    """Finds the true active Windows Desktop folder, accounting for OneDrive sync."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            raw_path, _ = winreg.QueryValueEx(key, "Desktop")
            expanded = os.path.expandvars(raw_path)
            p = Path(expanded)
            if p.exists():
                return p
    except Exception:
        pass

    onedrive = os.environ.get("OneDrive")
    if onedrive:
        od_desktop = Path(onedrive) / "Desktop"
        if od_desktop.exists():
            return od_desktop

    std_desktop = Path.home() / "Desktop"
    if std_desktop.exists():
        return std_desktop

    return Path.home()


def get_default_output_dir() -> Path:
    """
    Creates and returns an 'Output' folder directly on the user's Desktop.
    Falls back gracefully if the Desktop is inaccessible.
    """
    desktop = get_desktop_dir()
    candidate = desktop / "Output"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except Exception:
        pass

    # Fallback to User Pictures / Output
    try:
        pics = Path.home() / "Pictures" / "Output"
        pics.mkdir(parents=True, exist_ok=True)
        return pics
    except Exception:
        pass

    # Fallback to User Documents / Output
    try:
        docs = Path.home() / "Documents" / "Output"
        docs.mkdir(parents=True, exist_ok=True)
        return docs
    except Exception:
        pass

    # Final fallback to Temp
    fallback = Path(tempfile.gettempdir()) / "PravixUpscaler" / "Output"
    try:
        fallback.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return fallback

UPLOAD_DIR = Path(tempfile.gettempdir()) / "PravixUpscaler" / "uploads"
try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    UPLOAD_DIR = Path.home() / ".pravix" / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = get_default_output_dir()

# Active tasks tracking for real-time progress
tasks = {}

@app.route("/")
def index():
    return send_from_directory(str(BUNDLE_ROOT / "frontend"), "index.html")

@app.route("/api/system", methods=["GET"])
def get_system_info():
    gpu_name = "NVIDIA GeForce RTX 5070 (Vulkan)"
    return jsonify({
        "status": "online",
        "gpu": gpu_name,
        "acceleration": "NCNN Vulkan Hardware Acceleration",
        "models_count": len(AVAILABLE_MODELS),
        "output_dir": str(OUTPUT_DIR)
    })

@app.route("/api/models", methods=["GET"])
def list_models():
    return jsonify({
        "models": get_models_catalog()
    })

@app.route("/api/preview/<folder>/<filename>", methods=["GET"])
def preview_file(folder, filename):
    """Serves input uploads or output images/gifs for preview in browser."""
    if folder == "uploads":
        target = UPLOAD_DIR
    elif folder == "outputs":
        target = OUTPUT_DIR
        for t in tasks.values():
            res = t.get("result")
            if res and res.get("filename") == filename:
                out_p = Path(res["output_path"])
                if out_p.exists():
                    target = out_p.parent
                    break
    else:
        return jsonify({"error": "Invalid folder"}), 400
    return send_from_directory(str(target), filename)

@app.route("/api/preload-file", methods=["GET"])
def api_preload_file():
    path_str = request.args.get("path", "")
    if not path_str:
        return jsonify({"error": "No path provided"}), 400
    p = Path(path_str).resolve()
    if not p.exists() or not p.is_file():
        return jsonify({"error": "File does not exist"}), 404
    return send_file(str(p), download_name=p.name)

@app.route("/api/tasks/<task_id>/progress", methods=["GET"])
def task_progress(task_id):
    """Server-Sent Events (SSE) stream for live task progress logs."""
    def event_stream():
        last_log_idx = 0
        while True:
            task = tasks.get(task_id)
            if not task:
                yield f"data: {json.dumps({'status': 'not_found'})}\n\n"
                break

            current_logs = task.get("logs", [])
            if len(current_logs) > last_log_idx:
                new_logs = current_logs[last_log_idx:]
                last_log_idx = len(current_logs)
                for log_msg in new_logs:
                    yield f"data: {json.dumps({'status': 'processing', 'log': log_msg, 'progress': task.get('progress', 0)})}\n\n"

            if task.get("status") in ["completed", "failed"]:
                yield f"data: {json.dumps(task)}\n\n"
                break

            time.sleep(0.15)

    return Response(event_stream(), mimetype="text/event-stream")

def execute_upscale_worker(task_id, file_path, model_id, scale, custom_width, output_format, orig_filename, target_out_dir=None, enhance_quality=True, restore_faces=False, face_fidelity=0.75, discord_optimize=False, discord_target_mb=10.0):
    task = tasks[task_id]
    
    def log_callback(msg):
        task["logs"].append(msg)
        # Attempt to parse percentage from engine line (e.g. 45.00%)
        if "%" in msg:
            try:
                pct_str = msg.split("%")[0].strip().split()[-1]
                pct = float(pct_str)
                task["progress"] = min(99, int(pct))
            except Exception:
                pass

    try:
        input_p = Path(file_path)
        is_gif = False

        # Detect animated GIF
        try:
            with Image.open(input_p) as img:
                if getattr(img, "is_animated", False) and img.n_frames > 1:
                    is_gif = True
        except Exception:
            pass

        stem = Path(orig_filename).stem
        ext = output_format.lower()
        if is_gif:
            if ext not in ["gif", "webp"]:
                ext = "gif"
        else:
            if ext not in ["png", "jpg", "jpeg", "webp"]:
                ext = "png"

        dest_dir = Path(target_out_dir) if target_out_dir else OUTPUT_DIR
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            dest_dir = OUTPUT_DIR
            dest_dir.mkdir(parents=True, exist_ok=True)

        out_name = f"{stem}_upscaled_{model_id}_{scale}x_{int(time.time())}.{ext}"
        out_path = dest_dir / out_name

        task["status"] = "processing"
        log_callback(f"Detected file type: {'Animated GIF' if is_gif else 'Static Image'}")

        if is_gif:
            result = process_animated_gif(
                input_path=str(input_p),
                output_path=str(out_path),
                model_id=model_id,
                scale=scale,
                custom_width=custom_width,
                output_format=ext,
                enhance_quality=enhance_quality,
                discord_optimize=discord_optimize,
                discord_target_mb=discord_target_mb,
                on_log=log_callback
            )
        else:
            result = process_static_image(
                input_path=str(input_p),
                output_path=str(out_path),
                model_id=model_id,
                scale=scale,
                custom_width=custom_width,
                output_format=ext,
                enhance_quality=enhance_quality,
                restore_faces=restore_faces,
                face_fidelity=face_fidelity,
                discord_optimize=discord_optimize,
                discord_target_mb=discord_target_mb,
                on_log=log_callback
            )

        task["status"] = "completed"
        task["progress"] = 100
        task["result"] = {
            **result,
            "is_gif": is_gif,
            "input_preview_url": f"/api/preview/uploads/{input_p.name}",
            "output_preview_url": f"/api/preview/outputs/{out_name}",
            "filename": out_name
        }
        log_callback("Done! Ready to view and save.")

    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        log_callback(f"Error: {str(e)}")

@app.route("/api/upscale", methods=["POST"])
def start_upscale():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    model_id = request.form.get("model_id", "ultrasharp-4x")
    scale = int(request.form.get("scale", 2))
    custom_width = request.form.get("custom_width", type=int)
    output_format = request.form.get("output_format", "png")
    custom_output_dir = request.form.get("output_dir")
    enhance_quality = request.form.get("enhance_quality", "true").lower() == "true"
    restore_faces = request.form.get("restore_faces", "false").lower() == "true"
    face_fidelity = float(request.form.get("face_fidelity", 0.75))
    discord_optimize = request.form.get("discord_optimize", "false").lower() == "true"
    discord_target_mb = float(request.form.get("discord_target_mb", 10.0))

    task_id = str(uuid.uuid4())
    save_filename = f"{task_id}_{uploaded_file.filename}"
    save_path = UPLOAD_DIR / save_filename
    uploaded_file.save(str(save_path))

    tasks[task_id] = {
        "id": task_id,
        "status": "queued",
        "progress": 0,
        "logs": ["Upload received. Preparing engine..."],
        "filename": uploaded_file.filename,
        "created_at": time.time()
    }

    t = threading.Thread(
        target=execute_upscale_worker,
        args=(task_id, str(save_path), model_id, scale, custom_width, output_format, uploaded_file.filename, custom_output_dir, enhance_quality, restore_faces, face_fidelity, discord_optimize, discord_target_mb),
        daemon=True
    )
    t.start()

    return jsonify({
        "task_id": task_id,
        "status": "started",
        "progress_url": f"/api/tasks/{task_id}/progress"
    })

@app.route("/api/face-model-status")
def face_model_status():
    from backend.face_restorer import is_face_restoration_installed
    return jsonify({
        "installed": is_face_restoration_installed()
    })

@app.route("/api/open-url", methods=["POST"])
def open_url():
    """Opens an external URL in the user's default system browser."""
    try:
        req_data = request.get_json(silent=True) or {}
        url = req_data.get("url")
        if url and url.startswith(("http://", "https://")):
            import webbrowser
            webbrowser.open(url)
            return jsonify({"success": True})
        return jsonify({"error": "Invalid URL"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/open-output", methods=["POST"])
def open_output_folder():
    """Opens the output directory in Windows File Explorer."""
    try:
        req_data = request.get_json(silent=True) or {}
        target = req_data.get("folder") or str(OUTPUT_DIR)
        p = Path(target)
        p.mkdir(parents=True, exist_ok=True)
        os.startfile(str(p))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/browse-folder", methods=["POST"])
def browse_folder():
    """Opens the native Windows folder selection dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_selected = filedialog.askdirectory(initialdir=str(OUTPUT_DIR))
        root.destroy()
        if folder_selected:
            return jsonify({"folder": str(Path(folder_selected).resolve())})
        return jsonify({"folder": None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = 5000
    print(f"\n=======================================================")
    print(f"🚀 Local AI Image & GIF Upscaler Server Starting!")
    print(f"🌐 Access URL: http://localhost:{port}")
    print(f"⚡ GPU: NVIDIA GeForce RTX 5070 (Vulkan)")
    print(f"=======================================================\n")
    app.run(host="127.0.0.1", port=port, debug=False)
