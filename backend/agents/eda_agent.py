import statistics
from typing import List, Dict, Any


def source_comparison(reviews: List[Dict], aspect_summary: Dict) -> Dict[str, Any]:
    source_data: Dict[str, List[float]] = {}
    for review in reviews:
        source = review.get("source", "Other")
        if not source or source.lower() in ["unknown", "other"]:
            # If it was explicitly 'Personal', keep it
            if review.get("source") == "Personal":
                source = "Personal"
            else:
                source = "Other"
        
        # Use sentiment_score if available, otherwise normalize rating
        score = review.get("sentiment_score")
        if score is None:
            score = (float(review.get("rating", 3.0)) - 3.0) / 2.0
            
        source_data.setdefault(source, []).append(score)

    return {
        src: {
            "avg_sentiment": round(sum(scores) / len(scores), 3),
            "review_count": len(scores),
        }
        for src, scores in source_data.items()
    }


def detect_contradictions(aspect_summary: Dict) -> List[Dict]:
    contradictions = []
    for aspect, data in aspect_summary.items():
        snippets = data.get("snippets", [])
        if len(snippets) < 3:
            continue
        scores = [s["score"] for s in snippets]
        if len(scores) < 2:
            continue
        try:
            std = statistics.stdev(scores)
        except statistics.StatisticsError:
            continue
        if std > 0.4:
            pos = [s["text"] for s in snippets if s["score"] > 0.1][:2]
            neg = [s["text"] for s in snippets if s["score"] < -0.05][:2]
            contradictions.append({
                "aspect": aspect,
                "std": round(std, 3),
                "positive_samples": pos,
                "negative_samples": neg,
                "message": f"Reviewers are divided on {aspect} (σ={std:.2f})",
            })
    return contradictions


def top_pros_cons(aspect_summary: Dict, n: int = 5) -> Dict[str, List[str]]:
    all_snippets = []
    for data in aspect_summary.values():
        all_snippets.extend(data.get("snippets", []))
    all_snippets.sort(key=lambda x: x["score"], reverse=True)

    pros = []
    seen_pros = set()
    for s in all_snippets:
        if s["score"] > 0.3 and s["text"] not in seen_pros:
            pros.append(s["text"])
            seen_pros.add(s["text"])
            if len(pros) >= n: break

    cons = []
    seen_cons = set()
    for s in sorted(all_snippets, key=lambda x: x["score"]):
        if s["score"] < -0.1 and s["text"] not in seen_cons:
            cons.append(s["text"])
            seen_cons.add(s["text"])
            if len(cons) >= n: break

    return {"pros": pros, "cons": cons}
