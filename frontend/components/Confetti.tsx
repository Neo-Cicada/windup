import type { CSSProperties } from "react";

export type ConfettiPiece = {
  id: string;
  left: number;
  color: string;
  dur: number;
  delay: number;
  size: number;
  round: string;
};

const COLORS = [
  "#EF5B54",
  "#4FB0E5",
  "#F7C948",
  "#6FBF73",
  "#8B6FD6",
  "#F49AC1",
];

export function makeBurst(n: number): ConfettiPiece[] {
  return Array.from({ length: n }, (_, i) => ({
    id: `${Date.now()}-${i}`,
    left: Math.random() * 100,
    color: COLORS[i % COLORS.length],
    dur: 1.1 + Math.random() * 0.9,
    delay: Math.random() * 0.25,
    size: 8 + Math.random() * 9,
    round: Math.random() < 0.5 ? "50%" : "3px",
  }));
}

export function Confetti({ pieces }: { pieces: ConfettiPiece[] }) {
  const layer: CSSProperties = {
    position: "fixed",
    inset: 0,
    pointerEvents: "none",
    zIndex: 9999,
    overflow: "hidden",
  };
  return (
    <div style={layer} aria-hidden>
      {pieces.map((p) => (
        <div
          key={p.id}
          style={{
            position: "absolute",
            top: "-30px",
            left: `${p.left}%`,
            width: `${p.size}px`,
            height: `${p.size}px`,
            background: p.color,
            borderRadius: p.round,
            border: "2px solid rgba(46,38,32,.55)",
            animation: `cfall ${p.dur}s cubic-bezier(.35,.1,.5,1) ${p.delay}s forwards`,
          }}
        />
      ))}
    </div>
  );
}
