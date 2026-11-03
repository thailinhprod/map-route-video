#!/usr/bin/env python3
"""Video bản đồ tuyến đường 9:16 với 3 phong cách dùng chung một camera + dữ liệu.

  neon      — nền tối, đường OSM mờ, tuyến phát sáng lime
  osm       — bản đồ sáng từ dữ liệu OpenStreetMap (vector tile OpenFreeMap)
  satellite — ảnh vệ tinh do người dùng cung cấp (có quyền sử dụng), lớp phủ neon cyan

Dùng: python3 render3.py <style> <scene.json> <out_dir> [t1,t2,...]
Mốc giây t1,t2 → chỉ xuất PNG để QA. scene.json: xem example_scene.json.
Hệ toạ độ chung = pixel thế giới Web Mercator ở zoom 17.
"""
import json, math, os, subprocess, sys, base64
import cairo

W, H, FPS = 1080, 1920, 30
Z = 17
WORLD = 256 * 2 ** Z


# ---------- toạ độ ----------
def ll2w(lon, lat):
    r = math.radians(lat)
    return ((lon + 180) / 360 * WORLD,
            (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * WORLD)


def m_per_px(lat):  # mét / pixel z17
    return 156543.03392 * math.cos(math.radians(lat)) / 2 ** Z


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def back(x, k=1.7): x = clamp(x); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t


def hexc(h, a=1.0):
    h = h.lstrip('#'); return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


# ---------- phong cách ----------
STYLES = {
    'neon': dict(
        land='#0a0e13', water='#0f2a33', water_edge='#1f5866', park='#0d1a14', building='#141b23',
        road_minor=('#1a222c', 0), road_major=('#2a3644', 0), road_motor=('#3a4a5c', 0),
        casing=None, route='#c6ff3d', route_core='#ffffff', glow=True, accent='#c6ff3d',
        label_bg='#091017', label_fg='#ffffff', label_sub='#c6ff3d', label_border='#c6ff3d',
        place_fg='#8a98a8', place_halo='#0a0e13', title_fg='#ffffff', overlay=0.0,
        credit='Dữ liệu © OpenStreetMap · OpenFreeMap · Tuyến OSRM', credit_fg='#6b7785'),
    'osm': dict(
        land='#f3f0ea', water='#a9d3e6', water_edge='#8fc0d8', park='#cfe8c7', building='#e2ddd5',
        road_minor=('#ffffff', 1), road_major=('#ffffff', 1), road_motor=('#ffd27a', 1),
        casing='#cfc8bd', route='#1a73e8', route_core=None, glow=False, accent='#1a73e8',
        label_bg='#ffffff', label_fg='#1f2328', label_sub='#1a73e8', label_border=None,
        place_fg='#5b6470', place_halo='#f3f0ea', title_fg='#1f2328', overlay=0.0,
        credit='Bản đồ © OpenStreetMap contributors · OpenFreeMap · Tuyến OSRM', credit_fg='#6b7280'),
    'satellite': dict(
        land='#1b2418', water=None, park=None, building=None,
        road_minor=None, road_major=None, road_motor=None, casing=None,
        route='#38f2ff', route_core='#ffffff', glow=True, accent='#38f2ff',
        label_bg='#ffffff', label_fg='#0b1220', label_sub='#0a7d8c', label_border=None,
        place_fg='#ffffff', place_halo='#000000', title_fg='#ffffff', overlay=0.22,
        credit=''  # bắt buộc đặt scene['credit'] theo giấy phép của ảnh
       , credit_fg='#d0d6dc'),
}


# ---------- dữ liệu OSM (vector tile OpenMapTiles) ----------
ROAD_CLASS = {'motorway': 'motor', 'trunk': 'motor', 'primary': 'major', 'secondary': 'major',
              'tertiary': 'major', 'minor': 'minor', 'service': None, 'track': None, 'path': None}


def load_osm(path, bbox_w):
    """Đọc file JSON chứa tile .pbf base64 → các lớp hình học ở pixel z17, đã cắt theo bbox."""
    import mapbox_vector_tile as mvt
    d = json.load(open(path))
    tz = d['z']; k = 2 ** (Z - tz) * 256
    x0, y0, x1, y1 = bbox_w
    L = {'water': [], 'park': [], 'building': [], 'minor': [], 'major': [], 'motor': [], 'place': []}

    def conv(tx, ty, ext, pts):
        return [((tx + px / ext) * k, (ty + py / ext) * k) for px, py in pts]

    def rings(geom):
        t = geom['type']; c = geom['coordinates']
        if t == 'Polygon': return [c]
        if t == 'MultiPolygon': return c
        return []

    def lines(geom):
        t = geom['type']; c = geom['coordinates']
        if t == 'LineString': return [c]
        if t == 'MultiLineString': return c
        return []

    for key, b64 in d['tiles'].items():
        tx, ty = map(int, key.split('_'))
        if (tx + 1) * k < x0 or tx * k > x1 or (ty + 1) * k < y0 or ty * k > y1:
            continue
        dec = mvt.decode(base64.b64decode(b64), default_options={'y_coord_down': True})
        for lname, lay in dec.items():
            ext = lay.get('extent', 4096)
            for f in lay['features']:
                g = f['geometry']; p = f.get('properties', {})
                if lname == 'water':
                    for poly in rings(g): L['water'].append([conv(tx, ty, ext, r) for r in poly])
                elif lname == 'park' or (lname == 'landcover' and p.get('class') in ('grass', 'wood')):
                    for poly in rings(g): L['park'].append([conv(tx, ty, ext, r) for r in poly])
                elif lname == 'building':
                    for poly in rings(g): L['building'].append([conv(tx, ty, ext, r) for r in poly])
                elif lname == 'transportation':
                    c = ROAD_CLASS.get(p.get('class'))
                    if c and p.get('brunnel') != 'tunnel':
                        for ln in lines(g): L[c].append(conv(tx, ty, ext, ln))
                elif lname == 'place' and g['type'] == 'Point':
                    if p.get('class') in ('suburb', 'town', 'city'):
                        nm = p.get('name:vi') or p.get('name')
                        if nm:
                            L['place'].append((conv(tx, ty, ext, [g['coordinates']])[0], nm, p.get('class')))
    # bỏ nhãn trùng (tile kề nhau lặp lại)
    seen, pl = set(), []
    for pt, nm, c in L['place']:
        if nm not in seen: seen.add(nm); pl.append((pt, nm, c))
    L['place'] = pl
    return L


# ---------- vẽ cơ bản ----------
def path(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]: ctx.line_to(*p)


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def font(ctx, size, bold=True):
    ctx.select_font_face('Inter', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)


def tw(ctx, s): return ctx.text_extents(s).x_advance


def text(ctx, s, x, y, size, col, a=1.0, align='l', bold=True, halo=None, halo_w=6):
    font(ctx, size, bold)
    w = tw(ctx, s)
    if align == 'c': x -= w / 2
    elif align == 'r': x -= w
    ctx.move_to(x, y)
    if halo:
        ctx.text_path(s); c = hexc(halo); ctx.set_source_rgba(c[0], c[1], c[2], .85 * a)
        ctx.set_line_width(halo_w); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
        ctx.move_to(x, y)
    c = hexc(col) if isinstance(col, str) else col
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a); ctx.show_text(s)
    return w


