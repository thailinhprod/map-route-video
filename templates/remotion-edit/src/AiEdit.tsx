import React from 'react';
import {AbsoluteFill, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import edit from './edit.json';
import {C, FONT} from './theme';
import {Chip, Dot, fadeWindow, Rich, usePop} from './ui';
import {MapA, MapB, MapC, MapD} from './MapScenes';

const FPS = edit.fps;
const fr = (s: number) => Math.round(s * FPS);
const O = edit.overlays as any;
const SRC = staticFile('source.mp4');
const T = (edit as any).content;

// Các đoạn người nói (quay rộng) trong clip gốc → punch-in luân phiên để che jump cut
const HEAD = (edit as any).headRanges as [number, number][];
const isHead = (t: number) => HEAD.some(([a, b]) => t >= a && t < b);

const BaseCut: React.FC = () => {
  let acc = 0;
  return (
    <>
      {edit.segments.map(([a, b], i) => {
        const from = fr(acc);
        acc += b - a;
        const dur = fr(acc) - from;
        const head = isHead(a + 0.05);
        const zoom = head ? (i % 2 === 0 ? 1.32 : 1.55) : 1.06;
        return (
          <Sequence key={i} from={from} durationInFrames={dur} premountFor={30}>
            <SegVideo trim={fr(a)} zoom={zoom} dur={dur} head={head} />
          </Sequence>
        );
      })}
    </>
  );
};

const SegVideo: React.FC<{trim: number; zoom: number; dur: number; head: boolean}> = ({trim, zoom, dur, head}) => {
  const f = useCurrentFrame();
  const drift = head ? 1 + 0.03 * (f / Math.max(1, dur)) : 1 + 0.04 * (f / Math.max(1, dur));
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <OffthreadVideo src={SRC} trimBefore={trim} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom * drift})`, transformOrigin: head ? '52% 60%' : '50% 50%'}} />
    </AbsoluteFill>
  );
};

// Cảnh phủ (bản đồ, b-roll) có chuyển cảnh zoom nhanh
const Scene: React.FC<{from: number; to: number; children: React.ReactNode}> = ({from, to, children}) => {
  const a = fr(from), b = fr(to);
  return (
    <Sequence from={a} durationInFrames={b - a} premountFor={30}>
      <SceneWrap dur={b - a}>{children}</SceneWrap>
    </Sequence>
  );
};
const SceneWrap: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const f = useCurrentFrame();
  const inT = interpolate(f, [0, 7], [0, 1], {extrapolateRight: 'clamp'});
  const outT = interpolate(f, [dur - 5, dur], [1, 0], {extrapolateLeft: 'clamp'});
  const scale = 1 + (1 - inT) * 0.12 + (1 - outT) * 0.06;
  return <AbsoluteFill style={{opacity: Math.min(inT * 1.4, outT), transform: `scale(${scale})`, filter: inT < 1 ? `blur(${(1 - inT) * 10}px)` : undefined}}>{children}</AbsoluteFill>;
};

const Broll: React.FC<{srcStart: number; rate?: number}> = ({srcStart, rate = 1}) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <OffthreadVideo src={SRC} muted trimBefore={fr(srcStart)} playbackRate={rate} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${1.06 + f * 0.0012})`}} />
    </AbsoluteFill>
  );
};

// ---------- chữ ----------
const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const cur = edit.captions.find((c) => t >= c.from && t < c.to + 0.05);
  if (!cur || t >= O.end[0]) return null;
  const start = fr(cur.from);
  return <CaptionLine key={start} text={cur.text} start={start} />;
};
const CaptionLine: React.FC<{text: string; start: number}> = ({text, start}) => {
  const pop = usePop(start, 15);
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: 1300, display: 'flex', justifyContent: 'center'}}>
      <div style={{background: C.white, color: C.ink, fontFamily: FONT, fontWeight: 800, fontSize: 54, lineHeight: 1.2, textAlign: 'center',
        padding: '18px 34px', borderRadius: 24, boxShadow: '0 18px 50px rgba(11,15,25,0.35)', maxWidth: 940,
        transform: `translateY(${(1 - pop) * 26}px) scale(${0.92 + 0.08 * pop})`, opacity: Math.min(1, pop * 1.5)}}>
        <Rich text={text} />
      </div>
    </div>
  );
};

