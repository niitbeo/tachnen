#!/usr/bin/env python3
"""Gọi hộp thoại chọn thư mục thật của Windows.

Dùng IFileOpenDialog (hộp thoại kiểu Explorer, có ô gõ đường dẫn và thanh bên),
gọi thẳng qua ctypes nên không cần tkinter hay thư viện ngoài nào.

Nếu máy quá cũ không có IFileOpenDialog thì lùi về SHBrowseForFolder.
"""

import ctypes
from ctypes import POINTER, byref, c_int, c_uint, c_void_p, c_wchar_p
from ctypes.wintypes import HWND, LPCWSTR

ole32 = ctypes.OleDLL("ole32")
shell32 = ctypes.OleDLL("shell32")
user32 = ctypes.WinDLL("user32")

CLSCTX_INPROC_SERVER = 1
FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_PATHMUSTEXIST = 0x00000800
SIGDN_FILESYSPATH = 0x80058000
HRESULT_CANCELLED = -2147023673  # 0x800704C7 — người dùng bấm Huỷ


class GUID(ctypes.Structure):
    _fields_ = [("Data1", c_uint), ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)]

    def __init__(self, chuoi):
        super().__init__()
        ole32.CLSIDFromString(c_wchar_p(chuoi), byref(self))


CLSID_FileOpenDialog = GUID("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
IID_IFileOpenDialog = GUID("{D57C7288-D4AD-4768-BE02-9D969532D960}")
IID_IShellItem = GUID("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")

# Thứ tự hàm trong bảng ảo, đếm từ IUnknown.
_SHOW = 3
_SET_OPTIONS = 9
_SET_FOLDER = 12
_SET_TITLE = 17
_GET_RESULT = 20
_RELEASE = 2
_ITEM_GET_DISPLAY_NAME = 5


def _goi(con_tro, chi_so, *doi_so, kieu=None):
    """Gọi hàm thứ `chi_so` trong bảng ảo của một giao diện COM."""
    bang = ctypes.cast(con_tro, POINTER(POINTER(c_void_p)))[0]
    mau = ctypes.WINFUNCTYPE(ctypes.c_long, c_void_p, *(kieu or ()))
    return mau(bang[chi_so])(con_tro, *doi_so)


def _nha(con_tro):
    if con_tro:
        _goi(con_tro, _RELEASE)


def _bang_ifiledialog(tieu_de: str, thu_muc_dau: str | None, chu_so_huu: int) -> str | None:
    hop = c_void_p()
    ole32.CoCreateInstance(byref(CLSID_FileOpenDialog), None, CLSCTX_INPROC_SERVER,
                           byref(IID_IFileOpenDialog), byref(hop))
    try:
        _goi(hop, _SET_OPTIONS, c_uint(FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST),
             kieu=(c_uint,))
        _goi(hop, _SET_TITLE, c_wchar_p(tieu_de), kieu=(c_wchar_p,))

        if thu_muc_dau:
            muc = c_void_p()
            try:
                shell32.SHCreateItemFromParsingName(c_wchar_p(thu_muc_dau), None,
                                                    byref(IID_IShellItem), byref(muc))
                _goi(hop, _SET_FOLDER, muc, kieu=(c_void_p,))
            except OSError:
                pass  # đường dẫn cũ không còn — cứ mở ở chỗ mặc định
            finally:
                _nha(muc)

        try:
            _goi(hop, _SHOW, HWND(chu_so_huu), kieu=(HWND,))
        except OSError as e:
            if getattr(e, "winerror", 0) == HRESULT_CANCELLED:
                return None
            raise

        muc = c_void_p()
        _goi(hop, _GET_RESULT, byref(muc), kieu=(POINTER(c_void_p),))
        try:
            ten = c_wchar_p()
            _goi(muc, _ITEM_GET_DISPLAY_NAME, c_int(SIGDN_FILESYSPATH), byref(ten),
                 kieu=(c_int, POINTER(c_wchar_p)))
            duong = ten.value
            ole32.CoTaskMemFree(ten)
            return duong
        finally:
            _nha(muc)
    finally:
        _nha(hop)


def _bang_shbrowse(tieu_de: str, chu_so_huu: int) -> str | None:
    """Hộp thoại kiểu cũ, chỉ dùng khi IFileOpenDialog không chạy."""
    class BROWSEINFO(ctypes.Structure):
        _fields_ = [("hwndOwner", HWND), ("pidlRoot", c_void_p), ("pszDisplayName", c_void_p),
                    ("lpszTitle", LPCWSTR), ("ulFlags", c_uint), ("lpfn", c_void_p),
                    ("lParam", c_void_p), ("iImage", c_int)]

    dem = ctypes.create_unicode_buffer(260)
    bi = BROWSEINFO()
    bi.hwndOwner = chu_so_huu
    bi.pszDisplayName = ctypes.cast(dem, c_void_p)
    bi.lpszTitle = tieu_de
    bi.ulFlags = 0x00000040 | 0x00000010    # BIF_NEWDIALOGSTYLE | BIF_EDITBOX
    pidl = shell32.SHBrowseForFolderW(byref(bi))
    if not pidl:
        return None
    try:
        ra = ctypes.create_unicode_buffer(260)
        if shell32.SHGetPathFromIDListW(pidl, ra):
            return ra.value
        return None
    finally:
        ole32.CoTaskMemFree(pidl)


def chon_thu_muc(tieu_de: str = "Chọn thư mục", thu_muc_dau: str | None = None) -> str | None:
    """Mở hộp thoại; trả về đường dẫn, hoặc None nếu người dùng bấm Huỷ.

    Phải gọi trong một luồng riêng đã khởi tạo COM ở chế độ STA.
    """
    chu = user32.GetForegroundWindow() or 0
    try:
        return _bang_ifiledialog(tieu_de, thu_muc_dau, chu)
    except OSError:
        return _bang_shbrowse(tieu_de, chu)


def chon_thu_muc_an_toan(tieu_de: str = "Chọn thư mục", thu_muc_dau: str | None = None):
    """Chạy hộp thoại trong luồng STA riêng. Trả về (đường_dẫn, lỗi)."""
    import threading

    ket = {}

    def lam():
        try:
            ole32.CoInitializeEx(None, 2)      # COINIT_APARTMENTTHREADED
        except OSError:
            pass
        try:
            ket["duong"] = chon_thu_muc(tieu_de, thu_muc_dau)
        except Exception as e:  # noqa: BLE001
            ket["loi"] = f"{type(e).__name__}: {e}"
        finally:
            try:
                ole32.CoUninitialize()
            except OSError:
                pass

    t = threading.Thread(target=lam, daemon=True)
    t.start()
    t.join(300)
    if t.is_alive():
        return None, "hộp thoại không phản hồi"
    return ket.get("duong"), ket.get("loi")


if __name__ == "__main__":
    print(chon_thu_muc_an_toan("Thử chọn thư mục"))
