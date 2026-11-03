# Map Route Video

**Skill cho Claude giúp môi giới bất động sản làm video bản đồ dọc 9:16 và edit clip giới thiệu nhà, không cần biết dựng video.**

Khách mua nhà luôn hỏi: nhà nằm đâu, ra đường lớn bao xa, về trung tâm mất bao lâu? Thay vì gửi một định vị Google Maps, bạn đưa cho Claude hai địa điểm và nhận về một video 10 giây có tuyến đường tự vẽ.

Tác giả: [Thái Linh](https://facebook.com/thailinhprod) · Hỗ trợ: [Group Facebook](https://www.facebook.com/groups/1408241059869300/)

## Demo

Hai video dưới đây dùng cùng một tuyến, cùng chuyển động camera.

| Neon tối | Bản đồ sáng |
|---|---|
| ![Demo neon](docs/demo_neon.gif) | ![Demo bản đồ sáng](docs/demo_osm.gif) |

Bản mp4 render ở 1080×1920, 30 fps. GIF đã được thu nhỏ để tải nhanh. Tuyến mẫu: Vincom Mega Mall → The Global City, dữ liệu OpenStreetMap, thời gian là ước tính của OSRM.

## Video diễn ra thế nào

![Ba nhịp của video](docs/steps_osm.jpg)

1. **Mở đầu:** cận cảnh điểm xuất phát, ghim và nhãn tên.
2. **Vẽ tuyến:** camera bám đầu tuyến, địa điểm nổi tiếng hiện dần khi đi ngang qua.
3. **Kết:** lùi ra toàn tuyến, hiện điểm đến, km và thời gian.

## Tính năng

| Phong cách | Nền | Hợp với |
|---|---|---|
| **Neon tối** | Dữ liệu OpenStreetMap tông tối | Hook, video viral |
| **Bản đồ sáng** | Dữ liệu OpenStreetMap | Giải thích vị trí rõ ràng |
| **Ảnh vệ tinh hoặc flycam** | Ảnh bạn có quyền dùng | Cho thấy khu đất thật |

Skill cũng edit được clip tự quay: phiên âm, cắt khoảng lặng, phụ đề, thẻ thông số, chèn cảnh bản đồ và làm bản so sánh trước/sau.

## Ảnh vệ tinh

Skill có chế độ ảnh vệ tinh nhưng **không kèm sẵn ảnh và không tự tải ảnh**, vì nhiều dịch vụ không cho thu thập tile hay dùng lại ảnh trong video quảng cáo. Bạn đưa một ảnh được phép dùng, Claude căn đúng toạ độ bằng `scripts/prepare_imagery.py` rồi vẽ tuyến lên đó.

| Nguồn ảnh | Độ nét | Lưu ý |
|---|---|---|
| Ảnh flycam của bạn, chụp thẳng xuống | Rất nét | Cách đơn giản nhất. Cần đúng quy định bay tại khu vực. |
| Ảnh mua từ nhà cung cấp | Tuỳ gói | Đọc giấy phép có cho dùng trong video quảng cáo hay không. |
| [OpenAerialMap](https://openaerialmap.org/legal) | Tuỳ khu vực | CC BY 4.0, phải ghi nguồn. Nhiều nơi chưa có ảnh. Trang điều khoản không nói rõ về thương mại. |
| [Sentinel-2 cloudless](https://eox.at/2025/03/sentinel-2-cloudless-2024/) của EOX | Khoảng 10 m/điểm ảnh | Chỉ hợp cảnh toàn khu. Dịch vụ miễn phí dành cho mục đích phi thương mại, dùng thương mại cần giấy phép của EOX. |

[Google Earth Studio](https://www.google.com/earth/studio/faq/) không cấp giấy phép dùng ảnh Google Earth cho ứng dụng thương mại. Không nên dùng cho quảng cáo bán nhà.

## Remotion

[Remotion](https://www.remotion.dev) là công cụ dựng video bằng mã nguồn. Claude viết cảnh, Remotion xuất thành MP4. Skill dùng Remotion cho phần edit clip, nằm trong `templates/remotion-edit/`. Phần video bản đồ 10 giây không cần Remotion.

Skill đã kèm template nên chạy được ngay. Muốn Claude hiểu Remotion sâu hơn khi tự chỉnh cảnh, cài thêm [skill chính thức của Remotion](https://www.remotion.dev/docs/ai/skills):

```bash
npx skills add remotion-dev/skills
```

**Remotion không dùng giấy phép MIT.** Theo [FAQ của Remotion](https://www.remotion.dev/docs/license/faq), cá nhân và tổ chức từ 3 người trở xuống được dùng miễn phí, kể cả thương mại. Công ty trên 3 người cần mua Company License, kể cả khi chỉ một người dùng. Hãy kiểm tra lại trang này trước khi dùng cho công ty.

## Cài đặt

1. Tải repo về và giải nén, hoặc chạy `git clone`.
2. Thêm skill vào Claude:
   - **Claude Code:** chép thư mục vào `~/.claude/skills/map-route-video/`.
   - **Ứng dụng Claude:** nén thư mục thành file `.zip` rồi thêm vào phần Skills.
3. Cài công cụ trên máy chạy skill:

```bash
pip install pycairo mapbox-vector-tile pillow
# Cần thêm ffmpeg. Phần edit clip cần thêm Node.js, faster-whisper và numpy.
```

## Cách dùng

Nhắn cho Claude như sau:

```text
Làm video bản đồ từ Chợ Bến Thành đến Landmark 81, kiểu nền tối.
```

```text
Đây là clip giới thiệu căn nhà của tôi. Hãy cắt khoảng lặng, thêm phụ đề,
thẻ thông số và cảnh bản đồ. Tôi xác nhận giá và diện tích như sau: ...
```

## Giới hạn cần biết

- **Claude phải chạy được code và mở được nguồn bản đồ.** Nhiều môi trường chặn các nguồn này, khi đó skill lấy dữ liệu qua trình duyệt. Bản Claude chỉ chat là chưa đủ.
- **Thời gian di chuyển là ước tính,** chưa tính kẹt xe.
- **Chưa có chế độ quy hoạch.** Lớp quy hoạch không có trong OpenStreetMap.
- **Clip đưa vào phải là clip bạn có quyền dùng.** Mọi con số trên video cần được bạn xác nhận.

## Giấy phép và nguồn dữ liệu

Mã nguồn của skill dùng giấy phép MIT, xem `LICENSE`. Giấy phép này không áp dụng cho Remotion và dữ liệu bản đồ:

- Dữ liệu © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), giấy phép ODbL. Video phải giữ dòng ghi nguồn.
- Tuyến đường: [OSRM](https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy). Nền bản đồ: [OpenFreeMap](https://openfreemap.org).
- Ảnh nền theo giấy phép của nguồn ảnh bạn dùng.

Bạn tự kiểm tra điều khoản của từng nguồn trước khi đăng. Phần này chỉ để tham khảo, không phải tư vấn pháp lý.

## Tác giả và hỗ trợ

Skill do [Thái Linh](https://facebook.com/thailinhprod) xây dựng. Cần hỗ trợ hoặc muốn trao đổi cách dùng, mời vào [group Facebook](https://www.facebook.com/groups/1408241059869300/).
