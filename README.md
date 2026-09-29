# 🚀 Pravix Image Upscaler

<p align="center">
  <img src="frontend/assets/logo.png" alt="Pravix Image Upscaler" width="160">
  <br>
  <b>A 100% offline, GPU-accelerated desktop application to upscale images, enhance portraits, and optimize animated GIFs for Discord.</b>
  <br>
  <i>Powered by Vulkan NCNN, DirectML, and GFPGAN AI models.</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-blue?style=flat-square&logo=windows" alt="Platform">
  <img src="https://img.shields.io/badge/Hardware-Vulkan%20%2F%20DirectML-orange?style=flat-square" alt="Hardware Acceleration">
  <img src="https://img.shields.io/badge/AI%20Engine-NCNN%20%2B%20GFPGAN-red?style=flat-square" alt="AI Engine">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

---

## ✨ Features

- **⚡ 100% Offline & Free**: Zero cloud subscriptions, zero tracking, no internet connection required. Runs entirely on your local PC GPU (NVIDIA, AMD, Intel).
- **🎮 Discord File Size Optimizer**:
  - Automatically compresses upscaled animated GIFs and images to strictly fit under **10.0 MB** (Discord PFP / Profile Banner limit) or **25.0 MB** (Standard Discord upload limit).
  - Uses intelligent palette quantization and proportional Lanczos resampling while maximizing image clarity.
- **👤 AI Face Restoration (GFPGAN v1.4)**:
  - Detects human faces with OpenCV YuNet and restores photorealistic eyes, skin pores, and facial details on portrait photos.
  - Adjustable Likeness vs. Detail slider (30% to 100%).
- **🎞️ Full Animated GIF Upscaling**:
  - Preserves exact frame timings, delays, and loop settings with zero ghosting.
  - Export to high-res animated GIF or 24-bit TrueColor **Animated WebP**.
- **🧠 6 Pre-Trained AI Models Included**:
  - **UltraSharp (4x)**: Extreme edge clarity, deblurring, and crisp details.
  - **Universal Standard (4x)**: Best general-purpose model for natural photos.
  - **Digital Art (4x)**: Specially trained for anime, manga, 2D art, and digital paintings.
  - **Remacri (4x)**: Deep textured details (architecture, fabrics, natural surfaces).
  - **High Fidelity (4x)**: Faithful restoration preserving fine grain without over-sharpening.
  - **Fast Lite (4x)**: Rapid lightweight model optimized for high-frame-count animations.
- **🖱️ Windows Explorer Integration**:
  - Right-click any image in Windows File Explorer ➔ **"Upscale with Pravix"** to instantly open and preload it.
- **📂 Smart Desktop Output**:
  - Automatically creates and saves upscaled files into an `Output` folder directly on your Windows Desktop (with OneDrive support).

---

## 📥 Download & Installation

You can run **Pravix Image Upscaler** using either the precompiled releases or directly from source.

### Option 1: Pre-built Binaries (Releases)

Download the latest version from the [**Releases**](https://github.com/Pravix212/Pravix-Image-Upscaler/releases) tab:

1. **Windows Setup Installer (`PravixUpscaler_Setup.exe`)** *(Recommended)*:
   - Installs to your PC with instant 0.2s launch speed.
   - Adds Desktop icon, Start Menu shortcut, and Windows right-click context menu integration.
2. **Standalone Portable (`PravixUpscaler_Portable.exe`)**:
   - Single `.exe` file. No installation required. Runs anywhere from a USB stick or external drive.

---

### Option 2: Running from Source

#### Prerequisites
- **Python 3.10+**
- A Vulkan-compatible GPU (NVIDIA GeForce, AMD Radeon, or Intel Arc)

#### Setup
```bash
# 1. Clone the repository
git clone https://github.com/Pravix212/Pravix-Image-Upscaler.git
cd Pravix-Image-Upscaler

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch Desktop App
python desktop_app.py
```

---

## 🛠️ Building Standalone Binaries

To compile your own executable or Windows setup wizard from source:

```bash
# Build the Standalone Portable Executable (.exe)
python build_exe.py

# Build the Inno Setup Windows Installer (.exe)
python build_installer.py
```
*(Requires [Inno Setup 6](https://jrsoftware.org/isdl.php) installed to compile the setup installer).*

---

## ⚖️ License & Acknowledgements

- Built with [Vulkan NCNN](https://github.com/Tencent/ncnn) and [Upscayl](https://github.com/upscayl/upscayl) models.
- AI Face Restoration powered by [GFPGAN](https://github.com/TencentARC/GFPGAN) and [OpenCV YuNet](https://github.com/opencv/opencv_zoo).
- Licensed under the [MIT License](LICENSE).

---
<p align="center">Made with ❤️ by <b>Pravix</b></p>