const Hook: React.FC = () => {
  const p1 = usePop(4, 14), p2 = usePop(12, 14), p3 = usePop(20, 16);
  return (
    <div style={{position: 'absolute', left: 64, right: 64, top: 170, fontFamily: FONT}}>
      <div style={{opacity: p1, transform: `translateY(${(1 - p1) * 20}px)`}}><Chip><Dot /> {T.hook.chip}</Chip></div>
      <div style={{marginTop: 26, display: 'inline-block', background: C.white, borderRadius: 28, padding: '20px 34px', boxShadow: '0 20px 60px rgba(11,15,25,0.3)', transform: `scale(${0.9 + 0.1 * p2})`, transformOrigin: '0 0', opacity: p2}}>
        <div style={{fontWeight: 900, fontSize: 96, lineHeight: 1, color: C.ink}}>{T.hook.line1}</div>
        <div style={{fontWeight: 900, fontSize: 96, lineHeight: 1.05, color: C.blue}}>{T.hook.line2}</div>
      </div>
      <div style={{marginTop: 20, opacity: p3, transform: `translateY(${(1 - p3) * 16}px)`}}><Chip dark>{T.hook.summary}</Chip></div>
    </div>
  );
};

const Specs: React.FC = () => {
  const f = useCurrentFrame();
  const end = fr(O.specsEnd);
  if (f >= end + 8) return null;
  const out = interpolate(f, [end - 4, end + 6], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', right: 56, top: 300, display: 'flex', flexDirection: 'column', gap: 22, alignItems: 'flex-end', opacity: out}}>
      {O.specs.map(([t, val, lab]: [number, string, string], i: number) => <SpecCard key={i} start={fr(t)} val={val} lab={lab} />)}
    </div>
  );
};
const SpecCard: React.FC<{start: number; val: string; lab: string}> = ({start, val, lab}) => {
  const f = useCurrentFrame();
  const pop = usePop(start, 13);
  if (f < start) return null;
  return (
    <div style={{background: C.white, borderRadius: 24, padding: '18px 30px', boxShadow: '0 18px 46px rgba(11,15,25,0.32)', fontFamily: FONT, textAlign: 'right',
      transform: `translateX(${(1 - pop) * 80}px)`, opacity: Math.min(1, pop * 1.4), borderRight: `10px solid ${C.blue}`}}>
      <div style={{fontWeight: 800, fontSize: 22, letterSpacing: 3, color: C.blue}}>{lab}</div>
      <div style={{fontWeight: 900, fontSize: 60, color: C.ink, lineHeight: 1.05}}>{val}</div>
    </div>
  );
};

const TopChip: React.FC<{from: number; to: number; text: string}> = ({from, to, text}) => {
  const f = useCurrentFrame();
  const a = fadeWindow(f, fr(from), fr(to), 6, 6);
  if (a <= 0) return null;
  return <div style={{position: 'absolute', left: 64, top: 190, opacity: a, transform: `translateY(${(1 - a) * 16}px)`}}><Chip><Dot /> {text}</Chip></div>;
};

