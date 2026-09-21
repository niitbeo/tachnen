# Tách nền

Tách nền ảnh chân dung, chạy hoàn toàn tại chỗ. Có giao diện web làm hàng loạt, có bản
dòng lệnh, và có bản kéo thả.

> ### ⚠️ Repo này KHÔNG kèm model
>
> Hai tệp model là **tài sản của Leien Photo AI**, có bản quyền và được bảo vệ bằng hệ
> thống giấy phép riêng. Repo này chỉ có **mã nguồn**.
>
> Muốn chạy, bạn phải tự lấy model **từ bản Leien Photo AI mà chính bạn có giấy phép**.
> Chạy `python lay_model.py` là xong — nó tự dò và rút ra `models/`.
>
> Đừng đăng lại hai tệp model đó lên bất cứ đâu công khai.

## Cài

Cần Python 3.9–3.12 trên Windows.

```bash
pip install -r requirements.txt
python lay_model.py
```

`lay_model.py` tự dò bộ cài Leien trên máy bạn và rút đúng 2 tệp model ra `models/`. Không
tự tìm được thì chỉ đường cho nó:

```bash
python lay_model.py D:\ai
python lay_model.py D:\ai\1-leien-engine-env.zip
```

Nó cũng đọc được thư mục `leien_env/` đã giải nén sẵn. Model rút ra **giống hệt từng byte**
với bản trong bộ cài.

## Cách dùng

### Giao diện — làm hàng loạt

Bấm đúp **`Tach nen - giao dien web.bat`**. Trình duyệt tự mở ra trang điều khiển:

1. **Chọn thư mục** — duyệt cây thư mục ngay trong trang, thấy sẵn mỗi thư mục có bao nhiêu
   ảnh. Tích "gồm cả thư mục con" nếu ảnh nằm rải trong nhiều thư mục.
2. **Chọn nền** — trong suốt, trắng, đen, xanh ảnh thẻ, đỏ, xám, hoặc bảng màu tự chọn.
   Chọn luôn mức chất lượng và chỗ lưu kết quả.
3. **Bấm Bắt đầu** — thanh tiến trình chạy, hiện đang làm ảnh nào, còn bao lâu, nhật ký
   từng ảnh. Có nút **Dừng** (dừng sau khi xong ảnh đang làm) và nút **Mở thư mục kết quả**.
   Xong thì hiện luôn ảnh kết quả để xem ngay.

Trang chạy tại `127.0.0.1` trên chính máy bạn — **ảnh không gửi đi đâu cả**, và có mã ngẫu
nhiên mỗi lần chạy nên trang web khác không điều khiển được. Đóng cửa sổ đen để tắt.

### Kéo thả — làm nhanh vài ảnh

Kéo thả ảnh (hoặc cả thư mục ảnh) vào `Tach nen - keo tha anh vao day.bat`.

### Dòng lệnh

Dùng Python trong gói:

```bash
python\python.exe tachnen.py anh.jpg
```

Ra `anh_tachnen.png`, nền trong suốt.

| lệnh | kết quả |
|---|---|
| `python tachnen.py anh.jpg` | nền trong suốt (PNG) |
| `python tachnen.py anh.jpg --bg trang` | nền trắng |
| `python tachnen.py anh.jpg --bg xanh` | nền xanh ảnh thẻ |
| `python tachnen.py anh.jpg --bg "#2f7fd8"` | nền theo mã màu |
| `python tachnen.py anh.jpg --bg nen.jpg` | ghép vào ảnh nền (tự phủ kín, không bóp méo) |
| `python tachnen.py thu_muc_anh` | chạy cả thư mục, kết quả vào `thu_muc_anh/tachnen/` |

Hoặc **kéo thả ảnh** vào `Tach nen - keo tha anh vao day.bat`, khỏi gõ lệnh.

Thêm cờ:

- `--out <đường dẫn>` — đổi chỗ ghi kết quả
- `--mask` — lưu kèm mặt nạ alpha để soi chất lượng biên
- `--maxsize N` — giới hạn cạnh dài **lúc chạy model**; ảnh ra vẫn đúng cỡ gốc
- `--fast` — bỏ hẳn bước tinh biên, nhanh nhất nhưng biên tóc xấu
- `--alpha-tho` — giữ alpha thô của model, không kéo cho đặc (xem mục dưới)
- `--giu-mau-nen` — không khử viền dính màu nền cũ (xem mục dưới)

Màu có sẵn: `trong`, `trang`, `den`, `xanh`, `do`, `xam` (hoặc tên tiếng Anh).

## Tốc độ

