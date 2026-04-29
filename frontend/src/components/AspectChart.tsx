"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { AspectData } from "@/lib/api";

interface Props {
  aspectSummary: Record<string, AspectData>;
}

function barColor(s: number) {
  if (s > 0.1)  return "var(--green)";
  if (s < -0.05) return "var(--red)";
  return "var(--amber)";
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: "var(--bg-3)", border: "1px solid var(--border)",
      borderRadius: 8, padding: "0.7rem", fontSize: "0.83rem",
    }}>
      <div style={{ fontWeight: 600, marginBottom: "0.25rem", textTransform: "capitalize" }}>{label}</div>
      <div style={{ color: barColor(d.avg_sentiment) }}>
        Sentiment: {d.avg_sentiment > 0 ? "+" : ""}{d.avg_sentiment.toFixed(2)}
      </div>
      <div style={{ color: "var(--text-muted)" }}>{d.mention_count} mentions</div>
    </div>
  );
}

export default function AspectChart({ aspectSummary }: Props) {
  const data = Object.entries(aspectSummary)
    .filter(([, v]) => v.mention_count > 0)
    .map(([aspect, v]) => ({
      aspect: aspect[0].toUpperCase() + aspect.slice(1),
      avg_sentiment: v.avg_sentiment,
      mention_count: v.mention_count,
    }))
    .sort((a, b) => b.avg_sentiment - a.avg_sentiment);

  return (
    <div className="card fade-up-1">
      <div className="card-header">Aspect Sentiment</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <XAxis dataKey="aspect" tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis domain={[-1, 1]} tick={{ fill: "var(--text-muted)", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Bar dataKey="avg_sentiment" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={barColor(entry.avg_sentiment)} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
