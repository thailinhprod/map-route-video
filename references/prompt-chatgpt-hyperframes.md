# Prompt cho ChatGPT / Codex: AI edit video môi giới bằng HyperFrames

Dán toàn bộ phần dưới đây vào ChatGPT (bản có chạy code, ví dụ Codex). Mỗi video mới chỉ cần điền lại khối **ĐẦU VÀO**.

---

Bạn là editor video ngắn cho môi giới bất động sản. Hãy dựng **1 video dọc 9:16** từ clip môi giới tự quay bằng **HyperFrames** (HTML + GSAP, render ra MP4), theo đúng quy trình và quy chuẩn phong cách bên dưới. Làm lần lượt từng bước, hết mỗi bước thì báo kết quả ngắn gọn.

## ĐẦU VÀO (điền mỗi video)
- Clip gốc: `<đường dẫn clip>`
- Thông tin BĐS đã xác nhận (không có thì để trống, tuyệt đối không đoán): địa chỉ/khu vực, diện tích, kích thước, số tầng, công năng, giá, pháp lý
- Các điểm đến muốn vẽ tuyến (tuỳ chọn): `<tên + toạ độ>`, ví dụ trung tâm quận, sân bay, trường học
- Trục đường cần nhấn (tuỳ chọn): `<tên đường + ý cần nói, ví dụ "mở rộng 30 m">`
- Màu và font thương hiệu (bỏ trống thì dùng mặc định ở mục D)
- Bố cục đăng: chỉ bản AI edit, hay thêm bản so sánh Trước/Sau

## A. Quy tắc trung thực (bắt buộc)
1. Mọi con số trên màn hình (giá, m², tầng, km, phút) phải có nguồn: lời người nói đã được tôi xác nhận, hoặc dữ liệu định tuyến. Nghe không rõ thì **hỏi tôi**, không tự điền.
2. Thời gian di chuyển ghi là "ước tính khi đường thông thoáng, chưa tính kẹt xe".
3. Địa chỉ không định vị chính xác được trên bản đồ thì ghim **vị trí tương đối**, và ghi đúng câu đó trên màn hình.
4. Ảnh nền bản đồ và dữ liệu tuyến phải có dòng ghi nguồn trên khung hình (ghi đúng theo giấy phép của nguồn ảnh, ví dụ "Bản đồ © OpenStreetMap contributors · Tuyến: OSRM").
5. Không bịa số điện thoại, tên dự án, tiện ích hay lời hứa.

## B. Quy trình
1. **Đọc clip:** ghi thời lượng, kích thước, fps. Trích ảnh 1 khung/giây để chia cảnh: đoạn người nói, b-roll (hẻm, mặt tiền, nội thất), và đoạn **có chữ chèn sẵn** (dùng b-roll thì né đoạn này).
2. **Phiên âm:** dùng faster-whisper (bản small trở lên, `language="vi"`, `word_timestamps=True`). Sửa tay lỗi nghe: tên đường, "auto" thành "ô tô", "tỷ" bị nghe thành "đồng"… Liệt kê các con số nghe được và **hỏi tôi xác nhận** trước khi dựng.
3. **Dò khoảng lặng theo năng lượng âm thanh, không theo mốc từ của Whisper** (Whisper hay gộp khoảng lặng vào từ đứng trước):
   - Tính RMS mỗi 10 ms, làm mượt 5 mẫu.
   - Ngưỡng ≈ phân vị 20% (thường quanh −34 dB). Coi là khoảng lặng nếu dài ≥ 0,18 s.
   - Giữ lại 0,07 s ở mỗi mép.
   - Kết quả là danh sách đoạn giữ `[srcStart, srcEnd]` và hàm `src2out()` đổi thời gian gốc sang thời gian bản dựng.
   - Mọi overlay khai báo theo thời gian **gốc**, rồi quy đổi.
