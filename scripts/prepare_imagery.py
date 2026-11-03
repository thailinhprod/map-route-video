#!/usr/bin/env python3
"""Chuẩn bị một ảnh nhìn thẳng từ trên xuống để làm nền cho video bản đồ.

Dùng cho ảnh bạn có quyền sử dụng: ảnh flycam đã chỉnh thẳng hướng bắc, ảnh mua bản quyền,
hoặc ảnh vệ tinh tải hợp lệ. Script không tải ảnh từ mạng.

  python3 prepare_imagery.py <ảnh> <lon_tây> <lat_nam> <lon_đông> <lat_bắc> <ảnh_ra.jpg> [zoom]

Bốn toạ độ là bốn mép ảnh, hướng bắc ở trên. Bỏ trống zoom thì script chọn theo độ phân giải ảnh.
Script in ra đoạn JSON để dán vào `satellite` của scene.json hoặc `maps` của job.json.
Ảnh được coi là chiếu Web Mercator. Sai số không đáng kể với một khu vực vài chục km.
"""
import json, math, os, sys
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
MAX_SIDE = 12000


def tile_xy(lon, lat, z):
    n = 2 ** z
    la = math.radians(lat)
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n


def main():
    if len(sys.argv) < 7:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[6]
    west, south, east, north = map(float, sys.argv[2:6])
    if not (west < east and south < north):
        sys.exit('Toạ độ phải theo thứ tự: tây < đông, nam < bắc.')
    im = Image.open(src).convert('RGB')
    if len(sys.argv) > 7:
        z = int(sys.argv[7])
    else:
        span = (east - west) / 360  # tỉ lệ chiều ngang địa cầu
        z = max(10, min(19, round(math.log2(im.width / (span * 256)))))
    x0, y0 = tile_xy(west, north, z)
    x1, y1 = tile_xy(east, south, z)
    w, h = round((x1 - x0) * 256), round((y1 - y0) * 256)
    if max(w, h) > MAX_SIDE:
        sys.exit(f'Ảnh ra quá lớn ({w}×{h}). Hãy dùng zoom thấp hơn {z}.')
    im.resize((w, h), Image.LANCZOS).save(out, quality=90)
    name = os.path.basename(out)
    print(json.dumps({'scene.json > satellite': {'file': name, 'x': round(x0, 4), 'y': round(y0, 4), 'z': z},
                      'job.json > maps': {'img': name, 'z': z, 'x0': round(x0, 4), 'y0': round(y0, 4), 'w': w, 'h': h}},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