Đo thật trên ảnh **7952×5304 (42 MP)** của bạn trong `raw-cache/`:

| lệnh | thời gian | ghi chú |
|---|---|---|
| mặc định (full) | **38,3 s** | biên tóc sắc nhất |
| `--maxsize 2500` | **3,8 s** | độ phủ chủ thể giống hệt bản full (66,8%) |
| `--maxsize 2000` | **2,7 s** | |

**Nên dùng `--maxsize 2500` cho ảnh máy ảnh.** Nhanh gấp 10 lần mà mắt thường gần như
không thấy khác — model tinh biên chỉ làm việc quanh đường viền, hạ độ phân giải lúc chạy
không đổi hình dáng chủ thể.

Ảnh cỡ web (dưới 2000px) thì chạy thẳng, chưa tới 1 giây.

## Cần đúng những gì

### Thư viện — 3 cái

```bash
pip install MNN opencv-python numpy
```

| thư viện | cỡ cài | việc |
|---|---|---|
| `MNN` | 5,5 MB | chạy cả hai model |
| `opencv-python` | 174 MB | đọc/ghi ảnh, phóng thu, ghép nền |
| `numpy` | 34 MB | tính toán mảng |

**Không cần `torch`** (494 MB) và **không cần `onnxruntime`**. Xem mục dưới.

### Model — 2 cái, 17,7 MB

**Không có trong repo này.** Tự lấy từ bản Leien Photo AI mà bạn có giấy phép.

| tệp | cỡ | việc |
|---|---|---|
| `models/Hmhcv1_original.mnn` | 15,5 MB | tách thô toàn ảnh ở 512×512 |
| `models/Hm4Cpv1_original.mnn` | 2,2 MB | tinh biên theo từng ô (tóc, viền áo) |

Cả hai nằm trong `1-leien-engine-env.zip` của bộ cài Leien, ở đường dẫn `leien_env/`. Cũng
có bản y hệt trong `3-leien-models-raw.zip` tại `models/portrait/clibs/`. Phần còn lại của
bộ 9 GB là cho các tính năng khác (làm đẹp, xoá vật thể, ảnh thẻ) — tách nền không đụng tới.

Bản dự phòng `Hm4Cpv1_compat.xml` + `.bin` (2,3 MB, cùng thư mục `leien_env/`) chỉ cần khi
thiếu `Hm4Cpv1_original.mnn`, và khi đó mới cần `torch`. Không có cũng không sao.

### Vì sao bỏ được `torch` — có đo

Lúc đầu model tinh biên chạy bằng PyTorch qua `hm4cpv1_torch.py`, kéo theo 494 MB thư
viện. Hoá ra MNN chạy thẳng được `Hm4Cpv1_original.mnn`. Đối chiếu hai bản:

| phép đo | kết quả |
|---|---|
| một ô 512×512, sai lệch alpha lớn nhất | 0,0025 (thang 0–1) |
| mask đầy đủ 7952×5304, sai lệch lớn nhất | **1/255** |
| pixel lệch quá 1 (trên 42 triệu pixel) | **0** |

Tức là y hệt, chỉ khác chỗ làm tròn. Nên mặc định chạy MNN.

### Vá alpha cho đặc hẳn

Model không bao giờ cho alpha quá **253/255**, kể cả giữa thân người. Nghĩa là nền lọt qua
toàn bộ chủ thể khoảng 0,8% — ghép lên nền tối sẽ thấy chủ thể bị xỉn, và chồng nhiều lớp
thì lộ rõ. Đo trên hai ảnh khác nhau đều đóng trần ở đúng 253, nên đây là cố tật của model
chứ không phải lỗi ảnh.

`tachnen.py` nhân alpha với `255/250` để kéo đỉnh lên đặc hẳn. Hệ số nhỏ nên dải chuyển
tiếp ở viền tóc gần như không đổi:

| | trước vá | sau vá |
|---|---|---|
| pixel đặc hoàn toàn (=255) | 0,00% | **28,99%** |
| pixel nền (=0) | 69,08% | 69,08% (không đổi) |
| pixel bán trong (viền tóc) | 1,50% | 1,37% |

Phần 0,13% rời khỏi dải bán trong chính là các pixel 247–253 lẽ ra phải đặc. Đã soi ảnh
phóng to vùng tóc bay trên nền đen: từng sợi vẫn tách rời và mềm y như trước.

Muốn alpha thô đúng nguyên bản model thì thêm `--alpha-tho`.

### Khử viền dính màu nền