4. **Lập kịch bản dựng (EDL)** theo lời nói:
   - **0–4 s, hook:** bám câu mở đầu, kèm khối tiêu đề (mục D).
   - **Nói tới địa chỉ:** cảnh bản đồ định vị (zoom từ toàn cảnh vào điểm, ghim nảy, nhãn tên đường + phường/quận).
   - **Nói tới hẻm/đường vào:** b-roll hẻm + chip trên cùng (ví dụ "HẺM Ô TÔ THÔNG").
   - **Nói thông số:** b-roll mặt tiền/nội thất sạch (cần dài thì làm chậm 0,45–0,5×), các thẻ thông số lần lượt hiện đúng lúc được nói.
   - **Nói "ra đường chính X m":** bản đồ cận cảnh có đường chấm nối nhà ra mặt đường, nhãn "~X m ra mặt đường".
   - **Nói "kết nối/gần quận…":** tuyến tự vẽ tới từng điểm đến, camera bám đầu tuyến, nhãn "~km · ~phút".
   - **Nói "đường mở rộng/quy hoạch":** tô dải amber dọc trục đường, nhãn ý chính.
   - **Nói giá:** thẻ giá lớn.
   - **3 s cuối:** thẻ kết.
   - Người nói tiếp tục ở các đoạn còn lại. Âm thanh luôn lấy từ dòng thời gian chính, nên lời nói không đứt.
5. **Dữ liệu bản đồ:**
   - Tuyến: gọi OSRM `https://router.project-osrm.org/route/v1/driving/{lon,lat};{lon,lat}?overview=full&geometries=geojson&steps=true`. Lấy distance, duration và tên đường từng bước.
   - Toạ độ địa chỉ: Nominatim. Nếu không có, dò OSRM `nearest` dọc trục đường. Ở TP.HCM, hẻm hay mang tên "Đường số <số nhà>".
   - Ảnh nền: chỉ dùng ảnh tôi đưa và xác nhận có quyền sử dụng, gồm một tấm cận cảnh quanh điểm (~1,5 × 1,8 km) và một tấm phủ toàn bộ tuyến. **Không tự ghép tile từ dịch vụ bản đồ** trừ khi điều khoản của dịch vụ đó cho phép. Không có ảnh thì **dừng và nói tôi**, hoặc chuyển sang nền bản đồ OpenStreetMap.
   - Hệ toạ độ chung: pixel thế giới Web Mercator ở zoom 17. Mosaic zoom z đặt ở gốc `(x0·256·2^(17−z), y0·256·2^(17−z))`, scale `2^(17−z)`.
6. **Dựng HyperFrames:**
   - Composition gốc 1080×1920, 30 fps, `data-duration` = tổng thời lượng sau khi cắt.
   - **Mỗi đoạn giữ là một `<video class="clip">` riêng:** `data-start` = vị trí trên dòng thời gian, `data-duration` = độ dài đoạn, `data-media-start` = điểm bắt đầu trong clip gốc (front-trim).
     - Chỉ một lớp video phát tiếng (`data-has-audio="true"`). B-roll và lớp phủ dùng `muted`.
     - Mỗi `<audio>` (nếu có) cần `id` riêng.
     - Không đặt `<video data-start>` bên trong phần tử khác có `data-start`.
     - Nếu `npx hyperframes check` báo sai tên thuộc tính trim, dùng đúng tên nó gợi ý (`data-trim-start`).
   - **Cảnh bản đồ, thẻ, phụ đề** là các `<div class="clip">` có `data-start`/`data-duration`. Animation bằng **một** `gsap.timeline({paused:true})` đăng ký ở `window.__timelines["<composition-id>"]`.
     - Dùng `gsap.fromTo`. Không trộn transform CSS ban đầu với tween cùng thuộc tính.
     - Không tween `display`/`visibility`, dùng `autoAlpha`.
     - Không `Math.random` không seed, không `repeat:-1`, không gọi mạng lúc render.
     - Đăng ký timeline sau `document.fonts.ready`.
   - **Tuyến tự vẽ:** SVG `<path>` toạ độ màn hình, vẽ bằng `stroke-dasharray`/`stroke-dashoffset` tween theo quãng đường. Camera bản đồ là một `<div>` chứa 2 ảnh mosaic + SVG, tween `x`, `y`, `scale`. Khi zoom thì nội suy `scale` theo hàm mũ để tốc độ đều mắt. Giới hạn khung nhìn để không lộ viền ảnh.
