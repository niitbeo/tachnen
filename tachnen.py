#!/usr/bin/env python3
"""Tách nền ảnh chân dung — chạy độc lập, offline.

    python tachnen.py anh.jpg                  -> anh_tachnen.png (nền trong suốt)
    python tachnen.py anh.jpg --bg white       -> nền trắng
    python tachnen.py anh.jpg --bg "#2f7fd8"   -> nền xanh
    python tachnen.py anh.jpg --bg nen.jpg     -> ghép vào ảnh nền
    python tachnen.py thu_muc_anh --out ket_qua
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import matting

SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

MAU = {
    "trong": None,
    "transparent": None,
    "trang": (255, 255, 255),
    "white": (255, 255, 255),
    "den": (0, 0, 0),
    "black": (0, 0, 0),
    "xanh": (219, 132, 58),      # xanh ảnh thẻ
    "blue": (219, 132, 58),
    "do": (60, 60, 210),
    "red": (60, 60, 210),
    "xam": (200, 200, 200),
    "gray": (200, 200, 200),
    "grey": (200, 200, 200),
}


def doc_anh(path: Path):
    """cv2.imread chết với đường dẫn tiếng Việt trên Windows — đọc qua numpy."""
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def ghi_anh(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(path.suffix or ".png", image)
    if not ok:
        raise RuntimeError(f"Không mã hoá được ảnh: {path}")
    buf.tofile(str(path))


def phan_giai_nen(value, size):
    """Trả về None (trong suốt) hoặc ảnh nền BGR đúng cỡ `size` = (h, w)."""
    if value is None:
        return None
    key = value.strip().lower()
    if key in MAU:
        color = MAU[key]
        if color is None:
            return None
        return np.full((size[0], size[1], 3), color, dtype=np.uint8)
    if key.startswith("#") and len(key) == 7:
        r, g, b = (int(key[i : i + 2], 16) for i in (1, 3, 5))
        return np.full((size[0], size[1], 3), (b, g, r), dtype=np.uint8)

    nen_path = Path(value)
    if nen_path.is_file():
        nen = doc_anh(nen_path)
        if nen is None:
            raise ValueError(f"Không đọc được ảnh nền: {nen_path}")
        return _phu_kin(nen, size)
    raise ValueError(f"--bg không hiểu được: {value!r} (màu, mã #rrggbb, hay đường dẫn ảnh)")


def _phu_kin(nen: np.ndarray, size):
    """Phóng ảnh nền phủ kín khung, cắt phần thừa — không bóp méo."""
    h, w = size
    nh, nw = nen.shape[:2]
    scale = max(w / nw, h / nh)
    resized = cv2.resize(nen, (int(np.ceil(nw * scale)), int(np.ceil(nh * scale))),
                         interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    y = (resized.shape[0] - h) // 2
    x = (resized.shape[1] - w) // 2
    return resized[y : y + h, x : x + w]


# Model không bao giờ cho alpha quá ~253, nên vùng thân người vẫn hở ~0,8% nền.
# Ghép lên nền tối sẽ thấy chủ thể bị xỉn. Kéo đỉnh lên cho đặc hẳn; hệ số 255/250
# chỉ nhích dải giữa chưa tới 1 đơn vị nên viền tóc giữ nguyên độ mượt.
ALPHA_TRAN = 250


def lam_dac_alpha(alpha: np.ndarray) -> np.ndarray:
    return np.clip(alpha.astype(np.float32) * (255.0 / ALPHA_TRAN), 0, 255).astype(np.uint8)


def _lan_mau(image: np.ndarray, biet: np.ndarray, vong: int = 20) -> np.ndarray:
    """Lan màu từ vùng đã biết (`biet`) ra khắp ảnh, giữ nguyên chỗ đã biết.

    Làm ở cỡ nhỏ cho nhanh — màu nền và màu chủ thể quanh mép vốn mượt.
    """
    h, w = biet.shape
    ty_le = min(1.0, 512.0 / max(h, w))
    hs, ws = max(1, round(h * ty_le)), max(1, round(w * ty_le))
    im_s = cv2.resize(image, (ws, hs), interpolation=cv2.INTER_AREA).astype(np.float32)
    b_s = cv2.resize(biet.astype(np.float32), (ws, hs), interpolation=cv2.INTER_AREA)
    b_s = (b_s > 0.5).astype(np.float32)
    if b_s.max() == 0:
        return cv2.resize(im_s, (w, h), interpolation=cv2.INTER_LINEAR)

    tu = im_s * b_s[..., None]
    mau = b_s.copy()
    for _ in range(vong):
        tu = cv2.blur(tu, (9, 9))
        mau = cv2.blur(mau, (9, 9))
        tu = tu * (1 - b_s)[..., None] + im_s * b_s[..., None]
        mau = mau * (1 - b_s) + b_s
    ket = tu / np.maximum(mau, 1e-6)[..., None]
    return cv2.resize(ket, (w, h), interpolation=cv2.INTER_LINEAR)


def khu_vien_mau(image: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Gỡ màu nền cũ in vào mép chủ thể.

    Chụp trước tán cây thì mép tóc dính xanh lá, ghép lên nền sáng là lộ ngay.
    Không thể sửa theo alpha, vì đo thấy hơn 90% điểm bị ám lại có alpha ≥ 250 —
    model coi chúng là đặc hoàn toàn. Nên khoanh vùng theo *khoảng cách tới mép*.

    Với mỗi điểm trong vùng đó, ước lượng màu nền `B` và màu chủ thể sạch `F` ở
    lân cận, đo xem điểm bị kéo về phía nền bao nhiêu rồi kéo ngược lại đúng ngần
    ấy: `C' = C - t*(B - F)`. Không có phép chia cho alpha nên không vọt quá đà.
    """
    a = alpha.astype(np.float32) / 255.0
    trong = (a > 0.5).astype(np.uint8)
    if trong.max() == 0 or trong.min() == 1:
        return image

    ban_kinh = max(3, round(0.004 * max(image.shape[:2])))
    # khoảng cách từ mỗi điểm bên trong ra tới nền gần nhất
    xa = cv2.distanceTransform(trong, cv2.DIST_L2, 3)
    vung = (a > 0.02) & (xa <= ban_kinh)
    if not vung.any():
        return image

    nen = _lan_mau(image, a < 0.05)
    sach = _lan_mau(image, (a > 0.98) & (xa > ban_kinh))

    C = image[vung].astype(np.float32)
    B = nen[vung]
    F = sach[vung]
    hieu = B - F
    do_lon = np.sum(hieu * hieu, axis=1)
    t = np.sum((C - F) * hieu, axis=1) / np.maximum(do_lon, 1e-6)
    t = np.clip(t, 0.0, 1.0)
    # nhạt dần vào trong để không thấy đường nối
    t *= np.clip(1.0 - xa[vung] / ban_kinh, 0.0, 1.0)

    ra = image.copy()
    ra[vung] = np.clip(C - t[:, None] * hieu, 0, 255).astype(np.uint8)
    return ra


