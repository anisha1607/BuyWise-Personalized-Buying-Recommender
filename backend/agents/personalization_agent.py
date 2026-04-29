from typing import Dict, List, Any

DEAL_BREAKER_PENALTY = 8.0  # points per triggered deal breaker


def calculate_fit_score(
    aspect_summary: Dict,
    weights: Dict[str, float],
    deal_breakers: List[str],
) -> Dict[str, Any]:
    total_weight = 0.0
    weighted_score = 0.0
    preference_vs_reality = []
    deal_breaker_flags = []

    for aspect, weight in weights.items():
        data = aspect_summary.get(aspect, {})
        sentiment = data.get("avg_sentiment", 0.0)
        mention_count = data.get("mention_count", 0)

        aspect_score = (sentiment + 1) * 50  # map [-1,1] → [0,100]
        weighted_score += aspect_score * weight
        total_weight += weight

        if weight >= 0.8:
            priority = "high"
        elif weight >= 0.5:
            priority = "medium"
        else:
            priority = "low"

        if sentiment > 0.1:
            reality = "positive"
        elif sentiment < -0.05:
            reality = "negative"
        else:
            reality = "mixed"

        preference_vs_reality.append({
            "aspect": aspect,
            "priority": priority,
            "weight": weight,
            "reality_score": round(aspect_score, 1),
            "reality_label": reality,
            "mention_count": mention_count,
        })

        if aspect in deal_breakers and sentiment < -0.05:
            deal_breaker_flags.append(
                f"Deal breaker triggered: {aspect} has negative sentiment ({sentiment:.2f})"
            )

    base_score = (weighted_score / total_weight) if total_weight > 0 else 50.0
    final_score = max(0.0, min(100.0, base_score - len(deal_breaker_flags) * DEAL_BREAKER_PENALTY))

    return {
        "fit_score": round(final_score, 1),
        "preference_vs_reality": preference_vs_reality,
        "deal_breaker_flags": deal_breaker_flags,
    }
