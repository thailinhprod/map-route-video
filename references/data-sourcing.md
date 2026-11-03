# Lấy dữ liệu bản đồ

## Nguồn và điều kiện dùng
Điều khoản có thể đổi, nên kiểm tra lại trước khi dùng cho mục đích thương mại.

| Việc | Nguồn | Ghi chú |
|---|---|---|
| Tuyến, km, phút | OSRM demo `router.project-osrm.org` | Máy chủ thử nghiệm, không cam kết độ ổn định. Gọi ít, không bán lại quyền truy cập, ghi nguồn OSRM và OpenStreetMap. Làm số lượng lớn thì tự host OSRM. |
| Toạ độ địa điểm | Photon `photon.komoot.io` | Dữ liệu OSM. Nghỉ 1,5 giây giữa các lần gọi. |
| Nền bản đồ | Vector tile `tiles.openfreemap.org` | Dữ liệu OSM, cập nhật định kỳ. Ghi "© OpenStreetMap contributors". |
| Ảnh vệ tinh | Ảnh người dùng có quyền sử dụng | Xem mục dưới. |

## Ảnh vệ tinh
Skill không kèm công cụ tải ảnh vệ tinh, vì nhiều dịch vụ cấm thu thập tile hàng loạt, lưu lại hoặc dùng trong sản phẩm thương mại. Ví dụ tài liệu tóm tắt điều khoản của Esri không cho thu thập tile có hệ thống ngoài Content Packages và không cho tải về, phân phối lại hay tự lưu trữ nội dung do Esri host.

Đừng ghép tile từ một dịch vụ nếu chưa đọc điều khoản của dịch vụ đó. Hãy hỏi người dùng ảnh đến từ đâu và ghi nguồn đúng theo giấy phép. Dùng `scripts/prepare_imagery.py` để căn ảnh theo toạ độ. Không có ảnh hợp lệ thì dùng kiểu `osm`.

| Nguồn | Hợp với | Lưu ý |
|---|---|---|
| Flycam của người dùng | Cận cảnh khu đất | Cần ảnh nhìn thẳng xuống, chỉnh về hướng bắc, biết toạ độ bốn mép. |
| Ảnh mua từ nhà cung cấp | Mọi cảnh | Phải đọc giấy phép về video và quảng cáo. |
| OpenAerialMap | Nơi có ảnh | CC BY 4.0, cần ghi nguồn. Điều khoản không nói rõ về thương mại. |
| Sentinel-2 cloudless (EOX) | Cảnh toàn khu | Khoảng 10 m/điểm ảnh. Dịch vụ miễn phí chỉ cho phi thương mại, thương mại cần giấy phép của EOX. |
| Google Earth Studio | Không dùng cho quảng cáo | Google không cấp giấy phép cho ứng dụng thương mại. |

## Khi mạng bị chặn
Môi trường chạy code thường chặn các host trên. Thử theo thứ tự: gọi trực tiếp, công cụ đọc web của phiên làm việc, rồi trình duyệt của người dùng. Trình duyệt thường mở được OSRM, OpenFreeMap và Photon. Luôn xin phép trước khi tải file về máy người dùng.

## Định vị địa chỉ Việt Nam không cần geocoder
- Dùng OSRM `nearest` (`/nearest/v1/driving/lon,lat?number=8`) để lấy tên đường gần nhất, dò dọc trục đường rồi nội suy vị trí số nhà.
- Nhiều hẻm ở TP.HCM có tên "Đường số <số nhà>" trên OSM.
- Số hẻm không có trên OSM thì ghim **vị trí tương đối** sát mặt đường và ghi rõ trên video. Không phóng quá zoom 17.
- Mỗi lần chỉ truy vấn vài điểm. Quét dày dễ bị chặn và làm phiền máy chủ.

## Lấy tuyến
Trong trình duyệt, đứng trên origin OSRM rồi chạy:

```js
await fetch('/route/v1/driving/LON_A,LAT_A;LON_B,LAT_B?overview=full&geometries=geojson&steps=true').then(r => r.json())
```

Giữ `distance`, `duration` và `steps`. Giảm tuyến xuống khoảng 200 điểm nếu cần.
