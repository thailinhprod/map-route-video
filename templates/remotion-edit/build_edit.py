#!/usr/bin/env python3
"""Sinh src/edit.json cho Remotion từ job.json + gaps.json + routes.json.

  python3 build_edit.py <thư_mục_dữ_liệu>

Mọi nội dung riêng của video (phụ đề, thẻ, mốc thời gian, toạ độ) nằm trong job.json.
Xem job.example.json. Mốc thời gian khai báo theo clip GỐC, script tự quy đổi sang bản đã cắt lặng.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else HERE
FPS = 30
PAD = 0.07  # giữ lại ở mỗi mép khoảng lặng


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding='utf8'))


job, gaps, routes = load('job.json'), load('gaps.json'), load('routes.json')
SRC_START, SRC_END = job['source']['start'], job['source']['end']

cuts = [(a + PAD, b - PAD) for a, b in gaps
        if (b - a - 2 * PAD) >= 0.08 and a + PAD > SRC_START and b - PAD < SRC_END]
segs, t = [], SRC_START
for a, b in cuts:
    segs.append([round(t, 3), round(a, 3)])
    t = b
segs.append([round(t, 3), SRC_END])
segs = [s for s in segs if s[1] - s[0] > 0.05]


def src2out(ts):
    acc = 0.0
    for a, b in segs:
        if ts < a:
            return acc
        if ts <= b:
            return acc + (ts - a)
        acc += b - a
    return acc


O = lambda a: round(src2out(a), 3)
OUT_DUR = src2out(SRC_END)
captions = [{'from': O(a), 'to': O(b), 'text': tx} for a, b, tx in job['captions']]


def wpx(lon, lat, z=17):
    n = 256 * 2 ** z
    la = math.radians(lat)
    return [(lon + 180) / 360 * n, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n]


def line(s):
    return [wpx(*map(float, p.split(','))) for p in s.split()]


def mosaic(m):
    k = 2 ** (17 - m['z'])
    return {'img': m['img'], 'x': m['x0'] * 256 * k, 'y': m['y0'] * 256 * k,
            'w': m['w'], 'h': m['h'], 'scale': k}


ov = job['overlays']
times = lambda key: [O(ov[key][0]), O(ov[key][1])]
overlays = {k: times(k) for k in ('hook', 'mapA', 'mapB', 'mapC', 'mapD', 'price')}
overlays['brollAlley'] = times('broll1') + [ov['broll1'][2]]        # [from, to, srcStart]
overlays['facade'] = times('broll2') + ov['broll2'][2:4]            # [from, to, srcStart, tốc độ]
overlays['specs'] = [[O(a), val, lab] for a, val, lab in ov['specs']]
overlays['specsEnd'] = O(ov['specsEnd'])
overlays['chipSync'] = times('chipSync') + [ov['chipSync'][2]]
overlays['end'] = [O(ov['endStart']), round(OUT_DUR, 3)]

geo = {'home': wpx(*routes['home']), 'axisPoint': wpx(*job['axisPoint']),
       'routeA': line(routes['routeA']), 'routeB': line(routes['routeB']), 'axis': line(routes['axis']),
       'routeADest': wpx(*routes['routeA_meta']['dest']), 'routeBDest': wpx(*routes['routeB_meta']['dest']),
       'mpp': 156543.03392 * math.cos(math.radians(routes['home'][1])) / 2 ** 17}

edit = {'fps': FPS, 'srcDuration': job['source']['duration'], 'outDuration': round(OUT_DUR, 3),
        'durationInFrames': math.ceil(OUT_DUR * FPS), 'segments': segs, 'headRanges': job['headRanges'],
        'captions': captions, 'overlays': overlays, 'geo': geo,
        'maps': {'local': mosaic(job['maps']['local']), 'wide': mosaic(job['maps']['wide'])},
        'meta': {'routeA': routes['routeA_meta'], 'routeB': routes['routeB_meta']},
        'labels': job['labels'], 'content': job['content'], 'attribution': job['attribution']}
json.dump(edit, open(os.path.join(HERE, 'src', 'edit.json'), 'w', encoding='utf8'), ensure_ascii=False)
print('segments', len(segs), 'out', round(OUT_DUR, 2), 's')
