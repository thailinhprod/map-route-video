import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import {C, FONT} from './theme';

// Văn bản có *từ nhấn* → span xanh
export const Rich: React.FC<{text: string; hl?: string}> = ({text, hl = C.blue}) => {
  const parts = text.split('*');
  return (
    <>
      {parts.map((p, i) => (i % 2 === 1 ? <span key={i} style={{color: hl}}>{p}</span> : <span key={i}>{p}</span>))}
    </>
  );
};

export const usePop = (startFrame: number, damping = 14) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - startFrame, fps, config: {damping, mass: 0.6, stiffness: 180}});
};

export const fadeWindow = (f: number, a: number, b: number, inF = 6, outF = 6) =>
  b - a < inF + outF + 1 ? 0 : interpolate(f, [a, a + inF, b - outF, b], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

export const ease = Easing.bezier(0.45, 0, 0.2, 1);

export const Chip: React.FC<{children: React.ReactNode; style?: React.CSSProperties; dark?: boolean}> = ({children, style, dark}) => (
  <div style={{
    display: 'inline-flex', alignItems: 'center', gap: 12, padding: '14px 26px', borderRadius: 999,
    background: dark ? C.ink : C.white, color: dark ? C.white : C.ink, fontFamily: FONT, fontWeight: 800,
    fontSize: 30, letterSpacing: 1.5, boxShadow: '0 14px 40px rgba(11,15,25,0.28)', ...style,
  }}>{children}</div>
);

export const Dot: React.FC<{color?: string; size?: number}> = ({color = C.blue, size = 14}) => (
  <span style={{width: size, height: size, borderRadius: size, background: color, display: 'inline-block'}} />
);
