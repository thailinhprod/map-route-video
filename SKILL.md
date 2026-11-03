---
name: map-route-video
description: Dựng video dọc 9:16 có bản đồ tracking ở Việt Nam theo 3 phong cách (neon tối, bản đồ sáng OpenStreetMap, ảnh vệ tinh do người dùng cung cấp), với tuyến đường tự vẽ, camera bám theo, ghim, nhãn km/phút và địa điểm nổi tiếng; kèm quy trình edit clip môi giới tự quay (phiên âm, cắt lặng, phụ đề, thẻ thông số, bản so sánh trước/sau). Dùng skill này khi người dùng muốn làm video bản đồ, video vị trí hay kết nối bất động sản, video "từ A đến B mất bao lâu", hoặc nâng cấp clip giới thiệu nhà, kể cả khi họ không nói từ "tracking".
---

# Video bản đồ tracking và edit clip môi giới

## 0. Chọn hướng làm
- **Chỉ cần video bản đồ:** dùng `templates/three-styles/` (mục 1–2).
- **Có clip môi giới cần edit:** dùng `templates/remotion-edit/` (mục 3).

Ba phong cách dùng chung `scene.json` và cùng camera, nên đổi phong cách chỉ là đổi một tham số.

| Phong cách | Dữ liệu nền | Hợp với | Lệnh |
|---|---|---|---|
| **neon** | Đường, sông, toà nhà OSM tông tối, tuyến lime | Hook, infographic | `render3.py neon scene.json out` |
| **osm** | Vector tile OpenFreeMap, nền sáng | Phân tích vị trí, cần rõ tên phường | `render3.py osm scene.json out` |
| **satellite** | Ảnh người dùng có quyền sử dụng | Cho thấy khu đất thật | `render3.py satellite scene.json out` |

Thêm mốc giây làm tham số thứ 4 (`... out 1.2,5.5,9.5`) để xuất ảnh tĩnh kiểm tra trước khi render cả video.

## 1. Lấy dữ liệu
Đọc `references/data-sourcing.md` trước khi gọi bất kỳ nguồn nào.

1. **Toạ độ:** dùng `scripts/photon_geocode.browser.js`, không tự nhớ toạ độ.
2. **Tuyến:** dùng OSRM, giữ khoảng cách và thời gian. Thời gian luôn ghi là ước tính khi đường thông thoáng, không tự bịa tốc độ.
3. **Nền OSM:** mở `https://tiles.openfreemap.org/planet`, chạy `scripts/openfreemap_tiles.browser.js` sau khi xin phép tải file. Khoảng 24 tile z14 nặng 3,4 MB cho vùng 12 × 8 km.
4. **Ảnh vệ tinh hoặc flycam:** hỏi người dùng nguồn ảnh và quyền sử dụng, xem bảng nguồn trong `references/data-sourcing.md`. Không tự ghép tile từ dịch vụ bản đồ. Ảnh nhìn thẳng, hướng bắc ở trên, có toạ độ bốn mép thì chạy `scripts/prepare_imagery.py` và dán đoạn JSON nó in ra vào `satellite` của `scene.json` hoặc `maps` của `job.json`. Không có ảnh hợp lệ thì đề xuất kiểu `osm`.
5. **Địa chỉ trên thẻ chữ:** hỏi lại người dùng. Sau sáp nhập 7/2025, tên trên bản đồ và tên họ dùng có thể khác nhau. Dùng tên cũ thì ghi "(cũ)".

## 2. Viết `scene.json`
Mẫu: `templates/three-styles/example_scene.json`.

- `home`, `dest`: [lon, lat]. `route`: danh sách [lon, lat].
- `duration`; `timing.draw_start`, `timing.draw_end`: lúc tuyến bắt đầu và kết thúc vẽ.
- `kicker`, `title1`, `title2`: tiêu đề. Dòng 2 có màu nhấn, tối đa 18 ký tự.
- `home_label`, `home_sub`, `dest_label`, `dest_sub`, `note`.
- `pois`: `{name, kind, ll, side}`, với kind là tower, mall, metro, hospital, bridge, city hoặc stadium; side là r, l, t hoặc b. Khung cuối tự mở rộng để chứa mọi điểm, nên chỉ chọn 5–7 điểm gần tuyến.
- `osm_tiles`: file từ `openfreemap_tiles.browser.js`.
- `satellite`: `[{file, x, y, z}]`, với x, y là tile góc trên trái (được phép lẻ). Tấm z thấp nhất làm nền và giới hạn camera. Tấm phủ phải đủ lớn cho khung dọc ở tỉ lệ toàn tuyến, nếu không sẽ lộ viền đen.
- `credit`: bắt buộc với kiểu satellite, ghi đúng nguồn ảnh.
- `skip_places`: nhãn muốn ẩn.
- `style_tag`: chữ nhỏ ở góc, chỉ dùng khi so sánh phong cách.

## 3. Edit clip môi giới
Làm theo `templates/remotion-edit/README.md`. Mọi chữ và mốc thời gian nằm trong `job.json`. Template đã đủ để chạy. Nếu phiên làm việc có skill Remotion, đọc thêm khi cần chỉnh cảnh; nếu chưa có, người dùng có thể cài bằng `npx skills add remotion-dev/skills`.

Trước khi dùng cho công ty, nhắc người dùng: Remotion miễn phí cho cá nhân và tổ chức từ 3 người trở xuống; công ty lớn hơn cần Company License.

1. **Phiên âm:** `scripts/transcribe_vi.py`. Sửa tay tên riêng. **Hỏi lại mọi con số** trước khi đưa lên thẻ.
2. **Cắt lặng:** `scripts/silence_cut.py`, dò theo năng lượng âm thanh vì Whisper hay gộp khoảng lặng vào từ đứng trước. Khai báo overlay theo thời gian gốc để sửa lời không làm lệch cảnh.
3. **Che jump cut:** người nói punch-in luân phiên ×1,32 và ×1,55; b-roll ×1,06, có drift chậm.
4. **Thay hình theo lời:** nói địa chỉ thì hiện bản đồ định vị; nói "ra đường chính" thì cận cảnh có đường nối; nói "kết nối" thì tuyến tự vẽ; nói "mở rộng" thì tô trục đường. Âm thanh luôn lấy từ dòng thời gian chính.
5. **Chữ:** phụ đề 3–7 chữ, `*từ nhấn*` được tô màu. Thẻ thông số hiện đúng lúc được nói. Không bịa số điện thoại hay số liệu.
6. **Quyền sử dụng clip:** chỉ edit và đăng clip người dùng có quyền dùng.
7. **Bản so sánh:** composition `Compare`. Khung Trước phát clip gốc theo cùng điểm cắt để hai bên khớp lời.

Hậu kỳ: `ffmpeg -c:v libx264 -preset slow -crf 23 -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -ar 48000 -movflags +faststart`. Render tuần tự, không chạy nhiều still song song vì dễ hết RAM.

## 4. Kiểm tra trước khi giao
- Xem lưới 1 khung/2 giây: nhãn bị cắt, chữ đè nhau, tiêu đề rớt dòng, viền đen.
- Đối chiếu km và phút với OSRM.
- Dòng ghi nguồn phải có trên video. Khi ghim là vị trí tương đối hoặc thời gian là ước tính, phải có dòng ghi chú tương ứng.
- Với clip đã edit, phiên âm lại bản dựng để chắc không mất chữ.

## 5. Khi dùng công cụ AI khác
`references/prompt-chatgpt-hyperframes.md` là prompt để dựng cùng kiểu video bằng HyperFrames trên ChatGPT hoặc Codex.
