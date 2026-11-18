"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml

from ..common import ERROR, parse_yolo_line


DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE_CODES = {"LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _write_text(path, text):
    # Thay thế sau khi ghi xong để lỗi ghi không làm mất nội dung file cũ.
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        temporary_path.write_text(text, encoding="utf-8")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _clip_box(text):
    class_id, cx, cy, width, height = parse_yolo_line(text)
    left, right = cx - width / 2, cx + width / 2
    top, bottom = cy - height / 2, cy + height / 2
    if 0 <= left < right <= 1 and 0 <= top < bottom <= 1:
        return text

    left, right = max(0.0, left), min(1.0, right)
    top, bottom = max(0.0, top), min(1.0, bottom)
    if right <= left or bottom <= top:
        return None

    box = (class_id, (left + right) / 2, (top + bottom) / 2, right - left, bottom - top)
    return " ".join(map(str, box))


def fix(ds, issues, cfg):
    line_actions = defaultdict(dict)
    removed_images = set()
    needs_label = set()
    rename_classes = False

    for issue in issues:
        if issue.severity != ERROR:
            continue
        code = issue.code
        if code in REMOVE_CODES or code.startswith("DUP_IMAGE_"):
            removed_images.add(issue.image)
        elif code == "MISSING_LABEL_FILE":
            needs_label.add(issue.image)
        elif code == "BAD_CLASS_NAME":
            rename_classes = True
        elif issue.line is not None:
            if code in DROP_CODES:
                line_actions[issue.image][issue.line] = "drop_line"
            elif code == "BOX_OUT_OF_IMAGE":
                line_actions[issue.image].setdefault(issue.line, "clip_box")

    changes = []
    for stem in sorted(removed_images):
        image_path = ds.image_path(stem)
        label_path = ds.label_path(stem)
        files = [path for path in (image_path, label_path) if path is not None and path.exists()]
        for path in files:
            path.unlink(missing_ok=True)
        if files:
            changes.append(dict(image=stem, line=None, action="remove_image",
                                before=", ".join(path.name for path in files), after=""))

    if rename_classes:
        data = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) if ds.yaml_path.exists() else {}
        data = data or {}
        before = data.get("names")
        classes = cfg["classes"]
        after = list(classes) if isinstance(before, list) else dict(enumerate(classes))
        if before != after:
            data["names"] = after
            _write_text(ds.yaml_path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
            changes.append(dict(image="data.yaml", line=None, action="rename_classes",
                                before=str(before), after=str(after)))

    for stem in sorted(needs_label - removed_images):
        if not ds.label_path(stem).exists():
            changes.append(dict(image=stem, line=None, action="needs_label",
                                before="(không có file)", after="chuyển người gán"))

    for stem in sorted(line_actions.keys() - removed_images):
        label_path = ds.label_path(stem)
        if not label_path.exists():
            continue
        actions = line_actions[stem]
        lines = label_path.read_text(encoding="utf-8", errors="replace").splitlines()
        updated = []
        file_changes = []
        for line, before in enumerate(lines, 1):
            action = actions.get(line)
            if action is None or not before.strip():
                updated.append(before)
                continue

            after = _clip_box(before) if action == "clip_box" else None
            if after is not None:
                updated.append(after)
            if after != before:
                file_changes.append(dict(image=stem, line=line, action="drop_line" if after is None else action,
                                         before=before, after="" if after is None else after))

        if file_changes:
            _write_text(label_path, "".join(text + "\n" for text in updated))
            changes.extend(file_changes)

    return changes
