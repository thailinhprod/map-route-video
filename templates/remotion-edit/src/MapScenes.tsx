import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import edit from './edit.json';
import {C, FONT, W, H} from './theme';
import {ease, usePop} from './ui';

type P = number[];
type Cam = {x: number; y: number; s: number};
const G = edit.geo as unknown as {home: P; axisPoint: P; routeA: P[]; routeB: P[]; axis: P[]; routeADest: P; routeBDest: P; mpp: number};
const MW = edit.maps.wide;
const ML = edit.maps.local;
const L = (edit as any).labels;
const WIDE = {x0: MW.x, y0: MW.y, x1: MW.x + MW.w * MW.scale, y1: MW.y + MW.h * MW.scale};

const clampCam = (c: Cam): Cam => {
  const hw = W / 2 / c.s, hh = H / 2 / c.s;
  const x = Math.min(Math.max(c.x, WIDE.x0 + hw), WIDE.x1 - hw);
  const y = Math.min(Math.max(c.y, WIDE.y0 + hh), WIDE.y1 - hh);
  return {x: hw * 2 > WIDE.x1 - WIDE.x0 ? (WIDE.x0 + WIDE.x1) / 2 : x, y: hh * 2 > WIDE.y1 - WIDE.y0 ? (WIDE.y0 + WIDE.y1) / 2 : y, s: c.s};
};
const lerpCam = (a: Cam, b: Cam, t: number): Cam => ({x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, s: a.s * Math.pow(b.s / a.s, t)});
const toS = (c: Cam, p: P) => [W / 2 + (p[0] - c.x) * c.s, H / 2 + (p[1] - c.y) * c.s];

