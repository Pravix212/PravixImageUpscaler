import os
import sys
import urllib.request
from pathlib import Path
import cv2
import numpy as np

# Ensure PyInstaller / BUNDLE_ROOT compatibility
if getattr(sys, 'frozen', False):
    APP_ROOT = Path(sys.executable).parent
    BUNDLE_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parent.parent
    BUNDLE_ROOT = APP_ROOT

possible_models = [
    BUNDLE_ROOT / 'backend' / 'models',
    BUNDLE_ROOT / 'models',
    APP_ROOT / 'backend' / 'models',
    APP_ROOT / 'models',
    Path(__file__).resolve().parent / 'models'
]
MODELS_DIR = next((p for p in possible_models if p.exists()), possible_models[0])

YUNET_FILENAME = 'face_detection_yunet_2023mar.onnx'
GFPGAN_FILENAME = 'GFPGANv1.4.onnx'

YUNET_URL = 'https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx'
GFPGAN_URL = 'https://huggingface.co/hacksider/deep-live-cam/resolve/main/GFPGANv1.4.onnx'

FFHQ_TEMPLATE = np.array([
    [192.98138, 239.94708],  # viewer left eye
    [318.90277, 240.20473],  # viewer right eye
    [256.63416, 314.01935],  # nose tip
    [201.26117, 371.41043],  # viewer left mouth corner
    [313.08905, 371.15118]   # viewer right mouth corner
], dtype=np.float32)

_SESSION_CACHE = None
_DETECTOR_CACHE = None

def download_file_with_progress(url: str, dest: Path, desc: str = 'Downloading', on_log=None):
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = dest.with_suffix('.tmp')
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10; Win64; x64)'})
    with urllib.request.urlopen(req) as resp, open(temp_dest, 'wb') as f:
        total = int(resp.headers.get('Content-Length', 0))
        downloaded = 0
        block_size = 1024 * 1024  # 1MB
        last_pct = -1
        while True:
            chunk = resp.read(block_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0 and on_log:
                pct = int((downloaded / total) * 100)
                if pct != last_pct and pct % 5 == 0:
                    last_pct = pct
                    on_log(f'{desc}: {pct}% ({downloaded // (1024*1024)}MB / {total // (1024*1024)}MB)')
    
    if dest.exists():
        dest.unlink()
    temp_dest.rename(dest)

def is_face_restoration_installed() -> bool:
    yunet_p = MODELS_DIR / YUNET_FILENAME
    gfpgan_p = MODELS_DIR / GFPGAN_FILENAME
    return yunet_p.exists() and yunet_p.stat().st_size > 0 and gfpgan_p.exists() and gfpgan_p.stat().st_size > 0

def ensure_face_models(on_log=None):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    yunet_p = MODELS_DIR / YUNET_FILENAME
    gfpgan_p = MODELS_DIR / GFPGAN_FILENAME

    if not yunet_p.exists() or yunet_p.stat().st_size == 0:
        if on_log:
            on_log('Downloading Face Landmark Detector (YuNet)...')
        download_file_with_progress(YUNET_URL, yunet_p, 'Downloading Face Detector', on_log)

    if not gfpgan_p.exists() or gfpgan_p.stat().st_size == 0:
        if on_log:
            on_log('Downloading AI Face Restoration Model (GFPGAN v1.4 ~324MB)...')
        download_file_with_progress(GFPGAN_URL, gfpgan_p, 'Downloading Face Model', on_log)

def get_inference_session(on_log=None):
    global _SESSION_CACHE
    if _SESSION_CACHE is not None:
        return _SESSION_CACHE

    ensure_face_models(on_log)
    gfpgan_p = MODELS_DIR / GFPGAN_FILENAME

    import onnxruntime as ort
    providers = ['DmlExecutionProvider', 'CPUExecutionProvider']
    available = ort.get_available_providers()
    selected_providers = [p for p in providers if p in available]
    if not selected_providers:
        selected_providers = ['CPUExecutionProvider']

    if on_log:
        on_log(f'Initializing GFPGAN engine with {selected_providers[0]}...')

    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    _SESSION_CACHE = ort.InferenceSession(str(gfpgan_p), sess_options=sess_options, providers=selected_providers)
    return _SESSION_CACHE

def restore_faces_in_image(img_bgr: np.ndarray, fidelity: float = 0.85, on_log=None) -> np.ndarray:
    ensure_face_models(on_log)
    yunet_p = MODELS_DIR / YUNET_FILENAME

    h, w, _ = img_bgr.shape
    detector = cv2.FaceDetectorYN.create(
        str(yunet_p),
        '',
        (w, h),
        score_threshold=0.45,
        nms_threshold=0.3,
        top_k=5000
    )

    if on_log:
        on_log('Scanning image for human faces...')

    _, faces = detector.detect(img_bgr)
    if faces is None or len(faces) == 0:
        if on_log:
            on_log('No human faces detected in image. Keeping upscaled result.')
        return img_bgr

    num_faces = len(faces)
    if on_log:
        on_log(f'Detected {num_faces} face(s). Restoring realistic facial details with GFPGAN...')

    session = get_inference_session(on_log)
    input_name = session.get_inputs()[0].name

    result_img = img_bgr.copy().astype(np.float32)

    base_mask = np.zeros((512, 512), dtype=np.float32)
    cv2.ellipse(base_mask, (256, 300), (170, 200), 0, 0, 360, 1.0, -1)
    base_mask = cv2.GaussianBlur(base_mask, (51, 51), 20)

    for idx, face in enumerate(faces):
        confidence = face[-1]
        if confidence < 0.4:
            continue

        if on_log:
            on_log(f'Restoring face #{idx+1}/{num_faces} (confidence: {int(confidence*100)}%)...')

        landmarks = face[4:14].reshape(5, 2).astype(np.float32)

        M, _ = cv2.estimateAffinePartial2D(landmarks, FFHQ_TEMPLATE)
        if M is None:
            continue

        aligned_bgr = cv2.warpAffine(
            img_bgr, M, (512, 512),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )
        aligned_rgb = cv2.cvtColor(aligned_bgr, cv2.COLOR_BGR2RGB)

        tensor = (aligned_rgb.astype(np.float32) / 255.0 - 0.5) / 0.5
        tensor = np.transpose(tensor, (2, 0, 1))[np.newaxis, ...]

        out = session.run(None, {input_name: tensor})[0]
        out = (out[0].transpose(1, 2, 0).clip(-1, 1) * 0.5 + 0.5) * 255.0
        restored_bgr = cv2.cvtColor(out.astype(np.uint8), cv2.COLOR_RGB2BGR).astype(np.float32)

        blended_face = restored_bgr * fidelity + aligned_bgr.astype(np.float32) * (1.0 - fidelity)

        inv_M = cv2.invertAffineTransform(M)
        restored_warped = cv2.warpAffine(
            blended_face, inv_M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REFLECT
        )
        mask_warped = cv2.warpAffine(
            base_mask, inv_M, (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT
        )
        mask_warped = np.expand_dims(mask_warped, axis=2)

        result_img = restored_warped * mask_warped + result_img * (1.0 - mask_warped)

    if on_log:
        on_log('Face restoration and seamless portrait blending complete!')

    return np.clip(result_img, 0, 255).astype(np.uint8)
