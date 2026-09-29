

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

# Pravix Image Upscaler

A standalone, local image and animated GIF upscaler for Windows. Runs 100% offline on your local GPU using Vulkan NCNN, DirectML, and GFPGAN face restoration.

---

## Features

- **Local GPU Acceleration**: Runs completely on your device without cloud dependencies, API keys, or subscriptions. Compatible with modern NVIDIA, AMD, and Intel GPUs via Vulkan.
- **Discord File Size Optimizer**: Automatically compresses upscaled images and animated GIFs to stay strictly under Discord upload limits (10 MB for avatars and profile banners, 25 MB for standard chat).
- **AI Face Restoration**: Integrates GFPGAN v1.4 with OpenCV YuNet face detection to reconstruct realistic facial details and skin textures on low-resolution portrait photos.
- **Animated GIF Upscaling**: Extracts and processes individual frames in batch, preserving original timing, frame rates, and looping with zero ghosting. Supports export to animated GIF or 24-bit TrueColor animated WebP.
- **6 Bundled AI Models**:
  - `UltraSharp`: Sharpening and deblurring for digital images and detailed artwork.
  - `Universal Standard`: General-purpose model for natural photography and real-world scenes.
  - `Digital Art`: Trained specifically for anime, manga, and digital illustrations.
  - `Remacri`: Designed for high-frequency textures, fabrics, and architectural details.
  - `High Fidelity`: Subtle restoration that preserves natural film grain.
  - `Fast Lite`: Lightweight model optimized for rapid batch processing.
- **Windows Integration**: Optional right-click context menu integration ("Upscale with Pravix") in Windows Explorer to open and preload images directly.
- **Default Desktop Output**: Automatically creates an `Output` directory on the user's Desktop for convenient access, with automatic detection for OneDrive-synced desktop paths.

---

## Downloads

Precompiled binaries for Windows 10 and 11 are available on the [Releases](https://github.com/Pravix212/Pravix-Image-Upscaler/releases) page:

- **Setup Installer (`PravixUpscaler_Setup.exe`)**: Recommended for everyday use. Installs the application, adds Start Menu and Desktop shortcuts, and sets up Explorer right-click integration.
- **Standalone Portable (`PravixUpscaler_Portable.exe`)**: Single-file executable that requires no installation. Useful for portable drives or running without modifying system settings.

---

## Running from Source

If you prefer to run or modify the application locally using Python:

### Requirements
- Python 3.10 or newer
- Windows 10 / 11 (64-bit)
- A GPU with Vulkan support

### Installation
```bash
# Clone the repository
git clone https://github.com/Pravix212/Pravix-Image-Upscaler.git
cd Pravix-Image-Upscaler

# Install dependencies
pip install -r requirements.txt

# Run the application
python desktop_app.py
