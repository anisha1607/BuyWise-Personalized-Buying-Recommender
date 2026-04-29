import os
import json
from groq import Groq
from typing import List, Dict, Any

def analyze_tradeoffs(hypothesis: str, aspect_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Acts as a Devil's Advocate, testing the hypothesis and identifying real trade-offs.
    """
    aspect_data = {a: {"score": d["avg_sentiment"], "mentions": d["mention_count"]} for a, d in aspect_summary.items()}
    
    prompt = f"""
    Act as a skeptical Critical Analysis Agent for a product review system.
    
    Main Hypothesis: {hypothesis}
    Data Summary: {aspect_data}
    
    Your goal is to be the 'Devil's Advocate'. 
    - CRITICAL TAKE: Identify one specific weakness or contradiction in the main hypothesis. 
    - TRADE-OFFS: Identify EXACTLY 3 specific trade-offs using the format "Benefit vs. Sacrifice".
    
    Format your response as JSON:
    {{
        "critical_take": "One clear paragraph (max 40 words) starting with 'The catch is...' or 'However...'",
        "trade_offs": [
            {{"label": "Benefit vs. Sacrifice", "description": "Brief explanation..."}},
            {{"label": "Benefit vs. Sacrifice", "description": "Brief explanation..."}},
            {{"label": "Benefit vs. Sacrifice", "description": "Brief explanation..."}}
        ]
    }}
    """
    
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"Critical Agent Error: {e}")
        return {
            "critical_take": "The analysis is stable, but remember that individual units can vary in quality.",
            "trade_offs": [{"label": "Price vs. Features", "description": "Premium features come at a premium cost."}]
        }
