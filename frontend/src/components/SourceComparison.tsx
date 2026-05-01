"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { SourceData } from "@/lib/api";

interface Props {
  sourceComparison: Record<string, SourceData>;
}

const SOURCE_COLORS: Record<string, string> = {
  Amazon:     "#f5a623",
  BestBuy:    "#3fd68f",
  YouTube:    "#7c6af7",
  Reddit:     "#ff4500",
  Personal:   "#88aaff",
  "External Review Source": "#888888",
};

// Simple hash to generate a stable color for unknown sources
function stringToColor(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 70%, 65%)`;
}

function getColor(src: string) {
  return SOURCE_COLORS[src] ?? stringToColor(src);
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: "var(--bg-3)", border: "1px solid var(--border)",
      borderRadius: 8, padding: "0.7rem", fontSize: "0.83rem",
    }}>
      <div style={{ fontWeight: 600, marginBottom: "0.25rem" }}>{label}{d.estimated ? " (AI est.)" : ""}</div>
      <div>Sentiment: {d.avg_sentiment > 0 ? "+" : ""}{d.avg_sentiment.toFixed(2)}</div>
      <div style={{ color: "var(--text-muted)" }}>
        {d.estimated ? "Based on AI knowledge" : `${d.review_count} reviews`}
      </div>
    </div>
  );
}

export default function SourceComparison({ sourceComparison }: Props) {
  const data = Object.entries(sourceComparison).map(([source, d]) => ({
    source,
    avg_sentiment: d.avg_sentiment,
    review_count: d.review_count,
    estimated: d.estimated ?? false,
  }));

  return (
    <div className="card fade-up-3">
      <div className="card-header">Source Comparison</div>
      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "1.25rem", lineHeight: 1.4 }}>
        <strong>Why are these different?</strong> Different sites have different vibes. Amazon users might focus on shipping, while YouTube reviewers dive into pro-level features. This helps you see the "full picture" across the whole web.
      </p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <XAxis dataKey="source" tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[-1, 1]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Bar dataKey="avg_sentiment" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={getColor(entry.source)} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", marginTop: "0.75rem" }}>
        {data.map((d) => (
          <span
            key={d.source}
            style={{
              background: `${getColor(d.source)}22`,
              color: getColor(d.source),
              border: `1px solid ${getColor(d.source)}44`,
              borderRadius: 20,
              padding: "0.2rem 0.6rem",
              fontSize: "0.73rem",
              fontWeight: 500,
            }}
          >
            {d.source} ({d.review_count}){d.estimated ? " · AI est." : ""}
          </span>
        ))}
      </div>
    </div>
  );
}
