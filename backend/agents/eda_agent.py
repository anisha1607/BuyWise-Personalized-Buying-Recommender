import statistics
from typing import List, Dict, Any

from agents.aspect_agent import NEGATIVE_SIGNAL_WORDS

# Sources we always expect — shown in chart even if no data collected
KNOWN_SOURCES = ["Amazon", "BestBuy", "YouTube"]


def source_comparison(reviews: List[Dict], aspect_summary: Dict) -> Dict[str, Any]:
    source_data: Dict[str, List[float]] = {}

    # Pre-populate known sources so they always appear in the chart
    for src in KNOWN_SOURCES:
        source_data[src] = []

    for review in reviews:
        # Prefer the rich source_name if available
        source = review.get("source_name", review.get("source", "External Review Source"))
        if not source or source.lower() in ["unknown", "other", ""]:
            if review.get("source") == "Personal":
                source = "Personal"
            else:
                source = "External Review Source"
                
        # Normalize casing to prevent duplication (e.g. 'amazon' and 'Amazon')
        # We check against known sources to keep exact casing, otherwise title case.
        matched_known = next((ks for ks in KNOWN_SOURCES if ks.lower() == source.lower()), None)
        source = matched_known if matched_known else source.title()

        # Use sentiment_score if available (set by analyze_aspects), otherwise normalize rating
        score = review.get("sentiment_score")
        if score is None:
            score = (float(review.get("rating", 3.0)) - 3.0) / 2.0

        source_data.setdefault(source, []).append(score)

    result = {}
    for src, scores in source_data.items():
        if scores:
            result[src] = {
                "avg_sentiment": round(sum(scores) / len(scores), 3),
                "review_count": len(scores),
            }
        else:
            # Show the source with 0 reviews so the chart slot is visible
            result[src] = {
                "avg_sentiment": 0.0,
                "review_count": 0,
            }

    return result


def detect_contradictions(aspect_summary: Dict) -> List[Dict]:
    contradictions = []
    
    MIN_SIGNALS = 2 # Configurable threshold for mixed reviews
    
    for aspect, data in aspect_summary.items():
        snippets = data.get("snippets", [])
        if len(snippets) < (MIN_SIGNALS * 2):
            continue
            
        pos = [s["text"] for s in snippets if s["score"] > 0.1]
        neg = [s["text"] for s in snippets if s["score"] < -0.05]
        
        # Mixed reviews require BOTH positive and negative signals passing the threshold
        if len(pos) >= MIN_SIGNALS and len(neg) >= MIN_SIGNALS:
            contradictions.append({
                "aspect": aspect,
                "positive_samples": pos[:2],
                "negative_samples": neg[:2],
                "message": f"Mixed reviews detected because users praise the {aspect} but complain about it in other scenarios.",
            })
            
    return contradictions


def top_pros_cons(aspect_summary: Dict, n: int = 5) -> Dict[str, List[str]]:
    all_snippets = []
    for data in aspect_summary.values():
        all_snippets.extend(data.get("snippets", []))
    all_snippets.sort(key=lambda x: x["score"], reverse=True)

    # ── Pros ──
    pros = []
    seen_pros = set()
    for s in all_snippets:
        if s["score"] > 0.3 and s["text"] not in seen_pros:
            pros.append(s["text"])
            seen_pros.add(s["text"])
            if len(pros) >= n:
                break

    # ── Cons: lower threshold to -0.05 to catch VADER-scored-zero negatives ──
    cons = []
    seen_cons = set()
    for s in sorted(all_snippets, key=lambda x: x["score"]):
        if s["score"] < -0.05 and s["text"] not in seen_cons:
            cons.append(s["text"])
            seen_cons.add(s["text"])
            if len(cons) >= n:
                break

    # ── Keyword-based fallback if too few cons found ──
    if len(cons) < 3:
        for s in all_snippets:
            if s["text"] in seen_cons:
                continue
            sl = s["text"].lower()
            if any(neg in sl for neg in NEGATIVE_SIGNAL_WORDS):
                cons.append(s["text"])
                seen_cons.add(s["text"])
                if len(cons) >= n:
                    break

    return {"pros": pros, "cons": cons}
