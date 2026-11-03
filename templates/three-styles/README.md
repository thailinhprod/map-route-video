# three-styles: video tuyến đường 3 phong cách

```
pip install pycairo mapbox-vector-tile pillow   # cần thêm ffmpeg
python3 render3.py neon      scene.json out     # neon tối
python3 render3.py osm       scene.json out     # bản đồ sáng OSM
python3 render3.py satellite scene.json out     # ảnh vệ tinh của bạn
python3 render3.py osm scene.json out 1.2,5.5,9.5   # chỉ xuất ảnh tĩnh để QA
```

- Đường dẫn file trong `scene.json` tính từ thư mục chứa `scene.json`.
- Kiểu neon và osm cần `osm_tiles` (tạo bằng `scripts/openfreemap_tiles.browser.js`). Thiếu file này thì nền trống.
- Kiểu satellite cần `satellite` và `credit`. Ảnh phải căn đúng lưới tile Web Mercator; `x`, `y`, `z` là tile góc trên trái. Renderer dừng nếu thiếu `credit`.
- Màu từng phong cách nằm trong `STYLES` đầu file.
- `example_scene.json` có tuyến thật nhưng không kèm dữ liệu nền.
