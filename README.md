# VetGo 3D Demo — Bệnh viện Thú y mô phỏng

Trang web 3D isometric (Three.js, một file `index.html`, không cần build) mô phỏng
hoạt động một phòng khám thú y để demo giải pháp VetGo với khách hàng.

## Chạy

Mở thẳng `index.html` bằng trình duyệt, hoặc chạy một server tĩnh:

```bash
python3 -m http.server 5799
# rồi mở http://localhost:5799
```

Thư viện Three.js, GLTFLoader và SkeletonUtils tải từ CDN (cdnjs, jsDelivr) nên cần
mạng lần đầu. Toàn bộ mô hình nhân vật đã nhúng sẵn trong `index.html` (base64).

## Tính năng

- 9 khoa, tường kính, đồ đạc, lưới dẫn đường A\* (người đi qua cửa, tránh đồ đạc, tránh nhau).
- Chủ nuôi dắt chó bằng dây, mèo trong lồng, khách ngồi ghế chờ, nhân viên có mũ, khẩu trang, ống nghe.
- Công tắc **Trước / Với VetGo**: hai bộ tham số vận hành, bảng so sánh với số đo trực tiếp.
- **Theo chân một ca**: bấm vào khách, camera bám theo, dòng thời gian 10 trạm trong vòng đời ca khám.
- Lớp **Điểm nghẽn** (bản đồ nhiệt) và **Luồng thông tin** (giấy đi bộ so với hồ sơ số).
- Bảng điều khiển KPI, hàng chờ theo khoa, biểu đồ theo giờ và theo loài.

Số liệu chế độ "Trước" là số minh họa (xem `PARAMS` trong `index.html`), cần thay bằng
khảo sát thật trước khi demo.

## Cấu trúc

```
index.html                 trang hoàn chỉnh (mô hình đã nhúng)
models/*.glb               mô hình nhân vật, thú cưng, lồng (nguồn: models/CREDITS.md)
blender/build_characters.py   dựng lồng vận chuyển và nhân vật thủ công bằng Blender headless
blender/embed_models.py       nhúng lại models/*.glb vào index.html (chạy sau khi đổi mô hình)
blender/render_lineup.py      render ảnh xem nhanh các mô hình
```

Nhúng lại mô hình sau khi thay file trong `models/`:

```bash
python3 blender/embed_models.py
```

## Giấy phép mô hình

Nhân vật và thú cưng lấy từ Poly Pizza: Quaternius (CC0, một số CC-BY), J-Toastie (CC-BY),
Sherkiz (CC-BY). Chi tiết và yêu cầu ghi nguồn ở `models/CREDITS.md`; trang đã hiện dòng
ghi nguồn ở thanh chú thích phía dưới.
