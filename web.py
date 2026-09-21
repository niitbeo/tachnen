#!/usr/bin/env python3
"""Máy chủ nhỏ cho giao diện web tách nền.

Chỉ dùng thư viện sẵn có của Python. Chạy tại 127.0.0.1, kèm một mã ngẫu nhiên
để trang web khác trên máy không điều khiển được.
"""

import json
import mimetypes
import os
import secrets
import socket
import string
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import cv2
import numpy as np

GOC = Path(__file__).resolve().parent
sys.path.insert(0, str(GOC))
import tachnen

try:
    import hop_thoai
except Exception:  # noqa: BLE001 - không có thì dùng bộ duyệt trong trang
    hop_thoai = None

MA = secrets.token_urlsafe(16)
TRANG = GOC / "web" / "index.html"


# ------------------------------------------------------------------ công việc
class CongViec:
    def __init__(self):
        self.khoa = threading.Lock()
        self.dat_lai()

    def dat_lai(self):
        self.dang_chay = False
        self.xin_dung = False
        self.tong = 0
        self.xong = 0
        self.loi = 0
        self.hien_tai = ""
        self.nhat_ky: list[str] = []
        self.ket_qua: list[str] = []
        self.thu_muc_ra = ""
        self.t_dau = 0.0
        self.t_het = 0.0
        self.da_xong = False

    def trang_thai(self):
        with self.khoa:
            troi = (self.t_het or time.time()) - self.t_dau if self.t_dau else 0
            tron = self.xong + self.loi
            con = (troi / tron * (self.tong - tron)) if tron and self.dang_chay else 0
            return {
                "dangChay": self.dang_chay,
                "daXong": self.da_xong,
                "tong": self.tong,
                "xong": self.xong,
                "loi": self.loi,
                "hienTai": self.hien_tai,
                "nhatKy": self.nhat_ky[-400:],
                "ketQua": self.ket_qua[-60:],
                "thuMucRa": self.thu_muc_ra,
                "giay": round(troi, 1),
                "con": round(con, 1),
            }

    def ghi(self, dong):
        with self.khoa:
            self.nhat_ky.append(dong)


VIEC = CongViec()


def liet_ke_anh(goc: Path, sau: bool) -> list[Path]:
    """Ảnh cần xử lý, bỏ qua kết quả của lần chạy trước.

    Chỉ bỏ thư mục "tachnen" *ngay bên trên* ảnh — đó là chỗ chương trình ghi kết
    quả. Không bỏ theo cả đường dẫn, vì chính bộ công cụ này nằm trong một thư mục
    tên `tachnen`, và người dùng cũng có thể đặt tên thư mục như vậy.
    """
    it = goc.rglob("*") if sau else goc.iterdir()
    return sorted(p for p in it
                  if p.is_file()
                  and p.suffix.lower() in tachnen.SUFFIXES
                  and not p.stem.endswith(("_tachnen", "_mask"))
                  and p.parent.name.lower() != "tachnen")


def chay(danh_sach: list[Path], ch: dict):
    try:
        with VIEC.khoa:
            VIEC.t_dau = time.time()
        VIEC.ghi(f"Bắt đầu {len(danh_sach)} ảnh · nền: {ch['nen']}")
        for i, nguon in enumerate(danh_sach, 1):
            if VIEC.xin_dung:
                VIEC.ghi("Đã dừng theo yêu cầu.")
                break
            with VIEC.khoa:
                VIEC.hien_tai = nguon.name
            try:
                if ch.get("thuMucRa"):
                    dich = Path(ch["thuMucRa"]) / f"{nguon.stem}.png"
                else:
                    dich = nguon.parent / "tachnen" / f"{nguon.stem}.png"
                ra, giay, phu = tachnen.tach_mot_anh(
                    nguon, dich, ch["nen"], ch["nhanh"], ch["mask"], ch["maxsize"])
                with VIEC.khoa:
                    VIEC.xong += 1
                    VIEC.thu_muc_ra = str(ra.parent)
                    VIEC.ket_qua.append(str(ra))
                VIEC.ghi(f"[{i}/{len(danh_sach)}] {nguon.name} → {ra.name}  {giay:.1f}s · chủ thể {phu:.1f}%")
            except Exception as e:  # noqa: BLE001 - một ảnh lỗi không làm dừng cả mẻ
                with VIEC.khoa:
                    VIEC.loi += 1
                VIEC.ghi(f"[{i}/{len(danh_sach)}] {nguon.name}   LỖI: {e}")
    except Exception:  # noqa: BLE001
        VIEC.ghi("LỖI NẶNG:\n" + traceback.format_exc())
    finally:
        with VIEC.khoa:
            VIEC.dang_chay = False
            VIEC.da_xong = True
            VIEC.hien_tai = ""
            VIEC.t_het = time.time()


