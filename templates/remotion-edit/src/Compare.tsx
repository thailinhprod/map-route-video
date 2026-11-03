import React from 'react';
import '@fontsource/dancing-script/700.css';
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig} from 'remotion';
import {AiEdit} from './AiEdit';
import edit from './edit.json';
import {C, FONT, W, H} from './theme';

// Bố cục Before/After: khung Trước nhỏ, thấp, phía sau; khung Sau to, đè lên, bên phải.
const AFTER_Y = 470, AFTER_H = 967;
const BEFORE = {x: 104, y: Math.round(AFTER_Y + AFTER_H / 2 - 697 / 2), w: 392, h: 697};
const AFTER = {x: 432, y: AFTER_Y, w: 544, h: AFTER_H};
const SCRIPT = '"Dancing Script", cursive';

// Khung Trước: clip gốc thô, cắt theo cùng các đoạn giữ để luôn khớp lời với khung Sau
const RawCut: React.FC = () => {
  let acc = 0;
  return (
    <>
      {edit.segments.map(([a, b], i) => {
        const from = Math.round(acc * 30);
        acc += b - a;
        const dur = Math.round(acc * 30) - from;
        return (
          <Sequence key={i} from={from} durationInFrames={dur} premountFor={30}>
            <OffthreadVideo src={staticFile('source.mp4')} muted trimBefore={Math.round(a * 30)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          </Sequence>
        );
      })}
    </>
  );
};

const Label: React.FC<{text: string; dot: string; x: number; y: number; size: number; p: number}> = ({text, dot, x, y, size, p}) => (
  <div style={{position: 'absolute', left: x, top: y, transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 14, opacity: p}}>
    <span style={{width: 14, height: 14, borderRadius: 14, background: dot, boxShadow: `0 0 12px ${dot}`}} />
    <span style={{fontFamily: SCRIPT, fontWeight: 700, fontSize: size, color: '#141414', lineHeight: 1}}>{text}</span>
  </div>
);

const Card: React.FC<{box: typeof BEFORE; p: number; from: number; children: React.ReactNode; shadow: string}> = ({box, p, from, children, shadow}) => (
  <div style={{position: 'absolute', left: box.x, top: box.y, width: box.w, height: box.h, borderRadius: 34, overflow: 'hidden',
    border: '3px solid #1a1a1a', background: '#000', boxShadow: shadow,
    transform: `translateY(${(1 - p) * from}px)`, opacity: Math.min(1, p * 1.3)}}>
    {children}
  </div>
);

export const Compare: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pB = spring({frame: f - 2, fps, config: {damping: 16}});
  const pA = spring({frame: f - 8, fps, config: {damping: 16}});
  const pT = interpolate(f, [18, 32], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#FFFFFF', overflow: 'hidden'}}>
      {/* vòng cung xám mờ */}
      <div style={{position: 'absolute', width: 2300, height: 2300, borderRadius: '50%', left: -380, top: -1180,
        background: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,1) 62%, rgba(232,233,236,1) 66%, rgba(246,246,248,1) 72%, rgba(255,255,255,1) 80%)'}} />
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 520, background: 'linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(236,237,240,0.9) 100%)'}} />

      <Label text="Trước" dot="#E5484D" x={BEFORE.x + BEFORE.w / 2 - 20} y={BEFORE.y - 74} size={58} p={pB} />
      <Label text="Sau" dot="#7BD23B" x={AFTER.x + AFTER.w / 2} y={AFTER.y - 92} size={74} p={pA} />

      <Card box={BEFORE} p={pB} from={60} shadow="0 24px 50px rgba(0,0,0,0.16)"><RawCut /></Card>
      <Card box={AFTER} p={pA} from={90} shadow="-18px 30px 70px rgba(0,0,0,0.28)">
        <div style={{width: W, height: H, transform: `scale(${AFTER.w / W})`, transformOrigin: '0 0'}}><AiEdit /></div>
      </Card>

      <div style={{position: 'absolute', left: 0, right: 0, top: AFTER.y + AFTER.h + 74, textAlign: 'center', fontFamily: FONT, opacity: pT}}>
        <div style={{fontSize: 58, fontWeight: 900, color: '#1a1a1a', letterSpacing: -1}}>
          {(edit as any).content.compare.title} <span style={{color: C.blue}}>{(edit as any).content.compare.accent}</span>
        </div>
        <div style={{fontSize: 34, fontWeight: 500, color: '#3a3f4b', marginTop: 10}}>
          {(edit as any).content.compare.cta}
        </div>
      </div>
    </AbsoluteFill>
  );
};
