import hashlib
from typing import List, Dict
from datetime import datetime

SOURCE_MAP = {
    "amazon": "Amazon",
    "bestbuy": "BestBuy",
    "best_buy": "BestBuy",
    "youtube": "YouTube",
    "personal": "Personal",
    "pasted": "Personal",
    "unknown": "Unknown",
}

MIN_WORDS = 8
MAX_WORDS = 800


def _word_count(text: str) -> int:
    return len(text.split())


def _normalize_rating(rating) -> float:
    try:
        r = float(rating)
    except (TypeError, ValueError):
        return 3.0
    if r > 5:
        r = r / 2.0  # Convert 10-point scale (e.g. BestBuy API) to 5-point scale
    return max(1.0, min(5.0, r))


def _normalize_date(date_str: str) -> str:
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y"]:
        try:
            return datetime.strptime(str(date_str), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d")


def clean_reviews(reviews: List[Dict]) -> List[Dict]:
    seen: set = set()
    cleaned: List[Dict] = []

    for review in reviews:
        text = str(review.get("text", "")).strip()
        if not text:
            continue
        if not (MIN_WORDS <= _word_count(text) <= MAX_WORDS):
            continue

        h = hashlib.md5(text.lower().encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)

        source_raw = str(review.get("source", "unknown")).lower()
        cleaned.append({
            "source": SOURCE_MAP.get(source_raw, "Unknown"),
            "product": str(review.get("product", "")),
            "rating": _normalize_rating(review.get("rating", 3.0)),
            "text": text,
            "date": _normalize_date(str(review.get("date", ""))),
        })

    return cleaned