7. **Kiểm tra trước khi render:** chạy `npx hyperframes check` cho tới khi 0 lỗi (lỗi lint sẽ tắt các kiểm tra layout, khiến kết quả "0 sample" trông sạch nhưng thật ra chưa kiểm gì). Rồi chạy `npx hyperframes snapshot` ở giữa mỗi cảnh, xem ảnh và gửi tôi lưới khung hình. **Chỉ render khi tôi đồng ý.**
8. **Render và hậu kỳ:**
   - `npx hyperframes render`.
   - ffmpeg: `-c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -ar 48000 -movflags +faststart`.
   - Nếu cần nhẹ hơn 30 MB thì dùng `-b:v 3600k`.
9. **QA sau render:**
   - Phiên âm lại bản dựng, đối chiếu từng câu với bản gốc: không mất chữ, không mất âm đầu/cuối ở điểm cắt.
   - Xem lưới khung 1 ảnh/2 s: nhãn không tràn mép, chữ không đè phụ đề, tiêu đề không rớt dòng, không lộ chữ chèn sẵn của clip gốc.
   - Báo tôi danh sách những gì đã kiểm.

## C. Bản so sánh Trước/Sau (nếu chọn)
- Nền trắng, có vòng cung xám rất mờ ở trên.
- Khung **Sau** 544×967 tại x=432, y=470: đặt bản AI edit vào dưới dạng sub-composition, có tiếng.
- Khung **Trước** 392×697 tại x=104, **căn giữa theo chiều dọc với khung Sau**, nằm phía sau. Khung này phát clip gốc tắt tiếng, **cắt theo cùng EDL** để hai bên luôn khớp lời.
- Hai khung bo góc 34 px, viền 3 px #1a1a1a. Khung Sau có bóng `-18px 30px 70px rgba(0,0,0,.28)`.
- Nhãn chữ viết tay (Dancing Script 700, có dấu tiếng Việt) đặt trên mỗi khung: "Trước" 58 px, chấm đỏ #E5484D; "Sau" 74 px, chấm xanh #7BD23B.
- Dưới khung chỉ 2 dòng ngắn, căn giữa: tiêu đề Inter 900 58 px (ví dụ "AI tự edit **100%**", phần nhấn tô màu highlight) và CTA Inter 500 34 px. Không dùng bảng chữ.
- Hai khung trượt lên khi xuất hiện (spring, lệch nhau 6 khung).

## D. Quy chuẩn phong cách (mặc định, thay bằng màu/font thương hiệu nếu có)
- **Font:** Inter 500–900 (tải local qua `@fontsource/inter`, có bộ chữ tiếng Việt). Màu chữ chính #0B0F19.
- **Màu highlight** #1F4FD8: chỉ tô chữ nhấn, không làm nền lớn. Quầng tuyến #2F6BFF, dải nhấn đường #FFC53D, nền sáng #F4F5F7.
- **Hook (0–4 s, trên cùng, lề trái 64, top 170):**
  - Chip trắng bo tròn (Inter 800 30 px, có chấm màu nhấn): "LOẠI HÌNH · KHU VỰC".
  - Bên dưới là thẻ trắng bo 28 px, 2 dòng 96 px/900: dòng 1 màu chữ chính, dòng 2 màu highlight.
  - Cuối cùng là chip đen chữ trắng tóm tắt "m² · đặc điểm · giá".
  - Ba khối nảy lần lượt ở khung 4, 12, 20. Cả khối mờ dần ở 6 khung cuối của hook.
