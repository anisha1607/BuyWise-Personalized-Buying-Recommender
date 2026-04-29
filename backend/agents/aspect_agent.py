import re
from typing import List, Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Keywords that are long/specific enough to match as substrings safely
ASPECT_KEYWORDS: Dict[str, List[str]] = {
    "comfort":      ["comfort", "comfortable", "cushion", "padding", "clamp", "lightweight", "ergon",
                     "soft", "tight", "weight", "fit", "wear"],
    "price":        ["price", "cost", "expensive", "cheap", "value", "worth", "money", "afford",
                     "budget", "overpriced", "deal", "sale"],
    "battery":      ["battery", "charge", "charging", "drain", "power", "standby", "quick charge",
                     "hours", "battery life", "battery health"],
    "sound":        ["sound", "audio", "bass", "treble", "music", "equalizer", "eq", "frequency",
                     "hz", "soundstage", "instrumental", "vocals", "vocal"],
    "durability":   ["durable", "durability", "build quality", "material", "metal", "sturdy",
                     "fragile", "break", "crack", "plastic"],
    "performance":  ["performance", "anc", "noise cancel", "noise cancell", "microphone", "mic",
                     "call quality", "speed", "lag", "latency"],
    "design":       ["design", "aesthetic", "style", "color", "finish", "sleek", "bulky",
                     "elegant", "foldable", "compact", "look"],
    "connectivity": ["bluetooth", "connect", "wifi", "wireless", "pairing", "pair", "nfc",
                     "multipoint", "usb", "signal", "drop"],
}

# Short/ambiguous keywords that need word-boundary matching to avoid false positives
# e.g. "life" would match "lifesaver", "build" would match "building"
_WORD_BOUNDARY_KEYWORDS: Dict[str, List[str]] = {
    "comfort":      ["soft", "tight", "fit", "wear", "weight"],
    "battery":      ["hours", "life"],
    "sound":        ["quality"],
    "durability":   ["plastic", "break", "material"],
    "performance":  ["call", "speed", "lag"],
    "design":       ["look", "style", "compact"],
    "connectivity": ["drop", "signal", "connect"],
}

# Negative signal words for keyword-based fallback (used in eda_agent)
NEGATIVE_SIGNAL_WORDS = [
    "not ", "issue", "problem", "poor", "fail", "buggy", "crack", "unreliable",
    "too expensive", "overpriced", "disappointing", "uncomfortable", "worse",
    "terrible", "horrible", "broken", "weak", "lacks", "limited", "drops",
    "degrades", "difficult", "struggle", "hard to", "awkward",
]

_analyzer = SentimentIntensityAnalyzer()
# Boost scores for specific product review terms
_analyzer.lexicon.update({
    'steal': 4.0,
    'outstanding': 3.5,
    'best-in-class': 4.0,
    'flawlessly': 3.5,
    'incredible': 3.0,
    'stunning': 3.0,
    'impressive': 2.5,
    'solid': 2.0,
    'quick charge': 2.0,
    'minimal': 1.0,
    'stays': 1.0,
})


def _matches_aspect(sl: str, aspect: str, keywords: List[str]) -> bool:
    """Check if sentence matches aspect keywords using word-boundary for ambiguous terms."""
    boundary_kws = _WORD_BOUNDARY_KEYWORDS.get(aspect, [])
    for kw in keywords:
        if kw in boundary_kws:
            # Use word-boundary regex to avoid false substring matches
            if re.search(r'\b' + re.escape(kw) + r'\b', sl):
                return True
        else:
            # Multi-word phrases or specific enough terms: substring is fine
            if kw in sl:
                return True
    return False


def analyze_aspects(reviews: List[Dict]) -> Dict[str, Dict]:
    buckets: Dict[str, Dict] = {a: {"sentiments": [], "snippets": []} for a in ASPECT_KEYWORDS}

    for review in reviews:
        text = review.get("text", "")
        # Calculate overall sentiment for the review and save it
        review["sentiment_score"] = _analyzer.polarity_scores(text)["compound"]

        sentences = [s.strip() for s in text.replace(". ", ".|").split("|") if len(s.strip()) > 5]

        added_snippets: Dict[str, set] = {a: set() for a in ASPECT_KEYWORDS}

        for sentence in sentences:
            sl = sentence.lower()

            for aspect, keywords in ASPECT_KEYWORDS.items():
                if sl in added_snippets[aspect]:
                    continue

                if not _matches_aspect(sl, aspect, keywords):
                    continue

                score = _analyzer.polarity_scores(sentence)["compound"]

                # Manual Overrides for common False Negatives
                pos_patterns = ["without needing", "no lag", "minimal drain", "worth every penny",
                                 "steal", "rock solid", "no issue"]
                if any(p in sl for p in pos_patterns):
                    score += 0.4

                # Boost battery mentions with durations (e.g., "5 days", "30 hours")
                if aspect == "battery" and any(d in sl for d in ["day", "hour", "week"]):
                    if any(char.isdigit() for char in sl):
                        score += 0.3

                buckets[aspect]["sentiments"].append(score)
                if len(buckets[aspect]["snippets"]) < 10:
                    buckets[aspect]["snippets"].append({
                        "text": sentence,
                        "score": round(score, 3),
                        "source": review.get("source", "Unknown"),
                        "source_name": review.get("source_name", review.get("source", "Unknown").title()),
                        "source_type": review.get("source_type", "Review"),
                        "url": review.get("url", ""),
                        "title": review.get("title", ""),
                    })
                    added_snippets[aspect].add(sl)

    result: Dict[str, Dict] = {}
    for aspect, data in buckets.items():
        sents = data["sentiments"]
        if sents:
            result[aspect] = {
                "avg_sentiment": round(sum(sents) / len(sents), 3),
                "mention_count": len(sents),
                "snippets": data["snippets"],
            }
        else:
            result[aspect] = {"avg_sentiment": 0.0, "mention_count": 0, "snippets": []}

    return result
