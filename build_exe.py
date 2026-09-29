import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def build():
    print("=======================================================")
    print("[*] Building Standalone Windows Executable: PravixImageUpscaler")
    print("=======================================================")
    
    dist_dir = ROOT_DIR / "dist"
    build_dir = ROOT_DIR / "build"
    icon_path = ROOT_DIR / "assets" / "icon.ico"
    
    # PyInstaller arguments for Single Standalone Executable
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "PravixUpscaler_Portable",
        "--icon", str(icon_path),
        "--add-data", f"{ROOT_DIR / 'frontend'};frontend",
        "--add-data", f"{ROOT_DIR / 'assets'};assets",
        "--add-data", f"{ROOT_DIR / 'backend' / 'bin'};backend/bin",
        "--add-data", f"{ROOT_DIR / 'backend' / 'models'};backend/models",
        "--exclude-module", "torch",
        "--exclude-module", "torchvision",
        "--exclude-module", "torchaudio",
        "--exclude-module", "scipy",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--hidden-import", "flask",
        "--hidden-import", "flask_cors",
        "--hidden-import", "cv2",
        "--hidden-import", "onnxruntime",
        "--hidden-import", "onnxruntime.capi._pybind_state",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageSequence",
        "--hidden-import", "PIL.ImageFilter",
        "--hidden-import", "webview",
        "--hidden-import", "clr_loader",
        "--hidden-import", "pythonnet",
        "--collect-all", "webview",
        "--collect-all", "onnxruntime",
        "--collect-all", "cv2",
        str(ROOT_DIR / "desktop_app.py")
    ]
    
    print("Running PyInstaller command:")
    print(" ".join(cmd))
    
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"❌ Build failed with exit code {res.returncode}")
        sys.exit(res.returncode)
        
    print("\n=======================================================")
    print("[+] BUILD SUCCESSFUL!")
    output_exe = dist_dir / "PravixImageUpscaler.exe"
    print(f"Single Standalone Executable created at:")
    print(f"--> {output_exe}")
    print("=======================================================")

if __name__ == "__main__":
    build()
