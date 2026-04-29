"use client";
import { useState, useEffect } from "react";
import type { AnalyzeRequest, AnalyzeResponse, Preferences } from "@/lib/api";
import { analyzeProduct, askChat } from "@/lib/api";
import FitScore from "@/components/FitScore";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

function AspectChart({ aspectSummary }: { aspectSummary: Record<string, any> }) {
  const data = Object.entries(aspectSummary).map(([name, d]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    sentiment: d.avg_sentiment,
  })).sort((a, b) => b.sentiment - a.sentiment);

  return (
    <div className="card" style={{ height: 400 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <SectionLabel title="Sentiment by Feature" />
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", maxWidth: "350px", textAlign: "right", lineHeight: "1.4" }}>
          <strong>How to read this:</strong> Each bar represents a product feature. 
          <span style={{ color: "#10b981" }}> Green</span> bars mean positive feedback, while 
          <span style={{ color: "#ef4444" }}> Red</span> bars highlight common complaints. 
          The taller the bar, the more certain the sentiment.
        </div>
      </div>
      <div style={{ height: "300px", marginTop: "1rem" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ bottom: 40 }}>
            <XAxis 
              dataKey="name" 
              tick={{ fill: "var(--text-muted)", fontSize: 11 }} 
              interval={0}
              angle={-45}
              textAnchor="end"
            />
            <YAxis hide domain={[-1, 1]} />
            <Tooltip 
              cursor={{ fill: "var(--bg-3)" }}
              contentStyle={{ background: "var(--bg-2)", border: "1px solid var(--bg-3)", borderRadius: "8px" }}
            />
            <Bar dataKey="sentiment" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.sentiment > 0 ? "#10b981" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ScoreBreakdown({ result }: { result: AnalyzeResponse }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <button 
        onClick={() => setOpen(!open)}
        style={{ width: "100%", background: "none", border: "none", color: "var(--text)", textAlign: "left", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
      >
        <SectionLabel title="How is my Fit Score calculated?" />
        <span>{open ? "▲" : "▼"}</span>
      </button>
      
      {open && (
        <div style={{ marginTop: "1rem", fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
          <p>Your <strong>{result.fit_score}/100</strong> score isn't just an average. Here's the math in plain English:</p>
          <ul style={{ marginTop: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <li><strong>⚖️ Weighted Priorities:</strong> Aspects you marked as "High Priority" (like {result.pros[0] || 'Battery'}) affect the score 3x more than "Low Priority" items.</li>
            <li><strong>📉 Sentiment Analysis:</strong> We scan thousands of words to find hidden emotions. If 80% of users are happy with the {result.pros[1] || 'Design'}, that aspect gets a high rating.</li>
            <li><strong>🚫 Deal Breakers:</strong> If you set a deal breaker and the product fails it, the score is heavily penalized.</li>
          </ul>
        </div>
      )}
    </div>
  );
}
import PreferenceVsReality from "@/components/PreferenceVsReality";
import SourceComparison from "@/components/SourceComparison";
import { ContradictionDetector, EvidenceCards, ProsConsCard } from "@/components/ResultCards";

const ASPECTS = ["comfort", "price", "battery", "sound", "durability", "performance", "design", "connectivity"];
const USE_CASES = ["travel", "work", "gaming", "music", "everyday", "sports"];
const SUGGESTIONS = ["Sony WH-1000XM5", "Bose QuietComfort 45", "Apple MacBook Pro 14", "Anker Soundcore Q45"];
const SOURCES = ["Amazon", "BestBuy", "YouTube", "Personal"];

/* ─── Helpers ─── */
async function exportData(result: any, format: "json" | "csv") {
  const filename = `BuyWise_${result.product.replace(/\s+/g, '_')}`;
  let blob: Blob;
  
  if (format === "json") {
    blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  } else {
    const headers = "Aspect,Score,Sentiment,Meaning,Calculation\n";
    const rows = Object.entries(result.aspect_summary).map(([a, d]: [string, any]) => {
      // Map -1..1 sentiment to 0..100 score
      const score = ((d.avg_sentiment + 1) * 50).toFixed(1);
      const sentiment = d.avg_sentiment > 0.1 ? 'Positive' : d.avg_sentiment < -0.1 ? 'Negative' : 'Neutral';
      
      let meaning = "Average / Mixed";
      if (Number(score) > 85) meaning = "Exceptional / Elite";
      else if (Number(score) > 65) meaning = "Good / Solid";
      else if (Number(score) < 40) meaning = "Poor / Subpar";

      const calculation = `Sentiment of ${d.mention_count} mentions mapped to a 0-100 scale (50 is Neutral).`;
      
      return `${a},${score},${sentiment},"${meaning}","${calculation}"`;
    }).join("\n");
    blob = new Blob([headers + rows], { type: "text/csv" });
  }

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

const SectionLabel = ({ title }: { title: string }) => (
  <div style={{
    color: "var(--text-muted)", fontSize: "0.74rem", fontWeight: 600,
    textTransform: "uppercase", letterSpacing: "0.08em",
    marginBottom: "0.65rem", marginTop: "1.4rem",
  }}>
    {title}
  </div>
);

const DEFAULT_PREFS: Preferences = {
  budget: "mid",
  use_case: "everyday",
  aspect_priorities: Object.fromEntries(ASPECTS.map(a => [a, "medium"])) as Record<string, "high" | "medium" | "low">,
  deal_breakers: [],
};

/* ─── Step 1: Search ─── */
function SearchStep({ onNext }: { onNext: (p: string) => void }) {
  const [input, setInput] = useState("");
  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "4rem 1.5rem", textAlign: "center" }}>
      <div className="fade-up-1">
        <h1 style={{ fontFamily: "var(--font-serif)", fontSize: "3rem", lineHeight: 1.1, marginBottom: "0.75rem" }}>
          Buy<span style={{ color: "var(--accent)" }}>Wise</span>
        </h1>
        <p style={{ color: "var(--text-muted)", marginBottom: "2.5rem" }}>
          Turn product reviews into a personalized buying dashboard.
        </p>
      </div>
      <div className="fade-up-2" style={{ display: "flex", gap: "0.75rem", marginBottom: "1rem" }}>
        <input
          className="input-field"
          placeholder="Search a product (e.g. Sony WH-1000XM5)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && input.trim() && onNext(input.trim())}
        />
        <button
          className="btn-primary"
          disabled={!input.trim()}
          onClick={() => onNext(input.trim())}
          style={{ whiteSpace: "nowrap" }}
        >
          Analyze →
        </button>
      </div>
      <div className="fade-up-3" style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
        {SUGGESTIONS.map(s => (
          <button key={s} className="btn-ghost" style={{ fontSize: "0.8rem", padding: "0.38rem 0.8rem" }} onClick={() => onNext(s)}>
            {s}
          </button>
        ))}
      </div>
      <div style={{ marginTop: "1.75rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}>
        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Sources
        </span>
        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap", justifyContent: "center" }}>
          {SOURCES.map(s => (
            <span
              key={s}
              style={{
                background: "var(--bg-3)",
                border: "1px solid var(--border)",
                borderRadius: 20,
                padding: "0.18rem 0.6rem",
                fontSize: "0.73rem",
                color: "var(--text-muted)",
              }}
            >
              {s}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Step 2: Preferences Wizard ─── */
function PreferencesStep({
  product,
  onBack,
  onAnalyze,
  error,
}: {
  product: string;
  onBack: () => void;
  onAnalyze: (prefs: Preferences, pasted: string, ytIds: string[]) => void;
  error: string | null;
}) {
  const [prefs, setPrefs] = useState<Preferences>(DEFAULT_PREFS);
  const [pasted, setPasted] = useState("");

  const setPriority = (a: string, v: "high" | "medium" | "low") =>
    setPrefs(p => ({ ...p, aspect_priorities: { ...p.aspect_priorities, [a]: v } }));

  const toggleDB = (a: string) =>
    setPrefs(p => ({
      ...p,
      deal_breakers: p.deal_breakers.includes(a)
        ? p.deal_breakers.filter(x => x !== a)
        : [...p.deal_breakers, a],
    }));

  const handleSubmit = () => {
    onAnalyze(prefs, pasted);
  };


  return (
    <div style={{ maxWidth: 680, margin: "0 auto", padding: "2.5rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.75rem" }}>
        <button className="btn-ghost" onClick={onBack} style={{ fontSize: "0.83rem", padding: "0.38rem 0.75rem" }}>
          ← Back
        </button>
        <div>
          <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Analyzing</div>
          <div style={{ fontFamily: "var(--font-serif)", fontSize: "1.2rem" }}>{product}</div>
        </div>
      </div>

      {error && (
        <div style={{
          background: "rgba(247,106,106,.1)", border: "1px solid rgba(247,106,106,.3)",
          borderRadius: 8, padding: "0.65rem 0.9rem", color: "var(--red)",
          fontSize: "0.85rem", marginBottom: "1rem",
        }}>
          {error}
        </div>
      )}

      <div className="card fade-up">
        <SectionLabel title="Budget" />
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {(["low", "mid", "high"] as const).map(b => (
            <button key={b} className={`toggle-btn${prefs.budget === b ? " active" : ""}`} onClick={() => setPrefs(p => ({ ...p, budget: b }))}>
              {b === "low" ? "Budget" : b === "mid" ? "Mid-range" : "Premium"}
            </button>
          ))}
        </div>

        <SectionLabel title="Use Case" />
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {USE_CASES.map(u => (
            <button key={u} className={`toggle-btn${prefs.use_case === u ? " active" : ""}`} onClick={() => setPrefs(p => ({ ...p, use_case: u }))}>
              {u[0].toUpperCase() + u.slice(1)}
            </button>
          ))}
        </div>

        <SectionLabel title="Aspect Priorities" />
        <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
          {ASPECTS.map(a => (
            <div key={a} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "0.88rem", textTransform: "capitalize", minWidth: 110 }}>{a}</span>
              <div style={{ display: "flex", gap: "0.35rem" }}>
                {(["high", "medium", "low"] as const).map(lv => (
                  <button
                    key={lv}
                    className={`toggle-btn${prefs.aspect_priorities[a] === lv ? " active" : ""}`}
                    style={{ fontSize: "0.77rem", padding: "0.28rem 0.65rem" }}
                    onClick={() => setPriority(a, lv)}
                  >
                    {lv[0].toUpperCase() + lv.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>

        <SectionLabel title="Deal Breakers" />
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {ASPECTS.map(a => (
            <button
              key={a}
              className={`toggle-btn${prefs.deal_breakers.includes(a) ? " active" : ""}`}
              style={{ fontSize: "0.8rem" }}
              onClick={() => toggleDB(a)}
            >
              {a[0].toUpperCase() + a.slice(1)}
            </button>
          ))}
        </div>

        <SectionLabel title="Personal Recommendations" />
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
          Did a friend or family member give you their take? Paste it here to include it in the math.
        </p>
        <textarea
          className="input-field"
          rows={4}
          placeholder="e.g. My brother says the battery is okay but the screen is amazing..."
          value={pasted}
          onChange={e => setPasted(e.target.value)}
          style={{ resize: "vertical" }}
        />


        <div style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
          <button className="btn-primary" onClick={handleSubmit}>Generate Dashboard →</button>
        </div>
      </div>
    </div>
  );
}

/* ─── Dashboard Components ─── */


function MarketInsights({ intel }: { intel: MarketIntelligence }) {
  if (!intel) return (
    <div className="card" style={{ marginBottom: "2rem", color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", padding: "2rem" }}>
      ⚡ Gathering market intelligence...
    </div>
  );

  const trendIcons = {
    improving: "📈 Improving",
    stable: "⚖️ Stable",
    declining: "📉 Declining",
  };

  const badgeColors = {
    "Great Value": "#10b981",
    "Fair Price": "#3b82f6",
    "Premium": "#8b5cf6",
    "Overpriced": "#ef4444",
  };

  return (
    <div className="card" style={{ marginBottom: "2rem" }}>
      <SectionLabel title="Market Intelligence" />
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        <div style={{ background: "var(--bg-3)", padding: "1rem", borderRadius: "12px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>Value Assessment</div>
          <div style={{ 
            display: "inline-block", padding: "0.25rem 0.75rem", borderRadius: "20px", 
            background: badgeColors[intel.value_badge], color: "#fff", fontSize: "0.85rem", fontWeight: 700 
          }}>
            {intel.value_badge}
          </div>
        </div>
        <div style={{ background: "var(--bg-3)", padding: "1rem", borderRadius: "12px" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>Sentiment Trend</div>
          <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>{trendIcons[intel.sentiment_trend]}</div>
        </div>
      </div>

      <div style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>Release Status</div>
        <div style={{ fontSize: "0.95rem", padding: "0.75rem", borderLeft: "4px solid var(--accent)", background: "var(--bg-3)" }}>
          🚀 {intel.release_status}
        </div>
      </div>

      <div>
        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>Top Alternatives</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {intel.competitors.map((c, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem", border: "1px solid var(--border)", borderRadius: "8px" }}>
              <div>
                <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>{c.name}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{c.why}</div>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--accent)", fontWeight: 600 }}>{c.price_diff}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AskBuyWise({
  product, summary, pros, cons, verdict, evidence
}: {
  product: string;
  summary: any;
  pros: string[];
  cons: string[];
  verdict: string;
  evidence: any[];
}) {
  const [query, setQuery] = useState("");
  const [chat, setChat] = useState<{ role: "user" | "ai"; text: string; source?: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!query.trim() || loading) return;
    const userMsg = query;
    setQuery("");
    setChat(prev => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    // Trim summary to top 3 snippets per aspect to reduce payload size
    const trimmedSummary: Record<string, any> = {};
    if (summary && typeof summary === "object") {
      for (const [aspect, data] of Object.entries(summary as Record<string, any>)) {
        trimmedSummary[aspect] = {
          ...data,
          snippets: (data.snippets || []).slice(0, 3),
        };
      }
    }

    try {
      const ans = await askChat(product, userMsg, trimmedSummary, {
        pros,
        cons,
        verdict,
        evidence: (evidence || []).slice(0, 12),
      });
      setChat(prev => [...prev, { role: "ai", text: ans }]);
    } catch {
      setChat(prev => [...prev, {
        role: "ai",
        text: "⚠️ Couldn't reach BuyWise AI right now. Check your GROQ_API_KEY in the backend .env file."
      }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestedQuestions = [
    "What are the main pros?",
    "What are the main cons?",
    "How is the battery life?",
    "Is the sound quality good?",
  ];

  return (
    <div className="card" style={{ position: "sticky", top: "2rem" }}>
      <SectionLabel title="Ask BuyWise AI" />
      <div style={{ height: "320px", overflowY: "auto", marginBottom: "1rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {chat.length === 0 && (
          <div style={{ padding: "0.5rem 0" }}>
            <p style={{ color: "var(--text-muted)", fontSize: "0.78rem", marginBottom: "0.6rem" }}>Try asking:</p>
            {suggestedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => { setQuery(q); }}
                style={{
                  display: "block", width: "100%", textAlign: "left",
                  background: "var(--bg-3)", border: "1px solid var(--border)",
                  borderRadius: 8, padding: "0.45rem 0.7rem", marginBottom: "0.35rem",
                  color: "var(--text-muted)", fontSize: "0.8rem", cursor: "pointer",
                }}
              >
                {q}
              </button>
            ))}
          </div>
        )}
        {chat.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === "user" ? "flex-end" : "flex-start",
            background: m.role === "user" ? "var(--accent)" : "var(--bg-3)",
            color: m.role === "user" ? "#000" : "var(--text)",
            padding: "0.75rem", borderRadius: "12px", maxWidth: "90%", fontSize: "0.83rem",
            lineHeight: 1.5, whiteSpace: "pre-wrap",
          }}>
            {m.text}
          </div>
        ))}
        {loading && (
          <div style={{
            display: "flex", alignItems: "center", gap: "0.5rem",
            color: "var(--text-muted)", fontSize: "0.78rem",
          }}>
            <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>⟳</span>
            Thinking...
          </div>
        )}
      </div>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <input
          className="input-field"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask about battery, sound, comfort..."
          onKeyDown={e => e.key === "Enter" && handleAsk()}
          disabled={loading}
        />
        <button
          className="btn-primary"
          onClick={handleAsk}
          disabled={loading || !query.trim()}
          style={{ padding: "0.5rem 1rem", opacity: loading ? 0.6 : 1 }}
        >↑</button>
      </div>
    </div>
  );
}

/* ─── Step 3: Loading ─── */
function LoadingStep({ product }: { product: string }) {
  const [msgIdx, setMsgIdx] = useState(0);

  const messages = [
    "Searching YouTube for the latest reviews...",
    "Downloading video transcripts...",
    "Analyzing Amazon and BestBuy data...",
    "Cleaning and normalizing review data...",
    "Running VADER sentiment analysis...",
    "Calculating your personalized Fit Score...",
    "Generating AI hypothesis and verdict...",
    "Building your interactive dashboard...",
  ];

  useEffect(() => {
    const msgTimer = setInterval(() => setMsgIdx(i => (i + 1) % messages.length), 3500);
    return () => clearInterval(msgTimer);
  }, [messages.length]);

  return (
    <div style={{ textAlign: "center", padding: "6rem 1.5rem" }}>
      <div style={{
        width: 64, height: 64,
        border: "4px solid var(--bg-3)",
        borderTop: "4px solid var(--accent)",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
        margin: "0 auto 2rem",
        boxShadow: "0 0 20px rgba(var(--accent-rgb), 0.2)",
      }} />
      
      <h2 style={{ fontFamily: "var(--font-serif)", fontSize: "1.8rem", marginBottom: "0.75rem" }}>
        Analyzing {product}
      </h2>
      
      <div style={{ height: "1.5rem" }}>
        <p className="fade-in-out" style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
          {messages[msgIdx]}
        </p>
      </div>

      <style jsx>{`
        .fade-in-out {
          animation: fadeInOut 3.5s infinite;
        }
        @keyframes fadeInOut {
          0%, 100% { opacity: 0; transform: translateY(5px); }
          15%, 85% { opacity: 1; transform: translateY(0); }
        }
        .hover-scale {
          transition: transform 0.2s ease;
        }
        .hover-scale:hover {
          transform: scale(1.05);
        }
      `}</style>
    </div>
  );
}

/* ─── Step 4: Dashboard ─── */
function DashboardStep({ result, onReset }: { result: AnalyzeResponse; onReset: () => void }) {
  const [activeTab, setActiveTab] = useState<"verdict" | "sentiment" | "trust" | "evidence">("verdict");
  const [exporting, setExporting] = useState(false);

  const handleExport = async (fmt: "json" | "csv") => {
    setExporting(true);
    try { await exportData(result, fmt); } finally { setExporting(false); }
  };

  const TabButton = ({ id, label, icon }: { id: typeof activeTab | "catch", label: string, icon: string }) => (
    <button 
      onClick={() => setActiveTab(id as any)}
      style={{
        padding: "0.75rem 1.5rem",
        background: activeTab === id ? "var(--bg-2)" : "transparent",
        color: activeTab === id ? "var(--accent)" : "var(--text-muted)",
        border: "none",
        borderBottom: activeTab === id ? "2px solid var(--accent)" : "2px solid transparent",
        cursor: "pointer",
        fontSize: "0.9rem",
        fontWeight: 600,
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        transition: "all 0.2s"
      }}
    >
      <span>{icon}</span> {label}
    </button>
  );

  // Helper to render bold text from AI
  const formatText = (text: string) => {
    return text.split("**").map((part, i) => 
      i % 2 === 1 ? <strong key={i} style={{ color: "var(--accent)" }}>{part}</strong> : part
    );
  };

  return (
    <div style={{ padding: "2rem 1.5rem", maxWidth: 1100, margin: "0 auto" }}>
      {/* Header omitted for brevity */}
      <div style={{
        display: "flex", alignItems: "flex-start", justifyContent: "space-between",
        marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem",
      }}>
        <div>
          <button className="btn-ghost" onClick={onReset} style={{ fontSize: "0.78rem", padding: "0.32rem 0.7rem", marginBottom: "0.5rem" }}>
            ← New Search
          </button>
          <h1 style={{ fontFamily: "var(--font-serif)", fontSize: "1.8rem" }}>{result.product}</h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.83rem" }}>{result.review_count} reviews analyzed</p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button className="btn-ghost" style={{ fontSize: "0.8rem" }} onClick={() => handleExport("json")}>Export JSON</button>
          <button className="btn-ghost" style={{ fontSize: "0.8rem" }} onClick={() => handleExport("csv")}>Export CSV</button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{ display: "flex", borderBottom: "1px solid var(--border)", marginBottom: "2rem", overflowX: "auto" }}>
        <TabButton id="verdict" label="The Verdict" icon="🎯" />
        <TabButton id="sentiment" label="Sentiment" icon="📊" />
        <TabButton id="catch" label="The Catch" icon="⚖️" />
        <TabButton id="trust" label="Verification" icon="⚖️" />
        <TabButton id="evidence" label="Evidence" icon="💬" />
      </div>

      {/* Tab Content */}
      {activeTab === "verdict" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "2rem", animation: "fadeIn 0.3s ease" }}>
          <div className="fade-up">
            <FitScore
              score={result.fit_score}
              verdict={formatText(result.verdict)}
              hypothesis={formatText(result.hypothesis)}
              dealBreakerFlags={result.deal_breaker_flags}
            />
            <ScoreBreakdown result={result} />
            <ProsConsCard pros={result.pros} cons={result.cons} />
          </div>
          <div className="fade-up">
            <AskBuyWise
              product={result.product}
              summary={result.aspect_summary}
              pros={result.pros}
              cons={result.cons}
              verdict={result.verdict}
              evidence={result.evidence}
            />
          </div>
        </div>
      )}

      {activeTab === "sentiment" && (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
          <div style={{ marginBottom: "2rem" }}>
            <AspectChart aspectSummary={result.aspect_summary} />
          </div>
          <PreferenceVsReality data={result.preference_vs_reality} />
        </div>
      )}

      {activeTab === "catch" && (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
          <div className="card" style={{ borderLeft: "4px solid var(--amber)", marginBottom: "2rem" }}>
            <SectionLabel title="The Critical Take" />
            <p style={{ fontSize: "0.95rem", color: "var(--text)", lineHeight: 1.6, marginBottom: "1.5rem" }}>
              {result.critical_take || "Our critical agent is scanning for hidden catch... everything looks stable so far."}
            </p>
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }}>
              {result.trade_offs.map((t, i) => (
                <div key={i} style={{ background: "var(--bg-3)", padding: "1.25rem", borderRadius: "12px", border: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--accent)", marginBottom: "0.5rem", textTransform: "uppercase" }}>
                    {t.label}
                  </div>
                  <div style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.4 }}>
                    {t.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === "trust" && (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
          <div className="dashboard-grid">
            <SourceComparison sourceComparison={result.source_comparison} />
            {result.contradictions.length > 0 && (
              <ContradictionDetector contradictions={result.contradictions} />
            )}
          </div>
        </div>
      )}

      {activeTab === "evidence" && (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
          <EvidenceCards evidence={result.evidence} />
        </div>
      )}

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

/* ─── Root page ─── */
export default function Page() {
  const [step, setStep] = useState<"search" | "prefs" | "loading" | "results">("search");
  const [product, setProduct] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = (p: string) => { setProduct(p); setStep("prefs"); };

  const handleAnalyze = async (prefs: Preferences, pasted: string) => {
    setStep("loading");
    setError(null);
    try {
      const req: AnalyzeRequest = {
        product_name: product,
        pasted_reviews: pasted || undefined,
        preferences: prefs,
      };
      const res = await analyzeProduct(req);
      setResult(res);
      setStep("results");
    } catch (e: any) {
      setError(e.message ?? "Something went wrong");
      setStep("prefs");
    }
  };

  const handleReset = () => { setStep("search"); setProduct(""); setResult(null); setError(null); };

  return (
    <main style={{ minHeight: "100vh" }}>
      {step === "search"  && <SearchStep onNext={handleSearch} />}
      {step === "prefs"   && <PreferencesStep product={product} onBack={() => setStep("search")} onAnalyze={handleAnalyze} error={error} />}
      {step === "loading" && <LoadingStep product={product} />}
      {step === "results" && result && <DashboardStep result={result} onReset={handleReset} />}
    </main>
  );
}
