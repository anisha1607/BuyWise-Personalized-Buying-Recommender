import os
import json
import httpx
from groq import Groq
import re
from typing import Dict, Any, Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_TOKEN = os.getenv("HF_TOKEN")  # User should provide this in .env if needed

# Configuration
PRIMARY_MODEL = "llama-3.1-8b-instant" # Groq version of Grok-like power
HF_FALLBACK_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

def get_llm_response(prompt: str, schema: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    Central LLM handler with strict Grok -> HuggingFace fallback policy.
    Logs model usage and failure reasons.
    """
    
    # 1. Try Primary LLM (Groq/Grok)
    if GROQ_API_KEY:
        try:
            print(f"[LLMService] Attempting Primary LLM (Groq: {PRIMARY_MODEL})...")
            client = Groq(api_key=GROQ_API_KEY)
            
            completion_params = {
                "model": PRIMARY_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            }
            if schema:
                completion_params["response_format"] = {"type": "json_object"}
            
            res = client.chat.completions.create(**completion_params)
            content = res.choices[0].message.content
            
            try:
                data = json.loads(content)
                print(f"[LLMService] SUCCESS: Primary LLM ({PRIMARY_MODEL}) used.")
                return data
            except json.JSONDecodeError:
                print(f"[LLMService] FAILURE: Primary LLM returned invalid JSON.")
        except Exception as e:
            print(f"[LLMService] FAILURE: Primary LLM error: {e}")
    else:
        print("[LLMService] WARNING: GROQ_API_KEY not found.")

    # 2. Try Fallback LLM (HuggingFace)
    print(f"[LLMService] Attempting Fallback LLM (HuggingFace: {HF_FALLBACK_MODEL})...")
    try:
        # Construct a prompt that strongly enforces JSON output for models without native JSON mode
        hf_prompt = f"{prompt}\n\nSTRICT REQUIREMENT: Return ONLY valid JSON. No conversational filler."
        
        headers = {}
        if HF_API_TOKEN:
            headers["Authorization"] = f"Bearer {HF_API_TOKEN}"
        
        api_url = f"https://api-inference.huggingface.co/models/{HF_FALLBACK_MODEL}"
        
        with httpx.Client(timeout=30.0) as client:
            # Note: HF Inference API 'inputs' field. 
            # Some models use different schemas, but /models/ID usually takes {"inputs": "..."}
            response = client.post(
                api_url,
                json={"inputs": hf_prompt, "parameters": {"max_new_tokens": 1000}},
                headers=headers
            )
            
            if response.status_code == 200:
                raw_res = response.json()
                # HF Inference API often returns a list of completions
                if isinstance(raw_res, list) and len(raw_res) > 0:
                    text = raw_res[0].get("generated_text", "")
                elif isinstance(raw_res, dict):
                    text = raw_res.get("generated_text", "")
                else:
                    text = str(raw_res)

                # Try to extract JSON if it's wrapped in markdown or filler
                json_match = re.search(r'(\{.*\})', text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                
                data = json.loads(text)
                print(f"[LLMService] SUCCESS: Fallback LLM ({HF_FALLBACK_MODEL}) used.")
                return data
            else:
                print(f"[LLMService] FAILURE: HuggingFace API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[LLMService] FAILURE: Fallback LLM error: {e}")

    print("[LLMService] CRITICAL FAILURE: All LLM providers failed.")
    return None

