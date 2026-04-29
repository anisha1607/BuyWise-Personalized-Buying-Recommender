"use client";
import type { Contradiction, Evidence } from "@/lib/api";

/* ─── ContradictionDetector ─── */
interface ContradictionProps {
  contradictions: Contradiction[];
}

export function ContradictionDetector({ contradictions }: ContradictionProps) {
  if (!contradictions.length) {
    return (
      <div className="card fade-up-4">
        <div className="card-header">
          <span style={{ color: "var(--amber)" }}>⚡</span> Mixed Reviews Detected
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "0.5rem 0" }}>
          Not enough review data or disagreement to determine mixed sentiment.
        </div>
      </div>
    );
  }
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
  const color = e.sentiment === "positive" ? "var(--green)" : e.sentiment === "negative" ? "var(--red)" : "var(--amber)";
  const srcName = e.source_name || e.source_url || "External Source";
  const typeLabel = e.source_type ? ` • ${e.source_type}` : "";
  
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
      <div style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--text)", marginBottom: "0.4rem" }}>
        {e.claim}
      </div>
      <p style={{ fontSize: "0.81rem", color: "var(--text-muted)", lineHeight: 1.5, marginBottom: "0.4rem", fontStyle: "italic" }}>
        &ldquo;{e.evidence_snippet}&rdquo;
      </p>
      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center", flexWrap: "wrap" }}>
        {e.source_url ? (
          <a 
            href={e.source_url} 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ fontSize: "0.7rem", color: "var(--text-muted)", textDecoration: "underline" }}
            title={srcName}
          >
            {srcName}{typeLabel} ↗
          </a>
        ) : (
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
            {srcName}{typeLabel}
          </span>
        )}
      </div>
    </div>
  );
}

export function EvidenceCards({ evidence }: EvidenceProps) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="card col-span-2 fade-up">
        <div className="card-header">Evidence</div>
        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "0.5rem 0" }}>
          No strong evidence found from available sources.
        </p>
      </div>
    );
  }

  const supportsPros = evidence.filter(e => e.supports === "pros");
  const supportsCons = evidence.filter(e => e.supports === "cons");
  const supportsVerdict = evidence.filter(e => e.supports === "verdict");
  const supportsVerification = evidence.filter(e => e.supports === "verification");

  return (
    <div className="card col-span-2 fade-up">
      <div className="card-header">Evidence</div>
      <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "1.25rem", lineHeight: 1.4 }}>
        Direct evidence mapping to the claims made in the summary and verdict.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div>
          <div style={{ color: "var(--green)", fontWeight: 600, fontSize: "0.83rem", marginBottom: "0.75rem" }}>
            ✓ Supports Pros
          </div>
          {supportsPros.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem", marginBottom: "1rem" }}>None found</p>
            : supportsPros.map((e, i) => <EvidenceCard key={i} e={e} />)}

          {(supportsVerdict.length > 0 || supportsVerification.length > 0) && (
             <div style={{ color: "var(--amber)", fontWeight: 600, fontSize: "0.83rem", marginBottom: "0.75rem", marginTop: "1rem" }}>
               ℹ️ Supports Verdict & Verification
             </div>
          )}
          {supportsVerdict.map((e, i) => <EvidenceCard key={`verdict-${i}`} e={e} />)}
          {supportsVerification.map((e, i) => <EvidenceCard key={`verif-${i}`} e={e} />)}
        </div>
        <div>
          <div style={{ color: "var(--red)", fontWeight: 600, fontSize: "0.83rem", marginBottom: "0.75rem" }}>
            ✗ Supports Cons
          </div>
          {supportsCons.length === 0
            ? <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>None found</p>
            : supportsCons.map((e, i) => <EvidenceCard key={i} e={e} />)}
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
          {pros.length === 0 ? (
            <p style={{
              color: "var(--text-muted)", fontSize: "0.81rem",
              background: "rgba(16,185,129,0.06)", borderRadius: 8,
              padding: "0.6rem 0.8rem", border: "1px dashed rgba(16,185,129,0.2)"
            }}>
              None identified.
            </p>
          ) : (
            pros.map((p, i) => (
              <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.45rem", fontSize: "0.83rem" }}>
                <span style={{ color: "var(--green)", flexShrink: 0 }}>✓</span>
                <span>{p}</span>
              </div>
            ))
          )}
        </div>
        <div>
          <div style={{ color: "var(--red)", fontWeight: 600, marginBottom: "0.7rem", fontSize: "0.88rem" }}>Cons</div>
          {cons.length === 0 ? (
            <p style={{
              color: "var(--text-muted)", fontSize: "0.81rem",
              background: "rgba(239,68,68,0.06)", borderRadius: 8,
              padding: "0.6rem 0.8rem", border: "1px dashed rgba(239,68,68,0.2)"
            }}>
              None identified.
            </p>
          ) : (
            cons.map((c, i) => (
              <div key={i} style={{ display: "flex", gap: "0.5rem", marginBottom: "0.45rem", fontSize: "0.83rem" }}>
                <span style={{ color: "var(--red)", flexShrink: 0 }}>✗</span>
                <span>{c}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
