# Báo cáo Day 09 — Hồ Trung Kiên 2A202603090

## 1. Kết luận trước

**Hold.** Pipeline quét 224 ảnh raw, loại 19 ảnh (8,48%) và xuất bản nháp `clean_v1` gồm 205 ảnh. Sau khi duyệt 80/125 ảnh trong hàng đợi, còn 0 lỗi bắt buộc và 38/205 ảnh có cảnh báo chưa duyệt (18,54%), vượt ngưỡng 10%. [Tóm tắt pipeline](reports/08_summary.json)

## 2. Lỗi và phân việc

Báo cáo trước khi sửa có 208 mục gồm 55 lỗi bắt buộc và 153 cảnh báo. Trong đó có 19 lỗi ở cửa vào trên 224 ảnh raw và 189 mục QC trên 205 ảnh được nhận. Trước khi sửa, 199/205 ảnh có file nhãn, tổng cộng 675 dòng nhãn có nội dung. [Báo cáo trước khi sửa](reports/02_error_list_v1.csv)

| Mã lỗi và số lượng | Đơn vị | Ai xử lý và vì sao |
|---|---|---|
| `DUP_IMAGE_EXACT` 8, `DUP_IMAGE_NEAR` 2, `LEAK_TEST` 4, `BAD_SIZE` 3, `CORRUPT_IMAGE` 2 | Ảnh / 224 raw | Máy loại ảnh ở cửa vào theo tiêu chí trùng, rò rỉ, kích thước hoặc ảnh hỏng. |
| `BAD_CLASS_ID` 6, `BAD_FORMAT` 3, `BOX_ZERO` 4, `DUP_BOX` 7 | Dòng nhãn | Máy xóa 20 dòng sai ID, sai định dạng, box rỗng hoặc box lặp. |
| `BOX_OUT_OF_IMAGE` 8 | Dòng nhãn | Máy cắt 8 box về trong biên ảnh. |
| `BAD_CLASS_NAME` 2 | Mục cấp dataset | Máy sửa `Person` và `Bus` bằng một lần ghi lại `data.yaml`. |
| `MISSING_LABEL_FILE` 6 | Ảnh / 205 | Người gán nhãn cho 6 ảnh. Máy ghi `needs_label` để chuyển duyệt. |
| `POSSIBLE_MISSING` 53, `POSSIBLE_FALSE_POS` 29, `POSSIBLE_LOOSE_BOX` 28, `POSSIBLE_WRONG_CLASS` 18 | Cảnh báo | Người kiểm tra ảnh vì dự đoán của model là gợi ý. |
| `EMPTY_LABEL` 12, `BOX_TINY` 6, `BOX_HUGE` 3 | Cảnh báo | Người phân biệt ảnh nền, box hợp lệ và lỗi nhãn. |
| `CLASS_RARE` 4 | Mục cấp dataset | Người đối chiếu thống kê lớp. Các mục này hết sau khi máy bỏ các dòng có ID sai. |

Hàng đợi cộng điểm theo loại cảnh báo, độ tin cậy và các lần máy sửa. `img_0020` đứng đầu (11,524 điểm) vì có cả cờ nhầm lớp, thiếu box và một dòng đã bị xóa. Sáu ảnh thiếu file nhãn có điểm 10 và đều được duyệt. Đối chiếu QC sau tự sửa với log cho thấy 80/125 ảnh đã duyệt bao phủ **94/123 cảnh báo ngữ nghĩa**, trên 74/103 ảnh có cảnh báo loại này. Số này đo độ bao phủ của lượt duyệt. [Dấu vết tự sửa](reports/03_fixes.csv) · [QC sau tự sửa](reports/04_error_list_v2.csv) · [Hàng đợi](reports/05_review_queue.csv) · [Log duyệt](reports/06_review_log.csv)

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 4 | Trùng gần `1.00 / 0.50 → 1.00 / 0.67`. Trùng byte `1.00 / 1.00 → 1.00 / 1.00`. | Bắt thêm 1 ảnh gần trùng (3/6 → 4/6), với 0 báo sai trên calib. Đây là ngưỡng nhỏ nhất đạt kết quả đó trong nhóm 4–14. |
| `second_opinion.conf` | 0.25 | 0.60 | Nhầm lớp `0.56 / 0.83 → 0.62 / 0.83`. Thiếu box `0.50 / 1.00 → 0.57 / 1.00`. Box lỏng `0.29 / 0.40 → 0.20 / 0.20`. Box dư `0.31 / 1.00 → 0.31 / 1.00`. | Báo nhầm lớp sai giảm 4 → 3, báo thiếu box sai giảm 8 → 6, vẫn bắt 5/6 ca nhầm lớp và 8/8 ca thiếu box. Đánh đổi là chỉ bắt 1/5 ca box lỏng, so với 2/5 ban đầu. Box dư dùng ngưỡng `fp_conf` riêng. |

Trên calib, pHash 16 đạt precision 1.00 và bắt 5/6 ảnh gần trùng. Trên raw, ngưỡng này loại 31/224 ảnh ở cửa vào, so với 19/224 ở cả ngưỡng 2 và 4. Khi mở ảnh, cặp `img_0011` và `img_0008` (khoảng cách 16) lần lượt là cảnh chơi tennis và trượt tuyết. Cặp `img_0177` và `img_0113` (khoảng cách 16) lần lượt là cảnh lướt sóng và người ngồi ở bàn ăn. Cả hai cặp đều bị báo trùng sai ở ngưỡng 16. Vì vậy, precision 1.00 trên calib chưa đủ để dùng ngưỡng này để tự động loại ảnh raw.

