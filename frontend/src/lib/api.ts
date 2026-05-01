export interface Preferences {
  budget: "low" | "mid" | "high";
  use_case: string;
  aspect_priorities: Record<string, "high" | "medium" | "low">;
  deal_breakers: string[];
}

export interface AnalyzeRequest {
  product_name: string;
  pasted_reviews?: string;
  youtube_ids?: string[];
  preferences: Preferences;
}

export interface AspectData {
  avg_sentiment: number;
  mention_count: number;
  snippets: Array<{ text: string; score: number; source: string }>;
}

export interface SourceData {
  avg_sentiment: number;
  review_count: number;
  estimated?: boolean;
}

export interface Contradiction {
  aspect: string;
  std: number;
  positive_samples: string[];
  negative_samples: string[];
  message: string;
}

export interface Evidence {
  claim: string;
  evidence_snippet: string;
  source_name: string;
  source_type: string;
  source_url: string;
  sentiment: "positive" | "negative" | "neutral";
  supports: "pros" | "cons" | "verdict" | "verification";
  estimated?: boolean;
}

export interface PrefVsReality {
  aspect: string;
  priority: string;
  weight: number;
  reality_score: number;
  reality_label: string;
  mention_count: number;
}

export interface MarketIntelligence {
  competitors: Array<{
    name: string;
    link: string;
    description: string;
    pros: string[];
    cons: string[];
  }>;
  value_badge: "Great Value" | "Fair Price" | "Premium" | "Overpriced";
  value_score: number;
  release_status: string;
  sentiment_trend: "improving" | "stable" | "declining";
}

export interface ScoreComponent {
  label: string;
  score: number;
  max_score: number;
  weight_pct: number;
  contribution: number;
}

export interface ScoreBreakdown {
  components: ScoreComponent[];
  overall_explanation: string;
}

export interface AnalyzeResponse {
  product: string;
  fit_score: number;
  verdict: string[];
  hypothesis: string;
  aspect_summary: Record<string, AspectData>;
  source_comparison: Record<string, SourceData>;
  contradictions: Contradiction[];
  pros: string[];
  cons: string[];
  evidence: Evidence[];
  preference_vs_reality: PrefVsReality[];
  deal_breaker_flags: string[];
  review_count: number;
  market_intelligence: MarketIntelligence;
  score_breakdown: ScoreBreakdown;
  expert_reviews: Array<{ source: string; title: string; url: string; snippet: string }>;
  tiktok_links: Array<{ url: string; label: string }>;
  radar_data: Array<{ aspect: string; score: number }>;
  critical_take: string[];
  trade_offs: Array<{ label: string; description: string }>;
  raw_reviews: Array<{ source: string; source_type: string; url: string; title: string; text: string; rating: number | string; date: string }>;
}

export async function askChat(
  product: string,
  question: string,
  summary: any,
  extras?: {
    pros?: string[];
    cons?: string[];
    verdict?: string;
    evidence?: any[];
  }
): Promise<string> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      product_name: product,
      question,
      aspect_summary: summary,
      pros: extras?.pros ?? [],
      cons: extras?.cons ?? [],
      verdict: extras?.verdict ?? "",
      evidence: extras?.evidence ?? [],
    }),
  });
  if (!res.ok) return "Sorry, I couldn't process that question.";
  const data = await res.json();
  return data.answer;
}

export async function analyzeProduct(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
  
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Analysis failed: ${err}`);
    }
    return res.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error("Analysis timed out. The product search is taking longer than usual, please try again in a moment.");
    }
    throw error;
  }
}

export async function exportData(data: AnalyzeResponse, format: "json" | "csv"): Promise<void> {
  const res = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, data }),
  });
  if (!res.ok) throw new Error("Export failed");
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `buywise_analysis.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}