const cum = (pts: P[]) => {
  const c = [0];
  for (let i = 1; i < pts.length; i++) c.push(c[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return c;
};
const partial = (pts: P[], cm: number[], t: number): P[] => {
  const d = cm[cm.length - 1] * Math.max(0, Math.min(1, t));
  const out: P[] = [pts[0]];
  for (let i = 1; i < pts.length; i++) {
    if (cm[i] <= d) out.push(pts[i]);
    else {
      const k = (d - cm[i - 1]) / (cm[i] - cm[i - 1] || 1);
      out.push([pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k]);
      break;
    }
  }
  return out;
};
const pathD = (c: Cam, pts: P[]) => pts.map((p, i) => { const [x, y] = toS(c, p); return `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`; }).join(' ');

const CA = cum(G.routeA), CB = cum(G.routeB), CAXIS = cum(G.axis);

// ---------- nền ảnh vệ tinh ----------
const Imagery: React.FC<{cam: Cam; dim?: number}> = ({cam, dim = 0.18}) => {
  const wide = {left: W / 2 + (MW.x - cam.x) * cam.s, top: H / 2 + (MW.y - cam.y) * cam.s, width: MW.w * MW.scale * cam.s, height: MW.h * MW.scale * cam.s};
  const local = {left: W / 2 + (ML.x - cam.x) * cam.s, top: H / 2 + (ML.y - cam.y) * cam.s, width: ML.w * cam.s, height: ML.h * cam.s};
  const localOp = interpolate(cam.s, [0.35, 0.6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#1b2128', overflow: 'hidden'}}>
      <Img src={staticFile(MW.img)} style={{position: 'absolute', ...wide}} />
      {localOp > 0 && <Img src={staticFile(ML.img)} style={{position: 'absolute', ...local, opacity: localOp}} />}
      <AbsoluteFill style={{background: `rgba(6,12,24,${dim})`}} />
      <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(5,10,20,0.62) 0%, rgba(5,10,20,0) 24%, rgba(5,10,20,0) 62%, rgba(5,10,20,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};

const Route: React.FC<{cam: Cam; pts: P[]; color?: string; glow?: string; width?: number; opacity?: number}> = ({cam, pts, color = C.white, glow = C.blueGlow, width = 8, opacity = 1}) => {
  if (pts.length < 2) return null;
  const d = pathD(cam, pts);
  return (
    <g opacity={opacity} strokeLinecap="round" strokeLinejoin="round" fill="none">
      <path d={d} stroke={glow} strokeWidth={width * 4.5} opacity={0.22} filter="url(#blur)" />
      <path d={d} stroke={glow} strokeWidth={width * 2.2} opacity={0.7} />
      <path d={d} stroke={color} strokeWidth={width} />
    </g>
  );
};

const HeadDot: React.FC<{cam: Cam; p: P; color?: string}> = ({cam, p, color = C.white}) => {
  const [x, y] = toS(cam, p);
  return (
    <g>
      <circle cx={x} cy={y} r={26} fill={C.blueGlow} opacity={0.35} filter="url(#blur)" />
      <circle cx={x} cy={y} r={13} fill={color} stroke={C.blueGlow} strokeWidth={5} />
    </g>
  );
};

const Pin: React.FC<{cam: Cam; p: P; start: number}> = ({cam, p, start}) => {
  const f = useCurrentFrame();
  const pop = usePop(start, 10);
  if (f < start) return null;
  const [x, y] = toS(cam, p);
  const ring = ((f - start) % 36) / 36;
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%,-100%)'}}>
      <div style={{position: 'absolute', left: '50%', top: '100%', width: 220 * ring, height: 220 * ring * 0.42, transform: 'translate(-50%,-50%)', borderRadius: '50%', border: `4px solid ${C.white}`, opacity: 1 - ring}} />
      <div style={{transform: `scale(${pop}) translateY(${(1 - pop) * -60}px)`, transformOrigin: '50% 100%'}}>
        <svg width="92" height="120" viewBox="0 0 92 120">
          <path d="M46 116 C46 116 6 70 6 44 A40 40 0 0 1 86 44 C86 70 46 116 46 116 Z" fill={C.blue} stroke={C.white} strokeWidth="6" />
          <circle cx="46" cy="44" r="15" fill={C.white} />
        </svg>
      </div>
    </div>
  );
};

const Label: React.FC<{cam: Cam; p: P; start: number; title: string; sub: string; dx?: number; dy?: number; align?: 'l' | 'r'}> = ({cam, p, start, title, sub, dx = 40, dy = -190, align = 'r'}) => {
  const f = useCurrentFrame();
  const pop = usePop(start, 16);
  if (f < start) return null;
  const [x, y] = toS(cam, p);
  const bx = x + dx, by = y + dy;
  return (
    <>
      <svg style={{position: 'absolute', left: 0, top: 0}} width={W} height={H}>
        <line x1={x} y1={y} x2={bx + (align === 'r' ? 0 : 0)} y2={by + 50} stroke={C.white} strokeWidth={3} opacity={pop} />
      </svg>
      <div style={{position: 'absolute', left: bx, top: by, transform: `translateX(${align === 'r' ? 0 : -100}%) scale(${0.85 + 0.15 * pop})`, transformOrigin: align === 'r' ? '0 50%' : '100% 50%', opacity: pop,
        background: C.white, borderRadius: 22, padding: '18px 26px', boxShadow: '0 20px 50px rgba(0,0,0,0.35)', fontFamily: FONT, whiteSpace: 'nowrap'}}>
        <div style={{fontWeight: 900, fontSize: 36, color: C.ink, letterSpacing: 0.3}}>{title}</div>
        <div style={{fontWeight: 700, fontSize: 25, color: C.blue, marginTop: 4, letterSpacing: 1}}>{sub}</div>
      </div>
    </>
  );
};

const Title: React.FC<{kicker: string; big: string; start?: number}> = ({kicker, big, start = 2}) => {
  const pop = usePop(start, 18);
  return (
    <div style={{position: 'absolute', left: 64, right: 64, top: 150, fontFamily: FONT, opacity: pop, transform: `translateY(${(1 - pop) * 30}px)`}}>
      <div style={{display: 'inline-block', background: C.blue, color: C.white, fontWeight: 800, fontSize: 28, letterSpacing: 3, padding: '10px 20px', borderRadius: 10}}>{kicker}</div>
      <div style={{color: C.white, fontWeight: 900, fontSize: 76, lineHeight: 1.05, marginTop: 18, textShadow: '0 6px 30px rgba(0,0,0,0.55)'}}>{big}</div>
    </div>
  );
};

const Attribution: React.FC<{note?: string}> = ({note}) => (
  <div style={{position: 'absolute', left: 0, right: 0, bottom: 70, textAlign: 'center', fontFamily: FONT, fontWeight: 500, fontSize: 19, color: 'rgba(255,255,255,0.78)', lineHeight: 1.5}}>
    {note && <div>{note}</div>}
    <div>{(edit as any).attribution}</div>
  </div>
);

const Svg: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg style={{position: 'absolute', left: 0, top: 0}} width={W} height={H}>
    <defs><filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="10" /></filter></defs>
    {children}
  </svg>
);

const HOME_CAM: Cam = {x: G.home[0], y: G.home[1] + 120, s: 1.25};

// ---------- A: định vị ----------
export const MapA: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const t = interpolate(f, [0, dur * 0.62], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const startCam: Cam = {x: (G.home[0] + G.routeADest[0]) / 2, y: G.home[1], s: 0.2};
  const cam = clampCam(lerpCam(startCam, HOME_CAM, t));
  const pinAt = Math.round(dur * 0.55);
  return (
    <AbsoluteFill>
      <Imagery cam={cam} />
      <Svg><Route cam={cam} pts={G.axis} color={C.amber} glow="#b8860b" width={5} opacity={interpolate(f, [dur * 0.45, dur * 0.6], [0, 0.9], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})} /></Svg>
      <Pin cam={cam} p={G.home} start={pinAt} />
      <Label cam={cam} p={G.home} start={pinAt + 8} title={L.a.title} sub={L.a.sub} dx={-300} dy={-330} />
      <Title kicker={L.a.kicker} big={L.a.big} start={3} />
      <Attribution note={L.a.note} />
    </AbsoluteFill>
  );
};

// ---------- B: ra trục chính ----------
export const MapB: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const cam = clampCam(lerpCam(HOME_CAM, {x: G.home[0] - 60, y: G.home[1] + 60, s: 1.55}, interpolate(f, [0, dur], [0, 1], {extrapolateRight: 'clamp'})));
  const prog = interpolate(f, [4, dur * 0.7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const seg = [G.home, G.axisPoint];
  const [hx, hy] = toS(cam, G.home);
  const [nx, ny] = toS(cam, G.axisPoint);
  return (
    <AbsoluteFill>
      <Imagery cam={cam} dim={0.1} />
      <Svg>
        <Route cam={cam} pts={G.axis} color={C.amber} glow="#b8860b" width={7} opacity={0.95} />
        <line x1={hx} y1={hy} x2={hx + (nx - hx) * prog} y2={hy + (ny - hy) * prog} stroke={C.white} strokeWidth={7} strokeDasharray="4 16" strokeLinecap="round" />
      </Svg>
      <Pin cam={cam} p={G.home} start={0} />
      <Label cam={cam} p={G.axisPoint} start={8} title={L.b.title} sub={L.b.sub} dx={40} dy={-260} />
      <Title kicker={L.b.kicker} big={L.b.big} start={2} />
      <Attribution />
    </AbsoluteFill>
  );
};

// ---------- C: hai tuyến kết nối ----------
export const MapC: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const drawEnd = dur * 0.78;
  const p = interpolate(f, [6, drawEnd], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const routeA = partial(G.routeA, CA, p);
  const routeB = partial(G.routeB, CB, Math.min(1, p * (CA[CA.length - 1] / CB[CB.length - 1])));
  const head = routeA[routeA.length - 1];
  const endCam: Cam = {x: (G.routeADest[0] + G.routeBDest[0]) / 2 + 300, y: (G.routeADest[1] + G.routeBDest[1]) / 2 + 900, s: 0.2};
  const zoomOut = interpolate(f, [0, 22], [0, 1], {extrapolateRight: 'clamp', easing: ease});
  const follow = lerpCam(HOME_CAM, {x: head[0], y: head[1] + 600, s: 0.24}, zoomOut);
  const settle = interpolate(f, [drawEnd - 10, dur - 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const cam = clampCam(lerpCam(follow, endCam, settle));
  const doneB = p * (CA[CA.length - 1] / CB[CB.length - 1]) >= 1;
  const m = edit.meta;
  return (
    <AbsoluteFill>
      <Imagery cam={cam} />
      <Svg>
        <Route cam={cam} pts={routeB} width={6} />
        <Route cam={cam} pts={routeA} width={7} />
        <HeadDot cam={cam} p={head} />
        {doneB && <HeadDot cam={cam} p={G.routeBDest} />}
      </Svg>
      <Pin cam={cam} p={G.home} start={0} />
      {doneB && <Label cam={cam} p={G.routeB[G.routeB.length - 1]} start={Math.round(drawEnd * 0.72)} title={L.c.titleB} sub={`~${(m.routeB.dist / 1000).toFixed(0)} KM · ~${Math.round(m.routeB.dur / 60)} PHÚT`} dx={-30} dy={-210} align="l" />}
      <Label cam={cam} p={G.routeA[G.routeA.length - 1]} start={Math.round(drawEnd)} title={L.c.titleA} sub={`~${(m.routeA.dist / 1000).toFixed(0)} KM · ~${Math.round(m.routeA.dur / 60)} PHÚT`} dx={30} dy={-250} />
      <Title kicker={L.c.kicker} big={L.c.big} start={2} />
      <Attribution note={L.c.note} />
    </AbsoluteFill>
  );
};

// ---------- D: tô trục đường ----------
export const MapD: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const mid = G.axis[Math.floor(G.axis.length * 0.5)];
  const from: Cam = {x: (G.routeADest[0] + G.routeBDest[0]) / 2, y: G.routeADest[1], s: 0.2};
  const to: Cam = {x: mid[0], y: mid[1] + 250, s: 0.36};
  const cam = clampCam(lerpCam(from, to, interpolate(f, [0, 26], [0, 1], {extrapolateRight: 'clamp', easing: ease})));
  const grow = interpolate(f, [18, dur * 0.6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: ease});
  const band = partial(G.axis, CAXIS, grow);
  const pulse = 0.75 + 0.25 * Math.sin(f / 5);
  return (
    <AbsoluteFill>
      <Imagery cam={cam} dim={0.25} />
      <Svg>
        <Route cam={cam} pts={G.routeA} width={4} opacity={0.45} />
        <g opacity={pulse}><Route cam={cam} pts={band} color={C.amber} glow="#ff9f1a" width={16} /></g>
      </Svg>
      <Pin cam={cam} p={G.home} start={0} />
      <Label cam={cam} p={G.axis[Math.floor(G.axis.length * 0.3)]} start={Math.round(dur * 0.5)} title={L.d.title} sub={L.d.sub} dx={-200} dy={-330} />
      <Title kicker={L.d.kicker} big={L.d.big} start={2} />
      <Attribution />
    </AbsoluteFill>
  );
};
