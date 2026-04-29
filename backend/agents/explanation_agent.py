import os
import json
from typing import Dict, Any, List

GROQ_MODEL = "llama-3.3-70b-versatile"


def generate_explanation(
    product: str,
    user_preferences: Dict,
    fit_score: float,
    aspect_summary: Dict,
    top_evidence: List[str],
) -> Dict[str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "verdict": f"{product} scores {fit_score:.0f}/100 for your use case based on {len(aspect_summary)} analyzed aspects.",
            "hypothesis": "Set GROQ_API_KEY in your .env to get AI-powered insights.",
        }

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        aspect_scores = {
            aspect: {
                "avg_sentiment": data.get("avg_sentiment", 0),
                "mention_count": data.get("mention_count", 0),
            }
            for aspect, data in aspect_summary.items()
        }

        prompt = f"""You are analyzing {product} for a user with the following preferences:
- Budget: {user_preferences.get("budget", "mid")}
- Use case: {user_preferences.get("use_case", "everyday")}
- Top priorities: {user_preferences.get("aspect_priorities", {})}
- Deal breakers: {user_preferences.get("deal_breakers", [])}

Computed fit score: {fit_score:.1f}/100

Aspect sentiment summary (avg_sentiment range: -1 to +1):
{json.dumps(aspect_scores, indent=2)}

Key evidence snippets:
{chr(10).join(f"- {e}" for e in top_evidence[:5])}

Respond with a JSON object containing exactly two keys:
1. "verdict": 1-2 sentences — direct recommendation (buy or not, and why)
2. "hypothesis": 1-2 sentences — a notable or surprising insight specific to this user's needs

Return only valid JSON, no markdown."""

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        return {
            "verdict": result.get("verdict", ""),
            "hypothesis": result.get("hypothesis", ""),
        }

    except Exception:
        return {
            "verdict": f"{product} achieves a fit score of {fit_score:.0f}/100 for your {user_preferences.get('use_case', 'everyday')} use case.",
            "hypothesis": f"Analysis is based on reviewer sentiment across {len(aspect_summary)} product aspects.",
        }
