from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class Preferences(BaseModel):
    budget: str = "mid"
    use_case: str = "everyday"
    aspect_priorities: Dict[str, str] = {}
    deal_breakers: List[str] = []

class Competitor(BaseModel):
    name: str
    link: str
    description: str
    pros: List[str]
    cons: List[str]

class MarketIntelligence(BaseModel):
    competitors: List[Competitor]
    value_badge: str  # "Great Value" | "Fair Price" | "Premium" | "Overpriced"
    release_status: str
    sentiment_trend: str  # "improving" | "stable" | "declining"
    value_score: float

class ScoreComponent(BaseModel):
    label: str
    score: float
    max_score: float
    weight_pct: int
    contribution: float

class ScoreBreakdown(BaseModel):
    components: List[ScoreComponent]
    overall_explanation: str

class AnalyzeRequest(BaseModel):
    product_name: str
    pasted_reviews: Optional[str] = None
    youtube_ids: Optional[List[str]] = None
    preferences: Preferences

class AnalyzeResponse(BaseModel):
    product: str
    fit_score: float
    verdict: List[str]
    hypothesis: str
    aspect_summary: Dict[str, Any]
    source_comparison: Dict[str, Any]
    contradictions: List[Dict]
    pros: List[str]
    cons: List[str]
    evidence: List[Dict]
    preference_vs_reality: List[Dict]
    deal_breaker_flags: List[str]
    review_count: int
    market_intelligence: MarketIntelligence
    score_breakdown: ScoreBreakdown
    critical_take: List[str] = []
    trade_offs: List[Dict] = []
    raw_reviews: List[Dict] = []

class ChatRequest(BaseModel):
    product_name: str
    question: str
    aspect_summary: Dict[str, Any]
    pros: List[str] = []
    cons: List[str] = []
    verdict: List[str] = []
    evidence: List[Dict] = []

class ChatResponse(BaseModel):
    answer: str
    source: str = "ai"

class ExportRequest(BaseModel):
    format: str = "json"
    data: Dict[str, Any]