# --------------------------------------------------------------------- ổ đĩa
def cac_o_dia():
    ra = []
    for c in string.ascii_uppercase:
        d = f"{c}:\\"
        if os.path.exists(d):
            ra.append(d)
    return ra


def liet_ke_thu_muc(duong: str):
    if not duong:
        return {"duong": "", "cha": "", "thuMuc": cac_o_dia(), "soAnh": 0, "laGoc": True}
    p = Path(duong)
    if not p.is_dir():
        raise ValueError(f"Không phải thư mục: {duong}")
    con = []
    for m in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        try:
            if m.is_dir() and not m.name.startswith("$"):
                con.append(str(m))
        except OSError:
            pass
    try:
        so = len(liet_ke_anh(p, False))
    except OSError:
        so = 0
    cha = str(p.parent) if p.parent != p else ""
    return {"duong": str(p), "cha": cha, "thuMuc": con, "soAnh": so, "laGoc": False}


# ------------------------------------------------------------------- HTTP
class Tay(BaseHTTPRequestHandler):
    server_version = "TachNen/1.0"

    def log_message(self, *a):
        pass

    # -- tiện ích --
    def _json(self, du_lieu, ma=200):
        b = json.dumps(du_lieu, ensure_ascii=False).encode("utf-8")
        self.send_response(ma)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _nhi(self, b: bytes, kieu: str):
        self.send_response(200)
        self.send_header("Content-Type", kieu)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def _than(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _kiem_ma(self, q):
        return (q.get("ma", [""])[0] or self.headers.get("X-Ma", "")) == MA

    # -- GET --
    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                html = TRANG.read_text(encoding="utf-8").replace("__MA__", MA)
                return self._nhi(html.encode("utf-8"), "text/html; charset=utf-8")
            if not self._kiem_ma(q):
                return self._json({"loi": "sai mã"}, 403)
            if u.path == "/api/thu-muc":
                return self._json(liet_ke_thu_muc(unquote(q.get("duong", [""])[0])))
            if u.path == "/api/dem":
                goc = Path(unquote(q.get("duong", [""])[0]))
                sau = q.get("sau", ["1"])[0] == "1"
                return self._json({"so": len(liet_ke_anh(goc, sau))})
            if u.path == "/api/tien-trinh":
                return self._json(VIEC.trang_thai())
            if u.path == "/api/anh":
                return self._gui_anh(unquote(q.get("duong", [""])[0]),
                                     int(q.get("cao", ["260"])[0]))
        except Exception as e:  # noqa: BLE001
            return self._json({"loi": str(e)}, 400)
        self.send_error(404)

    def _gui_anh(self, duong, cao):
        p = Path(duong)
        if not p.is_file():
            return self.send_error(404)
        im = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if im is None:
            return self.send_error(404)
        if im.ndim == 3 and im.shape[2] == 4:      # ghép lên ô caro cho thấy chỗ trong suốt
            h, w = im.shape[:2]
            o = 16
            caro = np.indices((h, w)).sum(0) // o % 2
            nen = np.where(caro[..., None] == 0, 255, 205).astype(np.float32)
            nen = np.repeat(nen, 3, axis=2)
            a = (im[:, :, 3].astype(np.float32) / 255)[..., None]
            im = np.clip(im[:, :, :3] * a + nen * (1 - a), 0, 255).astype(np.uint8)
        h, w = im.shape[:2]
        if h > cao:
            im = cv2.resize(im, (max(1, round(w * cao / h)), cao), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok:
            return self.send_error(500)
        return self._nhi(buf.tobytes(), "image/jpeg")

    # -- POST --
    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if not self._kiem_ma(q):
            return self._json({"loi": "sai mã"}, 403)
        try:
            if u.path == "/api/bat-dau":
                return self._bat_dau(self._than())
            if u.path == "/api/dung":
                VIEC.xin_dung = True
                return self._json({"ok": True})
            if u.path == "/api/hop-thoai":
                return self._hop_thoai(self._than())
            if u.path == "/api/mo":
                d = self._than().get("duong", "")
                if d and Path(d).exists():
                    os.startfile(d)
                    return self._json({"ok": True})
                return self._json({"loi": "không thấy thư mục"}, 400)
        except Exception as e:  # noqa: BLE001
            return self._json({"loi": str(e), "chiTiet": traceback.format_exc()}, 400)
        self.send_error(404)

    def _hop_thoai(self, d):
        """Mở hộp thoại chọn thư mục thật của Windows."""
        if hop_thoai is None:
            return self._json({"khongCo": True})
        duong, loi = hop_thoai.chon_thu_muc_an_toan(
            d.get("tieuDe") or "Chọn thư mục", (d.get("batDau") or "").strip() or None)
        if loi:
            return self._json({"khongCo": True, "loi": loi})
        if not duong:
            return self._json({"huy": True})
        return self._json({"duong": duong, "so": len(liet_ke_anh(Path(duong), bool(d.get("sau", True))))})

    def _bat_dau(self, d):
        if VIEC.dang_chay:
            return self._json({"loi": "đang chạy"}, 409)

        danh_sach: list[Path] = []
        if d.get("thuMuc"):
            goc = Path(d["thuMuc"])
            if not goc.is_dir():
                return self._json({"loi": f"Không thấy thư mục: {goc}"}, 400)
            danh_sach = liet_ke_anh(goc, bool(d.get("sau", True)))
        for t in d.get("tep", []):
            p = Path(t)
            if p.is_file():
                danh_sach.append(p)
        # bỏ trùng, giữ thứ tự
        thay, sach = set(), []
        for p in danh_sach:
            if p not in thay:
                thay.add(p)
                sach.append(p)
        if not sach:
            return self._json({"loi": "Không có ảnh nào để xử lý."}, 400)

        ch = {
            "nen": d.get("nen", "trong"),
            "nhanh": bool(d.get("nhanh", False)),
            "maxsize": int(d.get("maxsize", 2500) or 0),
            "mask": bool(d.get("mask", False)),
            "thuMucRa": (d.get("thuMucRa") or "").strip(),
        }
        VIEC.dat_lai()
        with VIEC.khoa:
            VIEC.dang_chay = True
            VIEC.tong = len(sach)
        threading.Thread(target=chay, args=(sach, ch), daemon=True).start()
        return self._json({"ok": True, "tong": len(sach)})


def cong_trong():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    c = s.getsockname()[1]
    s.close()
    return c


def main():
    if not TRANG.is_file():
        sys.exit(f"Thiếu tệp giao diện: {TRANG}")
    mimetypes.init()
    cong = cong_trong()
    may = ThreadingHTTPServer(("127.0.0.1", cong), Tay)
    dia_chi = f"http://127.0.0.1:{cong}/?ma={MA}"
    print("=" * 62)
    print("  TÁCH NỀN — giao diện web")
    print("=" * 62)
    print(f"  Địa chỉ: {dia_chi}")
    print("  Trình duyệt sẽ tự mở. Đóng cửa sổ này để tắt chương trình.")
    print("=" * 62)
    threading.Timer(0.7, lambda: webbrowser.open(dia_chi)).start()
    try:
        may.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã tắt.")


if __name__ == "__main__":
    main()
