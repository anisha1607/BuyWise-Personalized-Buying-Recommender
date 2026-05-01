import httpx
import re
from typing import List, Dict

def search_web_snippets(query: str) -> str:
    """
    Performs a quick search on DuckDuckGo and returns a text blob of snippets.
    """
    # Use the /html/ endpoint which is more scraper-friendly than the JS version
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote(query)}+reviews"
    print(f"[Web Search] Attempting DDG Fallback: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        with httpx.Client(headers=headers, timeout=12.0, follow_redirects=True) as client:
            resp = client.get(url)
            print(f"[Web Search] Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                # DDG HTML snippets are usually inside <a class="result__snippet">...</a>
                # We use a more flexible regex to capture them
                snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.S)
                
                # Clean up HTML entities (like &amp; or &quot;)
                cleaned_snippets = []
                for s in snippets[:10]:
                    clean = re.sub(r'<[^>]+>', '', s) # Remove any nested tags
                    clean = clean.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")
                    cleaned_snippets.append(clean.strip())
                
                found_text = " ".join(cleaned_snippets)
                print(f"[Web Search] Found {len(cleaned_snippets)} snippets ({len(found_text)} chars).")
                return found_text
            else:
                print(f"[Web Search] DDG returned non-200 status. Content length: {len(resp.text)}")
    except Exception as e:
        print(f"[Web Search] Error during DDG scrape: {e}")
    
    return ""
