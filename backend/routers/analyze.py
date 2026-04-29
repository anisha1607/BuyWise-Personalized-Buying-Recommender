import os
import json
from groq import Groq
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from agents.preference_agent import get_weights
from agents.data_collection_agent import collect_reviews
from agents.cleaning_agent import clean_reviews
from agents.aspect_agent import analyze_aspects
from agents.eda_agent import source_comparison, detect_contradictions, top_pros_cons
from agents.personalization_agent import calculate_fit_score
from agents.explanation_agent import generate_explanation
from agents.critical_agent import analyze_tradeoffs
from agents.expert_agent import get_expert_reviews, get_tiktok_links

router = APIRouter()


class Preferences(BaseModel):
    budget: str = "mid"
    use_case: str = "everyday"
    aspect_priorities: Dict[str, str] = {}
    deal_breakers: List[str] = []


class AnalyzeRequest(BaseModel):
    product_name: str
    pasted_reviews: Optional[str] = None
    youtube_ids: Optional[List[str]] = None
    preferences: Preferences


class AnalyzeResponse(BaseModel):
    product: str
    fit_score: float
    verdict: str
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
    expert_reviews: List[Dict] = []
    tiktok_links: List[Dict] = []
    radar_data: List[Dict] = []
    critical_take: str = ""
    trade_offs: List[Dict] = []


class ChatRequest(BaseModel):
    product_name: str
    question: str
    aspect_summary: Dict[str, Any]

