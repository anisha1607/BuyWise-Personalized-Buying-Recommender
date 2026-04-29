import httpx
import re
from typing import List, Dict

def search_web_snippets(query: str) -> str:
    """
    Performs a quick search on DuckDuckGo and returns a text blob of snippets.
    """
    url = f"https://duckduckgo.com/html/?q={query}+reviews"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    
    try:
        with httpx.Client(headers=headers, timeout=10.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                # Basic regex to pull out result snippets from DDG HTML
                snippets = re.findall(r'class="result__snippet".*?>(.*?)</a>', resp.text, re.S)
                return " ".join(snippets[:10])
    except Exception as e:
        print(f"Web Search Error: {e}")
    return ""
