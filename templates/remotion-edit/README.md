# remotion-edit: edit clip môi giới có cảnh bản đồ

`MapScenes.tsx` lo camera, ảnh nền, tuyến, ghim, nhãn. `AiEdit.tsx` lo cắt ghép, phụ đề và các thẻ. Mọi chữ và mốc thời gian của từng video nằm trong `job.json`, không sửa trong mã nguồn.

## Chạy
1. `npm install`
2. Chép vào `public/`: `source.mp4`, ảnh cận cảnh `sat_local.jpg`, ảnh toàn cảnh `sat_wide.jpg`. Ảnh phải là ảnh bạn có quyền dùng. Chạy `scripts/prepare_imagery.py` để lấy giá trị cho `maps`.
3. Tạo một thư mục dữ liệu gồm:
   - `job.json`: chép từ `job.example.json` rồi sửa; `maps` khai báo z, x0, y0, w, h của từng ảnh.
   - `gaps.json`: kết quả của `scripts/silence_cut.py`.
   - `routes.json`: `home` [lon, lat]; `routeA`, `routeB`, `axis` là chuỗi `"lon,lat lon,lat ..."`; `routeA_meta`, `routeB_meta` gồm `dist` (m), `dur` (giây), `dest` [lon, lat].
4. `python3 build_edit.py <thư_mục_dữ_liệu>`, ra `src/edit.json`.
5. Xem thử một khung: `npx remotion still src/Root.tsx AiEdit out/s.jpg --frame=300`
6. Render: `npx remotion render src/Root.tsx AiEdit out/ai-edit.mp4 --concurrency=2`
7. Bản so sánh trước/sau: composition `Compare`.
