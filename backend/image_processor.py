import os
import shutil
import time
import tempfile
from pathlib import Path
from PIL import Image
# Remove Pillow decompression bomb pixel limit for large high-res images
Image.MAX_IMAGE_PIXELS = None
from backend.engine_manager import run_engine_command, ensure_model

def process_static_image(
    input_path: str,
    output_path: str,
    model_id: str = "ultrasharp-4x",
    scale: int = 2,
    tile_size: int = 0,
    gpu_id: int = 0,
    custom_width: int = None,
    output_format: str = "png",
    enhance_quality: bool = True,
    restore_faces: bool = False,
    face_fidelity: float = 0.75,
    discord_optimize: bool = False,
    discord_target_mb: float = 10.0,
    on_log=None
) -> dict:
    """
    Upscales a static image (PNG, JPG, WEBP, BMP, TIFF) using the AI engine.
    Respects selected scale factor (2x, 3x, 4x) and applies micro-texture
    clarity refinement when enhance_quality is enabled.
    """
    input_p = Path(input_path).resolve()
    output_p = Path(output_path).resolve()
    output_p.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    
    with Image.open(input_p) as orig_img:
        orig_w, orig_h = orig_img.size
        orig_mode = orig_img.mode
        file_size_before = input_p.stat().st_size
        icc_profile = orig_img.info.get("icc_profile")

    target_w = custom_width if custom_width else orig_w * scale
    target_h = int(orig_h * (target_w / orig_w))

    if on_log:
        on_log(f"Opened image {orig_w}x{orig_h} ({orig_mode}). Target: {target_w}x{target_h} ({scale}x)")

    # Run AI engine directly at the user's selected scale (2x, 3x, or 4x)
    engine_scale = scale

    temp_dir = Path(tempfile.gettempdir()) / "PravixUpscaler" / "temp" / f"upscale_{int(time.time()*1000)}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_out_file = temp_dir / f"out.{output_format.lower()}"

    try:
        run_engine_command(
            input_path=str(input_p),
            output_path=str(temp_out_file),
            model_id=model_id,
            scale=engine_scale,
            tile_size=tile_size,
            gpu_id=gpu_id,
            custom_width=None,
            format_out="png",
            on_log=on_log
        )

        if not temp_out_file.exists():
            candidates = list(temp_dir.glob("*.*"))
            if candidates:
                temp_out_file = candidates[0]
            else:
                raise FileNotFoundError(f"Upscaling finished but no output file was created in {temp_dir}")

        # Post-process with Lanczos super-sampling & clarity boost
        with Image.open(temp_out_file) as upscaled_img:
            curr_w, curr_h = upscaled_img.size

            # If downsampling from 4x to 2x/3x, apply reference Lanczos anti-aliasing
            if (curr_w != target_w or curr_h != target_h) and target_w > 0 and target_h > 0:
                if on_log:
                    on_log(f"Applying High-Precision Lanczos Anti-Aliasing ({curr_w}x{curr_h} -> {target_w}x{target_h})...")
                processed_img = upscaled_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                processed_img = upscaled_img.copy()

            # Subtle micro-contrast texture boost
            if enhance_quality:
                if on_log:
                    on_log("Refining micro-textures and edge clarity...")
                from PIL import ImageFilter
                processed_img = processed_img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=24, threshold=2))

            # AI Face Restoration (GFPGAN)
            if restore_faces:
                if on_log:
                    on_log("Applying AI Face Restoration (GFPGAN)...")
                try:
                    from backend.face_restorer import restore_faces_in_image
                    import numpy as np
                    import cv2
                    
                    np_img = np.array(processed_img)
                    if processed_img.mode == "RGBA":
                        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
                        restored_bgr = restore_faces_in_image(bgr, fidelity=face_fidelity, on_log=on_log)
                        restored_rgba = cv2.cvtColor(restored_bgr, cv2.COLOR_BGR2RGBA)
                        restored_rgba[:, :, 3] = np_img[:, :, 3]
                        processed_img = Image.fromarray(restored_rgba)
                    else:
                        if processed_img.mode != "RGB":
                            processed_img = processed_img.convert("RGB")
                            np_img = np.array(processed_img)
                        bgr = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
                        restored_bgr = restore_faces_in_image(bgr, fidelity=face_fidelity, on_log=on_log)
                        restored_rgb = cv2.cvtColor(restored_bgr, cv2.COLOR_BGR2RGB)
                        processed_img = Image.fromarray(restored_rgb)
                except Exception as e:
                    if on_log:
                        on_log(f"Warning: Face restoration failed ({e}); falling back to standard upscale.")

            save_kwargs = {}
            if icc_profile:
                save_kwargs["icc_profile"] = icc_profile

            fmt = output_format.lower()
            if fmt in ["jpg", "jpeg"]:
                if processed_img.mode in ("RGBA", "P"):
                    processed_img = processed_img.convert("RGB")
                processed_img.save(str(output_p), format="JPEG", quality=95, **save_kwargs)
            elif fmt == "webp":
                processed_img.save(str(output_p), format="WEBP", quality=95, **save_kwargs)
            else:
                processed_img.save(str(output_p), format="PNG", **save_kwargs)

    finally:
        if temp_dir.exists():
            shutil.rmtree(str(temp_dir), ignore_errors=True)

    discord_info = None
    if discord_optimize:
        from backend.optimizer import optimize_image_for_budget
        target_bytes = int(discord_target_mb * 1024 * 1024 * 0.98)
        discord_info = optimize_image_for_budget(str(output_p), target_max_bytes=target_bytes, output_format=output_format, on_log=on_log)

    with Image.open(output_p) as final_img:
        new_w, new_h = final_img.size
        file_size_after = output_p.stat().st_size

    elapsed = round(time.time() - start_time, 2)
    if on_log:
        on_log(f"Upscaling complete! {orig_w}x{orig_h} -> {new_w}x{new_h} in {elapsed}s")

    return {
        "success": True,
        "input_path": str(input_p),
        "output_path": str(output_p),
        "width_before": orig_w,
        "height_before": orig_h,
        "width_after": new_w,
        "height_after": new_h,
        "size_before": file_size_before,
        "size_after": file_size_after,
        "discord_optimized": discord_info["optimized"] if discord_info else False,
        "discord_final_mb": discord_info["final_mb"] if discord_info else None,
        "elapsed_seconds": elapsed
    }
