"use client";
import { useEffect, useRef, type ReactNode } from "react";

const RADIUS = 70;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function scoreColor(score: number) {
  if (score >= 70) return "var(--green)";
  if (score >= 45) return "var(--amber)";
  return "var(--red)";
}

interface Props {
  score: number;
  verdict: ReactNode;
  hypothesis: ReactNode;
  dealBreakerFlags: string[];
}

export default function FitScore({ score, verdict, hypothesis, dealBreakerFlags }: Props) {
  const circleRef = useRef<SVGCircleElement>(null);
  const color = scoreColor(score);
  const targetOffset = CIRCUMFERENCE * (1 - score / 100);

  useEffect(() => {
    const el = circleRef.current;
    if (!el) return;
    el.style.strokeDashoffset = String(CIRCUMFERENCE);
    const t = setTimeout(() => {
      el.style.transition = "stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)";
      el.style.strokeDashoffset = String(targetOffset);
    }, 120);
    return () => clearTimeout(t);
  }, [targetOffset]);

  const label = score >= 70 ? "Great Fit" : score >= 45 ? "Decent Fit" : "Poor Fit";

  return (
    <div
      className="card col-span-2 fade-up"
      style={{ display: "flex", gap: "2.5rem", alignItems: "center", flexWrap: "wrap" }}
    >
      {/* Animated ring */}
      <div style={{ flexShrink: 0, position: "relative", width: 180, height: 180 }}>
        <svg width={180} height={180} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={90} cy={90} r={RADIUS} fill="none" stroke="var(--bg-3)" strokeWidth={14} />
          <circle
            ref={circleRef}
            cx={90} cy={90} r={RADIUS}
            fill="none"
            stroke={color}
            strokeWidth={14}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE}
          />
        </svg>
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        }}>
          <span style={{ fontSize: "2.4rem", fontWeight: 700, color, fontFamily: "var(--font-mono)", lineHeight: 1 }}>
            {Math.round(score)}
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>/ 100</span>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color, marginTop: "0.2rem" }}>{label}</span>
        </div>
      </div>

      {/* Text content */}
      <div style={{ flex: 1, minWidth: 220 }}>
        <h2 style={{ fontFamily: "var(--font-serif)", fontSize: "1.4rem", marginBottom: "0.75rem" }}>
          Fit Analysis
        </h2>
        {verdict && (
          <p style={{ color: "var(--text)", lineHeight: 1.7, marginBottom: "0.65rem" }}>{verdict}</p>
        )}
        {hypothesis && (
          <p style={{ color: "var(--text-muted)", fontSize: "0.88rem", fontStyle: "italic", lineHeight: 1.6 }}>
            {hypothesis}
          </p>
        )}
        {dealBreakerFlags.length > 0 && (
          <div style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {dealBreakerFlags.map((flag, i) => (
              <div
                key={i}
                style={{
                  background: "rgba(247,106,106,.1)",
                  border: "1px solid rgba(247,106,106,.3)",
                  borderRadius: 8,
                  padding: "0.45rem 0.75rem",
                  color: "var(--red)",
                  fontSize: "0.83rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>⚠</span> {flag}
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