def set_c(ctx, h, a=1.0):
    c = hexc(h); ctx.set_source_rgba(c[0], c[1], c[2], c[3] * a)


# ---------- tuyến ----------
class Route:
    def __init__(self, pts_w):
        self.p = pts_w
        self.cum = [0.0]
        for a, b in zip(pts_w, pts_w[1:]): self.cum.append(self.cum[-1] + math.dist(a, b))
        self.L = self.cum[-1]

    def partial(self, f):
        d = f * self.L; out = [self.p[0]]
        for i in range(1, len(self.p)):
            if self.cum[i] <= d: out.append(self.p[i])
            else:
                a, b = self.p[i - 1], self.p[i]; t = (d - self.cum[i - 1]) / max(1e-9, self.cum[i] - self.cum[i - 1])
                out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t))); break
        return out


# ---------- camera ----------
def make_camera(scene, route):
    hx, hy = ll2w(*scene['home'])
    pw = [ll2w(*p['ll']) for p in scene.get('pois', [])]  # khung cuối chứa cả địa điểm nổi tiếng
    xs = [p[0] for p in route.p] + [p[0] for p in pw]; ys = [p[1] for p in route.p] + [p[1] for p in pw]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    fit = min(W * 0.80 / (max(xs) - min(xs)), H * 0.42 / max(1, max(ys) - min(ys)))
    s0 = scene.get('start_scale', 0.85)
    T = scene['timing']

    def cam(t):
        # 0..draw_start: cận cảnh nhà, đẩy nhẹ vào. draw: lùi dần theo hàm mũ, bám đầu tuyến → khung toàn tuyến.
        if t < T['draw_start']:
            k = t / T['draw_start']; return hx, hy, s0 * (1.0 + 0.06 * eout(k))
        u = eio(seg(t, T['draw_start'], T['draw_end'] + 0.6))
        s = s0 * 1.06 * (fit / (s0 * 1.06)) ** u
        f = eio(seg(t, T['draw_start'], T['draw_end']))
        tip = route.partial(f)[-1]
        # tâm: nhà → bám đầu tuyến (sớm) → tâm toàn tuyến (cuối)
        fol = eio(seg(t, T['draw_start'], T['draw_start'] + 1.4))
        fin = eio(seg(t, T['draw_end'] - 1.6, T['draw_end'] + 0.6))
        fx = lerp(lerp(hx, tip[0], fol), cx, fin)
        fy = lerp(lerp(hy, tip[1], fol), cy, fin)
        return clamp_cam((fx, fy, s), scene.get('_bounds'))
    return cam


