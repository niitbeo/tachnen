#!/usr/bin/env python3
"""Lõi tách nền Leien chạy độc lập: Hmhcv1 (thô) + Hm4Cpv1 (tinh biên).

Cùng bộ weight mà menu "Tách nền" của app dùng, nhưng chạy thẳng bằng MNN nên
không cần engine native, không cần khoá giấy phép.

Cả hai model đều chạy bằng MNN. Nếu thiếu `Hm4Cpv1_original.mnn` thì lùi về bản
IR chạy bằng PyTorch (`hm4cpv1_torch.py`) — cùng kết quả, chỉ nặng thêm ~500 MB
thư viện.

Tham khảo: leien-photo-ai-app/scripts/runtime/human_matting.py
"""

from pathlib import Path

import cv2
import numpy as np

try:
    import MNN
except ImportError:  # pragma: no cover
    MNN = None


MODELS_DIR = Path(__file__).resolve().parent / "models"
MODEL_PATH = MODELS_DIR / "Hmhcv1_original.mnn"
PATCH_MNN_PATH = MODELS_DIR / "Hm4Cpv1_original.mnn"
PATCH_XML_PATH = MODELS_DIR / "Hm4Cpv1_compat.xml"
PATCH_WEIGHTS_PATH = MODELS_DIR / "Hm4Cpv1_compat.bin"

_RUNTIME = None
_PATCH_RUNTIME = None


def _mnn_tensor(arr: np.ndarray):
    return MNN.Tensor(
        tuple(arr.shape),
        MNN.Halide_Type_Float,
        np.ascontiguousarray(arr, dtype=np.float32),
        MNN.Tensor_DimensionType_Caffe,
    )


def _mnn_read(tensor) -> np.ndarray:
    shape = tuple(tensor.getShape())
    host = MNN.Tensor(shape, MNN.Halide_Type_Float,
                      np.zeros(shape, dtype=np.float32),
                      MNN.Tensor_DimensionType_Caffe)
    tensor.copyToHostTensor(host)
    return np.asarray(host.getData(), dtype=np.float32).reshape(shape)


class Hm4Cpv1MnnRuntime:
    """Chạy model tinh biên bằng MNN. Cùng chữ ký `.run(rgb, rgba)` như bản torch."""

    def __init__(self, model_path: Path):
        self.interpreter = MNN.Interpreter(str(model_path))
        self.session = self.interpreter.createSession({"numThread": 4, "backend": "CPU"})
        self._shape = None

    def run(self, rgb: np.ndarray, rgba: np.ndarray) -> np.ndarray:
        shape = rgb.shape[2:]
        if shape != self._shape:
            inputs = self.interpreter.getSessionInputAll(self.session)
            self.interpreter.resizeTensor(inputs["input0"], (1, 3) + shape)
            self.interpreter.resizeTensor(inputs["input2"], (1, 4) + shape)
            self.interpreter.resizeSession(self.session)
            self._shape = shape

        inputs = self.interpreter.getSessionInputAll(self.session)
        inputs["input0"].copyFrom(_mnn_tensor(rgb))
        inputs["input2"].copyFrom(_mnn_tensor(rgba))
        self.interpreter.runSession(self.session)
        return _mnn_read(self.interpreter.getSessionOutputAll(self.session)["output0"])


def _get_runtime():
    global _RUNTIME
    if _RUNTIME is not None:
        return _RUNTIME
    if MNN is None:
        raise RuntimeError("Thiếu MNN cho Python — chạy: pip install MNN")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Không thấy model Hmhcv1: {MODEL_PATH}")

    interpreter = MNN.Interpreter(str(MODEL_PATH))
    session = interpreter.createSession({"numThread": 4, "backend": "CPU"})
    input_tensor = interpreter.getSessionInput(session)
    if any(dimension < 0 for dimension in input_tensor.getShape()):
        interpreter.resizeTensor(input_tensor, (1, 3, 512, 512))
        interpreter.resizeSession(session)
    _RUNTIME = (interpreter, session)
    return _RUNTIME


def _get_patch_runtime():
    global _PATCH_RUNTIME
    if _PATCH_RUNTIME is not None:
        return _PATCH_RUNTIME

    if PATCH_MNN_PATH.exists():
        if MNN is None:
            raise RuntimeError("Thiếu MNN cho Python — chạy: pip install MNN")
        _PATCH_RUNTIME = Hm4Cpv1MnnRuntime(PATCH_MNN_PATH)
    elif PATCH_XML_PATH.exists() and PATCH_WEIGHTS_PATH.exists():
        from hm4cpv1_torch import Hm4Cpv1TorchRuntime  # chỉ nạp torch khi thật sự cần
        _PATCH_RUNTIME = Hm4Cpv1TorchRuntime(PATCH_XML_PATH, PATCH_WEIGHTS_PATH)
    else:
        raise FileNotFoundError(f"Không thấy model tinh biên Hm4Cpv1 trong {MODELS_DIR}")
    return _PATCH_RUNTIME


