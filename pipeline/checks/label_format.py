"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from collections import defaultdict
from math import isclose

from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    limits = cfg["label_format"]
    overflow_tol = limits["overflow_tol"]
    issues = []

    for path in ds.label_files():
        stem = path.stem
        image_size = ds.image_size(stem)
        previous_boxes = defaultdict(list)

        for line, text in ds.read_label_lines(stem) or []:
            try:
                class_id, cx, cy, width, height = parse_yolo_line(text)
            except (ValueError, OverflowError) as error:
                issues.append(Issue("label_format", ERROR, "BAD_FORMAT", stem, str(error), line))
                continue
            if not 0 <= class_id < len(ds.classes):
                issues.append(Issue("label_format", ERROR, "BAD_CLASS_ID", stem,
                                    f"ID lớp {class_id} ngoài danh sách lớp", line))
                continue
            if width <= 0 or height <= 0:
                issues.append(Issue("label_format", ERROR, "BOX_ZERO", stem,
                                    "chiều rộng hoặc chiều cao không dương", line))
                continue

            overflow = max(0.0, width / 2 - cx, height / 2 - cy,
                           cx + width / 2 - 1, cy + height / 2 - 1)
            # Phép tính mép box có thể lệch vài chữ số cuối ở đúng ngưỡng.
            if overflow > overflow_tol and not isclose(overflow, overflow_tol, rel_tol=0, abs_tol=1e-15):
                issues.append(Issue("label_format", ERROR, "BOX_OUT_OF_IMAGE", stem,
                                    f"box tràn ảnh {overflow:.4g}", line, {"overflow": overflow}))

            box = (cx, cy, width, height)
            same_class = previous_boxes[class_id]
            if any(iou_xywh(box, previous) > limits["dup_box_iou"] for previous in same_class):
                issues.append(Issue("label_format", ERROR, "DUP_BOX", stem,
                                    "box trùng với dòng trước cùng lớp", line))
            same_class.append(box)

            if image_size is not None:
                image_width, image_height = image_size
                short_side = min(width * image_width, height * image_height)
                if short_side < limits["min_box_px"]:
                    issues.append(Issue("label_format", WARN, "BOX_TINY", stem,
                                        f"cạnh ngắn của box {short_side:.2f} px", line))
            area = width * height
            if area > limits["max_box_frac"]:
                issues.append(Issue("label_format", WARN, "BOX_HUGE", stem,
                                    f"box chiếm {area:.2%} diện tích ảnh", line))

    return issues
