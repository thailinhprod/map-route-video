// Chạy trong trình duyệt, sau khi mở https://tiles.openfreemap.org/planet (trang TileJSON).
// Tải vector tile OpenStreetMap mới nhất (OpenMapTiles schema, cập nhật hằng tuần) cho một bbox,
// gói thành 1 file JSON (tile .pbf dạng base64) rồi tải về Downloads. XIN PHÉP NGƯỜI DÙNG TRƯỚC KHI TẢI.
// Sửa BBOX và NAME trước khi chạy. z14 là zoom cao nhất của OpenFreeMap (đủ chi tiết tới toà nhà).
const BBOX = [106.70, 10.76, 106.78, 10.82];   // lon0, lat0, lon1, lat1
const NAME = 'osm_khuvuc_tiles.json';
const tj = JSON.parse(document.body.innerText);
const tmpl = tj.tiles[0];                          // .../planet/<version>/{z}/{x}/{y}.pbf
const version = tmpl.split('/planet/')[1].split('/')[0];
const z = 14, n = 2 ** z;
const lx = l => Math.floor((l + 180) / 360 * n);
const ly = a => { const r = a * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * n); };
const out = { z, version, source: 'OpenFreeMap / OpenMapTiles © OpenStreetMap contributors', tiles: {} };
for (let x = lx(BBOX[0]); x <= lx(BBOX[2]); x++) for (let y = ly(BBOX[3]); y <= ly(BBOX[1]); y++) {
  const u = new Uint8Array(await fetch(tmpl.replace('{z}', z).replace('{x}', x).replace('{y}', y)).then(r => r.arrayBuffer()));
  let s = ''; for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000));
  out.tiles[`${x}_${y}`] = btoa(s);
}
const blob = new Blob([JSON.stringify(out)], { type: 'application/json' });
const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = NAME; document.body.appendChild(a); a.click();
({ version, tiles: Object.keys(out.tiles).length, bytes: blob.size });
