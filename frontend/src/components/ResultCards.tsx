"use client";
import type { Contradiction, Evidence } from "@/lib/api";

/* ─── ContradictionDetector ─── */
interface ContradictionProps {
  contradictions: Contradiction[];
}

export function ContradictionDetector({ contradictions }: ContradictionProps) {
  if (!contradictions.length) return null;
  return (
    <div className="card fade-up-4">
      <div className="card-header">
        <span style={{ color: "var(--amber)" }}>⚡</span> Mixed Reviews Detected
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {contradictions.map((c, i) => (
          <div
            key={i}
            style={{
              background: "rgba(245,166,35,.08)",
              border: "1px solid rgba(245,166,35,.25)",
              borderRadius: 8,
              padding: "0.7rem 0.85rem",
            }}
          >
            <div style={{ fontWeight: 600, color: "var(--amber)", fontSize: "0.88rem", marginBottom: "0.4rem" }}>
              {c.message}
            </div>
            {c.positive_samples[0] && (
              <div style={{ fontSize: "0.81rem", color: "var(--green)", marginBottom: "0.2rem" }}>
                + {c.positive_samples[0]}
              </div>
            )}
            {c.negative_samples[0] && (
              <div style={{ fontSize: "0.81rem", color: "var(--red)" }}>
                − {c.negative_samples[0]}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── EvidenceCards ─── */
interface EvidenceProps {
  evidence: Evidence[];
}

function EvidenceCard({ e }: { e: Evidence }) {
  const color = e.sentiment === "positive" ? "var(--green)" : "var(--red)";
  return (
    <div
      style={{
        background: "var(--bg-3)",
        borderRadius: 8,
        padding: "0.6rem 0.75rem",
        marginBottom: "0.45rem",
        borderLeft: `3px solid ${color}`,
      }}
    >
      <p style={{ fontSize: "0.81rem", color: "var(--text)", lineHeight: 1.5, marginBottom: "0.3rem" }}>
        &ldquo;{e.text}&rdquo;
      </p>
      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
        <span className="tag-accent" style={{ fontSize: "0.69rem" }}>{e.aspect}</span>
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{e.source}</span>
      </div>
    </div>
  );
}

export function EvidenceCards({ evidence }: EvidenceProps) {
  const positive = evidence.filter(e => e.sentiment === "positive").slice(0, 6);
  const negative = evidence.filter(e => e.sentiment === "negative").slice(0, 6);

  return (
    <div className="card col-span-2 fade-up">
      <div className="card-header">Evidence</div>
      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "1.25rem", lineHeight: 1.4 }}>
        These are direct quotes from real people. We use these to double-check our AI's findings and make sure the sentiment is accurate.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div>
          <div style={{ color: "var(--green)", fontWeight: 600, fontSize: "0.83rem", marginBottom: "0.75rem" }}>
            ✓ Positive
          </div>
          {positive.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>None found</p>
            : positive.map((e, i) => <EvidenceCard key={i} e={e} />)}
        </div>
        <div>
          <div style={{ color: "var(--red)", fontWeight: 600, fontSize: "0.83rem", marginBottom: "0.75rem" }}>
            ✗ Negative
          </div>
          {negative.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>None found</p>
            : negative.map((e, i) => <EvidenceCard key={i} e={e} />)}
        </div>
      </div>
    </div>
  );
}

/* ─── ProsConsCard ─── */
interface ProsConsProps {
  pros: string[];
  cons: string[];
}

export function ProsConsCard({ pros, cons }: ProsConsProps) {
  return (
    <div className="card col-span-2 fade-up">
      <div className="card-header">Summary</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <div>
          <div style={{ color: "var(--green)", fontWeight: 600, marginBottom: "0.7rem", fontSize: "0.88rem" }}>Pros</div>
          {pros.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>None found</p>
            : pros.map((p, i) => (
              <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.45rem", fontSize: "0.83rem" }}>
                <span style={{ color: "var(--green)", flexShrink: 0 }}>✓</span>
                <span>{p}</span>
              </div>
            ))}
        </div>
        <div>
          <div style={{ color: "var(--red)", fontWeight: 600, marginBottom: "0.7rem", fontSize: "0.88rem" }}>Cons</div>
          {cons.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>None found</p>
            : cons.map((c, i) => (
              <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.45rem", fontSize: "0.83rem" }}>
                <span style={{ color: "var(--red)", flexShrink: 0 }}>✗</span>
                <span>{c}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