def tinh_alpha(image: np.ndarray, fast: bool, maxsize: int, tho_alpha: bool = False) -> np.ndarray:
    """Alpha ở đúng cỡ ảnh gốc. `maxsize` giới hạn cạnh dài lúc chạy model."""
    h, w = image.shape[:2]
    canh_dai = max(h, w)
    if maxsize and canh_dai > maxsize:
        scale = maxsize / canh_dai
        nho = cv2.resize(image, (max(1, round(w * scale)), max(1, round(h * scale))),
                         interpolation=cv2.INTER_AREA)
    else:
        nho = image

    alpha = matting.predict_human_alpha(nho) if fast else matting.predict_human_alpha_refined(nho)
    if alpha.shape[:2] != (h, w):
        alpha = cv2.resize(alpha, (w, h), interpolation=cv2.INTER_LINEAR)
    return alpha if tho_alpha else lam_dac_alpha(alpha)


def tach_mot_anh(src: Path, dst: Path, bg_value, fast: bool, luu_mask: bool, maxsize: int,
                 tho_alpha: bool = False, giu_mau_nen: bool = False):
    image = doc_anh(src)
    if image is None:
        raise ValueError(f"Không đọc được ảnh: {src}")

    t0 = time.time()
    alpha = tinh_alpha(image, fast, maxsize, tho_alpha)
    mau = image if giu_mau_nen else khu_vien_mau(image, alpha)
    elapsed = time.time() - t0

    nen = phan_giai_nen(bg_value, image.shape[:2])
    if nen is None:
        out = cv2.cvtColor(mau, cv2.COLOR_BGR2BGRA)
        out[:, :, 3] = alpha
        dst = dst.with_suffix(".png")  # chỉ PNG giữ được kênh trong suốt
    else:
        a = (alpha.astype(np.float32) / 255.0)[..., None]
        out = (mau.astype(np.float32) * a + nen.astype(np.float32) * (1.0 - a))
        out = np.clip(out, 0, 255).astype(np.uint8)

    ghi_anh(dst, out)
    if luu_mask:
        ghi_anh(dst.with_name(dst.stem + "_mask.png"), alpha)

    phu = float((alpha > 8).mean()) * 100.0
    return dst, elapsed, phu


