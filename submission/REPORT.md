# Báo cáo Day 09 — Hồ Trung Kiên, 2A202603090

> Xoá mọi  và dòng gợi ý. Mỗi ý trả lời bằng **số lấy từ `submission/reports/`**, kèm mẫu số. Cả báo cáo ~1–2 trang.

## 1. Kết luận trước
pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).

## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
|| | | |

vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy? Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa?

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 4 | Trùng gần `1.00 / 0.50 → 1.00 / 0.67`. Trùng byte `1.00 / 1.00 → 1.00 / 1.00`. | Bắt thêm 1 ảnh gần trùng (3/6 → 4/6), với 0 báo sai trên calib. Đây là ngưỡng nhỏ nhất đạt kết quả đó trong nhóm 4–14. |
| `second_opinion.conf` | 0.25 | 0.60 | Nhầm lớp `0.56 / 0.83 → 0.62 / 0.83`. Thiếu box `0.50 / 1.00 → 0.57 / 1.00`. Box lỏng `0.29 / 0.40 → 0.20 / 0.20`. Box dư `0.31 / 1.00 → 0.31 / 1.00`. | Báo nhầm lớp sai giảm 4 → 3, báo thiếu box sai giảm 8 → 6, vẫn bắt 5/6 ca nhầm lớp và 8/8 ca thiếu box. Đánh đổi là chỉ bắt 1/5 ca box lỏng, so với 2/5 ban đầu. Box dư dùng ngưỡng `fp_conf` riêng. |

Trên calib, pHash 16 đạt precision 1.00 và bắt 5/6 ảnh gần trùng. Trên raw, ngưỡng này loại 31/224 ảnh ở cửa vào, so với 19/224 ở cả ngưỡng 2 và 4. Khi mở ảnh, cặp `img_0011` và `img_0008` (khoảng cách 16) lần lượt là cảnh chơi tennis và trượt tuyết. Cặp `img_0177` và `img_0113` (khoảng cách 16) lần lượt là cảnh lướt sóng và người ngồi ở bàn ăn. Cả hai cặp đều bị báo trùng sai ở ngưỡng 16. Vì vậy, precision 1.00 trên calib chưa đủ để dùng ngưỡng này để tự động loại ảnh raw.

Ở ngưỡng 4, hai cặp gần trùng `img_0076`–`img_0042` và `img_0143`–`img_0037` đều cho thấy cùng một cảnh khi mở ảnh. Với hai ngưỡng đã chọn, lô raw có 38/205 ảnh còn cảnh báo sau duyệt (18,54%), giảm từ 60/205 (29,27%) ở cấu hình khởi đầu. Kết luận vẫn là `Hold` vì tỷ lệ này vượt ngưỡng 10%.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
(a) chứng minh gate chặn đúng: chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên), chỉ ra kết luận **Rework**, mã thoát 20 và việc **không xuất** dataset. (Đừng sửa tay `work/run/ds`: pipeline dựng lại thư mục này từ raw mỗi lần chạy.) (b) ≥ 2 điểm mù có bằng chứng (box lỏng nhẹ, nhầm lớp mà model lớn cũng nhầm, ảnh trùng biến đổi mạnh…).

Khi xem nhãn vẽ trên ảnh của lô raw, tôi ghi nhận ba lỗi:

- `img_0001` thiếu một box `person` cho người xuất hiện trong ảnh.
- `img_0002` có một box `person` gán nhầm cho động cơ thuyền.
- `img_0035` có một box `person` gán nhầm cho cây.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

chênh mAP50 (clean − raw) so với **độ lệch chuẩn giữa các seed**; kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm.

## 6. Quyết định và ghi chú AI
(a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release? (b) Dùng AI viết code? Ghi 3 dòng: prompt chính, cách bạn kiểm code AI, 1 lần AI sai. Không dùng: ghi "không dùng".

*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
