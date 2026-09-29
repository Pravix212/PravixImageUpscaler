import os
import sys
import time
from pathlib import Path
from PIL import Image, ImageDraw

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.engine_manager import ensure_model, get_models_catalog, AVAILABLE_MODELS
from backend.image_processor import process_static_image
from backend.gif_processor import process_animated_gif

def create_sample_image(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (128, 128), color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 108, 108], outline=(0, 255, 200), width=3)
    draw.ellipse([40, 40, 88, 88], fill=(255, 80, 120))
    draw.text((35, 55), "AI 4X", fill=(255, 255, 255))
    img.save(path, "PNG")
    print(f"Created sample image: {path} (128x128)")

def create_sample_gif(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    for i in range(6):
        frame = Image.new("RGB", (100, 100), color=(20, 20, 35))
        draw = ImageDraw.Draw(frame)
        x = 15 + i * 12
        y = 50
        draw.ellipse([x, y-15, x+30, y+15], fill=(80, 180, 255))
        draw.text((10, 10), f"F:{i+1}", fill=(255, 255, 0))
        frames.append(frame)

    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=150,
        loop=0
    )
    print(f"Created sample animated GIF: {path} (6 frames, 100x100)")

def run_tests():
    print("=== Testing Local AI Upscaler Core ===")
    
    test_dir = Path("backend/temp/test_run")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Test model check & download
    print("\n[1/3] Ensuring fast model 'upscayl-lite-4x' is downloaded...")
    ensure_model("upscayl-lite-4x", on_log=print)
    
    # 2. Test static image upscaling
    print("\n[2/3] Testing Static Image Upscaling...")
    sample_img = test_dir / "sample_in.png"
    sample_out = test_dir / "sample_out.png"
    create_sample_image(sample_img)
    
    res_img = process_static_image(
        input_path=str(sample_img),
        output_path=str(sample_out),
        model_id="upscayl-lite-4x",
        scale=4,
        on_log=print
    )
    print(f"Image result: {res_img['width_before']}x{res_img['height_before']} -> {res_img['width_after']}x{res_img['height_after']} in {res_img['elapsed_seconds']}s")
    assert res_img["width_after"] == 512, "Expected width 512"
    assert res_img["height_after"] == 512, "Expected height 512"
    print("✓ Static image upscale test passed!")

    # 3. Test animated GIF upscaling
    print("\n[3/3] Testing Animated GIF Upscaling...")
    sample_gif = test_dir / "sample_in.gif"
    sample_gif_out = test_dir / "sample_out.gif"
    create_sample_gif(sample_gif)
    
    res_gif = process_animated_gif(
        input_path=str(sample_gif),
        output_path=str(sample_gif_out),
        model_id="upscayl-lite-4x",
        scale=4,
        output_format="gif",
        on_log=print
    )
    print(f"GIF result: {res_gif['width_before']}x{res_gif['height_before']} -> {res_gif['width_after']}x{res_gif['height_after']} ({res_gif['total_frames']} frames) in {res_gif['elapsed_seconds']}s")
    assert res_gif["width_after"] == 400, "Expected width 400"
    assert res_gif["total_frames"] == 6, "Expected 6 frames"
    print("✓ Animated GIF upscale test passed!")
    
    print("\n==========================================")
    print("🎉 ALL CORE TESTS PASSED SUCCESSFULLY! 🎉")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
