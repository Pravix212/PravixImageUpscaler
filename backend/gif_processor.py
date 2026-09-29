import os
import shutil
import time
import tempfile
from pathlib import Path
from PIL import Image, ImageSequence
# Remove Pillow decompression bomb pixel limit
Image.MAX_IMAGE_PIXELS = None
from backend.engine_manager import run_engine_command, ensure_model

def extract_gif_frames(gif_path: Path, output_dir: Path) -> dict:
    """
    Extracts all frames of an animated GIF cleanly into 24-bit RGB PNG frames,
    preserving exact per-frame durations and loop counts with zero ghosting.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with Image.open(gif_path) as img:
        is_animated = getattr(img, "is_animated", False)
        loop_count = img.info.get("loop", 0)
        
        frames_metadata = []
        durations = []
        
        for frame_idx, frame in enumerate(ImageSequence.Iterator(img)):
            duration = frame.info.get("duration", 100)
            if duration <= 0:
                duration = 100  # fallback to standard 10 fps if duration missing
            durations.append(duration)
            
            # Convert directly to clean 24-bit RGB to avoid transparent canvas accumulation
            frame_rgb = frame.convert("RGB")
            frame_filename = f"frame_{frame_idx:05d}.png"
            frame_filepath = output_dir / frame_filename
            frame_rgb.save(frame_filepath, "PNG")
            
            frames_metadata.append({
                "index": frame_idx,
                "filename": frame_filename,
                "duration": duration
            })

    return {
        "is_animated": is_animated,
        "total_frames": len(durations),
        "durations": durations,
        "loop_count": loop_count,
        "original_size": img.size
    }


def reassemble_gif(frames_dir: Path, output_path: Path, durations: list, loop_count: int = 0, format_type: str = "gif", target_size: tuple = None, enhance_quality: bool = True):
    """
    Reassembles upscaled PNG frames into a pristine animated GIF or Animated WebP
    with full frame timing and smooth color reproduction.
    """
    frame_files = sorted(list(frames_dir.glob("*.png")))
    if not frame_files:
        raise FileNotFoundError(f"No upscaled frames found in {frames_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from PIL import ImageFilter
    loaded_frames = []
    for f in frame_files:
        img = Image.open(f)
        if target_size and img.size != target_size:
            img = img.resize(target_size, Image.Resampling.LANCZOS)
        if enhance_quality:
            img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=20, threshold=2))
        loaded_frames.append(img)
    
    if format_type.lower() in ["webp", "animated_webp"]:
        # Save as Animated WebP (true 24-bit TrueColor, lossless/high quality)
        loaded_frames[0].save(
            str(output_path),
            save_all=True,
            append_images=loaded_frames[1:],
            duration=durations,
            loop=loop_count,
            quality=92,
            method=4
        )
    else:
        # Standard Animated GIF: convert to solid RGB and save cleanly without crawling dither noise
        rgb_frames = [f.convert("RGB") for f in loaded_frames]
        rgb_frames[0].save(
            str(output_path),
            save_all=True,
            append_images=rgb_frames[1:],
            duration=durations,
            loop=loop_count,
            optimize=False,
            disposal=2
        )

    # Close open image handles
    for f in loaded_frames:
        f.close()

    return str(output_path)


def process_animated_gif(
    input_path: str,
    output_path: str,
    model_id: str = "ultrasharp-4x",
    scale: int = 2,
    tile_size: int = 0,
    gpu_id: int = 0,
    custom_width: int = None,
    output_format: str = "gif",
    enhance_quality: bool = True,
    discord_optimize: bool = False,
    discord_target_mb: float = 10.0,
    on_log=None
) -> dict:
    """
    High-level function to upscale an animated GIF:
    1. Extracts individual frames and timing metadata.
    2. Batch-upscales frames using the local AI engine.
    3. Reassembles them with optional Lanczos SSAA into high-fidelity animated GIF or WebP.
    """
    input_p = Path(input_path).resolve()
    output_p = Path(output_path).resolve()
    
    start_time = time.time()
    work_id = f"gif_{int(time.time()*1000)}"
    temp_base = Path(tempfile.gettempdir()) / "PravixUpscaler" / "temp" / f"gif_{work_id}"
    frames_in = temp_base / "frames_in"
    frames_out = temp_base / "frames_out"
    
    try:
        if on_log:
            on_log("Analyzing and extracting GIF frames...")
            
        meta = extract_gif_frames(input_p, frames_in)
        total_frames = meta["total_frames"]
        orig_w, orig_h = meta["original_size"]
        file_size_before = input_p.stat().st_size
        
        target_w = custom_width if custom_width else orig_w * scale
        target_h = int(orig_h * (target_w / orig_w))
        target_size = (target_w, target_h)

        # Run engine at target scale (2x, 3x, 4x)
        engine_scale = scale

        if on_log:
            on_log(f"Extracted {total_frames} frames ({orig_w}x{orig_h}). Target: {target_w}x{target_h} ({scale}x). Launching GPU batch upscale...")

        frames_out.mkdir(parents=True, exist_ok=True)
        
        # Batch upscale the frames directory with upscayl-bin
        run_engine_command(
            input_path=str(frames_in),
            output_path=str(frames_out),
            model_id=model_id,
            scale=engine_scale,
            tile_size=tile_size,
            gpu_id=gpu_id,
            custom_width=None,
            format_out="png",
            on_log=on_log
        )
        
        if on_log:
            on_log("All frames upscaled! Reassembling animation with Lanczos refinement...")

        reassemble_gif(
            frames_dir=frames_out,
            output_path=output_p,
            durations=meta["durations"],
            loop_count=meta["loop_count"],
            format_type=output_format,
            target_size=target_size,
            enhance_quality=enhance_quality
        )

        discord_info = None
        if discord_optimize:
            from backend.optimizer import optimize_gif_for_budget
            target_bytes = int(discord_target_mb * 1024 * 1024 * 0.98)
            discord_info = optimize_gif_for_budget(str(output_p), target_max_bytes=target_bytes, on_log=on_log)
        
        with Image.open(output_p) as final_img:
            new_w, new_h = final_img.size
            file_size_after = output_p.stat().st_size

        elapsed = round(time.time() - start_time, 2)
        if on_log:
            on_log(f"GIF Upscaling complete! {orig_w}x{orig_h} -> {new_w}x{new_h} ({total_frames} frames) in {elapsed}s")

        return {
            "success": True,
            "input_path": str(input_p),
            "output_path": str(output_p),
            "total_frames": total_frames,
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

    finally:
        if temp_base.exists():
            shutil.rmtree(str(temp_base), ignore_errors=True)
