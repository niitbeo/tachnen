"""
Wrapper chung cho nhiều model tách nền.
Mỗi model nhận ảnh BGR (numpy), trả về alpha mask (0–255, uint8).
"""
import cv2
import numpy as np
from pathlib import Path

GOC = Path(__file__).resolve().parent
MODEL_DIR = GOC / "models"

# ============================== Hmhcv1 (có sẵn) ==============================
_hmhcv1_session = None

def _load_hmhcv1():
    global _hmhcv1_session
    if _hmhcv1_session is not None:
        return _hmhcv1_session
    import matting
    _hmhcv1_session = matting
    return matting


def tach_hmhcv1(img_bgr, tinh_bien=True, maxsize=2500):
    """Model gốc Hmhcv1 + tinh biên. Trả về alpha uint8."""
    m = _load_hmhcv1()
    return m.tach(img_bgr, tinh_bien=tinh_bien, maxsize=maxsize)


# ============================== ONNX generic ==============================
_onnx_sessions = {}

def _load_onnx(model_path, input_size):
    key = str(model_path)
    if key in _onnx_sessions:
        return _onnx_sessions[key]
    import onnxruntime as ort
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess = ort.InferenceSession(str(model_path), opts, providers=["CPUExecutionProvider"])
    _onnx_sessions[key] = (sess, input_size)
    return sess, input_size


def _run_onnx(img_bgr, model_path, input_size, normalize_mean=None, normalize_std=None):
    """Chạy model ONNX segmentation, trả alpha uint8."""
    sess, sz = _load_onnx(model_path, input_size)

    h, w = img_bgr.shape[:2]
    # Preprocess: resize to model input, RGB, float32, normalize
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    img_resized = cv2.resize(img_rgb, (sz, sz), interpolation=cv2.INTER_LINEAR)
    img_f = img_resized.astype(np.float32) / 255.0

    if normalize_mean is not None:
        img_f = (img_f - np.array(normalize_mean, dtype=np.float32)) / np.array(normalize_std, dtype=np.float32)

    # NCHW
    inp = np.transpose(img_f, (2, 0, 1))[np.newaxis, ...]

    input_name = sess.get_inputs()[0].name
    output = sess.run(None, {input_name: inp})

    # Output mask — take first output, squeeze
    mask = output[0]
    if mask.ndim == 4:
        mask = mask[0]
    if mask.shape[0] in (1, 2):
        mask = mask[0]  # Take first channel

    # Normalize to 0-1
    mask_min, mask_max = mask.min(), mask.max()
    if mask_max - mask_min > 1e-6:
        mask = (mask - mask_min) / (mask_max - mask_min)
    else:
        mask = np.zeros_like(mask)

    # Resize back to original size
    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
    alpha = np.clip(mask * 255, 0, 255).astype(np.uint8)
    return alpha


# ============================== U2Net Human Seg ==============================
def tach_u2net(img_bgr, **_kwargs):
    """U2Net Human Segmentation — 176MB, chất lượng trung bình-cao."""
    model_path = MODEL_DIR / "u2net_human_seg.onnx"
    if not model_path.is_file():
        raise FileNotFoundError(f"Thiếu model: {model_path}")
    return _run_onnx(
        img_bgr, model_path,
        input_size=320,
        normalize_mean=[0.485, 0.456, 0.406],
        normalize_std=[0.229, 0.224, 0.225],
    )


# ============================== IS-Net (DIS) ==============================
def tach_isnet(img_bgr, **_kwargs):
    """IS-Net (DIS) — 176MB, chất lượng cao, tốt cho viền tóc."""
    model_path = MODEL_DIR / "isnet-general-use.onnx"
    if not model_path.is_file():
        raise FileNotFoundError(f"Thiếu model: {model_path}")
    # IS-Net dùng normalization khác: chỉ /255, không trừ mean/std
    return _run_onnx(
        img_bgr, model_path,
        input_size=1024,
        normalize_mean=None,
        normalize_std=None,
    )


# ============================== Registry ==============================
MODELS = {
    "hmhcv1": {
        "ten": "Hmhcv1 — Gốc (nhanh, 15MB)",
        "ham": tach_hmhcv1,
        "mo_ta": "Model gốc kèm theo, chạy MNN. Nhanh nhất, chất lượng vừa phải.",
    },
    "u2net": {
        "ten": "U2Net Human Seg (chất lượng cao, 176MB)",
        "ham": tach_u2net,
        "mo_ta": "Tốt cho ảnh chân dung, viền sạch hơn. Chạy ONNX.",
    },
}


def liet_ke_models():
    """Trả danh sách models [{id, ten, mo_ta, co_san}]."""
    result = []
    for mid, info in MODELS.items():
        co_san = True
        if mid == "u2net":
            co_san = (MODEL_DIR / "u2net_human_seg.onnx").is_file()
        elif mid == "isnet":
            co_san = (MODEL_DIR / "isnet-general-use.onnx").is_file()
        result.append({"id": mid, "ten": info["ten"], "moTa": info["mo_ta"], "coSan": co_san})
    return result


def tach_nen(img_bgr, model_id="hmhcv1", **kwargs):
    """Tách nền với model đã chọn. Trả về alpha uint8."""
    if model_id not in MODELS:
        model_id = "hmhcv1"
    return MODELS[model_id]["ham"](img_bgr, **kwargs)
