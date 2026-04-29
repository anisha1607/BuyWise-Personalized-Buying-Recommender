from typing import List, Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ASPECT_KEYWORDS: Dict[str, List[str]] = {
    "comfort":      ["comfort", "comfortable", "cushion", "padding", "fit", "soft", "tight", "clamp", "lightweight", "weight", "wear", "ergon"],
    "price":        ["price", "cost", "expensive", "cheap", "value", "worth", "money", "afford", "budget", "overpriced", "deal", "sale"],
    "battery":      ["battery", "charge", "charging", "hours", "drain", "power", "standby", "life", "quick charge"],
    "sound":        ["sound", "audio", "bass", "treble", "music", "quality", "equalizer", "eq", "frequency", "hz", "soundstage", "instrument", "vocal"],
    "durability":   ["durable", "durability", "build", "material", "plastic", "metal", "sturdy", "fragile", "break", "crack"],
    "performance":  ["performance", "anc", "noise cancel", "microphone", "mic", "call", "speed", "lag", "feature", "function"],
    "design":       ["design", "look", "aesthetic", "style", "color", "finish", "sleek", "bulky", "premium", "elegant", "fold", "compact"],
    "connectivity": ["bluetooth", "connect", "wifi", "wireless", "pairing", "pair", "nfc", "usb", "multipoint", "range", "drop", "signal"],
}

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


def analyze_aspects(reviews: List[Dict]) -> Dict[str, Dict]:
    buckets: Dict[str, Dict] = {a: {"sentiments": [], "snippets": []} for a in ASPECT_KEYWORDS}

    for review in reviews:
        text = review.get("text", "")
        # Calculate overall sentiment for the review and save it
        review["sentiment_score"] = _analyzer.polarity_scores(text)["compound"]
        
        sentences = [s.strip() for s in text.replace(". ", ".|").split("|") if len(s.strip()) > 5]

        added_snippets = set()
        for sentence in sentences:
            sl = sentence.lower()
            if sl in added_snippets:
                continue
                
            for aspect, keywords in ASPECT_KEYWORDS.items():
                if any(kw in sl for kw in keywords):
                    score = _analyzer.polarity_scores(sentence)["compound"]
                    
                    # Manual Overrides for common False Negatives
                    pos_patterns = ["without needing", "no lag", "minimal drain", "worth every penny", "steal", "rock solid"]
                    if any(p in sl for p in pos_patterns):
                        score += 0.4
                    
                    # Boost battery mentions with durations (e.g., "5 days", "30 hours")
                    if aspect == "battery" and any(d in sl for d in ["day", "hour", "week"]):
                        # If there's a number nearby, it's likely a positive duration
                        if any(char.isdigit() for char in sl):
                            score += 0.3

                    buckets[aspect]["sentiments"].append(score)
                    if len(buckets[aspect]["snippets"]) < 10:
                        buckets[aspect]["snippets"].append({
                            "text": sentence,
                            "score": round(score, 3),
                            "source": review.get("source", "Unknown"),
                        })
                        added_snippets.add(sl)

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