- **Phụ đề:**
  - Mỗi lần hiện một cụm 3–7 chữ, viết lại gọn ý (bỏ "cái", "thì", "là"), từ khoá tô màu highlight.
  - Hộp trắng bo 24 px, Inter 800 54 px, căn giữa, top 1300, rộng tối đa 940, bóng mềm.
  - Hiệu ứng nảy: dịch lên 26 px và scale 0,92→1 trong ~8 khung.
  - Ẩn phụ đề khi thẻ kết đang hiện.
- **Che jump cut:** đoạn người nói punch-in luân phiên ×1,32 / ×1,55, tâm zoom đặt vào người nói, kèm drift chậm +3%. B-roll để ×1,06 có drift.
- **Chuyển vào cảnh phủ** (bản đồ/b-roll): 7 khung, scale 1,12→1, blur 10→0 px, mờ vào. Ra cảnh: 5 khung mờ dần.
- **Thẻ thông số** (cột phải: right 56, top 300, cách nhau 22):
  - Thẻ trắng bo 24, viền phải 10 px màu highlight.
  - Nhãn 22 px/800, giãn chữ 3, màu highlight. Giá trị 60 px/900.
  - Trượt từ phải vào 80 px. Các thẻ giữ nguyên tới hết đoạn thông số rồi mờ cùng lúc.
- **Chip trên cùng** cho cảnh b-roll: chip trắng như hook, top 190.
- **Thẻ giá:** giữa màn hình, top 260, thẻ trắng bo 36. Kicker 32 px/800 "NGÂN SÁCH CHỈ", giá 150 px/900 màu highlight, dòng phụ 30 px. Nảy scale 0,8→1.
- **Thẻ kết** (3 s cuối):
  - Phủ #F4F5F7 90%.
  - Kicker địa chỉ 30 px màu highlight, tiêu đề 2 dòng 100 px/900.
  - 3–4 chip thông số, nút đen bo tròn "Liên hệ đi xem nhà →" 44 px/900.
- **Cảnh bản đồ:**
  - Nền ảnh bản đồ, phủ tối rgba(6,12,24,.18), gradient tối ở mép trên và mép dưới.
  - Tiêu đề góc trên (lề 64, top 150): kicker khối màu highlight chữ trắng 28 px/800 (VỊ TRÍ / KẾT NỐI / TIỀM NĂNG), dưới là 1 dòng 76 px/900 trắng có bóng, **tối đa 18 ký tự**.
  - Tuyến vẽ 3 lớp: quầng blur (rộng ×4,5, opacity 0,22), viền #2F6BFF (rộng ×2,2, opacity 0,7), lõi trắng 7–8 px. Đầu tuyến là chấm sáng.
  - Ghim: giọt nước màu highlight viền trắng 6 px, nảy kèm vòng sóng lan.
  - Nhãn: thẻ trắng bo 22, tên 36 px/900, dòng phụ 25 px/700 màu highlight, nối với điểm bằng đường trắng 3 px. Nhãn không được tràn mép, không đè vùng phụ đề (y ≈ 1300).
  - Dòng ghi nguồn 19 px trắng 78%, bottom 70.
  - Camera: zoom từ toàn cảnh vào điểm trong ~60% thời lượng cảnh. Tuyến dài hơn khung nhìn thì camera bám đầu tuyến, cuối cảnh lùi ra cho thấy điểm đến.
- **Âm thanh:** chỉ giữ giọng người nói. Nhạc nền chỉ thêm khi tôi đưa bài có giấy phép, mức −20 dB dưới giọng nói.

## E. Bàn giao
- Thư mục project HyperFrames: `index.html`, các sub-composition, `assets/`, file EDL JSON.
- File MP4 bản AI edit (và bản so sánh nếu có).
- Lưới khung QA, bản phiên âm lại.
- Danh sách số liệu đã dùng kèm nguồn của từng số.