const Price: React.FC = () => {
  const f = useCurrentFrame();
  const [a, b] = O.price;
  const op = fadeWindow(f, fr(a), fr(b), 6, 8);
  const pop = usePop(fr(a), 11);
  if (op <= 0) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 260, display: 'flex', justifyContent: 'center', opacity: op}}>
      <div style={{background: C.white, borderRadius: 36, padding: '30px 60px', textAlign: 'center', fontFamily: FONT, boxShadow: '0 24px 70px rgba(11,15,25,0.35)', transform: `scale(${0.8 + 0.2 * pop})`}}>
        <div style={{fontWeight: 800, fontSize: 32, letterSpacing: 4, color: C.ink}}>{T.price.kicker}</div>
        <div style={{fontWeight: 900, fontSize: 150, lineHeight: 1, color: C.blue}}>{T.price.value}</div>
        <div style={{fontWeight: 700, fontSize: 30, color: C.ink, marginTop: 8}}>{T.price.sub}</div>
      </div>
    </div>
  );
};

const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const s = fr(O.end[0]);
  const pop = usePop(s, 14);
  if (f < s) return null;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: `rgba(244,245,247,${0.9 * Math.min(1, pop)})`}} />
      <div style={{position: 'absolute', left: 70, right: 70, top: 520, fontFamily: FONT, opacity: Math.min(1, pop * 1.3), transform: `translateY(${(1 - pop) * 40}px)`}}>
        <div style={{fontWeight: 800, fontSize: 30, letterSpacing: 4, color: C.blue}}>{T.end.kicker}</div>
        <div style={{fontWeight: 900, fontSize: 100, lineHeight: 1.02, color: C.ink, marginTop: 16}}>{T.end.line1}<br /><span style={{color: C.blue}}>{T.end.line2}</span></div>
        <div style={{display: 'flex', flexWrap: 'wrap', gap: 16, marginTop: 34}}>
          {(T.end.chips as string[]).map((t) => (
            <div key={t} style={{background: C.white, borderRadius: 999, padding: '14px 26px', fontWeight: 700, fontSize: 30, color: C.ink, boxShadow: '0 10px 30px rgba(11,15,25,0.12)'}}>{t}</div>
          ))}
        </div>
        <div style={{marginTop: 60, display: 'inline-block', background: C.ink, color: C.white, borderRadius: 999, padding: '28px 56px', fontWeight: 900, fontSize: 44}}>{T.end.cta}</div>
      </div>
    </AbsoluteFill>
  );
};

export const AiEdit: React.FC = () => {
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <BaseCut />
      <Scene from={O.mapA[0]} to={O.mapA[1]}><MapA dur={fr(O.mapA[1]) - fr(O.mapA[0])} /></Scene>
      <Scene from={O.brollAlley[0]} to={O.brollAlley[1]}><Broll srcStart={O.brollAlley[2]} /></Scene>
      <Scene from={O.facade[0]} to={O.facade[1]}><Broll srcStart={O.facade[2]} rate={O.facade[3]} /></Scene>
      <Scene from={O.mapB[0]} to={O.mapB[1]}><MapB dur={fr(O.mapB[1]) - fr(O.mapB[0])} /></Scene>
      <Scene from={O.mapC[0]} to={O.mapC[1]}><MapC dur={fr(O.mapC[1]) - fr(O.mapC[0])} /></Scene>
      <Scene from={O.mapD[0]} to={O.mapD[1]}><MapD dur={fr(O.mapD[1]) - fr(O.mapD[0])} /></Scene>

      <Sequence from={fr(O.hook[0])} durationInFrames={fr(O.hook[1]) - fr(O.hook[0])}><HookFade dur={fr(O.hook[1]) - fr(O.hook[0])} /></Sequence>
      <TopChip from={O.brollAlley[0]} to={O.brollAlley[1]} text={T.chips.broll} />
      <TopChip from={O.chipSync[0]} to={O.chipSync[1]} text={O.chipSync[2]} />
      <TopChip from={O.mapD[1]} to={O.price[0]} text={T.chips.afterMap} />
      <Specs />
      <Price />
      <Captions />
      <EndCard />
    </AbsoluteFill>
  );
};

const HookFade: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [dur - 6, dur], [1, 0], {extrapolateLeft: 'clamp'});
  return <AbsoluteFill style={{opacity: op}}><Hook /></AbsoluteFill>;
};