def predict_human_alpha(image: np.ndarray) -> np.ndarray:
    """Alpha thô (uint8) ở đúng độ phân giải ảnh gốc."""
    if image is None or image.size == 0:
        raise ValueError("Ảnh vào rỗng")

    interpreter, session = _get_runtime()
    resized = cv2.resize(image, (512, 512), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    # Đúng bước tiền xử lý mà HumanMattingPipe của Leien dùng cho Hmhcv1.
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    nchw = np.transpose((rgb - mean) / std, (2, 0, 1))[None, ...]

    interpreter.getSessionInput(session).copyFrom(_mnn_tensor(nchw))
    interpreter.runSession(session)

    outputs = interpreter.getSessionOutputAll(session)
    output_tensor = outputs.get("output0") or next(iter(outputs.values()), None)
    if output_tensor is None:
        raise RuntimeError("Hmhcv1 không trả ra tensor nào")

    alpha = np.squeeze(_mnn_read(output_tensor))
    if alpha.ndim != 2:
        raise RuntimeError(f"Hmhcv1 ra shape lạ: {tuple(output_tensor.getShape())}")

    alpha = cv2.resize(alpha, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


def _tile_starts(length, tile_size, overlap):
    if length <= tile_size:
        return [0]
    step = tile_size - overlap
    starts = list(range(0, max(1, length - tile_size + 1), step))
    last = length - tile_size
    if starts[-1] != last:
        starts.append(last)
    return starts


def _tile_weight(height, width, overlap):
    weight_y = np.ones(height, dtype=np.float32)
    weight_x = np.ones(width, dtype=np.float32)
    edge_y = min(overlap, height // 2)
    edge_x = min(overlap, width // 2)
    if edge_y:
        ramp = np.sin(np.linspace(0.0, np.pi / 2.0, edge_y, dtype=np.float32)) ** 2
        weight_y[:edge_y] = ramp
        weight_y[-edge_y:] = ramp[::-1]
    if edge_x:
        ramp = np.sin(np.linspace(0.0, np.pi / 2.0, edge_x, dtype=np.float32)) ** 2
        weight_x[:edge_x] = ramp
        weight_x[-edge_x:] = ramp[::-1]
    return weight_y[:, None] * weight_x[None, :]


def predict_human_alpha_refined(image: np.ndarray) -> np.ndarray:
    """Alpha đã tinh biên: chạy cả model toàn cục lẫn model theo mảnh."""
    coarse_alpha = predict_human_alpha(image).astype(np.float32) / 255.0
    patch_runtime = _get_patch_runtime()
    height, width = image.shape[:2]

    # Đầu vào mảnh gốc là RGB đã đi qua tầng toàn cục 512px, cộng alpha thô
    # làm kênh thứ tư.
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    global_rgb = cv2.resize(image_rgb, (512, 512), interpolation=cv2.INTER_AREA)
    global_rgb = cv2.resize(global_rgb, (width, height), interpolation=cv2.INTER_LINEAR)
    coarse_rgba = np.concatenate([global_rgb, coarse_alpha[..., None]], axis=2)

    foreground = (coarse_alpha > 0.015).astype(np.uint8)
    points = cv2.findNonZero(foreground)
    if points is None:
        return np.zeros((height, width), dtype=np.uint8)
    x, y, box_w, box_h = cv2.boundingRect(points)
    margin = 96
    x0 = max(0, x - margin)
    y0 = max(0, y - margin)
    x1 = min(width, x + box_w + margin)
    y1 = min(height, y + box_h + margin)

    roi_rgb = image_rgb[y0:y1, x0:x1]
    roi_rgba = coarse_rgba[y0:y1, x0:x1]
    roi_h, roi_w = roi_rgb.shape[:2]
    refined_sum = np.zeros((roi_h, roi_w), dtype=np.float32)
    weight_sum = np.zeros((roi_h, roi_w), dtype=np.float32)
    tile_size = 1056
    overlap = 96

    for tile_y in _tile_starts(roi_h, tile_size, overlap):
        for tile_x in _tile_starts(roi_w, tile_size, overlap):
            tile_rgb = roi_rgb[tile_y : tile_y + tile_size, tile_x : tile_x + tile_size]
            tile_rgba = roi_rgba[tile_y : tile_y + tile_size, tile_x : tile_x + tile_size]
            tile_h, tile_w = tile_rgb.shape[:2]
            padded_h = int(np.ceil(tile_h / 8.0) * 8)
            padded_w = int(np.ceil(tile_w / 8.0) * 8)
            if (padded_h, padded_w) != (tile_h, tile_w):
                pad_bottom = padded_h - tile_h
                pad_right = padded_w - tile_w
                tile_rgb = cv2.copyMakeBorder(tile_rgb, 0, pad_bottom, 0, pad_right, cv2.BORDER_REFLECT_101)
                tile_rgba = cv2.copyMakeBorder(tile_rgba, 0, pad_bottom, 0, pad_right, cv2.BORDER_REFLECT_101)

            patch_output = patch_runtime.run(
                np.transpose(tile_rgb, (2, 0, 1))[None, ...],
                np.transpose(tile_rgba, (2, 0, 1))[None, ...],
            )
            patch_alpha = np.clip(patch_output[0, 3, :tile_h, :tile_w], 0.0, 1.0)
            weight = _tile_weight(tile_h, tile_w, overlap)
            refined_sum[tile_y : tile_y + tile_h, tile_x : tile_x + tile_w] += patch_alpha * weight
            weight_sum[tile_y : tile_y + tile_h, tile_x : tile_x + tile_w] += weight

    refined_roi = refined_sum / np.maximum(weight_sum, 1e-6)
    refined = np.zeros((height, width), dtype=np.float32)
    refined[y0:y1, x0:x1] = refined_roi
    return np.clip(refined * 255.0, 0, 255).astype(np.uint8)
