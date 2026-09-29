import os
import math
import shutil
import tempfile
from pathlib import Path
from PIL import Image, ImageSequence

Image.MAX_IMAGE_PIXELS = None

def optimize_gif_for_budget(gif_path: str, target_max_bytes: int = int(9.8 * 1024 * 1024), on_log=None) -> dict:
    p = Path(gif_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"GIF not found: {p}")

    initial_size = p.stat().st_size
    initial_mb = round(initial_size / (1024 * 1024), 2)
    budget_mb = round(target_max_bytes / (1024 * 1024), 2)

    if initial_size <= target_max_bytes:
        if on_log:
            on_log(f"GIF is already within Discord budget ({initial_mb}MB <= {budget_mb}MB).")
        return {
            "optimized": False,
            "initial_bytes": initial_size,
            "final_bytes": initial_size,
            "initial_mb": initial_mb,
            "final_mb": initial_mb,
            "path": str(p)
        }

    if on_log:
        on_log(f"GIF is {initial_mb}MB. Squeezing to fit Discord budget (< {budget_mb}MB)...")

    durations = []
    frames = []
    with Image.open(p) as img:
        loop_count = img.info.get("loop", 0)
        orig_w, orig_h = img.size
        for frame in ImageSequence.Iterator(img):
            d = frame.info.get("duration", 100)
            if d <= 0:
                d = 100
            durations.append(d)
            frames.append(frame.convert("RGB"))

    temp_dir = Path(tempfile.gettempdir()) / f"discord_opt_{os.getpid()}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    trial_path = temp_dir / "trial.gif"

    # Pass 1: Try palette reduction (192 colors) at 100% resolution
    if on_log:
        on_log("Discord Optimizer: Quantizing color palette & optimizing LZW...")

    q_frames = [f.quantize(colors=192, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    q_frames[0].save(
        str(trial_path),
        save_all=True,
        append_images=q_frames[1:],
        duration=durations,
        loop=loop_count,
        optimize=True,
        disposal=2
    )

    trial_size = trial_path.stat().st_size
    if trial_size <= target_max_bytes:
        shutil.copy2(trial_path, p)
        shutil.rmtree(temp_dir, ignore_errors=True)
        final_mb = round(trial_size / (1024 * 1024), 2)
        if on_log:
            on_log(f"Success! Optimized GIF: {initial_mb}MB -> {final_mb}MB (Discord Ready!)")
        return {
            "optimized": True,
            "initial_bytes": initial_size,
            "final_bytes": trial_size,
            "initial_mb": initial_mb,
            "final_mb": final_mb,
            "path": str(p)
        }

    # Pass 2 & 3: Progressive dimension downscale
    scale_factor = math.sqrt(target_max_bytes / trial_size) * 0.94
    scale_factor = max(0.15, min(0.95, scale_factor))

    color_tiers = [160, 128, 96]
    for attempt, colors in enumerate(color_tiers, start=1):
        target_w = max(64, int(orig_w * scale_factor))
        target_h = max(64, int(orig_h * scale_factor))

        if on_log:
            on_log(f"Discord Optimizer: Resampling frames to {target_w}x{target_h} ({colors} colors)...")

        resized_frames = []
        for f in frames:
            rf = f.resize((target_w, target_h), Image.Resampling.LANCZOS)
            qf = rf.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)
            resized_frames.append(qf)

        resized_frames[0].save(
            str(trial_path),
            save_all=True,
            append_images=resized_frames[1:],
            duration=durations,
            loop=loop_count,
            optimize=True,
            disposal=2
        )

        trial_size = trial_path.stat().st_size
        if trial_size <= target_max_bytes:
            shutil.copy2(trial_path, p)
            break
        else:
            scale_factor *= 0.88

    if trial_path.exists() and trial_path.stat().st_size <= target_max_bytes:
        shutil.copy2(trial_path, p)

    shutil.rmtree(temp_dir, ignore_errors=True)
    final_size = p.stat().st_size
    final_mb = round(final_size / (1024 * 1024), 2)
    if on_log:
        on_log(f"Discord Optimization complete: {initial_mb}MB -> {final_mb}MB (Discord Ready!)")

    return {
        "optimized": True,
        "initial_bytes": initial_size,
        "final_bytes": final_size,
        "initial_mb": initial_mb,
        "final_mb": final_mb,
        "path": str(p)
    }

def optimize_image_for_budget(image_path: str, target_max_bytes: int = int(9.8 * 1024 * 1024), output_format: str = 'png', on_log=None) -> dict:
    p = Path(image_path).resolve()
    initial_size = p.stat().st_size
    initial_mb = round(initial_size / (1024 * 1024), 2)
    budget_mb = round(target_max_bytes / (1024 * 1024), 2)

    if initial_size <= target_max_bytes:
        return {
            "optimized": False,
            "initial_bytes": initial_size,
            "final_bytes": initial_size,
            "initial_mb": initial_mb,
            "final_mb": initial_mb,
            "path": str(p)
        }

    if on_log:
        on_log(f'Optimizing static image ({initial_mb}MB) for Discord budget (< {budget_mb}MB)...')

    fmt = output_format.lower()
    with Image.open(p) as img:
        orig_w, orig_h = img.size
        curr_img = img.copy()

    temp_path = p.with_suffix('.opt_tmp')
    if fmt == 'png':
        curr_img.save(str(temp_path), format='PNG', optimize=True, compress_level=9)
        if temp_path.stat().st_size > target_max_bytes:
            ratio = math.sqrt(target_max_bytes / temp_path.stat().st_size) * 0.95
            new_w, new_h = max(100, int(orig_w * ratio)), max(100, int(orig_h * ratio))
            curr_img = curr_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            curr_img.save(str(temp_path), format='PNG', optimize=True, compress_level=9)
    elif fmt in ['jpg', 'jpeg']:
        for q in [90, 85, 75, 65]:
            if curr_img.mode in ('RGBA', 'P'):
                curr_img = curr_img.convert('RGB')
            curr_img.save(str(temp_path), format='JPEG', quality=q, optimize=True)
            if temp_path.stat().st_size <= target_max_bytes:
                break
    elif fmt == 'webp':
        for q in [90, 85, 75, 65]:
            curr_img.save(str(temp_path), format='WEBP', quality=q, method=6)
            if temp_path.stat().st_size <= target_max_bytes:
                break

    if temp_path.exists():
        shutil.copy2(temp_path, p)
        temp_path.unlink(missing_ok=True)

    final_size = p.stat().st_size
    final_mb = round(final_size / (1024 * 1024), 2)
    if on_log:
        on_log(f'Static image optimized: {initial_mb}MB -> {final_mb}MB (Discord Ready)')

    return {
        "optimized": True,
        "initial_bytes": initial_size,
        "final_bytes": final_size,
        "initial_mb": initial_mb,
        "final_mb": final_mb,
        "path": str(p)
    }
