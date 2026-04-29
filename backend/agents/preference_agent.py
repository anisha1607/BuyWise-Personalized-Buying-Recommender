from typing import Dict, Any

ASPECTS = ["comfort", "price", "battery", "sound", "durability", "performance", "design", "connectivity"]

PRIORITY_WEIGHTS = {"high": 1.0, "medium": 0.6, "low": 0.2}

USE_CASE_BOOSTS: Dict[str, Dict[str, float]] = {
    "travel":    {"comfort": 0.3, "battery": 0.3, "connectivity": 0.2, "performance": 0.2},
    "work":      {"performance": 0.3, "connectivity": 0.3, "battery": 0.2, "sound": 0.1},
    "gaming":    {"performance": 0.4, "sound": 0.3, "connectivity": 0.2},
    "music":     {"sound": 0.5, "comfort": 0.2, "battery": 0.2},
    "everyday":  {"comfort": 0.2, "price": 0.2, "durability": 0.2, "battery": 0.2},
    "sports":    {"durability": 0.3, "comfort": 0.3, "connectivity": 0.2, "battery": 0.2},
}

BUDGET_PRICE_FLOOR = {"low": 0.8, "mid": 0.4, "high": 0.1}


def get_weights(preferences: Dict[str, Any]) -> Dict[str, float]:
    budget = preferences.get("budget", "mid")
    use_case = preferences.get("use_case", "everyday")
    aspect_priorities: Dict[str, str] = preferences.get("aspect_priorities", {})

    weights = {a: PRIORITY_WEIGHTS.get(aspect_priorities.get(a, "medium"), 0.6) for a in ASPECTS}

    for aspect, boost in USE_CASE_BOOSTS.get(use_case, {}).items():
        weights[aspect] = min(1.0, weights[aspect] + boost)

    weights["price"] = max(weights["price"], BUDGET_PRICE_FLOOR.get(budget, 0.4))

    max_w = max(weights.values()) or 1.0
    return {k: round(v / max_w, 3) for k, v in weights.items()}