def clamp_cam(cam, b):
    """Giữ khung hình nằm trong mosaic vệ tinh (không lộ viền đen)."""
    x, y, s = cam
    if not b: return cam
    x0, y0, x1, y1 = b
    hw, hh = W / 2 / s, H / 2 / s
    if x1 - x0 > 2 * hw: x = clamp(x, x0 + hw, x1 - hw)
    if y1 - y0 > 2 * hh: y = clamp(y, y0 + hh, y1 - hh)
    return x, y, s


def to_screen(cam, p):
    x, y, s = cam
    return ((p[0] - x) * s + W / 2, (p[1] - y) * s + H / 2)


# ---------- lớp bản đồ ----------
def draw_vector(ctx, st, L, cam):
    x, y, s = cam
    set_c(ctx, st['land']); ctx.paint()
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(s, s); ctx.translate(-x, -y)
    vx0, vy0 = x - W / 2 / s, y - H / 2 / s; vx1, vy1 = x + W / 2 / s, y + H / 2 / s

    def vis(pts):
        return any(vx0 - 200 < px < vx1 + 200 and vy0 - 200 < py < vy1 + 200 for px, py in pts[::max(1, len(pts) // 8)] + [pts[-1]])

    def polys(lst, col, edge=None, ew=1.0):
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        for poly in lst:
            if not vis(poly[0]): continue
            for r in poly: path(ctx, r); ctx.close_path()
        set_c(ctx, col); ctx.fill_preserve() if edge else ctx.fill()
        if edge: ctx.set_line_width(ew / s); set_c(ctx, edge); ctx.stroke()

    polys(L['park'], st['park'])
    polys(L['water'], st['water'], st.get('water_edge'), 1.5)
    if s > 0.32:
        a = clamp((s - 0.32) / 0.25)
        ctx.push_group(); polys(L['building'], st['building']); ctx.pop_group_to_source(); ctx.paint_with_alpha(a)

    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    widths = {'minor': 7, 'major': 13, 'motor': 18}
    mins = {'minor': 0.8, 'major': 1.6, 'motor': 2.6}
    order = ['minor', 'major', 'motor']
    if s < 0.2: order = ['major', 'motor']  # toàn cảnh: bỏ hẻm nhỏ cho đỡ rối
    for pass_ in ('casing', 'fill'):
        for c in order:
            col, _ = st['road_' + c]
            w = max(mins[c], widths[c] * s) / s
            if pass_ == 'casing':
                if not st['casing']: continue
                ctx.set_line_width(w + 2.2 / s); set_c(ctx, st['casing'])
            else:
                ctx.set_line_width(w); set_c(ctx, col)
            for ln in L[c]:
                if vis(ln): path(ctx, ln)
            ctx.stroke()
    ctx.restore()


class Sat:
    def __init__(self, files):
        self.layers = []
        for f, tx, ty, z in files:
            png = f + '.png'
            if not os.path.exists(png):
                from PIL import Image; Image.open(f).convert('RGB').save(png)
            surf = cairo.ImageSurface.create_from_png(png)
            k = 2 ** (Z - z)
            self.layers.append((surf, tx * 256 * k, ty * 256 * k, k, z))
        self.layers.sort(key=lambda l: l[4])

    def draw(self, ctx, cam):
        x, y, s = cam
        ctx.set_source_rgb(0.1, 0.12, 0.1); ctx.paint()
        for i, (surf, ox, oy, k, z) in enumerate(self.layers):
            # tấm thô nhất luôn nằm dưới; tấm nét hơn hiện dần khi 1 pixel của nó ≥ ~0,5 pixel màn hình
            a = 1.0 if i == 0 else clamp((s * k - 0.45) / 0.3)
            if a <= 0: continue
            ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(s * k, s * k); ctx.translate((ox - x) / k, (oy - y) / k)
            ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD); ctx.paint_with_alpha(a)
            ctx.restore()


# ---------- lớp phủ ----------
def draw_route(ctx, st, route, cam, f, t):
    if f <= 0: return
    pts = [to_screen(cam, p) for p in route.partial(f)]
    if len(pts) < 2: return
    ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    c = hexc(st['route'])
    if st['glow']:
        for w, a in ((34, .10), (20, .22), (11, .55)):
            path(ctx, pts); ctx.set_line_width(w); ctx.set_source_rgba(c[0], c[1], c[2], a); ctx.stroke()
        path(ctx, pts); ctx.set_line_width(6); ctx.set_source_rgba(*c); ctx.stroke()
        path(ctx, pts); ctx.set_line_width(2.2); set_c(ctx, st['route_core'], .9); ctx.stroke()
    else:  # kiểu Google Maps: viền trắng + lõi xanh
        path(ctx, pts); ctx.set_line_width(16); ctx.set_source_rgba(1, 1, 1, 1); ctx.stroke()
        path(ctx, pts); ctx.set_line_width(10); ctx.set_source_rgba(*c); ctx.stroke()
    hx, hy = pts[-1]
    if f < 0.999:
        g = cairo.RadialGradient(hx, hy, 0, hx, hy, 34)
        g.add_color_stop_rgba(0, 1, 1, 1, .95); g.add_color_stop_rgba(.35, c[0], c[1], c[2], .55); g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.new_path(); ctx.set_source(g); ctx.arc(hx, hy, 34, 0, 2 * math.pi); ctx.fill()


def draw_pin(ctx, st, x, y, t, t0, kind='home'):
    k = seg(t, t0, t0 + 0.5)
    if k <= 0: return
    c = hexc(st['accent'])
    for i in range(2):  # sóng lan
        ph = ((t - t0) * 0.8 + i * 0.5) % 1
        ctx.new_path()  # arc() nối từ điểm hiện tại (cuối chữ vừa vẽ) nếu không xoá path
        ctx.set_source_rgba(c[0], c[1], c[2], (1 - ph) * .45 * k); ctx.set_line_width(3)
        ctx.arc(x, y, 14 + ph * 46, 0, 2 * math.pi); ctx.stroke()
    sc = back(k)
    ctx.new_path(); ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc)
    if kind == 'home':
        # ghim giọt nước
        ctx.move_to(0, 0); ctx.curve_to(-24, -30, -24, -62, 0, -62); ctx.curve_to(24, -62, 24, -30, 0, 0); ctx.close_path()
        ctx.set_source_rgba(c[0], c[1], c[2], 1); ctx.fill_preserve(); ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(3); ctx.stroke()
        ctx.arc(0, -40, 8, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
    else:
        ctx.arc(0, 0, 13, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
        ctx.arc(0, 0, 8, 0, 2 * math.pi); ctx.set_source_rgba(c[0], c[1], c[2], 1); ctx.fill()
    ctx.restore()


def callout(ctx, st, x, y, title, sub, a, side='r', dy=-150):
    if a <= 0: return
    font(ctx, 38); w1 = tw(ctx, title); font(ctx, 30); w2 = tw(ctx, sub)
    bw, bh = max(w1, w2) + 52, 112
    bx = x + 40 if side == 'r' else x - 40 - bw
    bx = clamp(bx, 40, W - 40 - bw); by = y + dy - bh / 2
    ox = bx if side == 'r' else bx + bw
    ctx.set_line_width(2.5); set_c(ctx, st['accent'], .9 * a)
    ctx.move_to(x, y); ctx.line_to(ox, by + bh / 2); ctx.stroke()
    off = (1 - eout(a)) * 20
    rrect(ctx, bx, by + off, bw, bh, 16); set_c(ctx, st['label_bg'], .94 * a); ctx.fill_preserve()
    if st['label_border']:
        ctx.set_line_width(2.5); set_c(ctx, st['label_border'], .9 * a); ctx.stroke()
    else:
        ctx.new_path()
    text(ctx, title, bx + 26, by + off + 50, 38, st['label_fg'], a)
    text(ctx, sub, bx + 26, by + off + 92, 30, st['label_sub'], a)


POI_COL = {'tower': '#7b1fa2', 'mall': '#ef6c00', 'metro': '#1565c0', 'hospital': '#d93025',
           'bridge': '#455a64', 'city': '#00897b', 'stadium': '#2e7d32', 'park': '#2e7d32'}


def poi_glyph(ctx, kind, r):
    """Hình vẽ trắng trong vòng tròn icon (kiểu Google Maps), toạ độ quanh (0,0)."""
    ctx.set_source_rgba(1, 1, 1, 1); ctx.set_line_width(r * 0.16); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if kind == 'tower':
        for dx, h in ((-0.32, 0.55), (0, 0.95), (0.32, 0.4)):
            ctx.rectangle(dx * r - r * 0.12, r * 0.5 - h * r, r * 0.24, h * r)
        ctx.fill()
    elif kind == 'mall':
        ctx.rectangle(-r * 0.42, -r * 0.18, r * 0.84, r * 0.68); ctx.fill()
        ctx.arc(0, -r * 0.18, r * 0.24, math.pi, 2 * math.pi); ctx.stroke()
    elif kind == 'metro':
        font(ctx, r * 1.15); w = tw(ctx, 'M'); ctx.move_to(-w / 2, r * 0.42); ctx.show_text('M')
    elif kind == 'hospital':
        ctx.rectangle(-r * 0.14, -r * 0.5, r * 0.28, r); ctx.rectangle(-r * 0.5, -r * 0.14, r, r * 0.28); ctx.fill()
    elif kind == 'bridge':
        ctx.arc(0, r * 0.35, r * 0.45, math.pi, 2 * math.pi); ctx.stroke()
        ctx.move_to(-r * 0.6, -r * 0.05); ctx.line_to(r * 0.6, -r * 0.05); ctx.stroke()
    elif kind == 'stadium':
        ctx.save(); ctx.scale(1, 0.62); ctx.arc(0, 0, r * 0.48, 0, 2 * math.pi); ctx.restore(); ctx.stroke()
    else:  # city
        ctx.rectangle(-r * 0.45, -r * 0.1, r * 0.38, r * 0.6); ctx.rectangle(-r * 0.02, -r * 0.5, r * 0.45, r * 1.0); ctx.fill()


def poi_reveal_times(scene, route):
    """Mỗi địa điểm hiện lên khi đầu tuyến đi ngang gần nó nhất (theo chiều dài tuyến)."""
    T = scene['timing']; out = []
    for p in scene.get('pois', []):
        w = ll2w(*p['ll'])
        i = min(range(len(route.p)), key=lambda j: math.dist(route.p[j], w))
        f = route.cum[i] / route.L
        lo, hi = 0.0, 1.0  # đảo hàm eio: tìm u sao cho eio(u) = f
        for _ in range(30):
            mid = (lo + hi) / 2
            if eio(mid) < f: lo = mid
            else: hi = mid
        out.append(lerp(T['draw_start'], T['draw_end'], lo) + 0.1)
    return out


def draw_pois(ctx, st, scene, cam, t, times):
    dark = st['title_fg'] == '#ffffff'
    for p, t0 in zip(scene.get('pois', []), times):
        a = seg(t, t0, t0 + 0.35)
        if a <= 0: continue
        x, y = to_screen(cam, ll2w(*p['ll']))
        if not (-50 < x < W + 50 and 300 < y < H - 300): continue
        r = 19
        sc = back(a, 2.2)
        ctx.new_path(); ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc)
        # bóng + vòng trắng + nền màu
        ctx.arc(0, 2, r + 4, 0, 2 * math.pi); ctx.set_source_rgba(0, 0, 0, .28); ctx.fill()
        ctx.arc(0, 0, r + 3, 0, 2 * math.pi); ctx.set_source_rgba(1, 1, 1, 1); ctx.fill()
        ctx.arc(0, 0, r, 0, 2 * math.pi); set_c(ctx, POI_COL.get(p['kind'], '#5f6368')); ctx.fill()
        poi_glyph(ctx, p['kind'], r)
        ctx.restore()
        side = p.get('side', 'r')
        size = 25
        font(ctx, size); w = tw(ctx, p['name'])
        tx = x + r + 12 if side == 'r' else x - r - 12 - w
        ty = y + 9 if side in ('r', 'l') else (y - r - 14 if side == 't' else y + r + 32)
        if side in ('t', 'b'): tx = x - w / 2
        col = '#ffffff' if dark else '#202124'
        halo = '#000000' if st['_name'] == 'satellite' else ('#0a0e13' if dark else '#ffffff')
        text(ctx, p['name'], tx, ty, size, col, eout(a), bold=True, halo=halo, halo_w=7)


def places(ctx, st, L, cam, a, skip=(), avoid=()):
    if not L or a <= 0: return
    for (p, nm, c) in L['place']:
        if nm in skip: continue
        sx, sy = to_screen(cam, p)
        if any(abs(sx - ax) < 170 and abs(sy - ay) < 60 for ax, ay in avoid): continue  # nhường chỗ cho icon địa điểm
        if 60 < sx < W - 60 and 380 < sy < H - 380:
            size = 26 if c in ('suburb', 'town', 'city') else 22
            text(ctx, nm.upper() if c in ('suburb', 'town', 'city') else nm, sx, sy, size, st['place_fg'], a * .9,
                 align='c', bold=c in ('suburb', 'town', 'city'), halo=st['place_halo'], halo_w=6)


def chrome(ctx, st, scene, t):
    # gradient trên/dưới cho chữ dễ đọc
    for (y0, y1, a0, a1) in ((0, 520, .62, 0), (H - 420, H, 0, .55)):
        g = cairo.LinearGradient(0, y0, 0, y1)
        dark = st['title_fg'] == '#ffffff'
        base = (0, 0, 0) if dark else (1, 1, 1)
        g.add_color_stop_rgba(0, *base, a0 if dark else a0 * 1.25); g.add_color_stop_rgba(1, *base, a1 if dark else a1 * 1.25)
        ctx.set_source(g); ctx.rectangle(0, y0, W, y1 - y0); ctx.fill()
    T = scene['timing']
    a = eout(seg(t, 0.15, 0.75))
    off = (1 - a) * 30
    # kicker
    kick = scene['kicker']
    font(ctx, 28); kw = tw(ctx, kick) + 36
    rrect(ctx, 64, 150 + off, kw, 50, 10); set_c(ctx, st['accent'], a); ctx.fill()
    text(ctx, kick, 82, 186 + off, 28, '#0b1220' if st['accent'] != '#1a73e8' else '#ffffff', a)
    text(ctx, scene['title1'], 64, 290 + off, 76, st['title_fg'], a)
    text(ctx, scene['title2'], 64, 378 + off, 76, st['accent'], a)
    # dòng chú thích dưới
    b = eout(seg(t, T['draw_end'], T['draw_end'] + 0.6))
    if b > 0:
        text(ctx, scene['note'], W / 2, H - 230, 30, st['title_fg'], b * .92, align='c', bold=False,
             halo=None)
    text(ctx, scene.get('credit') or st['credit'], W / 2, H - 70, 19, st['credit_fg'], .95, align='c', bold=False)
    # nhãn phong cách nhỏ góc phải trên (chỉ cho bản demo)
    if scene.get('style_tag'):
        text(ctx, scene['style_tag'][st['_name']], W - 64, 186, 24, st['title_fg'], .55 * a, align='r', bold=False)


# ---------- render ----------
def render(style, scene, out_dir, osm=None, sat=None, stills=None):
    """stills='1.0,5.5,9' → chỉ xuất PNG ở các mốc giây đó (QA nhanh), không render video."""
    st = dict(STYLES[style]); st['_name'] = style
    route = Route([ll2w(*p) for p in scene['route']])
    cam_f = make_camera(scene, route)
    T = scene['timing']; dur = scene['duration']
    home = ll2w(*scene['home']); dest = ll2w(*scene['dest'])
    poi_times = poi_reveal_times(scene, route)
    os.makedirs(out_dir, exist_ok=True)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    times = [float(x) for x in stills.split(',')] if stills else [i / FPS for i in range(int(dur * FPS))]
    ff = None if stills else subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                           '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(out_dir, f'{style}.mp4')],
                          stdin=subprocess.PIPE)
    for t in times:
        ctx = cairo.Context(surf)
        cam = cam_f(t)
        if style == 'satellite': sat.draw(ctx, cam)
        else: draw_vector(ctx, st, osm, cam)
        if st['overlay']: ctx.set_source_rgba(0, 0, 0, st['overlay']); ctx.paint()
        avoid = [to_screen(cam, ll2w(*p['ll'])) for p in scene.get('pois', [])] + [to_screen(cam, dest), to_screen(cam, home)]
        places(ctx, st, osm, cam, eout(seg(t, 0.3, 1.2)) * 0.85, skip=scene.get('skip_places', ()), avoid=avoid)
        f = eio(seg(t, T['draw_start'], T['draw_end']))
        draw_route(ctx, st, route, cam, f, t)
        draw_pois(ctx, st, scene, cam, t, poi_times)
        hx, hy = to_screen(cam, home); dx, dy = to_screen(cam, dest)
        draw_pin(ctx, st, dx, dy, t, T['draw_end'] - 0.1, 'dest')
        draw_pin(ctx, st, hx, hy, t, 0.35, 'home')
        callout(ctx, st, hx, hy - 60, scene['home_label'], scene['home_sub'], eout(seg(t, 0.7, 1.2)) * (1 - seg(t, T['draw_start'] + 0.6, T['draw_start'] + 1.0)), side='r', dy=-120)
        callout(ctx, st, dx, dy, scene['dest_label'], scene['dest_sub'], eout(seg(t, T['draw_end'], T['draw_end'] + 0.5)), side='l', dy=-230)
        chrome(ctx, st, scene, t)
        surf.flush()
        if ff: ff.stdin.write(bytes(surf.get_data()))
        else: surf.write_to_png(os.path.join(out_dir, f'{style}_{t:04.1f}.png'))
    if ff: ff.stdin.close(); ff.wait()


if __name__ == '__main__':
    style, scene_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
    scene = json.load(open(scene_p))
    base = os.path.dirname(os.path.abspath(scene_p))
    osm = sat = None
    pad = 6000
    ws = [ll2w(*p) for p in scene['route']]
    bb = (min(p[0] for p in ws) - pad, min(p[1] for p in ws) - pad, max(p[0] for p in ws) + pad, max(p[1] for p in ws) + pad)
    if scene.get('osm_tiles') and os.path.exists(os.path.join(base, scene['osm_tiles'])):
        osm = load_osm(os.path.join(base, scene['osm_tiles']), bb)
    if style == 'satellite':
        if not scene.get('credit'):
            sys.exit("Thiếu scene['credit']: phải ghi nguồn ảnh vệ tinh theo giấy phép của ảnh.")
        sat = Sat([(os.path.join(base, m['file']), m['x'], m['y'], m['z']) for m in scene['satellite']])
        surf, ox, oy, k, _ = sat.layers[0]
        scene['_bounds'] = (ox, oy, ox + surf.get_width() * k, oy + surf.get_height() * k)
    render(style, scene, out, osm, sat, stills=sys.argv[4] if len(sys.argv) > 4 else None)