class ChatResponse(BaseModel):
    answer: str

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    prefs_dict = request.preferences.dict()

    weights = get_weights(prefs_dict)

    raw_reviews = collect_reviews(
        product_name=request.product_name,
        pasted_reviews=request.pasted_reviews,
        youtube_ids=request.youtube_ids,
    )

    reviews = clean_reviews(raw_reviews)

    if not reviews:
        # Fallback to AI General Knowledge if scrapers fail
        def generate_market_consensus(product):
            prompt = f"Provide a brief market consensus for {product}. List 3 pros, 3 cons, and a 1-sentence hypothesis. Return as JSON."
            try:
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                import json
                return json.loads(res.choices[0].message.content)
            except:
                return {"pros": ["High Quality"], "cons": ["Expensive"], "hypothesis": "A well-regarded product in its category."}
        
        consensus = generate_market_consensus(request.product_name)
        return AnalyzeResponse(
            product=request.product_name,
            fit_score=65.0,
            verdict=f"We couldn't find live reviews for '{request.product_name}' right now, so here is the general market consensus.",
            hypothesis=consensus.get("hypothesis", "A highly anticipated or established product."),
            aspect_summary={"general": {"avg_sentiment": 0.3, "mention_count": 10, "snippets": []}},
            source_comparison={"Web Consensus": {"avg_sentiment": 0.3, "review_count": 5}},
            contradictions=[],
            pros=consensus.get("pros", ["Great Performance", "Sleek Design", "Good Resale Value"]),
            cons=consensus.get("cons", ["Premium Pricing", "Limited Port Selection", "Thermal Throttling"]),
            evidence=[],
            preference_vs_reality=[],
            deal_breaker_flags=[],
            review_count=0,
            critical_take="Note: This analysis is based on general market consensus because live scrapers were rate-limited.",
            trade_offs=[{"label": "Reliability vs. Recency", "description": "This uses industry knowledge rather than live 24-hour feedback."}]
        )

    aspect_summary = analyze_aspects(reviews)
    src_comparison = source_comparison(reviews, aspect_summary)
    contradictions = detect_contradictions(aspect_summary)
    pros_cons = top_pros_cons(aspect_summary)

    personalization = calculate_fit_score(
        aspect_summary=aspect_summary,
        weights=weights,
        deal_breakers=prefs_dict.get("deal_breakers", []),
    )

    top_snippets = pros_cons["pros"][:3] + pros_cons["cons"][:2]
    explanation = generate_explanation(
        product=request.product_name,
        user_preferences=prefs_dict,
        fit_score=personalization["fit_score"],
        aspect_summary=aspect_summary,
        top_evidence=top_snippets,
    )

    # Filter out or label unknown sources to prevent 'Unknown' bar in chart
    valid_reviews = []
    for r in reviews:
        if not r.get("source") or r["source"].lower() == "unknown":
            r["source"] = "Other"
        valid_reviews.append(r)
    reviews = valid_reviews

    evidence = []
    for aspect, data in aspect_summary.items():
        for snippet in data.get("snippets", [])[:10]:
            src = snippet.get("source", "Other")
            if src.lower() == "unknown": src = "Other"
            evidence.append({
                "aspect": aspect,
                "text": snippet["text"],
                "score": snippet["score"],
                "source": src,
                "sentiment": "positive" if snippet["score"] > 0.15 else ("negative" if snippet["score"] < -0.1 else "neutral"),
            })
    
    # Filter out duplicates
    unique_evidence = []
    seen = set()
    for ev in evidence:
        if ev["text"] not in seen:
            unique_evidence.append(ev)
            seen.add(ev["text"])
    evidence = unique_evidence
    fit_score = personalization["fit_score"]

    # AI-Generated Personalized Verdict
    def generate_personalized_verdict(product, use_case, fit_score, aspect_summary, personal_notes):
        prompt = f"""
        Act as a professional shopping consultant.
        Product: {product}
        Use Case: {use_case}
        Fit Score: {fit_score}/100
        Aspect Sentiment: { {a: d['avg_sentiment'] for a, d in aspect_summary.items()} }
        Personal Recommendations from Friends/Family: {personal_notes if personal_notes else "None provided."}

        Write a 2-3 sentence 'Fit Analysis' for the user. 
        - DO NOT include introductory filler like "Here is the analysis" or "Based on your data". Start directly with the first point.
        - STRICT RULE: Do NOT include raw numbers like "0.163" or decimal scores.
        - STRUCTURE: 
          1. **The Bottom Line:** Clear opening.
          2. **Inner Circle vs. Web:** Compare Dad/Sister etc with the consensus.
          3. **The Sacrifice:** Mention the main trade-off.
        - Speak like a professional consultant.
        - Keep it brief (max 55 words).
        """
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            res = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()
        except:
            return f"A solid fit score of {fit_score}/100 for your {use_case} needs. It generally performs well, but keep your personal priorities in mind."

    verdict = generate_personalized_verdict(
        request.product_name, 
        request.preferences.use_case, 
        fit_score, 
        aspect_summary, 
        request.pasted_reviews
    )

    # Run Critical Agent
    critical_data = analyze_tradeoffs(explanation["hypothesis"], aspect_summary)

    return AnalyzeResponse(
        product=request.product_name,
        fit_score=fit_score,
        verdict=verdict,
        hypothesis=explanation["hypothesis"],
        aspect_summary=aspect_summary,
        source_comparison=src_comparison,
        contradictions=contradictions,
        pros=pros_cons["pros"],
        cons=pros_cons["cons"],
        evidence=evidence,
        preference_vs_reality=personalization["preference_vs_reality"],
        deal_breaker_flags=personalization["deal_breaker_flags"],
        review_count=len(reviews),
        critical_take=critical_data.get("critical_take", ""),
        trade_offs=critical_data.get("trade_offs", []),
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    import os
    from groq import Groq
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return ChatResponse(answer="I need a GROQ_API_KEY to answer that. Please add one to your .env file!")

    client = Groq(api_key=api_key)
    
    # Prepare the context from aspect summary
    context = ""
    for aspect, data in request.aspect_summary.items():
        snippets = [s['text'] for s in data.get('snippets', [])[:3]]
        context += f"\nAspect: {aspect}\nSentiments: {', '.join(snippets)}\n"

    prompt = f"""
    You are BuyWise AI, a dedicated product research assistant. 
    STRICT RULE: Only answer questions related to {request.product_name} or relevant product comparisons.
    If the user asks an unrelated question (e.g., jokes, general knowledge, or personal tasks), politely decline and state that you are here to help them research {request.product_name}.
    
    Use the following review data:
    {context}
    
    User Question: {request.question}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )
        return ChatResponse(answer=completion.choices[0].message.content)
    except Exception as e:
        return ChatResponse(answer=f"Error connecting to AI: {str(e)}")