Ở ngưỡng 4, hai cặp gần trùng `img_0076`–`img_0042` và `img_0143`–`img_0037` đều cho thấy cùng một cảnh khi mở ảnh. Với hai ngưỡng đã chọn, lô raw có 38/205 ảnh còn cảnh báo sau duyệt (18,54%), giảm từ 60/205 (29,27%) ở cấu hình khởi đầu. Kết luận vẫn là `Hold` vì tỷ lệ này vượt ngưỡng 10%.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

Chạy `python -X utf8 -m pipeline.run --budget 0 --work work/report-gate-0a92/run --reports work/report-gate-0a92/reports --export-dir work/report-gate-0a92/export`. Với 0 ảnh được duyệt, 6/205 ảnh còn thiếu file nhãn. Gate trả **Rework**, mã thoát **20**, `exported` là `null` và không sinh `clean_v1/manifest.json`.

- **Sai ngữ nghĩa.** Khi xem nhãn raw, tôi thấy `img_0002` có box `person` gán nhầm cho động cơ thuyền. Ảnh này được nhận và không có cờ trong báo cáo trước sửa, hàng đợi hay báo cáo cuối. Trong hai quan sát còn lại, `img_0001` thiếu box `person` và được báo `POSSIBLE_MISSING`, còn `img_0035` có box `person` gán nhầm cho cây và vẫn còn cờ `POSSIBLE_FALSE_POS` dòng 2 sau duyệt. [Báo cáo sau duyệt](reports/07_error_list_v3.csv)
- **Ảnh trùng bị biến đổi mạnh.** Ở pHash 4, bộ kiểm bỏ sót 2/6 ca gần trùng trên calib là `calib_037` (biến đổi mức 3) và `calib_038` (mức 4). [Kết quả calibration](calibration/calibration_report.md) · [Nhãn đối chiếu calib](../data/calib/MANIFEST.csv)

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Hai biến thể dùng `yolo26n.pt`, 20 epoch, seed 0 và 1, batch 16, kích thước ảnh 640. Cả hai dùng chung tập validation 40 ảnh và tập test 100 ảnh theo quy trình của repo. Bảng ghi trung bình và độ lệch chuẩn giữa hai seed. [Bảng tổng hợp Colab](results/comparison.md)

| Biến thể | Ảnh train | mAP50 | mAP50–95 | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| raw | 224 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 205 | 0.700 ± 0.030 | 0.486 ± 0.013 | 0.715 ± 0.073 | 0.615 ± 0.017 |

SHA-1 của cấu hình khớp cả bốn lần train. SHA-1 của manifest khớp cả hai lần train `clean`.

Chênh mAP50 trung bình (clean − raw) là **−0.0254**. Chênh lệch nhỏ hơn độ lệch chuẩn của clean (0.0305), trong khi độ lệch chuẩn của raw là 0.0002. Raw có mAP50 cao hơn ở cả hai seed, nhưng mức chênh thay đổi từ 0.0468 (seed 0) xuống 0.0040 (seed 1). Hai seed chưa đủ để kết luận raw tốt hơn một cách ổn định.

- Ảnh raw trùng với kho test/val có thể làm điểm raw cao hơn. Có thể kiểm tra các cặp `LEAK_TEST` trong `01_intake.csv`, rồi train lại một bản raw chỉ bỏ các ảnh trùng đã xác nhận, với cùng seed và cùng tập đánh giá.
- Clean có ít hơn 19 ảnh train và có thể mất ví dụ hữu ích của lớp `truck`. AP50 trung bình của lớp này giảm từ khoảng 0.648 xuống 0.559. Có thể đếm box `truck` theo lớp trong 19 ảnh bị loại, đối chiếu với nhãn còn lại và so sánh lại trên hai tập train có cùng số ảnh.

## 6. Quyết định và ghi chú AI

Giữ **Hold**. Với 205 ảnh, điều kiện Release là 0 lỗi bắt buộc và tối đa 20 ảnh còn cảnh báo chưa duyệt. Cần xử lý hoặc xác nhận ít nhất 18/38 ảnh đang còn cảnh báo, rồi chạy lại QC và gate theo quy trình duyệt. Giữ ngưỡng gate 10% và ngân sách 80 ảnh của bài lab.

- **Prompt chính.** Nhờ AI viết bốn module theo docstring và test của repo, sau đó yêu cầu một script chỉ đọc nhãn YOLO, in tên file, số dòng và lý do khi box tràn ảnh.
- **Cách kiểm.** Chạy 79 test và chạy pipeline với ngân sách 80 và 0. Kiểm script tràn box trên ca mẫu và bản sao calib, gồm bốn mép ảnh và dòng thiếu cột.
- **Một lỗi của AI.** Bản đầu của script tràn box dừng khi gặp dòng thiếu cột. Bản sửa ghi tên file, số dòng và lý do ra `stderr`, rồi tiếp tục quét. Bản sao calib báo đủ 2 dòng sai định dạng đã chèn.