def main():
    ap = argparse.ArgumentParser(description="Tách nền ảnh chân dung (Hmhcv1 + Hm4Cpv1, offline)")
    ap.add_argument("input", help="Ảnh hoặc thư mục ảnh")
    ap.add_argument("--bg", default="trong",
                    help="trong | trang | den | xanh | do | xam | #rrggbb | đường dẫn ảnh nền")
    ap.add_argument("--out", default=None, help="Tệp ra, hoặc thư mục ra nếu vào là thư mục")
    ap.add_argument("--fast", action="store_true", help="Chỉ chạy model thô, bỏ bước tinh biên (nhanh ~5x, biên tóc xấu hơn)")
    ap.add_argument("--mask", action="store_true", help="Lưu thêm mặt nạ alpha")
    ap.add_argument("--maxsize", type=int, default=0, metavar="N",
                    help="Giới hạn cạnh dài khi chạy model (vd 3000) cho nhanh; ảnh ra vẫn cỡ gốc. 0 = full")
    ap.add_argument("--alpha-tho", action="store_true",
                    help="Giữ nguyên alpha thô của model, không kéo cho đặc hẳn")
    ap.add_argument("--giu-mau-nen", action="store_true",
                    help="Không khử viền dính màu nền cũ (vd viền xanh khi chụp trước cây)")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        sys.exit(f"Không thấy: {src}")

    if src.is_dir():
        # Bỏ qua chính kết quả của lần chạy trước, nếu nó nằm cùng thư mục.
        files = sorted(p for p in src.iterdir()
                       if p.suffix.lower() in SUFFIXES
                       and not p.stem.endswith(("_tachnen", "_mask")))
        if not files:
            sys.exit(f"Thư mục không có ảnh: {src}")
        out_dir = Path(args.out) if args.out else src / "tachnen"
        jobs = [(p, out_dir / f"{p.stem}.png") for p in files]
    else:
        dst = Path(args.out) if args.out else src.with_name(f"{src.stem}_tachnen.png")
        jobs = [(src, dst)]

    print(f"{len(jobs)} ảnh · nền: {args.bg} · chế độ: {'thô' if args.fast else 'tinh biên'}")
    loi = 0
    for i, (s, d) in enumerate(jobs, 1):
        try:
            out, elapsed, phu = tach_mot_anh(s, d, args.bg, args.fast, args.mask, args.maxsize,
                                             args.alpha_tho, args.giu_mau_nen)
            print(f"[{i}/{len(jobs)}] {s.name} -> {out.name}  {elapsed:.1f}s  chủ thể {phu:.1f}%")
        except Exception as exc:  # noqa: BLE001 - báo lỗi từng ảnh, chạy tiếp ảnh sau
            loi += 1
            print(f"[{i}/{len(jobs)}] {s.name}  LỖI: {exc}")

    if loi:
        sys.exit(f"Xong, nhưng {loi}/{len(jobs)} ảnh lỗi.")
    print("Xong.")


if __name__ == "__main__":
    main()
