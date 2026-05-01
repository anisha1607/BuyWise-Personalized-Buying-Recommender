"use client";
import { useEffect, useRef } from "react";
import type { PrefVsReality } from "@/lib/api";

interface Props {
  data: PrefVsReality[];
}

function labelColor(label: string) {
    if (label === "positive") return "var(--green)";
    if (label === "negative") return "var(--red)";
    if (label === "no data") return "var(--text-muted)";
    return "var(--amber)";
}

function Bar({ row, delay }: { row: PrefVsReality; delay: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      if (ref.current) ref.current.style.width = `${row.reality_score}%`;
    }, delay + 200);
    return () => clearTimeout(t);
  }, [row.reality_score, delay]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.3rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span className={`dot-${row.priority}`} />
          <span style={{ fontSize: "0.85rem", textTransform: "capitalize" }}>{row.aspect}</span>
          <span style={{ fontSize: "0.73rem", color: "var(--text-muted)" }}>({row.mention_count})</span>
        </div>
        <span style={{ fontSize: "0.77rem", color: labelColor(row.reality_label), fontWeight: 500 }}>
          {row.reality_label}
        </span>
      </div>
      <div style={{ background: "var(--bg-3)", borderRadius: 4, height: 6, overflow: "hidden" }}>
        <div
          ref={ref}
          style={{
            height: "100%",
            width: "0%",
            background: labelColor(row.reality_label),
            borderRadius: 4,
            transition: "width 0.8s cubic-bezier(0.4,0,0.2,1)",
          }}
        />
      </div>
    </div>
  );
}

export default function PreferenceVsReality({ data }: Props) {
  return (
    <div className="card fade-up-2">
      <div className="card-header">Preference vs Reality</div>
      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "1rem", lineHeight: 1.4 }}>
        This chart compares what <strong>you</strong> care about with what <strong>actual users</strong> are saying. 
        Longer bars mean the product meets or exceeds your expectations for that feature.
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.9rem" }}>
        {data.map((row, i) => (
          <Bar key={row.aspect} row={row} delay={i * 60} />
        ))}
      </div>
    </div>
  );
}
