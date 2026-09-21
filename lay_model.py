#!/usr/bin/env python3
"""Rút 2 model tách nền từ bộ cài Leien Photo AI của chính bạn.

Repo không kèm model vì đó là tài sản có bản quyền của Leien. Script này lấy
chúng ra từ bản cài mà bạn có giấy phép, rồi đặt vào `models/`.

    python lay_model.py                      # tự dò trong các ổ đĩa
    python lay_model.py D:\\ai                # dò trong một thư mục
    python lay_model.py D:\\ai\\1-leien-engine-env.zip
"""

import shutil
import string
import sys
import zipfile
from pathlib import Path

GOC = Path(__file__).resolve().parent
DICH = GOC / "models"

# tên tệp -> các đường dẫn có thể gặp bên trong zip của Leien
CAN = {
    "Hmhcv1_original.mnn": ["leien_env/Hmhcv1_original.mnn",
                            "models/portrait/clibs/Hmhcv1_original.mnn"],
    "Hm4Cpv1_original.mnn": ["leien_env/Hm4Cpv1_original.mnn",
                             "models/portrait/clibs/Hm4Cpv1_original.mnn"],
}
THEM = {  # bản dự phòng, thiếu cũng chạy được
    "Hm4Cpv1_compat.xml": ["leien_env/Hm4Cpv1_compat.xml"],
    "Hm4Cpv1_compat.bin": ["leien_env/Hm4Cpv1_compat.bin"],
}

TEN_ZIP = ["1-leien-engine-env.zip", "3-leien-models-raw.zip"]


def tu_zip(zip_path: Path, can: dict, da_co: set) -> int:
    lay = 0
    try:
        with zipfile.ZipFile(zip_path) as z:
            co = set(z.namelist())
            for ten, cho in can.items():
                if ten in da_co:
                    continue
                for duong in cho:
                    if duong in co:
                        DICH.mkdir(parents=True, exist_ok=True)
                        with z.open(duong) as vao, open(DICH / ten, "wb") as ra:
                            shutil.copyfileobj(vao, ra)
                        print(f"  lấy được  {ten}  ({(DICH / ten).stat().st_size / 1048576:.1f} MB)")
                        da_co.add(ten)
                        lay += 1
                        break
    except zipfile.BadZipFile:
        print(f"  (bỏ qua, không phải zip hợp lệ: {zip_path.name})")
    return lay


def tu_thu_muc(goc: Path, can: dict, da_co: set) -> int:
    """Model đã giải nén sẵn thì chép thẳng."""
    lay = 0
    for ten in list(can):
        if ten in da_co:
            continue
        for p in goc.rglob(ten):
            if p.is_file():
                DICH.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, DICH / ten)
                print(f"  lấy được  {ten}  ({p.stat().st_size / 1048576:.1f} MB)")
                da_co.add(ten)
                lay += 1
                break
    return lay


def cho_can_tim(dau_vao: str | None):
    """Danh sách zip và thư mục đáng dò."""
    if dau_vao:
        p = Path(dau_vao)
        if p.is_file():
            return [p], []
        if p.is_dir():
            return sorted(p.rglob("*leien*.zip")), [p]
        sys.exit(f"Không thấy: {p}")

    zips, thu_muc = [], []
    for c in string.ascii_uppercase:
        o = Path(f"{c}:\\")
        if not o.exists():
            continue
        for ten in TEN_ZIP:
            if (o / ten).is_file():
                zips.append(o / ten)
        for con in o.glob("*"):          # chỉ dò một cấp, cho nhanh
            try:
                if not con.is_dir():
                    continue
            except OSError:
                continue
            for ten in TEN_ZIP:
                if (con / ten).is_file():
                    zips.append(con / ten)
            if (con / "leien_env").is_dir():
                thu_muc.append(con)
    return zips, thu_muc


def main():
    dau_vao = sys.argv[1] if len(sys.argv) > 1 else None
    print("Tìm model tách nền của Leien…")
    zips, thu_muc = cho_can_tim(dau_vao)

    if not zips and not thu_muc:
        sys.exit(
            "\nKhông tự tìm được bộ cài Leien.\n"
            "Chỉ đường dẫn cho nó, ví dụ:\n"
            "    python lay_model.py D:\\ai\n"
            "    python lay_model.py D:\\ai\\1-leien-engine-env.zip\n")

    for p in zips:
        print(f"  thấy zip: {p}")
    for p in thu_muc:
        print(f"  thấy thư mục: {p}")

    da_co = {t for t in list(CAN) + list(THEM) if (DICH / t).is_file()}
    for t in sorted(da_co):
        print(f"  đã có sẵn {t}, bỏ qua")

    can_het = {**CAN, **THEM}
    print("\nĐang rút:")
    for p in zips:
        tu_zip(p, can_het, da_co)
    for p in thu_muc:
        tu_thu_muc(p, can_het, da_co)

    thieu = [t for t in CAN if t not in da_co]
    print()
    if thieu:
        sys.exit("CHƯA ĐỦ. Còn thiếu: " + ", ".join(thieu)
                 + "\nHai tệp này nằm trong `leien_env/` của bộ cài Leien.")
    print(f"Xong. Model đã nằm trong {DICH}")
    print("Chạy thử:  python tachnen.py anh.jpg")


if __name__ == "__main__":
    main()
