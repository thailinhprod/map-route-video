#!/usr/bin/env python3
"""Toán tile Web Mercator cho ảnh nền.

  python3 tile_math.py bbox <lon0> <lat0> <lon1> <lat1> <zoom>
      → in dải tile x0 y0 x1 y1, số tile, kích thước mosaic (px)
  python3 tile_math.py px <lon> <lat> [zoom=17]
      → toạ độ pixel thế giới (dùng làm hệ toạ độ chung cho camera Remotion)

Quy ước trong template: mọi điểm/tuyến quy về pixel thế giới ở zoom 17.
Mosaic zoom z có gốc (x0*256, y0*256) ở zoom z → nhân 2**(17-z) để ra zoom 17.
"""
import math, sys

def tile(lon, lat, z):
    n = 2 ** z
    la = math.radians(lat)
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n

def world_px(lon, lat, z=17):
    x, y = tile(lon, lat, z)
    return x * 256, y * 256

def meters_per_px(lat, z):
    return 156543.03392 * math.cos(math.radians(lat)) / 2 ** z

if __name__ == '__main__':
    if sys.argv[1] == 'bbox':
        lo0, la0, lo1, la1, z = map(float, sys.argv[2:7]); z = int(z)
        x0, y0 = tile(lo0, la1, z); x1, y1 = tile(lo1, la0, z)
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        nx, ny = x1 - x0 + 1, y1 - y0 + 1
        print(f"z={z} x0={x0} y0={y0} x1={x1} y1={y1} tiles={nx*ny} mosaic={nx*256}x{ny*256}px "
              f"({meters_per_px((la0+la1)/2, z):.2f} m/px)")
    elif sys.argv[1] == 'px':
        lon, lat = float(sys.argv[2]), float(sys.argv[3]); z = int(sys.argv[4]) if len(sys.argv) > 4 else 17
        print(world_px(lon, lat, z))
