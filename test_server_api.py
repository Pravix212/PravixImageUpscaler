import os
import sys
import time
import io
from pathlib import Path
from PIL import Image, ImageDraw

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.server import app, tasks

def run_api_tests():
    print("=== Testing Server API and End-to-End Upscaling ===")
    client = app.test_client()

    # 1. Test /api/system
    print("\n[1/4] Testing GET /api/system...")
    res = client.get("/api/system")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    sys_data = res.get_json()
    print(f"System Response: {sys_data}")
    assert "gpu" in sys_data
    print("✓ GET /api/system passed!")

    # 2. Test /api/models
    print("\n[2/4] Testing GET /api/models...")
    res = client.get("/api/models")
    assert res.status_code == 200
    models_data = res.get_json()
    print(f"Found {len(models_data['models'])} models: {[m['id'] for m in models_data['models']]}")
    assert len(models_data["models"]) >= 5
    print("✓ GET /api/models passed!")

    # 3. Test POST /api/upscale with Static Image
    print("\n[3/4] Testing POST /api/upscale with Static Image...")
    img_buf = io.BytesIO()
    test_img = Image.new("RGB", (64, 64), color=(40, 60, 120))
    d = ImageDraw.Draw(test_img)
    d.rectangle([10, 10, 54, 54], outline=(255, 255, 0), width=2)
    test_img.save(img_buf, format="PNG")
    img_buf.seek(0)

    res = client.post(
        "/api/upscale",
        data={
            "file": (img_buf, "test_api_image.png"),
            "model_id": "upscayl-lite-4x",
            "scale": "4",
            "output_format": "png"
        },
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    task_info = res.get_json()
    task_id = task_info["task_id"]
    print(f"Started task: {task_id}. Waiting for completion...")

    # Wait for task completion
    for _ in range(30):
        t = tasks.get(task_id)
        if t and t["status"] in ["completed", "failed"]:
            break
        time.sleep(0.5)

    assert tasks[task_id]["status"] == "completed", f"Task failed: {tasks[task_id].get('error')}"
    res_info = tasks[task_id]["result"]
    print(f"Image upscaled: {res_info['width_before']}x{res_info['height_before']} -> {res_info['width_after']}x{res_info['height_after']} in {res_info['elapsed_seconds']}s")
    assert res_info["width_after"] == 256
    print("✓ Static image upscale via API passed!")

    # 4. Test POST /api/upscale with Animated GIF
    print("\n[4/4] Testing POST /api/upscale with Animated GIF...")
    gif_buf = io.BytesIO()
    frames = []
    for i in range(4):
        f = Image.new("RGB", (60, 60), color=(20, 20, 40))
        draw = ImageDraw.Draw(f)
        draw.ellipse([10 + i * 8, 20, 25 + i * 8, 35], fill=(0, 255, 200))
        frames.append(f)
    frames[0].save(gif_buf, format="GIF", save_all=True, append_images=frames[1:], duration=120, loop=0)
    gif_buf.seek(0)

    res = client.post(
        "/api/upscale",
        data={
            "file": (gif_buf, "test_api_anim.gif"),
            "model_id": "upscayl-lite-4x",
            "scale": "4",
            "output_format": "gif"
        },
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    gif_task_id = res.get_json()["task_id"]
    print(f"Started GIF task: {gif_task_id}. Waiting for completion...")

    for _ in range(40):
        t = tasks.get(gif_task_id)
        if t and t["status"] in ["completed", "failed"]:
            break
        time.sleep(0.5)

    assert tasks[gif_task_id]["status"] == "completed", f"GIF Task failed: {tasks[gif_task_id].get('error')}"
    gif_res_info = tasks[gif_task_id]["result"]
    print(f"GIF upscaled: {gif_res_info['width_before']}x{gif_res_info['height_before']} -> {gif_res_info['width_after']}x{gif_res_info['height_after']} ({gif_res_info['total_frames']} frames) in {gif_res_info['elapsed_seconds']}s")
    assert gif_res_info["width_after"] == 240
    assert gif_res_info["total_frames"] == 4
    print("✓ Animated GIF upscale via API passed!")

    print("\n=======================================================")
    print("🎉 ALL END-TO-END API TESTS COMPLETED AND PASSED! 🎉")
    print("=======================================================")

if __name__ == "__main__":
    run_api_tests()
