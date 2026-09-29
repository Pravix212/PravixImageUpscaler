import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ISCC_PATH = Path(r"C:\Users\Prav2\AppData\Local\Programs\Inno Setup 6\ISCC.exe")

def build_installer():
    print("=======================================================")
    print("[*] STEP 1: Building Onedir Application for Installer")
    print("=======================================================")
    
    icon_path = ROOT_DIR / "assets" / "icon.ico"
    
    # 1. Build Onedir app
    cmd_pyinstaller = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "PravixUpscaler",
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
    
    res = subprocess.run(cmd_pyinstaller, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"❌ PyInstaller build failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    print("\n=======================================================")
    print("[*] STEP 2: Compiling Windows Installer (Inno Setup)")
    print("=======================================================")
    
    if not ISCC_PATH.exists():
        print(f"❌ Inno Setup compiler not found at {ISCC_PATH}")
        sys.exit(1)
        
    cmd_inno = [str(ISCC_PATH), "/Qp", str(ROOT_DIR / "installer.iss")]
    res_inno = subprocess.run(cmd_inno, cwd=str(ROOT_DIR))
    if res_inno.returncode != 0:
        print(f"❌ Inno Setup compilation failed with exit code {res_inno.returncode}")
        sys.exit(res_inno.returncode)

    # 3. Ensure Portable exe has clear name
    portable_src = ROOT_DIR / "dist" / "PravixImageUpscaler.exe"
    portable_dst = ROOT_DIR / "dist" / "PravixUpscaler_Portable.exe"
    if portable_src.exists() and not portable_dst.exists():
        shutil.copy2(portable_src, portable_dst)

    print("\n=======================================================")
    print("[+] ALL BUILDS SUCCESSFUL!")
    print("-------------------------------------------------------")
    print(f"1. Windows Installer (Setup Wizard):")
    print(f"   --> {ROOT_DIR / 'dist' / 'PravixUpscaler_Setup.exe'}")
    print(f"2. Standalone Portable Executable:")
    print(f"   --> {ROOT_DIR / 'dist' / 'PravixUpscaler_Portable.exe'}")
    print("=======================================================")

if __name__ == "__main__":
    build_installer()