Chụp trước tán cây thì mép tóc **dính xanh lá**, ghép lên nền trắng là lộ ngay. Đo trên ảnh
thật: mép xanh hơn màu tóc sạch tại chính chỗ đó **+3,12**, và 19,5% điểm mép lệch nặng.

Chỗ bẫy: **không sửa được theo alpha**. Đo thấy **90,9%** điểm bị ám lại có alpha ≥ 250 —
model coi chúng là đặc hoàn toàn. Công thức gỡ nền theo alpha thông thường không chạm tới
chúng, mà còn dễ vọt quá đà vì phải chia cho alpha.

Cách làm ở đây: khoanh vùng theo **khoảng cách tới mép** (8px với ảnh 2000px), ước lượng
màu nền `B` và màu chủ thể sạch `F` ở lân cận, đo điểm ảnh bị kéo về phía nền bao nhiêu rồi
kéo ngược lại đúng ngần ấy — `C' = C - t*(B - F)`. Không có phép chia nên không vọt.

| | lệch màu so với chủ thể sạch tại chỗ | % điểm lệch nặng |
|---|---|---|
| chưa khử | +3,12 | 19,5% |
| đã khử | **−0,24** | **6,2%** |

Chỉ động vào dải mép: thử trên ảnh có cây dù trong suốt, chỉ 1,48% điểm ảnh đổi, giọt nước
và nan dù nguyên vẹn. Tốn thêm khoảng 1,8 giây với ảnh 42 MP.

Muốn tắt thì thêm `--giu-mau-nen`.

### Vì sao không dùng `Hm4Cpv1_ov.onnx`

Bản `.onnx` trong `3-leien-models-raw.zip` **hỏng** — `onnxruntime` báo
`INVALID_PROTOBUF`. Đúng như bảng kiểm kê của chính dự án ghi nhận: tra
`docs/research/original-116-model-inventory.csv` dòng 19, cột trạng thái là `FAIL` và
`not-wired`.

## Vì sao bản này không dính lỗi giấy phép

App gốc chạy 2 model này qua engine native (`leien-native.node`), mà engine đó bắt buộc
phải sinh được `ori_key` từ 2 mảnh khoá — đây chính là chỗ phát sinh `KeyError 'ori_key'`
và `登陆信息过期`.

Bản này nạp thẳng tệp `.mnn` bằng thư viện MNN và tệp IR bằng PyTorch, **không đi qua
`ModelManager` và `SecurityCheck`**, nên không có gì để hỏng.

## Đem sang máy khác

Chép cả thư mục đi, chạy được ngay. **Không cần cài Python, không cần pip, không cần
mạng.** Thư mục `python\` là bản Python 3.11 nhúng, đã có sẵn 3 thư viện bên trong.

Đã kiểm thật: chạy với `PATH` chỉ còn `C:\Windows`, không có Python nào của máy — vẫn
chạy đúng. Ba thư viện đều nạp từ `python\Lib\site-packages\`, không đụng tới
`C:\Users\...\AppData` của máy.

Nếu máy kia đã có sẵn Python thì xoá thư mục `python\` đi cũng được (còn 20 MB), rồi chạy
một lần `pip install MNN opencv-python numpy`.

## Cấu trúc

| | cỡ | việc |
|---|---|---|
| `Tach nen - giao dien web.bat` | 1 KB | mở giao diện làm hàng loạt |
| `Tach nen - keo tha anh vao day.bat` | 1 KB | kéo thả ảnh vào là chạy |
| `web.py` | 12 KB | máy chủ cho giao diện (chỉ dùng thư viện sẵn có) |
| `web\index.html` | 17 KB | trang giao diện |
| `tachnen.py` | 10 KB | dòng lệnh: đọc ảnh, ghép nền, ghi kết quả |
| `matting.py` | 9 KB | lõi tách nền, chạy 2 model |
| `hm4cpv1_torch.py` | 7 KB | chỉ dùng cho bản dự phòng `.xml/.bin` (cần torch) |
| `models\` | 20 MB | 2 model chính + 1 bản dự phòng |
| `python\` | 150 MB | Python 3.11 + MNN + OpenCV + numpy |
| **tổng** | **179 MB** | |

Giao diện web **không cần cài thêm gì** — dùng `http.server` có sẵn trong Python. Bản
`tkinter` đã thử rồi bỏ, vì Python nhúng không kèm Tcl/Tk, phải chép thêm 10 MB.

Mã tham khảo từ `leien-photo-ai-app/scripts/runtime/human_matting.py`. Thư mục `D:\ai`
không bị sửa gì ngoài việc thêm thư mục `tachnen` này.
