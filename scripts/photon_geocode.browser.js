// Chạy trong trình duyệt (origin bất kỳ; Photon cho phép CORS). Tìm toạ độ địa điểm nổi tiếng
// từ dữ liệu OpenStreetMap qua Photon (komoot). Nghỉ 1,5 s giữa các lần
// để tránh "Failed to fetch" do giới hạn tốc độ. lat/lon = điểm ưu tiên (gần khu vực đang làm).
const QUERIES = ['Chợ Bến Thành', 'Landmark 81'];
const NEAR = { lat: 10.79, lon: 106.76 };
const res = [];
for (const q of QUERIES) {
  await new Promise(r => setTimeout(r, 1500));
  try {
    const j = await fetch(`https://photon.komoot.io/api/?limit=3&lat=${NEAR.lat}&lon=${NEAR.lon}&q=${encodeURIComponent(q)}`).then(r => r.json());
    res.push([q, j.features.map(f => [f.properties.name, `${f.properties.osm_key}:${f.properties.osm_value}`, f.geometry.coordinates.map(v => +v.toFixed(5))])]);
  } catch (e) { res.push([q, 'ERR ' + e]); }
}
res;
// Chọn kết quả có tên khớp và loại hợp lý (building/shop:mall/railway/man_made:bridge…).
// Điểm "highway:bus_stop" mang tên toà nhà vẫn dùng được như vị trí gần đúng.
