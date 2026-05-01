import random
from typing import List, Dict, Any
from agents.aspect_agent import ASPECT_KEYWORDS
from models import ScoreBreakdown, ScoreComponent, MarketIntelligence, Competitor

def calculate_fit_score(aspect_sentiments: Dict[str, float], preferences: Any) -> tuple:
    priority_map = preferences.aspect_priorities or {}
    deal_breakers = preferences.deal_breakers or []
    weight_values = {"high": 3.0, "medium": 1.5, "low": 0.5}
    
    total_weight = 0
    weighted_sentiment_sum = 0
    
    for aspect, sentiment in aspect_sentiments.items():
        priority = priority_map.get(aspect, "medium")
        w = weight_values.get(priority, 1.5)
        norm_sentiment = (sentiment + 1) / 2.0
        weighted_sentiment_sum += (norm_sentiment * w)
        total_weight += w

    base_fit_score = (weighted_sentiment_sum / total_weight * 100) if total_weight > 0 else 70.0
    
    penalties = 0
    deal_breaker_flags = []
    for db in deal_breakers:
        if aspect_sentiments.get(db, 0) < -0.1:
            penalties += 20
            deal_breaker_flags.append(db)
            
    fit_score = max(0, min(100, round(base_fit_score - penalties, 1)))
    return fit_score, base_fit_score, deal_breaker_flags

def generate_score_breakdown(base_fit_score: float, fit_score: float, reviews: List[Dict], value_score: float, priority_map: Dict) -> ScoreBreakdown:
    overall_polarity = sum(r.get("sentiment_score", 0) for r in reviews) / len(reviews) if reviews else (base_fit_score/100.0 * 2 - 1)
    
    high_priorities = [a for a, p in priority_map.items() if p == 'high']
    priority_text = f"prioritizing your interest in {', '.join(high_priorities[:2])}" if high_priorities else "analyzing overall quality"
    
    penalty_text = ""
    deduction = round(base_fit_score - fit_score, 1)
    if deduction >= 0.1:
        penalty_text = f" However, we applied a deduction of {deduction} points due to your identified deal-breakers being mentioned negatively in recent reviews."

    explanation = f"Your score of {fit_score} is calculated by {priority_text}.{penalty_text}"

    return ScoreBreakdown(
        components=[
            ScoreComponent(label="Feature Fit", score=round(base_fit_score/10.0, 1), max_score=10, weight_pct=50, contribution=round((base_fit_score/10.0) * 0.5, 1)),
            ScoreComponent(label="Sentiment Match", score=round((overall_polarity + 1) * 5, 1), max_score=10, weight_pct=30, contribution=round((overall_polarity + 1) * 5 * 0.3, 1)),
            ScoreComponent(label="Price Fit", score=value_score, max_score=10, weight_pct=20, contribution=round(value_score * 0.2, 1))
        ],
        overall_explanation=explanation
    )

def detect_release_status(product_name: str, reviews: List[Dict]) -> str:
    versions = ["M1", "M2", "M3", "M4", "GEN 1", "GEN 2", "GEN 3", "V1", "V2", "V3", "PRO", "MAX", "ULTRA", "2020", "2021", "2022", "2023", "2024", "2025"]
    found_versions = []
    text_to_scan = (product_name + " " + " ".join([r.get("text", "")[:50] for r in reviews[:10]])).upper()
    for v in versions:
        if v.upper() in text_to_scan:
            found_versions.append(v)
    
    if found_versions:
        latest_found = sorted(found_versions, key=lambda x: versions.index(x), reverse=True)[0]
        if latest_found.upper() in product_name.upper():
            return "Latest model"
        return f"Newer model available ({latest_found})"
    return "Latest version could not be verified."
