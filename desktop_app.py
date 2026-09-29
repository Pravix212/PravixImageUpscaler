import os
import sys
import time
import socket
import threading
from pathlib import Path

# If running as PyInstaller bundled exe, find bundle dir
if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BUNDLE_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(BUNDLE_DIR))

import webview
from backend.server import app

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def start_server(port):
    # Silence werkzeug access logs in desktop mode
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)

def main():
    port = get_free_port()
    
    # Start internal Flask API server in daemon thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    time.sleep(0.4)
    url = f"http://127.0.0.1:{port}"
    
    # Handle image file passed via command line or Windows context menu
    if len(sys.argv) > 1 and sys.argv[1]:
        raw_path = sys.argv[1].strip('\"\'')
        candidate = Path(raw_path)
        if candidate.is_file() and candidate.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]:
            import urllib.parse
            url += f"?preload={urllib.parse.quote(str(candidate.resolve()))}"

    # Launch native desktop window via Windows WebView2
    icon_file = BUNDLE_DIR / "assets" / "icon.ico"
    icon_arg = str(icon_file) if icon_file.exists() else None

    window = webview.create_window(
        title="Pravix Image Upscaler",
        url=url,
        width=1280,
        height=850,
        min_size=(1000, 700),
        background_color="#0f1118"
    )
    
    # gui='edgechromium' forces the modern Microsoft Edge WebView2 runtime
    webview.start(gui="edgechromium", icon=icon_arg)

if __name__ == "__main__":
    main()
