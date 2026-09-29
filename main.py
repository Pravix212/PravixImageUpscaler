import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

# Ensure root dir is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.server import app

def find_chrome_path():
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def launch_app_ui(port=5000):
    url = f"http://127.0.0.1:{port}"
    chrome_path = find_chrome_path()
    
    time.sleep(1.0)  # Wait for server to bind
    if chrome_path:
        print(f"Launching in desktop application mode via Chrome...")
        subprocess.Popen([chrome_path, f"--app={url}", "--window-size=1280,850"])
    else:
        print(f"Opening default browser at {url}...")
        webbrowser.open(url)

if __name__ == "__main__":
    port = 5000
    print("\n" + "=" * 60)
    print("🚀  UPSCAYL+ | LOCAL AI IMAGE & GIF UPSCALER")
    print(f"⚡  Hardware Acceleration: NVIDIA GeForce RTX 5070 (Vulkan)")
    print(f"🌐  Local URL: http://127.0.0.1:{port}")
    print("=" * 60 + "\n")
    
    import threading
    t = threading.Thread(target=launch_app_ui, args=(port,), daemon=True)
    t.start()
    
    # Run server
    app.run(host="127.0.0.1", port=port, debug=False)
